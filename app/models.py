from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default="learner")
    create_dt = db.Column(db.DateTime, default=datetime.utcnow)
    lastlogin_dt = db.Column(db.DateTime, default=datetime.utcnow)
    password_reset_id = db.Column(db.String(12))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.name)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    description = db.Column(db.String(10000))
    category = db.Column(db.String(100))
    slug = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    create_dt = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean)
    pass_condition = db.Column(db.Float)

    def __repr__(self):
        return '<Course {}>'.format(self.name)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="CASCADE"))
    module_rank = db.Column(db.Integer)
    name = db.Column(db.String(300))
    vdo_url = db.Column(db.String(300))
    description = db.Column(db.String(10000))
    file_url = db.Column(db.String(1000))
    pass_condition = db.Column(db.Float)

    def __repr__(self):
        return '<Module {}>'.format(self.name)

class Test_question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="CASCADE"))
    module_id = db.Column(db.Integer, db.ForeignKey('module.id', ondelete="CASCADE"))
    question_rank = db.Column(db.Integer)
    question = db.Column(db.String(10000))

    def __repr__(self):
        return '<Test_question {}>'.format(self.question)

class Test_answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_question_id = db.Column(db.Integer, db.ForeignKey('test_question.id', ondelete="CASCADE"))
    answer_rank = db.Column(db.Integer)
    answer = db.Column(db.String(10000))
    correct = db.Column(db.Boolean)
    feedback = db.Column(db.String(10000))

    def __repr__(self):
        return '<Test_answer {}>'.format(self.answer)

class Learner_progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="CASCADE"))
    module_id = db.Column(db.Integer, db.ForeignKey('module.id', ondelete="CASCADE"))
    module_score = db.Column(db.Float)
    module_pass_dt = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Learner_progress {}>'.format(self.id)

class Learner_enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete="CASCADE"))
    course_enroll_dt = db.Column(db.DateTime, default=datetime.utcnow)
    cert_id = db.Column(db.String(12))

    def __repr__(self):
        return '<Learner_enrollment {}>'.format(self.id)

"""
# To create a database, run the following:
$ export FLASK_APP=appname.py (set env var so flask cmd know where the app is)
$ flask db init
$ flask db migrate -m "commit message"
$ flask db upgrade

# To add a user and password, use Python prompt:
>>> from app import db
>>> from app.models import User, Post
>>> u = User(email='name@domain.com')
>>> u.set_password('MyPassword')
>>> u.check_password('MyPassword')
True
>>> db.session.add(u)
>>> db.session.commit()

#To query database:
>>> users = User.query.all()
>>> users
>>> for u in users:
...     print(u.id, u.email, u.password_hash)

# To create a password hash for a user:
>>> from werkzeug.security import generate_password_hash
>>> hash = generate_password_hash('foobar')
>>> hash
Use this hash as a password_hash entry in db

# To verify hash:
>>> from werkzeug.security import check_password_hash
>>> check_password_hash(hash, 'foobar')
True
"""

@login.user_loader
def load_user(id):
    return User.query.get(int(id))