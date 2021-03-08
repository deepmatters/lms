from flask import render_template, redirect, url_for, flash, request
from app import app, db, mail
from app.forms import SignupForm, LoginForm, ForgetForm, PasswordChangeForm, PasswordResetForm, CourseForm, ModuleForm, TestQuestionForm, TestAnswerForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Course, Module, Test_question, Test_answer, Learner_progress, Learner_enrollment
from flask_mail import Message
import pymongo
import random
from datetime import datetime
from threading import Thread
import bisect
from PIL import Image, ImageDraw, ImageFont
import now_date_th_gen
import boto3
from pathlib import Path

@app.route('/')
def home():
    return render_template('home.html')

"""
Login and user sub-system
"""

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = SignupForm()

    if form.validate_on_submit():
        # Get data from form
        name = form.name.data
        email = form.email.data
        password = form.password.data
        password_check = form.password_check.data

        # Check if email already exist
        email_exist = User.query.filter_by(email=email).first()
        if email_exist:
            comment = f"อีเมล {email} เคยลงทะเบียนไว้แล้ว"   
            return render_template('signup-error.html', comment=comment)

        # Check if passwords match
        if password == password_check:
            password_final = password
        else:
            comment = "คุณพิมพ์รหัสผ่านสองช่องไม่ตรงกัน"
            return render_template('signup-error.html', comment=comment)

        # Create user with name, email, password
        new_user = User(name=name, email=email)
        new_user.set_password(password_final)
        db.session.add(new_user)
        db.session.commit()

        # Give confirmation, login, and redirect to profile page
        user = User.query.filter_by(email=form.email.data).first()
        login_user(user)
        flash("ลงทะเบียนสำเร็จ และล็อกอินเรียบร้อยแล้ว")
        return redirect('/profile')

    return render_template('signup.html', form=form)

# Function to send mail using thread
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

@app.route('/forget', methods=('GET', 'POST'))
def forget():
    form = ForgetForm()
    if form.validate_on_submit():
        # Get data from form
        email = form.email.data

        # Check if entered email is an existing user or not
        user = User.query.filter_by(email=email).first()
        if user is None:
            # Return comment and error type
            comment = "ไม่พบอีเมลที่กรอกในระบบสมาชิก"
            error_type = "wrong_email"
            return render_template('forget-result.html', comment=comment, error_type=error_type)
        # If email exists, proceed to password recovery process
        else:
            # Generate password_reset_id
            rand_universe = [1,2,3,4,5,6,7,8,9,"a","b","c","d","e","f","g","A","B","C","D","E","F","G"]
            rand_str = ""
            rand_list = random.sample(rand_universe, k=12)
            password_reset_id = rand_str.join([str(i) for i in rand_list])

            # Insert password_reset_id in db for this user
            user.password_reset_id = password_reset_id
            db.session.commit()

            # Send an email to user

            """
            !!! MUST CUSTOMISE MESSAGE BODY IN IMPLEMENTATION !!!
            """
            msg = Message(subject='[SoKru.org] รีเซ็ตรหัสผ่าน',
                  sender = 'support@cfapp.org',
                  recipients = [email])  # <<< CONFIGURE WEBSITE URL
            msg.body = ("คุณได้กดขอรหัสผ่านใหม่จากเว็บ SoKru.org กรุณากดลืงก์นี้ https://sokru.org/password-reset/" + password_reset_id + " เพื่อตั้งรหัสผ่านใหม่")  # <<< CONFIGURE EMAIL MESSAGE AND URL

            Thread(target=send_async_email, args=(app, msg)).start()  # Send mail asynchronously

            # Return comment
            comment = "เราได้ส่งคำแนะนำในการตั้งรหัสผ่านใหม่ไปยังอีเมลของท่านแล้ว"
            return render_template('forget-result.html', comment=comment)

    return render_template('forget.html', form=form)

# Password recovery API endpoint
@app.route('/password-reset/<string:password_reset_id>')
def password_reset(password_reset_id):
    # Check if password_reset_id is valid or not
    user = User.query.filter_by(password_reset_id=password_reset_id).first()
    if user is None:
        flash("ลิงก์รีเซ็ตรหัสผ่านไม่ผ่านการตรวจสอบ หรือได้ใช้ลิงก์นี้ไปแล้ว")
        return redirect('/')
    # If password_reset_id is valid, proceed to reset password
    else:
        form = PasswordResetForm()
        return render_template('password-reset.html', password_reset_id=password_reset_id, form=form)

