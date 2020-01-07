from app import app
from flask import render_template, flash, redirect, url_for,request, jsonify, Response
from app.forms import *
from flask_login import current_user, login_user,logout_user,login_required
from app.models import *
from werkzeug.urls import url_parse
from app import db
from datetime import datetime
import os
from PIL import Image
from app.email import *
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from app.decorators import post_verification_admin_required
import base64
from io import BytesIO
from app import socketio, send, emit

users_sid = {}

# @socketio.on("message")
# @login_required
# def messageHandler(message):
# 	users_sid[ current_user.username ] = request.sid
# 	print("Message: "+message)
# 	print(users_sid)

def convert_save_image(filedata,filename):
	path = os.path.join(app.root_path+"/static/profile_pic/{}/{}".format(current_user.username,filename+".png") )
	i=Image.open(filedata)
	size=(128,128)
	i.thumbnail(size)
	i.save(path)


@app.route("/", methods=["POST","GET"])
@app.route("/index", methods=["POST","GET"])
@login_required
def index():
	return render_template("index.html",user=current_user)

@app.route("/explore")
@login_required
def explore():	
	return render_template('explore.html', title="Explore", user=current_user)

@app.route("/edit",methods=["POST","GET"])
@login_required
def edit():
	
	form2 = EditForm()

	if form2.submit.data and form2.validate_on_submit():
		if current_user.email!=form2.email.data:
			current_user.email=form2.email.data
			current_user.email_verified = False
		if current_user.about_me!=form2.about_me.data:
			current_user.about_me=form2.about_me.data
		db.session.commit()
		flash('Your account has been updated','success')
		return redirect(url_for('edit'))


	if request.method == "GET": 
		form2.email.data=current_user.email
		form2.about_me.data=current_user.about_me

	if current_user.current_image=="default.jpg":
		image_path = url_for('static',filename="profile_pic/default.jpg")
	else:
		image_path = url_for('static',filename="profile_pic/{}/{}".format(current_user.username, current_user.current_image ) )

	return render_template('edit_profile.html',
							user=current_user,
							form=form2,
							image=image_path
								)

@app.route("/user/<username>")
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	if user.current_image=="default.jpg":
		image=url_for( 'static', filename="profile_pic/default.jpg")
	else:
		image=url_for( 'static', filename="profile_pic/{}/{}".format( username,user.current_image ) )

	return render_template("user.html",profile_user=user,
								current_user=current_user,
								current_image=image
							)

@login_required	
@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()

