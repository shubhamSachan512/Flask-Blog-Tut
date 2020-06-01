from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import pymysql
import os
import math
from werkzeug.utils import secure_filename


with open('templates/config.json', 'r') as c:
    params = json.load(c)["params"]

app =   Flask(__name__)
app.secret_key = 'superSecretKey'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['email_userId'],
    MAIL_PASSWORD=params['email_password']
)
app.config['UPLOAD_FOLDER']=params['upload_location']
sendMail = Mail(app);

if(params['local_server']):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email_id = db.Column(db.String(30), nullable=False)
    phone_no = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    posted_by = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    date = db.Column(db.String(20), nullable=True)
    img_file = db.Column(db.String(20), nullable=True)
    subheading = db.Column(db.String(50), nullable=False)


@app.route("/", methods=['GET'])
def home():
    posts_1 = Posts.query.filter_by().all()
    page = request.args.get('page')
    last = math.ceil(len(posts_1)/params['no_of_post'])
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts_1 = posts_1[(page-1)*int(params['no_of_post']):(page-1)*int(params['no_of_post']) + int(params['no_of_post'])]
    if page==1:
        next = "?page=" + str(page + 1)
        print("in if --- " + next)
        prev = '#'

    elif(page==last):
        next = '#'
        print("in elif --- " + next)
        prev = "?page=" + str(page - 1)

    else:
        prev = "?page=" + str(page - 1)
        next = "?page=" + str(page + 1)
        print("in else --- " + next)

    return render_template('index.html', params=params, posts=posts_1, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/contact", methods = ['GET','POST'])
def contact():
    if request.method=='POST':
        '''add entry to db'''
        name = request.form.get('name')
        message = request.form.get('message')
        email = request.form.get('email')
        phone = request.form.get('phone')
        entry = Contact(name = name, phone_no = phone, message = message, email_id = email, date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        sendMail.send_message('New Message from ' + name,
                              sender=email,
                              recipients=[params['email_userId']],
                              body=message + "\n" + phone + "\n" + email)
    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods= ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params = params, posthtml=post)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username==params['admin_user'] and userpass==params['admin_pwd']):
            session['user'] = username
            #         set the session variable
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params)
    # redirect to admin panel
    return render_template('login.html', params=params)

# @app.route("/addNew/<string:sno>", methods= ['GET','POST'])
# def addNew(sno):
#     if 'user' in session and session['user'] == params['admin_user']:
#         if request.method == 'POST':
#             title = request.form.get('title')
#             tagLine = request.form.get('tagLine')
#             postContent = request.form.get('postContent')
#             slug = request.form.get('slug')
#             img_file = request.form.get('img_file')
#             posted_by = request.form.get('posted_by')
#             if sno=='0':
#                 postEntry = Posts(title = title, content = postContent, slug = slug,
#                               subheading = tagLine, img_file = img_file, date = datetime.now(), posted_by = posted_by)
#                 db.session.add(postEntry)
#                 db.session.commit()
#         return render_template('addNew.html', params=params, sno=sno)

@app.route("/edit/<string:sno>", methods= ['GET','POST'])
def edit(sno):
    global counter
    if 'user' in session and session['user'] == params['admin_user']:
        # print("I reached here")
        if request.method == 'POST':
            # print("jjjjjj")
            title = request.form.get('title')
            tagLine = request.form.get('tagLine')
            postContent = request.form.get('postContent')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            posted_by = request.form.get('posted_by')
            # print(posted_by)

            if sno=='0':
                postEntry = Posts(title = title, content = postContent, slug = slug,
                              subheading = tagLine, img_file = img_file, date = datetime.now(), posted_by = posted_by)
                db.session.add(postEntry)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.content = postContent
                post.slug = slug
                post.subheading = tagLine
                post.img_file = img_file
                post.posted_by = posted_by
                db.session.commit()
                return redirect('/edit/'+sno)
        # print("I reached to end")
        post = Posts.query.filter_by(sno=sno).first()
        # counter=post.sno
        if post is None:
            # global counter
            counter=0
            # print("counter")
        else:
            counter=post.sno
        # print(counter)
        return render_template('edit.html', params = params, post=post, counter=counter)

@app.route("/uploader", methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'].secure_filename(f.filename)))
            flash('File successfully uploaded')
            return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


app.run(debug=True)