@app.route('/password-reset-result', methods=('GET', 'POST'))
def password_reset_result():
    form = PasswordResetForm()

    if form.validate_on_submit():
        # Get data from form
        password_reset_id = form.password_reset_id.data
        password_new = form.password_new.data
        password_new_check = form.password_new_check.data

        # Get the user who belong to this password_reset_id
        user = User.query.filter_by(password_reset_id=password_reset_id).first()

        # Check if new passwords match each other
        if password_new != password_new_check:
            # Return comment and error type
            comment = "คุณพิมพ์รหัสผ่านสองช่องไม่ตรงกัน"
            error_type = "unmatched_password_check_reset"
            return render_template('password-change-result.html', comment=comment, error_type=error_type, password_reset_id=password_reset_id)
        # Proceed if passwords check passed
        else:
            # Generate new password hash
            user.set_password(password_new)

            # Update password_reset_id with blank string so the id can be used only this time only
            # and can't be used in API
            user.password_reset_id = ""
            db.session.commit()

            # Login user instantly
            login_user(user)
            flash("ล็อกอินเรียบร้อยแล้ว")

            # Return comment
            comment = "กรุณาใช้รหัสผ่านใหม่เมื่อล็อกอินครั้งถัดไป"
            return render_template('password-change-result.html', comment=comment)

    return render_template('password-change-result.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            return render_template('fail.html')
        
        login_user(user)

        # Update lastlogin_dt to the current time
        user.lastlogin_dt = datetime.now()
        db.session.commit()

        flash("ล็อกอินสำเร็จ")
        return redirect('/profile')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("ออกจากระบบเรียบร้อยแล้ว")
    return redirect(url_for('home'))

@app.route('/password-change', methods=('GET', 'POST'))
@login_required
def password_change():
    form = PasswordChangeForm()

    if form.validate_on_submit():
        # Get data from form
        pass_current = form.password_current.data
        pass_new = form.password_new.data
        pass_new_check = form.password_new_check.data

        # Connect to db
        user = User.query.filter_by(id=current_user.id).first()

        # Check if current pass matches pass in db
        if not user.check_password(pass_current):
            # Return comment and error type
            comment = "คุณใส่รหัสผ่านปัจจุบันไม่ถูกต้อง"
            error_type = "wrong_pass_current"
            return render_template('password-change-result.html', comment=comment, error_type=error_type)
        # Check if new passwords match each other
        elif pass_new != pass_new_check:
            # Return comment and error type
            comment = "คุณพิมพ์รหัสผ่านสองช่องไม่ตรงกัน"
            error_type = "unmatched_password_check"
            return render_template('password-change-result.html', comment=comment, error_type=error_type)
        # Proceed if 2 above checks passed
        else:
            # Generate new password hash
            user.set_password(pass_new)
            db.session.commit()

            # Return comment
            comment = "กรุณาใช้รหัสผ่านใหม่เมื่อล็อกอินครั้งถัดไป"
            return render_template('password-change-result.html', comment=comment)

    return render_template('password-change.html', form=form)

"""
Profile
"""

@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(id=current_user.id).first()
    user_id = user.id
    user_name = user.name
    user_email = user.email
    user_role = user.role
    user_create_dt = user.create_dt
    user_lastlogin_dt = user.lastlogin_dt

    # Return courses only if there's a course that belongs to current user
    courses = Course.query.filter(Course.user_id == current_user.id).order_by(Course.create_dt).all()

    # Return learners_enrollments if the current user has already enrolled in any courses
    learner_enrollments = Learner_enrollment.query.filter(Learner_enrollment.user_id == current_user.id).all()

    if learner_enrollments:
        # Join Learner_enrollment with Course table. This returns a list of tuples, so need to unpack
        joined_enrollment_courses = db.session.query(Course, Learner_enrollment).filter(Course.id == Learner_enrollment.course_id, Learner_enrollment.user_id == current_user.id).order_by(Learner_enrollment.course_enroll_dt.desc()).all()

        # Produce lists of course objects
        joined_courses = [i[0] for i in joined_enrollment_courses]

        # Produce list of enrolled course that has cert for this user
        enrollments_cert = Learner_enrollment.query.filter(Learner_enrollment.user_id == current_user.id, Learner_enrollment.cert_id != None).all()
        enrollment_list = [enrollment.course_id for enrollment in enrollments_cert]

        return render_template('profile.html', user_id=user_id, user_name=user_name, user_email=user_email, user_role=user_role, user_create_dt=user_create_dt, user_lastlogin_dt=user_lastlogin_dt, courses=courses, learner_enrollments=learner_enrollments, joined_courses=joined_courses, enrollment_list=enrollment_list)
    else:
        return render_template('profile.html', user_id=user_id, user_name=user_name, user_email=user_email, user_role=user_role, user_create_dt=user_create_dt, user_lastlogin_dt=user_lastlogin_dt, courses=courses)

"""
Learning path control
"""

@app.route('/course/<string:slug>/reentry')
@login_required
def learn_reentry(slug):
    course = Course.query.filter(Course.slug == slug).first()
    modules = Module.query.filter(Module.course_id == course.id).all()

    if modules:  # If this course has at least one module
        # Identify the lowest module_rank (from module_id) then resume this module_id
        starting_module = min([module.module_rank for module in modules])

        return redirect('/learn/' + slug + '/' + str(starting_module))
    else:  # If the course doesn't have any module
        flash("ขออภัย คอร์สนี้ยังไม่มีเนื้อหา กรุณากลับมาดูใหม่ภายหลัง")
        return redirect('/profile')

@app.route('/course/<string:slug>/continue')
@login_required
def learn_continue(slug):
    course = Course.query.filter(Course.slug == slug).first()

    # Return if the user has enrolled in this course
    learner_enrollment = Learner_enrollment.query.filter(Learner_enrollment.user_id == current_user.id, Learner_enrollment.course_id == course.id).first()

    # If this user has enrolled in this course
    if learner_enrollment:
        # Check if the user has started the course already or not by checking learner_progress table
        learn_started = Learner_progress.query.filter(Learner_progress.user_id == current_user.id, Learner_progress.course_id == course.id).first()

        # Check if the user has finished the course already or not by checking the existence of cert_id in Learner_enrollment
        learn_finished = Learner_enrollment.query.filter(Learner_enrollment.user_id == current_user.id, Learner_enrollment.course_id == course.id, Learner_enrollment.cert_id != None).first()

        # If the user has finished the course
        if learn_finished:
                flash('ยินดีด้วย คุณเรียนจบคอร์สนี้แล้ว')
                return redirect('/profile')

        elif not learn_started:  # If the user is enrolled but hasn't started the course yet
            # Check if the course has at least one module or not
            modules = Module.query.filter(Module.course_id == course.id).all()

            if modules:  # If this course has at least one module
                # Identify the lowest module_rank (from module_id) then resume this module_id
                starting_module = min([module.module_rank for module in modules])

                return redirect('/learn/' + slug + '/' + str(starting_module))
            else:  # If the course doesn't have any module
                flash("ขออภัย คอร์สนี้ยังไม่มีเนื้อหา กรุณากลับมาดูใหม่ภายหลัง")
                return redirect('/profile')

        # If the user has already started the course (finished at least 1 module)
        elif learn_started:   
            # First, locate the module_rank of the current module for this course
            modules = Module.query.filter(Module.course_id == course.id).all()

            progresses = Learner_progress.query.filter(Learner_progress.user_id == current_user.id, Learner_progress.course_id == course.id).all()

            progress_mod_ids = [progress.module_id for progress in progresses]

            progress_mod_ranks = []

            for progress_mod_id in progress_mod_ids:
                progress_mod_ranks.append(Module.query.filter(Module.id == progress_mod_id).first())

            mod_ranks = [progress_mod_rank.module_rank for progress_mod_rank in progress_mod_ranks]

            current_module = max(mod_ranks)

            # Then, locate the next module by creating a list of sorted module_rank for this module, then use bisect algorithm to find the next higher integer in list
            module_ranks_unsorted = [j_module.module_rank for j_module in modules]
            module_ranks = sorted(module_ranks_unsorted)
            next_int_in_list = bisect.bisect_right(module_ranks, current_module)

            try:  # Will locate the next higher int, except when at the highest already
                next_module = module_ranks[next_int_in_list]
            except:  # So need an exception in which case the next module should be current_module + 1
                next_module = current_module + 1

            return redirect('/learn/' + slug + '/' + str(next_module))
        
    # If this user hasn't enrolled in this course yet
    else:
        flash("ขออภัย คุณยังไม่ได้สมัครเรียนคอร์สนี้ กรุณาสมัครเรียนก่อน")
        return redirect('/profile')

@app.route('/learn/<string:slug>/<int:current_module>')
@login_required
def learn_current(slug, current_module):
    course = Course.query.filter(Course.slug == slug).first()
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == current_module).first()

    # Firstly, check if this current_module exceed the last module or not.
    # To do so, we need to find the max module_rank of this module in this course, 
    # then compare with current_module
    modules = Module.query.filter(Module.course_id == course.id).order_by(Module.module_rank.asc()).all()

    last_module = max([i_module.module_rank for i_module in modules])

    # Check if the user has achieved Course.pass_condition already or not
    passed_modules_raw = []

    for mod in modules:
        passed_modules_raw.append(Learner_progress.query.filter(Learner_progress.user_id == current_user.id, Learner_progress.module_id == mod.id).first())

    passed_modules = [i for i in passed_modules_raw if i != None]  # Remove None type
    pct_progress = len(passed_modules) / len(modules)

    if pct_progress >= course.pass_condition:
        course_passed = True
    else:
        course_passed = False

    # If the user reached the last module
    if current_module > last_module:
        if course_passed: # AND achieved Course.pass_condition
            # At this point, the user is eligible for a cert

            # Connect to certificate collection in db
            client = pymongo.MongoClient(app.config['DB_CERT_URI'])

            """
            !!! MUST CONFIGURE CLIENT DB NAME AND COLLECTION IN IMPLEMENTATION !!!
            """
            cert_db = client.lms  # <<< CONFIGURE DB NAME

            # Generate hash as cert_id
            rand_universe = [1,2,3,4,5,6,7,8,9,"a","b","c","d","e","f","g","A","B","C","D","E","F","G"]
            rand_str = ""
            rand_list = random.sample(rand_universe, k=12)
            cert_id = rand_str.join([str(i) for i in rand_list])

            # Inser cert_id in cert db (MongoDB)
            cert_db.certificate.insert_one({"hash": cert_id})

            # Insert cert_id in db (PostgreSQL)
            enrollment = Learner_enrollment.query.filter(Learner_enrollment.user_id == current_user.id, Learner_enrollment.course_id == course.id).first()

            enrollment.cert_id = cert_id
            db.session.commit()

            flash("ยินดีด้วย คุณเรียนจบหลักสูตรในคอร์สนี้แล้ว")
            return redirect('/profile')

        else:  # If at the last module but Course.pass_condition has not been met yet
            flash("คุณเรียนผ่านโมดูลสุดท้ายแล้ว แต่ยังไม่จบคอร์สเพราะยังไม่ผ่านบางโมดูล กรุณาเรียนโมดูลที่ยังไม่มีสัญลักษณ์ \"ผ่านแล้ว\" ให้จบจนครบ แล้วกลับมาเรียนโมดูลสุดท้ายให้ผ่านอีกครั้ง จึงจะได้รับประกาศนียบัตรจบหลักสูตร")

            return redirect('/course/' + slug + '/reentry')

    # If the user is NOT at the last module
    else:  # Proceed normally
        # Generate navigation content
        module_list = [mod for mod in modules]

        # Generate a list of passed module for current user
        progress = Learner_progress.query.filter(Learner_progress.user_id == current_user.id).all()
        passed_mod_list = [passed_mod.module_id for passed_mod in progress]

        # Check whether there's a test associated with this module
        test_questions = Test_question.query.filter(Test_question.module_id == module.id).all()

        # Now check if the current module has tests or not
        # - if have tests, generate the next link to the test
        # - if not, generate the next link to the next module
        if test_questions:  # If there's at least one test question for this module
            # Create a list of test_question ids
            test_question_ids = [test_question.id for test_question in test_questions]

            # Check whether there's a test answer for ANY of test questions
            test_answers = []

            for test_question_id in test_question_ids:
                test_answers.append(Test_answer.query.filter(Test_answer.test_question_id == test_question_id))

            # If test_answers list has at least one element, 
            # it means there's at least one answer for ANY of test questions.
            # So PROCEED to test question ONLY IF this condition is met.
            if test_answers:  # If the test_answers list is not empty
                # Mark the learn.html template that the NEXT link should go to the test
                to_test = True

                return render_template('learn.html', slug=slug, current_module=current_module, course=course, module=module, module_list=module_list, passed_mod_list=passed_mod_list, to_test=to_test)
            # If test_answers is empty, it means there's no answer, 
            # so a learner should proceed to the next module.
            else:
                # Mark the learn.html template that the NEXT link should go to the next module
                to_next_module = True

                # Locate the next module by creating a list of sorted module_rank for this module, 
                # then use bisect algorithm to find the next higher integer in list
                module_ranks_unsorted = [j_module.module_rank for j_module in modules]
                module_ranks = sorted(module_ranks_unsorted)
                next_int_in_list = bisect.bisect_right(module_ranks, current_module)

                try:  # Will locate the next higher int, except when at the highest already
                    next_module = module_ranks[next_int_in_list]
                except:  # So need an exception in which case the next module should be current_module + 1
                    next_module = current_module + 1

                return render_template('learn.html', slug=slug, current_module=current_module, course=course, module=module, module_list=module_list, passed_mod_list=passed_mod_list, to_next_module=to_next_module, next_module=next_module)

        else:  # If there's no test question, proceed to the next module
            # Insert a new progress data in learner_progress table (passed without test)
            # Note module_score equals 0 to distinguish from course passed with test
            progress = Learner_progress(user_id=current_user.id, course_id=course.id, module_id=module.id, module_pass_dt=datetime.now(), module_score=0)

            db.session.add(progress)
            db.session.commit()

            # Mark the learn.html template that the NEXT link should go to the next module
            to_next_module = True
            
            # Locate the next module by creating a list of sorted module_rank for this module, 
            # then use bisect algorithm to find the next higher integer in list
            module_ranks_unsorted = [j_module.module_rank for j_module in modules]
            module_ranks = sorted(module_ranks_unsorted)
            next_int_in_list = bisect.bisect_right(module_ranks, current_module)

            try:  # Will locate the next higher int, except when at the highest already
                next_module = module_ranks[next_int_in_list]
            except:  # So need an exception in which case the next module should be current_module + 1
                next_module = current_module + 1

            return render_template('learn.html', slug=slug, current_module=current_module, course=course, module=module, module_list=module_list, passed_mod_list=passed_mod_list, to_next_module=to_next_module, next_module=next_module)

