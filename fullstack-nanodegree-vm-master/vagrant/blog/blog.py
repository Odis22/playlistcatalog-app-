import os
import re

from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
    autoescape = True)

def render_str(template, ** params):
    t = jinja_env.get_template(template)
    return t.render(params)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)


def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)


class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

class SignUpHandler(BaseHandler):
    def get(self):
        self.render("signup-form.html")

def post(self):
    errors = False
    self.username = self.request.get('username')
    self.password = self.request.get('password')
    self.confirm = self.request.get('confirm')
    self.email = self.request.get('email')

params = dict(username = self.username,
    email = self.email)

u = User.by_name(self.username)
if u:
    params['error_username1'] = 'Username Already Exists'
errors = True

if not valid_username(self.username):
    params['error_username2'] = "Invalid Username."
    errors = True

if not valid_password(self.password):
    params['error_pass'] = "Invalid Password."
    errors = True
elif self.password != self.confirm:
    params['error_confirm'] = "Passwords Do Not Match."
    errors = True

if not valid_email(self.email):
    params['error_email'] = "Invalid Email."
    errors = True

if errors:
    self.render('signup-form.html', ** params)

else :
    u = User.register(self.username, self.password, self.email)
    u.put()
    self.login(u)
    self.redirect('/')


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login-form.html')

def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    u = User.login(username, password)
if u:
    self.login(u)
    self.redirect('/')
else :
    msg = "Invalid Username/Password"
    self.render('login-form.html', error = msg)


class LogoutHandler(BaseHandler):
    def get(self):
        self.logout()
        self.redirect('/login')

class Comment(db.Model):
    author = db.StringProperty()
    post_id = db.StringProperty(required = True)
    comment = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now = True)

class NewCommentHandler(BaseHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)
if not self.user:
    self.redirect("/login")
else :
    comments = db.GqlQuery("SELECT * FROM Comment " +
        "WHERE post_id = :1 " +
        "ORDER BY created DESC",
        post_id)

self.render("newcomment.html",
    post = post,
    comments = comments,
    loggedIn = self.user)

def post(self, post_id):
    if not self.user:
        self.redirect("/login")
    else :
        posts = db.GqlQuery(
        "SELECT * FROM Post ORDER BY votes DESC LIMIT 10")
    author = self.user.name
    comment = self.request.get('comment')

if comment:
    c = Comment(author = author,
        post_id = post_id,
        comment = comment)
c.put()

self.render('front.html', posts = posts, loggedIn = self.user)


class EditPostHandler(BaseHandler):
    def get(self):
        if not self.user:
            self.redirect("/login")
        else :
            post_id = self.request.get('id')
            key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(key)

if self.user.name == post.author:
    self.render('editpost.html', p = post, loggedIn = self.user)
else :
    msg = "You are not authorized to edit this post."
    self.render('message.html', msg = msg)

def post(self):
    post_id = self.request.get('id')
    key = db.Key.from_path('Post', int(post_id), parent = blog_key())
    p = db.get(key)

if self.user.name != p.author:
    self.redirect("/login")
else :
    new_content = self.request.get('editpost')
if new_content:
    p.content = new_content
    p.put()
    self.redirect('/')
else :
    error = "Content cannot be empty."
    self.render("editpost.html", p = p, error = error)


class DeletePostHandler(BaseHandler):
    def get(self):
        if not self.user:
            self.redirect("/login")
        else :
            post_id = self.request.get('id')
            key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(key)

if self.user.name == post.author:
    db.delete(key)
    self.redirect('/')
else :
        self.redirect('/')


class EditCommentHandler(BaseHandler):
    def get(self):
        if not self.user:
            self.redirect("/login")
        else :
            comment_id = self.request.get('id')
            key = db.Key.from_path('Comment', int(comment_id))
            comment = db.get(key)

self.render("editcomment.html",
    comment = comment,
    loggedIn = self.user)

def post(self):
    comment_id = self.request.get('id')
    edit_comment = self.request.get('editcomment')
    key = db.Key.from_path('Comment', int(comment_id))
    comment = db.get(key)
if self.user.name != comment.author:
    self.redirect("/login")
else :
    if edit_comment:
        comment.comment = edit_comment
        comment.put()
        self.redirect("/")
    else :
        self.redirect("/editcomment?id=" + comment_id)


class DeleteCommentHandler(BaseHandler):
    def get(self):
        comment_id = self.request.get('id')
    key = db.Key.from_path('Comment', int(comment_id))
    comment = db.get(key)
if not self.user:
    self.redirect("/login")
else :
    if self.user.name != comment.author:
        self.redirect("/login")
    else :
        db.delete(key)
    self.redirect("/")

class BlogHandler(webapp2.RequestHandler):
    def write(self, * a, ** kw):
        self.response.out.write( * a, ** kw)

def render_str(self, template, ** params):
    return render_str(template, ** params)

def render(self, template, ** kw):
    self.write(self.render_str(template, ** kw))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class MainPage(BlogHandler):
    def get(self):
        self.write('Hello, Udacity!')



def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    likes = db.IntegerProperty(required = True)
    liked_by = db.ListProperty(str)

def render(self):
    self._render_text = self.content.replace('\n', '<br>')
    return render_str("post.html", p = self)

class LikeError(BlogHandler):
    def get(self):
        self.write("You can't like your own post & can only like a post once.")

class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

def post(self):
    subject = self.request.get('subject')
    content = self.request.get('content')

if subject and content:
    p = Post(parent = blog_key(), subject = subject, content = content)
    p.put()
    self.redirect('/blog/%s' % str(p.key().id()))
else :
    error = "subject and content, please!"
    self.render("newpost.html", subject = subject, content = content, error = error)




class Rot13(BlogHandler):
    def get(self):
        self.render('rot13-form.html')

def post(self):
    rot13 = ''
    text = self.request.get('text')
if text:
    rot13 = text.encode('rot13')

    self.render('rot13-form.html', text = rot13)


    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

    PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

    EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(BlogHandler):

    def get(self):
        self.render("signup-form.html")

def post(self):
    have_error = False
    username = self.request.get('username')
    password = self.request.get('password')
    verify = self.request.get('verify')
    email = self.request.get('email')

params = dict(username = username,
    email = email)

if not valid_username(username):
    params['error_username'] = "That's not a valid username."
have_error = True

if not valid_password(password):
    params['error_password'] = "That wasn't a valid password."
    have_error = True
elif password != verify:
    params['error_verify'] = "Your passwords didn't match."
    have_error = True

if not valid_email(email):
    params['error_email'] = "That's not a valid email."
have_error = True

if have_error:
    self.render('signup-form.html', ** params)
else :
    self.redirect('/unit2/welcome?username=' + username)

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
if valid_username(username):
    self.render('welcome.html', username = username)
else :
    self.redirect('/unit2/signup')

app = webapp2.WSGIApplication([('/', MainPage), ('/unit2/rot13', Rot13), ('/unit2/signup', Signup), ('/unit2/welcome', Welcome), ('/blog/?', BlogFront), ('/blog/([0-9]+)', PostPage), ('/blog/newpost', NewPost), ],
    debug = True)
