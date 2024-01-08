from app import app,db,socketio
from app.models import User,Post,Role,RoleManager

@app.shell_context_processor
def make_shell_context():
	return {'db' : db, 'User' : User, 'Post' : Post, 'Role': Role, 'RoleManager': RoleManager}