@app.route('/learn/<string:slug>/<int:current_module>/test', methods=('GET', 'POST'))
@login_required
def test_current(slug, current_module):
    course = Course.query.filter(Course.slug == slug).first()
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == current_module).first()

    # Return a list of test_questions object for this module
    test_questions = Test_question.query.filter(Test_question.course_id == course.id, Test_question.module_id == module.id).order_by(Test_question.question_rank).all()

    # Create a dict of question-answers as key-values pair
    joined_answers_list = {}

    for test_question in test_questions:  # test_questions are dict keys
        joined_answers_list[test_question.question] = Test_answer.query.filter(Test_answer.test_question_id == test_question.id).order_by(Test_answer.answer_rank).all()

    joined_answers = dict(joined_answers_list)  # The output is a list so need to convert to dict again

    # Generate navigation content
    modules = Module.query.filter(Module.course_id == course.id).order_by(Module.module_rank.asc()).all()
    module_list = [mod for mod in modules]

    # Generate a list of passed module for current user
    progress = Learner_progress.query.filter(Learner_progress.user_id == current_user.id).all()
    passed_mod_list = [passed_mod.module_id for passed_mod in progress]

    if request.method == 'POST':
        # Get form data as dict with answer.test_question_id: answer.id as key:value
        answers = request.form.to_dict()

        # FIRST, check for num of correct answers to indicate whether a user passes or not
        # Check answer.id with Answer table whether each id is a correct or incorrect answer
        answer_ids_raw = [v for v in answers.values()]
        answer_ids = answer_ids_raw[1:]  # Remove CSRF value which is the first val of the list

        answer_corrects = []  # Create a list correct values of answers. Elements are booleans.

        for answer_id in answer_ids:
            answer_corrects.append(Test_answer.query.filter(Test_answer.id == int(answer_id)).first().correct)

        correct_num = 0  # Create the number of correct answer

        for answer_correct in answer_corrects:
            if answer_correct == True:
                correct_num += 1

        total_num = len(answers) - 1  # Have to remove a csrf_token key from dict
        correct_ratio = correct_num / total_num

        # THEN, generate the feedback for wrong answers
        """
        1. Locate ids of Test_answer with correct == False (using answer_ids in first step)
        2. Use those ids to identify test_question_id
        3. Use test_question_id to filter Test_question.id 
        """

        # Generate a list of Test answer objects with FALSE answer ids only
        false_test_answers = []

        for answer_id in answer_ids:
            false_test_answers.append(Test_answer.query.filter(Test_answer.id == answer_id, Test_answer.correct == False).first())

        false_test_answers = [i for i in false_test_answers if i != None]  # Remove None type

        false_test_questions = []

        for false_test_answer in false_test_answers:
            false_test_questions.append(Test_question.query.filter(Test_question.id == false_test_answer.test_question_id).first().question)

        # Create a dict from above two lists for iteration in template
        joined_feedback = dict(zip(false_test_questions, false_test_answers))

        if correct_ratio >= module.pass_condition:
            passed = True

            # Insert a new progress data in learner_progress table
            progress = Learner_progress(user_id=current_user.id, course_id=course.id, module_id=module.id, module_pass_dt=datetime.now(), module_score=correct_ratio)

            db.session.add(progress)
            db.session.commit()

            # Locate the next module by creating a list of sorted module_rank for this module, 
            # then use bisect algorithm to find the next higher integer in list
            modules = Module.query.filter(Module.course_id == course.id).all()

            module_ranks_unsorted = [j_module.module_rank for j_module in modules]
            module_ranks = sorted(module_ranks_unsorted)
            next_int_in_list = bisect.bisect_right(module_ranks, current_module)

            try:  # Will locate the next higher int, except when at the highest already
                next_module = module_ranks[next_int_in_list]
            except:  # So need an exception in which case the next module should be current_module + 1
                next_module = current_module + 1

            return render_template('test-result.html', course=course, module=module, module_list=module_list, passed_mod_list=passed_mod_list, correct_num=correct_num, total_num=total_num, correct_ratio=correct_ratio, passed=passed, slug=slug, next_module=next_module, test_questions=test_questions, joined_answers=joined_answers, joined_feedback=joined_feedback)
        else:
            passed = False

            return render_template('test-result.html', course=course, module=module, module_list=module_list, passed_mod_list=passed_mod_list, correct_num=correct_num, total_num=total_num, correct_ratio=correct_ratio, passed=passed, slug=slug, current_module=current_module, test_questions=test_questions, joined_answers=joined_answers, joined_feedback=joined_feedback)
    
    elif request.method == 'GET':
        return render_template('test.html', course=course, module=module, module_list=module_list, passed_mod_list=passed_mod_list, test_questions=test_questions, joined_answers=joined_answers)

