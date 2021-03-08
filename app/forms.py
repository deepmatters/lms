from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField, URLField
from wtforms.fields import PasswordField, SubmitField, StringField, RadioField, TextAreaField, BooleanField, IntegerField, DecimalField
from wtforms.validators import DataRequired
from flask_pagedown.fields import PageDownField

class SignupForm(FlaskForm):
    name = StringField('ชื่อ: ', validators=[DataRequired()])
    email = EmailField('อีเมล: ', validators=[DataRequired()])
    password = PasswordField('รหัสผ่าน: ', validators=[DataRequired()])
    password_check = PasswordField('ยืนยันรหัสผ่าน: ', validators=[DataRequired()])
    submit = SubmitField('สมัครสมาชิก')

class LoginForm(FlaskForm):
    email = EmailField('อีเมล: ', validators=[DataRequired()])
    password = PasswordField('รหัสผ่าน: ', validators=[DataRequired()])
    submit = SubmitField('ล็อกอิน')

class ForgetForm(FlaskForm):
    email = EmailField('อีเมล: ', validators=[DataRequired()])
    submit = SubmitField('ขอรหัสผ่านใหม่')

class PasswordChangeForm(FlaskForm):
    password_current = PasswordField('รหัสผ่านปัจจุบัน: ', validators=[DataRequired()])
    password_new = PasswordField('รหัสผ่านใหม่: ', validators=[DataRequired()])
    password_new_check = PasswordField('ยืนยันรหัสผ่านใหม่: ', validators=[DataRequired()])
    submit = SubmitField('เปลี่ยนรหัสผ่าน')

class PasswordResetForm(FlaskForm):
    password_reset_id = StringField('Password Reset ID: ', validators=[DataRequired()])
    password_new = PasswordField('รหัสผ่านใหม่: ', validators=[DataRequired()])
    password_new_check = PasswordField('ยืนยันรหัสผ่านใหม่: ', validators=[DataRequired()])
    submit = SubmitField('เปลี่ยนรหัสผ่าน')

class CourseForm(FlaskForm):
    name = StringField('ชื่อคอร์ส: ', validators=[DataRequired()])
    description = PageDownField('คำอธิบายคอร์ส: ', validators=[DataRequired()])
    category = StringField('หมวดหมู่คอร์ส: ', validators=[DataRequired()])
    slug = StringField('URL ของคอร์ส เป็นภาษาอังกฤษและ/หรือตัวเลข พิมพ์ติดกันทั้งหมด: ', validators=[DataRequired()])
    pass_condition = DecimalField('เกณฑ์การผ่านคอร์ส: ', places=2, validators=[DataRequired()])
    submit = SubmitField('สร้างคอร์ส')
    submit_edit = SubmitField('แก้ไขคอร์ส')

class ModuleForm(FlaskForm):
    module_rank = IntegerField('โมดูลลำดับที่: ', validators=[DataRequired()])
    name = StringField('ชื่อโมดูล: ', validators=[DataRequired()])
    vdo_url = URLField('URL ของ Youtube VDO: ')
    description = PageDownField('เนื้อหาโมดูล: ', validators=[DataRequired()])
    file_url = URLField('URL ของไฟล์เอกสารประกอบ: ')
    pass_condition = DecimalField('เกณฑ์การสอบผ่านโมดูล (0 = 0%, 0.5 = 50%, 1 = 100%): ', places=2, validators=[DataRequired()])
    submit = SubmitField('สร้างโมดูล')
    submit_edit = SubmitField('แก้ไขโมดูล')

class TestQuestionForm(FlaskForm):
    question_rank = IntegerField('คำถามข้อที่: ', validators=[DataRequired()])
    question = PageDownField('คำถาม: ', validators=[DataRequired()])
    submit = SubmitField('สร้างคำถาม')
    submit_edit = SubmitField('แก้ไขคำถาม')

class TestAnswerForm(FlaskForm):
    answer_rank = IntegerField('คำตอบลำดับที่: ', validators=[DataRequired()])
    answer = TextAreaField('คำตอบ: ', validators=[DataRequired()])
    correct = BooleanField('ถ้าข้อนี้เป็นคำตอบที่ถูกต้อง เลือกตัวเลือกข้างล่าง')
    feedback = TextAreaField('คำอธิบายคำตอบ: ')
    submit = SubmitField('สร้างคำตอบ')
    submit_edit = SubmitField('แก้ไขคำตอบ')