from flask import render_template
from app import app
@app.route('/')
@app.route('/index')
def index():
	user = {'username':'Seeker'}
	posts = [{'author':{'username':'Tannu'}
			'body':'"He is Stupid"'},{'author':{'usename':'Chirag'}
			'body':'"Nice"'}]
	return render_template('index.html',title='Home',user=user,posts=posts)
