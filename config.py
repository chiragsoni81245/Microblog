import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):

	POST_ON_LOAD = 6

	REDIS_URL = "redis://:password@localhost"

	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

	# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, "app.db")
	
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:123@localhost:3306/microblog' 

	SQLALCHEMY_TRACK_MODIFICATIONS = False

	# MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_SERVER = 'smtp.googlemail.com'
	# MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_PORT = 587
	# MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USE_TLS = 1
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'example-email@gmail.com'
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '123'
	ADMINS = ['example-email@gmail.com']
