from flask_login import current_user
from flask import url_for,flash,redirect

def post_verification_admin_required(function):
	def check(*arrgs, **kwargs):
		if "post_verification" in { i.split()[0] for i in urrent_user.Permission() }:
			return function(*arrgs,**kwargs)
		else:
			flash("Permission Denied you can not access this page",'danger')
			redirect(url_for('index'))
	return check