"""
Course
"""

@app.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = CourseForm()
    if form.validate_on_submit():
        # Check if the same slug exist
        previous_slug = Course.query.filter(Course.slug == form.slug.data).first()
        if previous_slug is not None:
            return render_template('create-error.html')
        else:  # If slug is unique, proceed to post
            name = form.name.data
            description = form.description.data
            category = form.category.data
            now = datetime.now()
            slug = form.slug.data
            pass_condition = form.pass_condition.data

            course = Course(name=name, description=description, category=category, slug=slug, user_id=current_user.id, create_dt=now, active=True, pass_condition=pass_condition)
            db.session.add(course)
            db.session.commit()

            flash("สร้างคอร์สสำเร็จแล้ว")
            return redirect('/course/' + slug)

    return render_template('create.html', form=form)

@app.route('/create/error')
@login_required
def create_error():
    return render_template('create-error.html')

@app.route('/course/<string:slug>')
def course_view(slug):
    course = Course.query.filter(Course.slug == slug).first()

    # Return module only of there's a module that belongs to this course
    modules = Module.query.filter(Module.course_id == course.id).order_by(Module.module_rank).all()

    if current_user.is_authenticated:
        # Return course_creator only if current user is the owner of this course
        course_creator = Course.query.filter(Course.user_id == current_user.id).first()

        # Return if logged in user is a learner
        learner = User.query.filter(User.id == current_user.id, User.role == "learner").first()

        if course_creator:  # For course creator (author)
            return render_template('/course-view.html', course=course, course_creator=course_creator, modules=modules, slug=slug)
        elif learner:  # For other loggedin user (learner)
            # Check if current user has already enrolled or not
            learner_enrollment = Learner_enrollment.query.filter(Learner_enrollment.user_id == learner.id, Learner_enrollment.course_id == course.id).first()

            if learner_enrollment:
                learner_enrolled = True

                # Check if the user already has certificate from this course
                enrollment_cert = Learner_enrollment.query.filter(Learner_enrollment.user_id == learner.id, Learner_enrollment.course_id == course.id, Learner_enrollment.cert_id != None).first()

                # Check if the user has achieved Course.pass_condition already or not
                passed_modules = []

                for mod in modules:
                    passed_modules.append(Learner_progress.query.filter(Learner_progress.user_id == current_user.id, Learner_progress.module_id == mod.id).first())

                passed_modules = [i for i in passed_modules if i != None]  # Remove None type
                pct_progress = len(passed_modules) / len(modules)

                if enrollment_cert:
                    enrolled_cert = True

                    return render_template('/course-view.html', course=course, learner=learner, modules=modules, slug=slug, learner_enrolled=learner_enrolled, enrolled_cert=enrolled_cert, pct_progress=pct_progress)
                else:  # If no cert
                    return render_template('/course-view.html', course=course, learner=learner, modules=modules, slug=slug, learner_enrolled=learner_enrolled, pct_progress=pct_progress)
            else:
                return render_template('/course-view.html', course=course, learner=learner, modules=modules, slug=slug)
    
    else:  # For visitors
        return render_template('/course-view.html', course=course, modules=modules, slug=slug)

