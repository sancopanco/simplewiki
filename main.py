#!/usr/bin/env python
import webapp2
import utility.wiki_utility
import  lib.db_classes
import os 
import logging

class WikiHandler(webapp2.RequestHandler):
	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.user = uid and lib.db_classes.User.by_id(int(uid))
	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and utility.wiki_utility.check_secure_val(cookie_val)
	def set_secure_cookie(self, name, val):
		cookie_val = utility.wiki_utility.make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val)
		)
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
	def render_str(self, template, **params):
		params['user'] = self.user
		return utility.wiki_utility.render_template(template, **params)
	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))
	def logout(self):
		self.set_secure_cookie('user_id','')

class Signup(WikiHandler):
	def get(self):
		self.render('signup-form.html')
	def post(self):
		self.username = self.request.get('username')
		self.password = self.request.get('password')
		self.verify = self.request.get('verify')
		self.email = self.request.get('email')
		params = dict(username = self.username,
						email = self.email)
		have_error = False				
		if not utility.wiki_utility.valid_username(self.username):
			params['error_username'] = "That's not a valid username."
			have_error = True
		if not utility.wiki_utility.valid_password(self.password):
			params['error_password'] = "That wasn't a valid password."
			have_error = True
		elif self.password != self.verify:
			params['error_verify'] ="Your passwords didn't match."
			have_error = True
		if not utility.wiki_utility.valid_email(self.email):
			params['error_email'] = "That's not a valid email."
			have_error = True
			
		if 	have_error:
			self.render('signup-form.html', **params)
		else:
			self.done()

	def done(self, *a, **kw):
		raise NotImplementedError

class Register(Signup):
	def done(self):
		#make sure the user doesn't already exist
		u = lib.db_classes.User.by_name(self.username)
		if u:
			msg = 'That user already exists.'
			self.render('signup-form.html',error_username = msg)
		else:
			u = lib.db_classes.User.register(self.username, self.password,
						    	              self.email)
			u.put()
			self.login(u)
			self.redirect('/welcome')	
		
			
class Login(WikiHandler):
	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		if  username and password:
			u = lib.db_classes.User.login(username, password)
			if u:
				self.login(u)
				self.redirect('/welcome')
			else:
				msg = 'Login did not work, check your email and password and try again.'
				self.render('front.html',error = msg)
		else:
			msg ='Invalid login'
			self.render('front.html',error = msg)
		
		
class Logout(WikiHandler):
	def get(self):
		self.logout()
		self.redirect('/signup')
		
		
class EditPage(WikiHandler):
	def get(self, page_name):
		p = lib.db_classes.Page.get_page(page_name, 
								user = self.user)
		self.render('edit.html', username = self.user.name,
				 	 page = p)	
	def post(self, page_name):
		content = self.request.get('code')
		if content:
			#logging.error(page_name+','+content)
			lib.db_classes.Page.save(name =  page_name,
			user = self.user, content = content)
			self.redirect(page_name)
		
class WikiPage(WikiHandler):
	def get(self,page_name):
		if not self.user:
			p = lib.db_classes.Page.by_name(page_name)
			if p:
				self.render('front.html',wiki_content = p.content)
			else:
				self.render('front.html')
		else:
			if page_name:
				v = self.request.get('v')
				#logging.error(v)
				p = None
				if v:
					p = lib.db_classes.Page.by_name_and_version(name = page_name[:-1], version = v)
				else: 
					p = lib.db_classes.Page.by_name(page_name)
				#logging.error(p)	
				if p:
					self.render('welcome.html', 
					               username = self.user.name,
					                 wiki_content = p.content,
									 page_name = page_name)
					return 				 
				self.redirect('_edit' + str(page_name))	
			
	
			
class Welcome(WikiHandler):
	def get(self):
		if self.user:
			self.render('welcome.html', username = self.user.name)
		else:
			self.redirect('/signup')

			
class HistoryPage(WikiHandler):
	def get(self, page_name):
		page_h = []
		if page_name:
			page_h = lib.db_classes.Page.get_page_history(page_name)
			self.render('history.html', history = page_h)
				

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
							   ('/welcome',Welcome),
							   ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/_edit' + PAGE_RE, EditPage),
							   ('/_history' + PAGE_RE, HistoryPage),
                               (PAGE_RE, WikiPage)
							  ],
                              debug=True)
