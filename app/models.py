from app import db,ma
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from time import time
import jwt
from app import app
from pyotp import TOTP
import base64 
import os




followers = db.Table('followers',
	db.Column('follower_username',db.ForeignKey('user.username')),
	db.Column('followed_username',db.ForeignKey('user.username'))
)


class User(UserMixin,db.Model):

	otp_secret = db.Column(db.String(16))

	def __init__(self,**kwargs):
		super(User, self).__init__(**kwargs)		
		if self.otp_secret is None:
			self.otp_secret = base64.b32encode(os.urandom(10)).decode("utf-8")


	id = db.Column(db.Integer,primary_key=True,autoincrement=True)
	username = db.Column(db.String(64),unique=True,primary_key=True)
	email = db.Column(db.String(120), index=True, unique=True)
	email_verified = db.Column(db.Boolean,default=False)
	password_hash = db.Column(db.String(128), index=True, unique=True)
	posts = db.relationship('Post',backref="author",lazy='dynamic',cascade="save-update, delete")
	# image = db.Column(db.String(100),default='default')
	images = db.relationship( 'ProfileImage', backref="image_user", lazy="dynamic", cascade="save-update, delete")
	current_image = db.Column(db.String(100),default='default.jpg')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	roles = db.relationship('RoleManager',backref="roles",lazy="dynamic",cascade="save-update, delete")

	followed = db.relationship(
		'User', secondary=followers,
		primaryjoin=(followers.c.follower_username == username),
		secondaryjoin=(followers.c.followed_username == username),
		backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

        def get_id(self):
            try:
                return self.username
            except AttributeError:
                raise NotImplementedError('No `id` attribute - override `get_id`')

	def get_reset_password_token(self, expire_in=600):
		return jwt.encode( {'reset_password': self.username, 'exp': time()+ expire_in}, app.config['SECRET_KEY'], algorithm='HS256' ).decode('utf-8')

	@staticmethod
	def varify_reset_password_token(token):
		try:
			username = jwt.decode( token, app.config['SECRET_KEY'], algorithm=['HS256'] )['reset_password']
		except:
			return

		return User.query.filter_by(username=username).first()

	def get_otp(self):
		return TOTP(self.otp_secret,interval=180).now()

	def varify_otp(self,otp):
		return TOTP(self.otp_secret,interval=180).verify(otp)


	def follow(self, user):
		if not self.is_followed(user):
			self.followed.append(user)

	def unfollow(self, user):
		if self.is_followed(user):
			self.followed.remove(user)

	def is_followed(self, user):
		return self.followed.filter(followers.c.followed_username == user.username).count() > 0


	def followed_posts(self):
		followed = Post.query.join(followers,
			(followers.c.followed_username == Post.user_username)).filter(
				followers.c.follower_username == self.username) 		

		own = Post.query.filter_by(user_username=self.username)
		return (followed.union(own)).order_by(Post.timestamp.desc())

	def set_password(self,password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash,password)

	def permissions(self):
		a=set()
		for i in self.roles.all():
			a.add( i.user_permission.permission )
		return a


	def __repr__(self):
		return "<User {}>".format(self.username)


class Post(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	user_username = db.Column(db.String(64), db.ForeignKey('user.username'))


	def __repr__(self):
		return "<Post %r>"%(self.body)

class PostVerification(db.Model):

	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	author = db.Column(db.String(64))

	def __repr__(self):
		return "<PostVerififcation {}>".format(self.body)


class Role(db.Model):
	id = db.Column(db.Integer,primary_key=True, unique=True)
	permission = db.Column(db.String(30),unique=True)
	user_role = db.relationship("RoleManager",backref="user_permission")

	def __repr__(self):
		return self.permission
	

class RoleManager(db.Model):
	id  = db.Column(db.Integer,primary_key=True)
	user = db.Column(db.String(64), db.ForeignKey('user.username') )
	role_id = db.Column(db.Integer, db.ForeignKey('role.id') )


class ProfileImage(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	user = db.Column( db.String(64), db.ForeignKey('user.username') )
	image = db.Column( db.String(100) )

@login.user_loader
def load_user(username):
	return	User.query.filter_by(username=username).first()


# ............................Marshmallow Schemas............................................

class UserSchema(ma.ModelSchema):
	class Meta:
		model = User

class PostSchema(ma.ModelSchema):
	class Meta:
		model = Post