@app.route('/course/<string:slug>/learners/<string:sort_mode>')
def course_learners(slug, sort_mode):
    course = Course.query.filter(Course.slug == slug).first()
    
    if sort_mode == "sort-enrollment":
        joined_learners = db.session.query(User, Learner_enrollment).filter(User.id == Learner_enrollment.user_id, Learner_enrollment.course_id == course.id).order_by(Learner_enrollment.course_enroll_dt.desc()).all()
    elif sort_mode == "sort-user":
        joined_learners = db.session.query(User, Learner_enrollment).filter(User.id == Learner_enrollment.user_id, Learner_enrollment.course_id == course.id).order_by(User.name.asc()).all()
    elif sort_mode == "sort-email":
        joined_learners = db.session.query(User, Learner_enrollment).filter(User.id == Learner_enrollment.user_id, Learner_enrollment.course_id == course.id).order_by(User.email.asc()).all()
    elif sort_mode == "sort-cert":
        joined_learners = db.session.query(User, Learner_enrollment).filter(User.id == Learner_enrollment.user_id, Learner_enrollment.course_id == course.id).order_by(Learner_enrollment.cert_id.asc()).all()

    learner_num = len(joined_learners)

    joined_users = [i[0] for i in joined_learners]
    joined_enrollments = [i[1] for i in joined_learners]

    learners = dict(zip(joined_users, joined_enrollments))

    return render_template('course-learners.html', course=course, learners=learners, learner_num=learner_num)

@app.route('/course/<string:slug>/enroll')
@login_required
def course_enroll(slug):
    course = Course.query.filter(Course.slug == slug).first()
    learner = User.query.filter(User.id == current_user.id).first()

    # Check if the user has already enrolled in the course
    enrolled = Learner_enrollment.query.filter(Learner_enrollment.user_id == learner.id, Learner_enrollment.course_id == course.id).first()

    if enrolled:
        flash("ขออภัย คุณได้สมัครเรียนคอร์สนี้ไว้แล้ว")

        return redirect('/profile')
    else:
        enroll = Learner_enrollment(user_id=learner.id, course_id=course.id)
        db.session.add(enroll)
        db.session.commit()

        flash("สมัครเรียนเรียบร้อยแล้ว")

        return redirect('/profile')

@app.route('/course/<string:slug>/edit', methods=('GET', 'POST'))
@login_required
def course_edit(slug):
    course = Course.query.filter(Course.slug == slug).first()

    # Return course_creator only if current user is the owner of this course
    course_creator = Course.query.filter(Course.user_id == current_user.id).first()

    form = CourseForm()

    if course_creator:  # Check if current user is the creator of this course
        if form.validate_on_submit():
            # Check if slug has been changed
            if form.slug.data != slug:
                # If slug was changed, check if the same slug already exist
                previous_slug = Course.query.filter(Course.slug == form.slug.data).first()
                if previous_slug is not None:  # If new slug exists already in DB
                    return render_template('create-error.html')
                else:  # If new slug is unique, proceed to commit the change
                    course.name = form.name.data
                    course.description = form.description.data
                    course.category = form.category.data
                    course.slug = form.slug.data
                    course.pass_condition = form.pass_condition.data

                    db.session.commit()

                    flash(f"แก้ไขข้อมูลคอร์สเรียบร้อย > URL slug ถูกเปลี่ยนเป็น /course/{course.slug}")
                    # Redirect by using new slug from form, not original slug
                    return redirect('/course/' + course.slug)
            else:  # If slug hasn't been changed, proceed to commit the change
                course.name = form.name.data
                course.description = form.description.data
                course.category = form.category.data
                course.slug = form.slug.data
                course.pass_condition = form.pass_condition.data

                db.session.commit()

                flash("แก้ไขข้อมูลคอร์สเรียบร้อย")
                return redirect('/course/' + slug)
        else:  # Put normal query in else to prevent data overwrite when edited
            form.name.data = course.name
            form.description.data = course.description
            form.category.data = course.category
            form.slug.data = course.slug
            form.pass_condition.data = course.pass_condition
        
        return render_template('course-edit.html', course=course, form=form, slug=slug)

    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/delete')
@login_required
def course_delete(slug):
    course = Course.query.filter(Course.slug == slug).first()

    # Return course_creator only if current user is the owner of this course
    course_creator = Course.query.filter(Course.user_id == current_user.id).first()

    if course_creator:  # Check if current user is the creator of this course
        return render_template('course-delete.html', course=course, slug=slug)
    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/delete/confirm')
