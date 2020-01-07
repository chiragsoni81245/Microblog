from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import ValidationError, DataRequired,Email, Length,EqualTo, regexp
from app.models import User
from flask_login import current_user

class LoginForm(FlaskForm):
	username = StringField('Username',validators=[DataRequired()]) 
	password = PasswordField('Password',validators=[DataRequired()]) 
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In') 

class RegistrationForm(FlaskForm):

	username = StringField('Username',validators=[DataRequired(),regexp('^(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$',
											message="Dont use Special Characters and space's"),Length(min=6)])
	email = StringField('Email',validators=[DataRequired(),Email()])
	password = PasswordField('Password',validators=[DataRequired(),Length(min=6)])
	password2 = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
	submit = SubmitField('Register')


	''' 

	 .....................This is a method to obtain a varible from routes by passing init form class.......................................

		def __init__(self, original_username, *args, **kwargs):                        
			super(RegistrationForm, self).__init__(*args, **kwargs)
			self.original_username = original_username
	'''

	def validate_username(self,username):
		user = User.query.filter_by(username=username.data).first()

		if (user is not None):
			raise ValidationError('Please Use a diffrent username')

	def validate_email(self,email):
		user = User.query.filter_by(email=email.data).first()

		if (user is not None):
			raise ValidationError('Please use a diffrent email')


class EditForm(FlaskForm):

	email = StringField('Email',validators=[DataRequired(),Email()])
	about_me = TextAreaField('About Me',validators=[])
	submit = SubmitField('Update')


	def validate_username(self,username):
		user = User.query.filter_by(username=username.data).first()

		if (user is not None) and current_user.username!=username.data:
			raise ValidationError('Please Use a diffrent username')


	def validate_email(self,email):
		user = User.query.filter_by(email=email.data).first()

		if (user is not None) and current_user.email!=email.data:
			raise ValidationError('Please use a diffrent email')


class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Email',validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('New Password', validators=[DataRequired(),Length(min=6)])
	password2 = PasswordField('Confirm Password', validators=[DataRequired(),Length(min=6),EqualTo('password')])
	submit = SubmitField('Submit')

class OtpForm(FlaskForm):
	otp = StringField('OTP',validators=[DataRequired()])
	submit = SubmitField('Submit')


