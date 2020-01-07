from app import db
from app.models import *
import random
from faker import Faker
import sys

fake = Faker()

nouns = ["puppy", "car", "rabbit", "girl", "monkey"]
verbs = ["runs", "hits", "jumps", "drives", "barfs"]
adv =["crazily.", "dutifully.", "foolishly.", "merrily.", "occasionally."]
adj = ["adorable", "clueless", "dirty", "odd", "stupid"]

def reandom_sentence():
	num = random.randrange(0,5)
	return "{} {} {} {}".format(nouns[num], verbs[num], adv[num], adj[num])

def random_post(user):
	return Post( body=reandom_sentence(),author=user )
	  

def random_user():
	username = fake.name().split()[0]+str( random.randint(1,999) )+str( random.randint(1,999) )
	user = User( username=username, email=fake.email() )
	user.set_password("1234567")
	return user


def generate_random_user(n):
	a=[]
	for i in range(n):
		user=random_user()
		a.append( user )
		print( "{} user {} is created with email {}".format( i+1, user.username, user.email ) )
	return a

if __name__=="__main__":
	
	n,m = map(int,sys.argv[1:])
	generated_users = []
	for i in range(n//100):
		w=generate_random_user(100)
		generated_users+=w
		db.session.add_all( w )
		db.session.commit()
		db.session.flush()
	w=generate_random_user( n%100 )
	generated_users+=w
	db.session.add_all( w )
	db.session.commit()
	db.session.flush()	
	users=User.query.all()
	
	for k in range(len(generated_users)//100):
		b=[]
		for j in range(100):
			for i in range(m):
				post=random_post(generated_users[(k*100)+j])
				b.append( post )
				print( "\t\tpost '{}' has been submited by {}".format( post.body, post.author.username ) )
		db.session.add_all(b)
		db.session.commit()
		db.session.flush()

	b=[]
	for j in range(len(generated_users)%100):
		for i in range(m):
			post=random_post(generated_users[j])
			b.append( post )
			print( "\t\tpost '{}' has been submited by {}".format( post.body, post.author.username ) )
	db.session.add_all(b)
	db.session.commit()
	db.session.flush()



	for user in generated_users:
		w = random.randrange(5,6)
		for i in range(w):
			rl=User.query.all()
			rl.remove(user)
			u2=random.choice(rl)
			user.follow( u2 )
			print( "\t\t\t\t{} follow {}".format(user,u2) )
	db.session.commit()
