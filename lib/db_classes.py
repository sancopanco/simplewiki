from google.appengine.ext import db
import utility.wiki_utility
import datetime 
import logging

def users_key(group = 'default'):
	return db.Key.from_path('users', group)


class User(db.Model):
	name = db.StringProperty(required = True)
	pw_hash = db.StringProperty(required = True)
	email = db.StringProperty()
	
	@classmethod
	def by_id(cls, uid):
		return cls.get_by_id(uid, parent = users_key())
	@classmethod
	def by_name(cls, name):
		u = cls.all().filter('name = ', name).get()
		return u
	@classmethod	
	def register(cls, name, pw, email = None):
		pw_hash = utility.wiki_utility.make_pw_hash(name, pw)
		return User(parent = users_key(),
					name = name,
					pw_hash = pw_hash,
					email = email)
	@classmethod				
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and utility.wiki_utility.valid_pw(name, pw,
												u.pw_hash):
			return u 									


class Page(db.Model):
	name = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)
	user = db.Reference(User, required = True)
	version = db.IntegerProperty(default = 1, required= True)
	def render(self):
		return utility.wiki_utility.render_template('pagehistory.html',
														h = self)
	@staticmethod
	def get_page(name, version = 1, user = None):
		p = Page.by_name(name, user)
		#logging.error(p)
		content = '<h3>%s</h3>' % name
		if p:
			version = p.version + 1
			content = p.content
		now = datetime.datetime.now()
		return Page(name = name, user=user, content = content,
			created = now, last_modified = now, version = version)	
			
	@classmethod
	def by_name(cls, name, user = None):
		p = cls.all().filter('name = ', name).order('-version').get()
		return p
	@classmethod	
	def by_name_and_version(cls, name, version = 1, user = None):
		#TODO:should be changed
		q = Page.gql('WHERE name = :1 and version = :2' , name,
														int(version))
		#logging.error(list(q))										
		return q.get()
	@staticmethod	
	def get_last_version():
		p = Page.all().order('-version').get()
	@classmethod	
	def get_page_history(cls, name,user = None):
		q = Page.gql('WHERE name = :1', name)
		pages = list(q)
		return pages
	@classmethod
	def save(cls, name, user = None, content = None):
		p = Page.get_page(name,version = 1, user = user)
		#logging.error(p.user.name)
		if content:
			p.content = content
			p.put()
		
		
	
	
	
	
			