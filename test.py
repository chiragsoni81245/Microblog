from datetime  import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Post
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class UserModelCase(unittest.TestCase):


	def setUp(self):
		app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///' + os.path.join(basedir, "app.db")
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def test_password_hashing(self):

		u=User(username="chirag")
		u.set_password("jarvis")
		self.assertTrue(u.check_password('jarvis'))
		self.assertFalse(u.check_password('123'))


	def test_follow(self):
		u=User(username="tanu")
		u1=User(username="ajay")
		db.session.add_all([u,u1])
		db.session.commit()
		self.assertEqual(u.followed.all(), [])
		self.assertEqual(u1.followed.all(), [])

		u.follow(u1)

		self.assertTrue(u.is_followed(u1))
		self.assertEqual(u.followed.count(), 1)
		self.assertEqual(u.followed.first().username, "ajay")

		u.unfollow(u1)

		self.assertEqual(u.followed.all(), [])


	def test_follow_post(self):

		u=[]

		for i in range(4):
			u.append ( User(username=f"chirag{i}",email=f"chirag{i}") )

		db.session.add_all(u)

		now=datetime.utcnow()

		p=[]
		p.append(Post(body=f"this is post of {u[0].username}",author=u[0],timestamp=now+timedelta(seconds=4) ) )
		p.append(Post(body=f"this is post of {u[1].username}",author=u[1],timestamp=now+timedelta(seconds=3) ) )
		p.append(Post(body=f"this is post of {u[2].username}",author=u[2],timestamp=now+timedelta(seconds=2) ) )
		p.append(Post(body=f"this is post of {u[3].username}",author=u[3],timestamp=now+timedelta(seconds=1) ) )

		db.session.add_all(p)

		db.session.commit()

		u[0].follow(u[1])
		u[0].follow(u[3])
		u[1].follow(u[2])
		u[2].follow(u[3])

		db.session.commit()

		f=[]
		for i in range(4):
			f.append( u[i].followed_posts().all() )

		self.assertEqual(f[0],[p[0],p[1],p[3]])
		self.assertEqual(f[1],[p[1],p[2]])
		self.assertEqual(f[2],[p[2],p[3]])
		self.assertEqual(f[3],[p[3]])


if __name__=='__main__':
	unittest.main(verbosity=2)
