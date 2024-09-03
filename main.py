from flask import Flask, render_template, url_for, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashlib import sha256
import random
import string
import sqlite3


def generate_random_string(length=256):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def hash_password(password):
    return sha256(f"{password} Some Salt".encode('utf-8')).hexdigest()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


TOKENS = {}


class Articles(db.Model):
    __tablename__ = 'Articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Article %r>' % self.id


class Accounts(db.Model):
    __tablename__ = 'Accounts'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False, unique=True)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.id


@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def index():
    userToken = request.cookies.get('TOKEN')
    username = ''
    try:
        if userToken:
            username = TOKENS[userToken]
    finally:
        return render_template('index.html', username=username)


@app.route('/about')
def about():
    userToken = request.cookies.get('TOKEN')
    username = ''
    try:
        if userToken:
            username = TOKENS[userToken]
    finally:
        return render_template('about.html', username=username)


@app.route('/posts')
def posts():
    articles = Articles.query.order_by(Articles.date.desc()).all()
    userToken = request.cookies.get('TOKEN')
    username = ''
    try:
        if userToken:
            username = TOKENS[userToken]
    finally:
        return render_template('posts.html', articles=articles, username=username)


@app.route('/posts/<int:id>')
def post_detail(_id):
    article = Articles.query.get(_id)
    userToken = request.cookies.get('TOKEN')
    username = ''
    try:
        if userToken:
            username = TOKENS[userToken]
    finally:
        return render_template('post_detail.html', article=article, username=username)


@app.route('/posts/<int:id>/del')
def post_delete(_id):
    article = Articles.query.get_or_404(_id)

    try:
        db.session.delete(article)
        db.session.commit()
        return redirect('/posts')
    except:
        return "An error occurred while deleting an article"


@app.route('/posts/<int:id>/update', methods=['POST', 'GET'])
def post_update(id):
    article = Articles.query.get(id)
    if request.method == "POST":
        article.title = request.form['title']
        article.intro = request.form['intro']
        article.text = request.form['text']

        try:
            db.session.commit()
            return redirect('/posts')
        except:
            return "An error occurred while editing an article"
    else:
        userToken = request.cookies.get('TOKEN')
        username = ''
        try:
            if userToken:
                username = TOKENS[userToken]
        finally:
            return render_template('post_update.html', article=article, username=username)


@app.route('/create-article', methods=['POST', 'GET'])
def create_article():
    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']

        article = Articles(title=title, intro=intro, text=text)

        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/posts')
        except:
            return "An error occurred while adding an article"
    else:
        userToken = request.cookies.get('TOKEN')
        username = ''
        try:
            if userToken:
                username = TOKENS[userToken]
        finally:
            return render_template('create-article.html', username=username)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "GET":
        if "logout" in request.args.keys():
            print(1231)
            response = make_response('redirected')
            userToken = request.cookies.get('TOKEN')
            TOKENS.pop(userToken, None)
            response.set_cookie('TOKEN', '', expires=0)
            return redirect('/')
        elif "fail" in request.args.keys():
            return render_template('auth.html', error="Incorrect credentials")
        else:
            return render_template('auth.html')
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        password_verify = request.form['confirm_password']

        try:
            if password == password_verify:
                err = 'Successful'
                try:
                    db.session.add(Accounts(username=username, password=hash_password(password), email=email))
                    db.session.commit()
                except Exception as error:
                    err = "Username Claimed"
                return render_template('auth.html', error=err)
            else:
                return render_template('auth.html', error="Password Mismatch")
        except:
            return "An error occurred while adding an article"



@app.route('/', methods=['POST'])
def signin():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)
        password_db_raw = Accounts.query.filter_by(username=username).first()
        if password_db_raw is None:
            return redirect('/signup?fail')
        password_db = password_db_raw.password
        if password_db == password_hash:
            # Login
            response = make_response(render_template('index.html', username=username))
            user_token = generate_random_string()
            TOKENS[user_token] = username
            response.set_cookie('TOKEN', user_token)
            return response
        else:
            return redirect('/signup?fail')



with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)