@login_required
def course_delete_confirm(slug):
    course = Course.query.filter(Course.slug == slug).first()

    # Return course_creator only if current user is the owner of this course
    course_creator = Course.query.filter(Course.user_id == current_user.id).first()

    if course_creator:  # Check if current user is the creator of this course
        db.session.delete(course)
        db.session.commit()

        flash("ลบคอร์สเรียบร้อยแล้ว")
        return redirect('/profile') 
    else:
        return render_template('owner-error.html')

"""
Module
"""

@app.route('/course/<string:slug>/add', methods=('GET', 'POST'))
@login_required
def module_add(slug):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Return course_creator only if current user is the owner of this course
    course_creator = Course.query.filter(Course.user_id == current_user.id).first()

    form = ModuleForm()

    if course_creator:  # Check if current user is the creator of this course
        if form.validate_on_submit():
            module_rank = form.module_rank.data
            name = form.name.data
            vdo_url = form.vdo_url.data
            description = form.description.data
            file_url = form.file_url.data
            pass_condition = form.pass_condition.data

            # Check for duplicate module_rank
            duplicate_module_rank = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

            if duplicate_module_rank:  # If entered module_rank already exist
                return render_template('module-add-error.html', module_rank=module_rank)
            else:
                module = Module(course_id=course.id, module_rank=module_rank, name=name, vdo_url=vdo_url, description=description, file_url=file_url, pass_condition=pass_condition)
                db.session.add(module)
                db.session.commit()

                flash("สร้างโมดูลสำเร็จแล้ว")
                return redirect('/course/' + slug + '/' + str(module_rank))

        return render_template('module-add.html', form=form, slug=slug)

    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/<int:module_rank>')
