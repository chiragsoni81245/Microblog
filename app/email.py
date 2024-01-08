from flask_mail import Message
from app import app
from app import mail
from flask import render_template
from threading import Thread


def send_email(subject, sender, recipients, text_body, html_body):
	
	msg = Message(subject, sender=sender, recipients=recipients)
	msg.body=text_body
	msg.html=html_body
	# Thread( target=send_async_email, args=(app, msg) ).start()

def send_async_email(app, msg):
	with app.app_context():
		mail.send(msg)


def send_password_reset_email(user):
	token = user.get_reset_password_token()
	send_email('[Microblog] Reset Your Password',sender=app.config['ADMINS'][0], recipients=[user.email],
					text_body=render_template('email/reset_password.txt', user=user, token=token),
					html_body=render_template('email/reset_password.html', user=user, token=token) )



def send_email_verification_otp(otp,user):
	send_email('[Microblog] Varify Your Email',sender=app.config['ADMINS'][0], recipients=[user.email],
			text_body=render_template('email/email_verification.txt',user=user,otp=otp),html_body=None)

def send_post_request_reject_email(user,post):
	print(user,post)
	send_email('[Microblog] Your post request has been rejected',sender=app.config['ADMINS'][0],recipients=[user.email],
			text_body=render_template('email/post_request_reject_email.txt',user=user,post=post),html_body=None)

def send_post_request_accepted_email(user,post):
	print(user,post)
	send_email('[Microblog] Your post request has been accepted',sender=app.config['ADMINS'][0],recipients=[user.email],
			text_body=render_template('email/post_request_accepted_email.txt',user=user,post=post),html_body=None)