@app.route("/login", methods=["POST","GET"])
def login():
	if current_user.is_authenticated:
		return redirect(url_for("index"))

	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash("Invalid username or password",'danger')
			return redirect(url_for('login'))
		login_user(user,remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != "":
			next_page = url_for('index')
		return redirect(next_page)
	return render_template("login.html",title="Sign In",form=form)

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect('login')


@app.route('/register',methods=["POST","GET"])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm() 
	if form.validate_on_submit():
		u=User(username=form.username.data,email=form.email.data)
		u.set_password(form.password.data)
		db.session.add(u)
		db.session.commit()
		flash("Congratulations you are now a registered user!!",'success')
		os.system("mkdir app/static/profile_pic/{}".format(form.username.data)) 
		return redirect(url_for('login'))
	return render_template("register.html",title="Register",form=form)


@app.route('/delete_account/<username>', methods=["POST","GET"])
@login_required
def delete_account(username):
	user = User.query.filter_by(username=username).first()
	if user==current_user:
		if user is None:
			flash('User Not found','info')
			return redirect( url_for('user',username=current_user.username) )
		else:
			flash('Your Account has been deleted','success')
			db.session.delete(user)
			db.session.commit()
			return redirect( url_for('login') )
	flash('You can delete only your account','warning')
	return redirect( url_for('index') )

@app.route('/reset_password_request', methods=["POST","GET"])
def reset_password_request():

	if current_user.is_authenticated:
		return redirect( url_for('index') )
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user= User.query.filter_by(email=form.email.data).first()
		if user:
			send_password_reset_email(user)
		flash("check your email for instructions to reset your password",'info')
		return redirect( url_for('login') )
	return render_template('reset_password_request.html',title="Reset Password",form=form)


@app.route('/reset_password/<token>', methods=["POST","GET"])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect( url_for('index') )
	user=User.varify_reset_password_token(token)
	if not user:
		flash("Invalid/Expired Token",'warning')
		return redirect( url_for('index') )
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		db.session.commit()
		flash("Your password has been reset",'success')
		return redirect( url_for('login') )
	return render_template('reset_password.html',form=form)


@app.route('/email_verification_request')
@login_required
def email_verification_request():
	if current_user.email_verified:
		return redirect(url_for( 'user',username=current_user.username ))
	otp=current_user.get_otp()
	send_email_verification_otp(otp,current_user)
	return redirect('email_verification')

@app.route('/email_verification', methods=["POST","GET"])
@login_required
def email_verificaion():
	form=OtpForm()
	if form.validate_on_submit():
		otp= request.form['otp']
		if current_user.varify_otp(otp):
			current_user.email_verified=True
			db.session.commit()
			flash("Email has been verified",'success')
			return redirect(url_for('user',username=current_user.username))
		flash("Wrong OTP","danger")
		redirect('email_verificaion')
	flash("Otp will expire in one minute",'info')
	return render_template('otp.html',form=form)


@login_required
@app.route("/search", methods=["POST","GET"])
def search():
	search_text = request.form['search']
	results = User.query.filter(User.username.like("%{}%".format(search_text))).all()
	return render_template('search_result.html',results=results)


# .................................... Ajax Calls.....................................................

@login_required
@post_verification_admin_required
@app.route("/post_request_deleted" , methods=["POST","GET"])
def post_request_deleted():
	id = request.form['id']
	post = PostVerification.query.filter_by(id=int(id))
	user = User.query.filter_by(username=post.first().author).first()
	send_post_request_reject_email(user,post.first())	
	post.delete()
	db.session.commit()
	return jsonify({'message': "Post request has been rejected"})

@login_required
@post_verification_admin_required
@app.route("/post_request_verified", methods=["POST","GET"])
def post_request_verified():
	id = request.form['id']
	post = PostVerification.query.filter_by(id=int(id))
	user = User.query.filter_by(username=post.first().author).first()
	post1 = Post(body=post.first().body,author=user)
	db.session.add(post1)
	send_post_request_accepted_email(user,post.first())
	post.delete()
	db.session.commit()
	return jsonify({'message': "Post request has been accepted"})

@login_required
@app.route("/upload_image", methods=["POST"])
def upload_image():
	if request.form:
		image_data = request.form['image'].split(",")[1]
		image_data = BytesIO( base64.b64decode(image_data) )
		if current_user.current_image == "default.jpg":
			image_name = "1"
		else:
			image_name = str( 
							int(
								( current_user.images.order_by(
											 ProfileImage.id.desc() 
											 ).first().image 
								).split(".")[0]
								) +1 
							) 
		convert_save_image(image_data,image_name)		
		current_user.current_image = image_name+".png"
		img = ProfileImage(user=current_user.username,image=image_name+".png")
		db.session.add(img)
		db.session.commit()
	return jsonify({'text':'done'})

@login_required
@app.route("/load_profile_images" ,methods=["POST"])
def load_profile_images():
# 	number of images before ajax call
	NOI_before_load = int(request.form['prev_images'])
	print(NOI_before_load)
	result=[]
	for i in current_user.images.all():
		image = url_for( 'static', filename="profile_pic/{}/{}".format( current_user.username, i.image ) )
		result.append( [i.image, image] ) 
	return jsonify({'images': result[NOI_before_load:] })

@login_required
@app.route("/search_result", methods=["POST"])
def search_result():
	search_text = request.form['search_text']
	if search_text!="":
		result = User.query.filter( User.username.op("regexp")('.*{}.*'.format(search_text)) ).all()
	else:
		result = []
	sorted_users = [(i,len(i.followers.all())) for i in result ]
	sorted_users = sorted(sorted_users,reverse=True,key=lambda x:x[1])

	final_result = []
	for i in sorted_users[:5]:
		if i[0].current_image=="default.jpg":
			image = url_for('static',filename="profile_pic/default.jpg")
		else:
			image = url_for( 'static', filename="profile_pic/{}/{}".format(i[0].username,i[0].current_image) )

		final_result.append({
			"username": i[0].username,
			"profile_link": url_for('user',username=i[0].username),
			"image": image
			})
	
	return jsonify({'search_result': final_result})

@login_required
@app.route("/load_post_index", methods=["POST"])
@app.route("/load_post_explore", methods=["POST"])
@app.route("/load_post_user", methods=["POST"])
def load_post():
	from_where = int(request.form['from_where'])
	if (request.url=="http://127.0.0.1:8000/load_post_index"):
		result = current_user.followed_posts().filter(Post.id<from_where).limit(15).all()
	elif (request.url=="http://127.0.0.1:8000/load_post_explore"):
		result = Post.query.order_by(Post.timestamp.desc()).filter(Post.id<from_where).limit(15).all()
	else:
		user = User.query.filter_by( username=request.form['user'] ).first()
		result = user.posts.order_by(Post.timestamp.desc()).filter(Post.id<from_where).limit(15).all()
	final_result = [] 
	for i in result:
		if i.author.current_image=="default.jpg":
			image = url_for('static',filename="profile_pic/default.jpg")
		else:
			image = url_for('static',filename="profile_pic/{}/{}".format(i.author.username,i.author.current_image))
		final_result.append({"id":str(i.id), 
							"body":i.body,
							"author": i.author.username,
							"timestamp": str(i.timestamp), 
							"image":image, 
							"link":url_for('user',username=i.author.username) 
							});
	stop = "false"
	if len(final_result)==0:
		stop="true"
	return jsonify({'posts': final_result, "stop":stop})

@app.route('/post_submit', methods=["POST"])
def post_submit():
	if request.form['body']:
		post= PostVerification(body=request.form['body'], author=current_user.username)
		db.session.add(post)
		db.session.commit()
		return jsonify({'text': "Your Post is sent to admin for verification", 'class':'success'})

@login_required
@app.route("/profile_image_update", methods=["POST"])
def profile_image_update():
	if request.form:
		current_user.current_image = request.form['selected_image']
		db.session.commit()
		return jsonify({ 'text': "Profile Image Updated", "class": "success" })

@login_required
@app.route('/delete_post', methods=["POST"])
def delete_post():
	post = request.form['id']
	post = Post.query.get(int(post))
	if (post!=None) and post.user_username == current_user.username:
		db.session.delete(post)
		db.session.commit()
		result = {'text': "Post has been deleted", 'class': 'success'}
	else:
		result = {'text': "Invalid",'class': 'danger' }
	return result

@login_required
@app.route("/follow", methods=["POST"])
def follow():
	user 	= request.form['user']
	user=User.query.filter_by(username=user).first()
	if user is None:
		flash("User {} Not Found!".format(username),"warning")
		return redirect( url_for('user', username=current_user.username) )
	elif user==current_user:
		flash("You Cant follow yourself","warning")
		return redirect( url_for('user', username=current_user.username) )
	current_user.follow(user)
	db.session.commit()
	print(users_sid)
	try:
		sid = users_sid[user.username]
	except :
		sid = ''
	# socketio.emit('from_flask',{'text': "{} start following you".format(current_user.username), 'class': 'info'}, room=sid, namespace="/notify")
	result = { 
				'text': "Now you following {}".format(user.username), 
				'class': "success", 
				"followers": str(user.followers.count()),
				"following": str(user.followed.count()) }
	return jsonify( result )

@app.route("/unfollow", methods=["POST"])
@login_required
def unfollow():
	user = request.form['user']
	user=User.query.filter_by(username=user).first()
	if user is None:
		flash("User {} Not Found!".format(username),"warning")
		return redirect( url_for('user', username=current_user.username) )
	elif user==current_user:
		flash("You Cant unfollow userself","warning")
		return redirect( url_for('user', username=current_user.username) )
	current_user.unfollow(user)
	db.session.commit()
	try:
		sid = users_sid[user.username]
	except :
		sid = ''
	# socketio.emit('from_flask',{'text': "{} unfollowed you".format(current_user.username), 'class': 'info'}, room=sid, namespace="/notify")
	result = { 
				'text': "You unfollow {}".format(user.username), 
				'class': "success",
				"followers": str(user.followers.count()),
				"following": str(user.followed.count()) }
	return jsonify(result)



class UserModelView(ModelView):
	
	column_exclude_list = ('password_hash','otp_secret')
	can_view_details = True
	can_edit=False
	can_create=False

	def is_accessible(self):
		return "user" in { i.split()[0] for i in current_user.permissions() }

	@property
	def can_delete(self):
		return "user w" in current_user.permissions()

class PostModelView(ModelView):

	@property
	def can_delete(self):
		return "post w" in current_user.permissions()

	can_edit=False
	can_create=False

	def is_accessible(self):
		return "post" in { i.split()[0] for i in current_user.permissions() }

class RoleManagerModelView(ModelView):

	@property
	def can_create(self):
		return "role w" in current_user.permissions()

	@property
	def can_edit(self):
		return "role w" in current_user.permissions()

	@property
	def can_delete(self):
		return "role w" in current_user.permissions()

	def is_accessible(self):
		return "role" in  { i.split()[0] for i in current_user.permissions() }

class RolesModelView(ModelView):

	@property
	def can_create(self):
		return "role w" in current_user.permissions()

	@property
	def can_edit(self):
		return "role w" in current_user.permissions()

	@property
	def can_delete(self):
		return "role w" in current_user.permissions()

	def is_accessible(self):
		return "role" in { i.split()[0] for i in current_user.permissions() }

class PostVerificationView(BaseView):

	@expose("/")
	def index(self):
		return self.render('admin/post_verification.html',PostVerification=PostVerification)

	def is_accessible(self):
		print(current_user.permissions())
		return "post_verification" in { i.split()[0] for i in current_user.permissions() }

class MyAdminIndexView(AdminIndexView):
	def is_accessible(self):
		return (current_user.is_authenticated and len(current_user.permissions())!=0)

admin = Admin(app,index_view=MyAdminIndexView(),name="Microblog")
admin.add_view(UserModelView( User, db.session ))
admin.add_view(PostModelView( Post, db.session ))
admin.add_view(RoleManagerModelView( Role, db.session ))
admin.add_view(RolesModelView( RoleManager, db.session ))
admin.add_view(PostVerificationView(name="Post Verification", endpoint="PostVerification"))