@login_required
def module_view(slug, module_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    # Return test_questions only of there's a test_question that belongs to this module
    test_questions = Test_question.query.filter(Test_question.module_id == module.id).order_by(Test_question.question_rank).all()

    return render_template('module-view.html', course=course, module_creator=module_creator, module=module, slug=slug, module_rank=module_rank, test_questions=test_questions)

@app.route('/course/<string:slug>/<int:module_rank>/edit', methods=('GET', 'POST'))
@login_required
def module_edit(slug, module_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    form = ModuleForm()

    if module_creator:  # Check if current user is the creator of this module
        if form.validate_on_submit():
            # Check for duplicate module_rank
            # Need this check before getting form data otherwise module_rank would have been overwritten
            duplicate_module_rank = Module.query.filter(Module.course_id == course.id, Module.module_rank == form.module_rank.data).first()

            # Get data from form
            module.module_rank = form.module_rank.data
            module.name = form.name.data
            module.vdo_url = form.vdo_url.data
            module.description = form.description.data
            module.file_url = form.file_url.data
            module.pass_condition = form.pass_condition.data

            # Check if module_rank is changed or not
            if form.module_rank.data == module_rank:  # If module_rank is not changed
                db.session.commit()

                flash("แก้ไขข้อมูลคอร์สเรียบร้อย")
                return redirect('/course/' + slug + '/' + str(module_rank))
            else:  # If module_rank is changed
                if duplicate_module_rank:  # If updated module_rank already exist in DB
                    return render_template('module-add-error.html', module_rank=form.module_rank.data)
                else:  # If module_ranked is changed but new one has no duplicate rank in DB
                    db.session.commit()

                    flash("แก้ไขข้อมูลคอร์สเรียบร้อย")
                    return redirect('/course/' + slug + '/' + str(form.module_rank.data))
        else:  # Put normal query in else to prevent data overwrite when edited
            form.module_rank.data = module.module_rank  # Populate form with original module_rank
            form.name.data = module.name
            form.vdo_url.data = module.vdo_url
            form.description.data = module.description
            form.file_url.data = module.file_url
            form.pass_condition.data = module.pass_condition
        
            return render_template('module-edit.html', module=module, form=form, slug=slug, module_rank=module_rank)

    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/<int:module_rank>/delete')
@login_required
def module_delete(slug, module_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    if module_creator:  # Check if current user is the creator of this module
        return render_template('module-delete.html', module=module, slug=slug)
    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/<int:module_rank>/delete/confirm')
@login_required
def module_delete_confirm(slug, module_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    if module_creator:  # Check if current user is the creator of this module
        db.session.delete(module)
        db.session.commit()

        flash("ลบโมดูลเรียบร้อยแล้ว")
        return redirect('/course/' + slug)
    else:
        return render_template('owner-error.html')

"""
Test question and answer
"""

@app.route('/course/<string:slug>/<int:module_rank>/add', methods=('GET', 'POST'))
@login_required
def test_question_add(slug, module_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    form = TestQuestionForm()

    if module_creator:  # Check if current user is the creator of this module
        if form.validate_on_submit():
            question_rank = form.question_rank.data
            question = form.question.data

            # Check for duplicate question_rank
            duplicate_test_question_rank = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == question_rank).first()

            if duplicate_test_question_rank:  # If entered question_rank already exist
                return render_template('test-question-add-error.html', question_rank=question_rank)
            else:
                question = Test_question(course_id=course.id, module_id=module.id, question_rank=question_rank, question=question)
                db.session.add(question)
                db.session.commit()

                flash("สร้างคำถามสำเร็จแล้ว")
                return redirect('/course/' + slug + '/' + str(module_rank) + '/' + str(question_rank))

        return render_template('test-question-add.html', form=form, slug=slug, module_rank=module_rank)

    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/<int:module_rank>/<int:question_rank>')
@login_required
def test_question_view(slug, module_rank, question_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Select the working test_question identified by working module and question_rank
    test_question = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == question_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    # Return test_questions only if there's a test_question that belongs to this module
    test_questions = Test_question.query.filter(Test_question.module_id == module.id).order_by(Test_question.question_rank).all()

    # Return test_answers only if there's a test_answer that belongs to this test_question
    test_answers = Test_answer.query.filter(Test_answer.test_question_id == test_question.id).order_by(Test_answer.answer_rank).all()

    return render_template('test-question-view.html', course=course, module_creator=module_creator, module=module, slug=slug, module_rank=module_rank, test_question=test_question, test_questions=test_questions, test_answers=test_answers)

@app.route('/course/<string:slug>/<int:module_rank>/<int:question_rank>/edit', methods=('GET', 'POST'))
@login_required
def test_question_edit(slug, module_rank, question_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Select the working test_question identified by working module and question_rank
    test_question = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == question_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    form = TestQuestionForm()

    if module_creator:  # Check if current user is the creator of this module
        if form.validate_on_submit():
            # Check for duplicate question_rank
            # Need this check before getting form data otherwise question_rank would have been overwritten
            duplicate_question_rank = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == form.question_rank.data).first()

            # Get data from form
            test_question.question_rank = form.question_rank.data
            test_question.question = form.question.data

            # Check if question_rank is changed or not
            if form.question_rank.data == question_rank:  # If question_rank is not changed
                db.session.commit()

                flash("แก้ไขคำถามเรียบร้อย")
                return redirect('/course/' + slug + '/' + str(module_rank) + '/' + str(question_rank))
            else:  # If question_rank is changed
                if duplicate_question_rank:  # If updated question_rank already exist in DB
                    return render_template('test-question-add-error.html', question_rank=form.question_rank.data)
                else:  # If question_ranked is changed but new one has no duplicate rank in DB
                    db.session.commit()

                    flash("แก้ไขคำถามเรียบร้อย")
                    return redirect('/course/' + slug + '/' + str(module_rank) + '/' + str(form.question_rank.data))
        else:  # Put normal query in else to prevent data overwrite when edited
            form.question_rank.data = test_question.question_rank  # Populate form with original question_rank
            form.question.data = test_question.question
        
            return render_template('test-question-edit.html', module=module, question_rank=question_rank, form=form, slug=slug, module_rank=module_rank)

    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/<int:module_rank>/<int:question_rank>/delete')
@login_required
def test_question_delete(slug, module_rank, question_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Select the working test_question identified by working module and question_rank
    test_question = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == question_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    if module_creator:  # Check if current user is the creator of this module
        return render_template('test-question-delete.html', module=module, slug=slug, test_question=test_question)
    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/<int:module_rank>/<int:question_rank>/delete/confirm')
@login_required
def test_question_delete_confirm(slug, module_rank, question_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Select the working test_question identified by working module and question_rank
    test_question = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == question_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    if module_creator:  # Check if current user is the creator of this module
        db.session.delete(test_question)
        db.session.commit()

        flash("ลบคำถามเรียบร้อยแล้ว")
        return redirect('/course/' + slug + '/' + str(module_rank))
    else:
        return render_template('owner-error.html')

"""
Test answer
"""

@app.route('/course/<string:slug>/<int:module_rank>/<int:question_rank>/add', methods=('GET', 'POST'))
def test_answer_add(slug, module_rank, question_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Select the working question identified by working module and question_rank
    test_question = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == question_rank).first()

    # Return test_questions only if there's a test_question that belongs to this module
    test_questions = Test_question.query.filter(Test_question.module_id == module.id).order_by(Test_question.question_rank).all()

    # Return test_answers only if there's a test_answer that belongs to this test_question
    test_answers = Test_answer.query.filter(Test_answer.test_question_id == test_question.id).order_by(Test_answer.answer_rank).all()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    form = TestAnswerForm()

    if module_creator:  # Check if current user is the creator of this module
        enable_answer_form = True  # Enable the answer form in test-question-view template

        if form.validate_on_submit():
            answer_rank = form.answer_rank.data
            answer = form.answer.data
            correct = form.correct.data
            feedback = form.feedback.data

            # Check for duplicate answer_rank
            duplicate_test_answer_rank = Test_answer.query.filter(Test_answer.test_question_id == test_question.id, Test_answer.answer_rank == answer_rank).first()

            if duplicate_test_answer_rank:  # If entered answer_rank already exist
                return render_template('test-answer-add-error.html', answer_rank=answer_rank)
            else:
                answer = Test_answer(test_question_id=test_question.id, answer_rank=answer_rank, answer=answer, correct=correct, feedback=feedback)
                db.session.add(answer)
                db.session.commit()

                flash("สร้างคำคอบสำเร็จแล้ว")
                return redirect('/course/' + slug + '/' + str(module_rank) + '/' + str(question_rank))

        return render_template('test-question-view.html', form=form, slug=slug, course=course, module=module, module_rank=module_rank, test_question=test_question, test_questions=test_questions, test_answers=test_answers, question_rank=question_rank, module_creator=module_creator, enable_answer_form=enable_answer_form)

    else:
        return render_template('owner-error.html')

@app.route('/course/<string:slug>/<int:module_rank>/<int:question_rank>/<int:answer_rank>/delete')
@login_required
def test_answer_delete(slug, module_rank, question_rank, answer_rank):
    # Select the working course identified by slug
    course = Course.query.filter(Course.slug == slug).first()

    # Select the working module identified by working course and module_rank
    module = Module.query.filter(Module.course_id == course.id, Module.module_rank == module_rank).first()

    # Select the working test_question identified by working module and question_rank
    test_question = Test_question.query.filter(Test_question.module_id == module.id, Test_question.question_rank == question_rank).first()

    # Select the working test_answer identified by working test_question and answer_rank
    test_answer = Test_answer.query.filter(Test_answer.test_question_id == test_question.id, Test_answer.answer_rank == answer_rank).first()

    # Return module_creator only if current user is the owner of this module
    module_creator = Module.query.filter(Course.slug == slug, Course.user_id == current_user.id).first()

    if module_creator:  # Check if current user is the creator of this module
        db.session.delete(test_answer)
        db.session.commit()

        flash("ลบตัวเลือกเรียบร้อยแล้ว")
        return redirect('/course/' + slug + '/' + str(module_rank) + '/' + str(question_rank))
    else:
        return render_template('owner-error.html')

"""
Certificate issuer
"""

@app.route('/cert/<string:slug>')
@login_required
def cert_issue(slug):
    course = Course.query.filter(Course.slug == slug).first()
    user = Learner_enrollment.query.filter(Learner_enrollment.user_id == current_user.id, Learner_enrollment.course_id == course.id).first()

    # Get cert_id from db
    if user.cert_id is None:
        return redirect('/profile')
    else:
        cert_id = user.cert_id

        # Connect to certificate collection in db
        client = pymongo.MongoClient(app.config['DB_CERT_URI'])

        """
        !!! MUST CONFIGURE CLIENT DB NAME AND COLLECTION IN IMPLEMENTATION !!!
        """
        cert_db = client.lms  # <<< CONFIGURE DB NAME

        # Check if the cert has been issued
        mongo_cert_id = cert_db.certificate.find_one(
            {"$and": [{"hash": cert_id}, {"used": True}]}
            )

        # If a cert hasn't been issued yet, issue a cert
        if mongo_cert_id is None:
            cert_status = "unissued"
            return render_template('cert-issue.html', cert_id=cert_id, cert_status=cert_status, course=course)
        # Else, a user has already been issued a cert, just show the cert
        else:
            cert_status = "issued"
            return render_template('cert-issue.html', cert_id=cert_id, cert_status=cert_status, course=course)

@app.route('/cert/<string:slug>/issue/<string:cert_id>')
@login_required
def cert_form(slug, cert_id):
    course = Course.query.filter(Course.slug == slug).first()

    return render_template('cert-form.html', course=course, cert_id=cert_id)

@app.route('/cert/<string:slug>/issued', methods=['GET', 'POST'])
def cert_issued(slug):
    if request.method == 'POST':
        # Get information from the form
        form_hash = request.form['hash']
        form_name = request.form['name']
        form_school = request.form['school']

        # Remove Zero-width Space to prevent white block display
        form_name = form_name.replace('\u200b', '')
        form_school = form_school.replace('\u200b', '')

        client = pymongo.MongoClient(app.config['DB_CERT_URI'])

        """
        !!! MUST CONFIGURE CLIENT DB NAME AND COLLECTION IN IMPLEMENTATION !!!
        """
        cert_db = client.lms  # <<< CONFIGURE DB NAME

        # Find the given hash
        hash_check = cert_db.certificate.find_one({"hash": form_hash})
        duplicate_check = cert_db.certificate.find_one({"hash": form_hash, "used": True})

        if hash_check is None:  # If hash doesn't exist
            hash_valid = False
            hash_output = "ขออภัย ไม่พบรหัสประกาศนียบัตรดังกล่าว"

            return render_template('cert-error.html', hash_valid=hash_valid, hash_output=hash_output)
        elif duplicate_check is not None:  # If hash was already used
            hash_valid = False
            hash_output = "ขออภัย รหัสดังกล่าวเคยใช้ออกประกาศนียบัตรไปแล้ว"

            return render_template('cert-error.html', hash_valid=hash_valid, hash_output=hash_output)
        else:  # If hash exists and hasn't been used
            hash_valid = True
            hash_output = "ขอแสดงความยินดีด้วย เราได้ออกประกาศนียบัตรของคุณเรียบร้อยแล้ว กรุณาดาวน์โหลดภาพข้างล่าง"

            # Generate the date using custom now_date_th_gen module
            now = datetime.now()  # machine date for db
            now_date_th = now_date_th_gen.gen_date_th()  # human-readable date in TH

            # Update the document with name, grade, school, issue_date, and used status
            cert_db.certificate.update_one(
                {"hash": form_hash},
                {"$set": {
                    "name": form_name,
                    "school": form_school,
                    "issue_date": now,
                    "used": True
                    }
                }
            )

            # Generate the certificate
            
            """
            PUT CERT TEMPLATE HERE. FOR MULTIPLE TEMPLATES, USE SLUG TO IDENTIFY IN CONDITIONAL STATEMENT.
            """
            path_cert_template = Path.cwd() / 'app/static/cert-template-coursename.png'  # <<< CONFIGURE CERT TEMPLATE
            
            path_cert = Path.cwd() / 'app/static/cert'

            with Image.open(path_cert_template) as im:
                issue_name = form_name
                issue_school = form_school
                issue_date = now_date_th
                issue_verify = "sokru.org/verify/" + form_hash  # <<< CONFIGURE WEBSITE URL

                d_issue_name = ImageDraw.Draw(im)
                d_issue_school = ImageDraw.Draw(im)
                d_issue_date = ImageDraw.Draw(im)
                d_issue_verify = ImageDraw.Draw(im)

                loc_issue_name = (81, 313)
                loc_issue_school = (199, 398)
                loc_issue_date = (256, 588)
                loc_issue_verify = (1092, 900)
                text_color = "black"
                font_issue_name = ImageFont.truetype('thsarabunnew_bold.ttf', 52)
                font_issue_school = ImageFont.truetype('thsarabunnew_bold.ttf', 30)
                font_issue_date = ImageFont.truetype('thsarabunnew_bold.ttf', 30)
                font_issue_verify = ImageFont.truetype('Kanit-Regular.ttf', 12)

                d_issue_name.text(loc_issue_name, issue_name, fill=text_color, font=font_issue_name)
                d_issue_school.text(loc_issue_school, issue_school, fill=text_color, font=font_issue_school)
                d_issue_date.text(loc_issue_date, issue_date, fill=text_color, font=font_issue_date)
                d_issue_verify.text(loc_issue_verify, issue_verify, fill=text_color, font=font_issue_verify)

                cert_file = (slug + "-cert-" + form_hash + ".png")
                im.save(str(path_cert) + '/' + cert_file)

                # Upload cert image to S3
                s3_destination = ("certs/" + cert_file)  # <<< CONFIGURE S3 BUCKET PATH (FOLDER)
                s3_lms = boto3.resource('s3').Bucket('deepmatters-lms')  # <<< CONFIGURE S3 BUCKET NAME
                s3_lms.upload_file(Filename=(str(path_cert) + '/' + cert_file), Key=s3_destination, ExtraArgs={'ACL': 'public-read'})

            return redirect('/cert/' + slug)

    elif request.method == 'GET':
        return redirect('/profile')

@app.route('/verify/<string:hash_id>')
def cert_verified(hash_id):
    # Connect and define the database
    client = pymongo.MongoClient(app.config['DB_CERT_URI'])

    """
    !!! MUST CONFIGURE CLIENT DB NAME AND COLLECTION IN IMPLEMENTATION !!!
    """
    cert_db = client.lms  # <<< CONFIGURE DB NAME

    # Find the given hash
    hash_verify = cert_db.certificate.find_one({"hash": hash_id})

    if hash_verify is None:  # If hash doesn't exist
        hash_verify_output = "ขออภัย ไม่พบรหัสประกาศนียบัตรดังกล่าว"
    else:
        hash_verify_output = "พบรหัสประกาศนียบัตรดังกล่าว ยืนยันว่าเป็นของแท้"

    return render_template('cert-verified.html', hash_id=hash_id, hash_verify_output=hash_verify_output)

"""
Course browser
"""

@app.route('/courses')
def courses():
    # Return all ACTIVE courses
    courses = Course.query.filter(Course.active == True).order_by(Course.create_dt).all()

    return render_template('courses.html', courses=courses)

"""
Static
"""

@app.route('/about')
def about():
    return render_template('about.html')