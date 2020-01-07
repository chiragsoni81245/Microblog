from app import app,db,socketio
from app.models import User,Post

@app.shell_context_processor
def make_shell_context():
	return {'db' : db, 'User' : User, 'Post' : Post}

if __name__=="__main__":
	socketio.run(app, host="127.0.0.1", port="5000")	
