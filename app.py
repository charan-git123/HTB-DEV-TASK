import hashlib
import os
import re
import secrets
import time
from datetime import timedelta
from functools import wraps

import click
from dotenv import load_dotenv
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from sqlalchemy import URL, delete, select, func, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash
from catalog import MOVIES, MOVIE_IDS

load_dotenv()
db = SQLAlchemy()
csrf = CSRFProtect()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.BigInteger, nullable=False, default=lambda:int(time.time()))

class LoginSession(db.Model):
    __tablename__ = 'login_sessions'
    token_hash = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    expires_at = db.Column(db.BigInteger, nullable=False)

class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    movie_id = db.Column(db.Integer, primary_key=True)
    watched = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.BigInteger, nullable=False, default=lambda:int(time.time()))

class AuthAttempt(db.Model):
    __tablename__ = 'auth_attempts'
    id = db.Column(db.Integer, primary_key=True)
    bucket = db.Column(db.String(64), index=True, nullable=False)
    created_at = db.Column(db.BigInteger, nullable=False, index=True)


def create_app(test_config=None):
    app = Flask(__name__)
    secret = os.getenv('SECRET_KEY', '')
    if not test_config and (len(secret)<32 or secret.startswith('replace-')):
        raise RuntimeError('Set SECRET_KEY in .env to a random value of at least 32 characters. See README.md.')
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://','mysql+pymysql://',1)
    if not database_url:
        database_url = URL.create('mysql+pymysql', username=os.getenv('MYSQL_USER','root'), password=os.getenv('MYSQL_PASSWORD','sqlcharan'), host=os.getenv('MYSQL_HOST','127.0.0.1'), port=int(os.getenv('MYSQL_PORT','3306')), database=os.getenv('MYSQL_DATABASE','netflix_clone'), query={'charset':'utf8mb4'})
    production = os.getenv('APP_ENV') == 'production'
    app.config.update(SECRET_KEY=secret, SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False, SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping':True,'pool_recycle':280},
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=production or os.getenv('SECURE_COOKIES','false').lower()=='true',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7), MAX_CONTENT_LENGTH=16384)
    if test_config: app.config.update(test_config)
    db.init_app(app)
    csrf.init_app(app)

    @app.before_request
    def load_user():
        g.user = None
        token = session.get('auth_token')
        if token:
            login = db.session.get(LoginSession, hashlib.sha256(token.encode()).hexdigest())
            if login and login.expires_at > time.time():
                g.user = db.session.get(User, login.user_id)
            else: session.pop('auth_token', None)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.endpoint != 'static': response.headers['Cache-Control']='no-store'
        if production: response.headers['Strict-Transport-Security']='max-age=31536000'
        return response

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user: return redirect(url_for('login'))
            return view(*args, **kwargs)
        return wrapped

    def authenticate(user):
        old_token=session.get('auth_token')
        if old_token: db.session.execute(delete(LoginSession).where(LoginSession.token_hash==hashlib.sha256(old_token.encode()).hexdigest()))
        session.clear()
        token=secrets.token_urlsafe(32)
        db.session.add(LoginSession(token_hash=hashlib.sha256(token.encode()).hexdigest(),user_id=user.id,expires_at=int(time.time())+604800))
        db.session.execute(delete(LoginSession).where(LoginSession.expires_at<int(time.time())))
        db.session.commit()
        session['auth_token']=token
        session.permanent=True

    def limited(email):
        now=int(time.time())
        bucket=hashlib.sha256(email.encode()).hexdigest()
        db.session.execute(delete(AuthAttempt).where(AuthAttempt.created_at<now-900))
        count=db.session.scalar(select(func.count()).select_from(AuthAttempt).where(AuthAttempt.bucket==bucket))
        if count>=10:
            db.session.commit()
            return True
        db.session.add(AuthAttempt(bucket=bucket,created_at=now))
        db.session.commit()
        return False

    @app.get('/')
    def home(): return render_template('home.html', movies=MOVIES)

    @app.route('/signup', methods=['GET','POST'])
    def signup():
        if g.user: return redirect(url_for('browse'))
        errors={}
        values={'name':'','email':request.args.get('email','')[:254]}
        if request.method=='POST':
            values={'name':request.form.get('name','').strip(), 'email':request.form.get('email','').strip().lower()}
            password=request.form.get('password','')
            if not 2<=len(values['name'])<=80: errors['name']='Enter a name between 2 and 80 characters.'
            if len(values['email'])>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', values['email']): errors['email']='Enter a valid email address.'
            if not 8<=len(password)<=128: errors['password']='Use between 8 and 128 characters.'
            if password!=request.form.get('confirm_password'): errors['confirm_password']='Your passwords do not match.'
            if not errors:
                if limited(values['email']): return render_template('auth.html', mode='signup',values=values,errors={'general':'Too many attempts. Please try again in 15 minutes.'}),429
                user=User(name=values['name'], email=values['email'],password_hash=generate_password_hash(password,method='scrypt'))
                db.session.add(user)
                try: db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    errors['email']='An account already uses this email. Please sign in.'
                else:
                    authenticate(user)
                    flash('Your account is ready. Find your next favourite.','success')
                    return redirect(url_for('browse'))
        return render_template('auth.html', mode='signup',errors=errors,values=values), (400 if errors else 200)

    @app.route('/login', methods=['GET','POST'])
    def login():
        if g.user: return redirect(url_for('browse'))
        errors={}; values={'email':''}
        if request.method=='POST':
            email=request.form.get('email','').strip().lower()[:254]
            values['email']=email
            if limited(email): return render_template('auth.html',mode='login',errors={'general':'Too many attempts. Please try again in 15 minutes.'},values=values),429
            user=db.session.scalar(select(User).where(User.email==email))
            password=request.form.get('password','')
            # A dummy hash keeps unknown-user and wrong-password work comparable.
            valid=check_password_hash(user.password_hash if user else app.config['DUMMY_HASH'],password[:128])
            if not user or not valid or len(password)>128: errors['general']='Incorrect email or password. Please try again.'
            else:
                authenticate(user)
                return redirect(url_for('browse'))
        return render_template('auth.html',mode='login',errors=errors,values=values), (400 if errors else 200)

    @app.post('/logout')
    def logout():
        token=session.get('auth_token')
        if token:
            db.session.execute(delete(LoginSession).where(LoginSession.token_hash==hashlib.sha256(token.encode()).hexdigest()))
            db.session.commit()
        session.clear()
        return redirect(url_for('home'))

    @app.get('/browse')
    @login_required
    def browse():
        saved={row.movie_id:row for row in db.session.scalars(select(Watchlist).where(Watchlist.user_id==g.user.id))}
        return render_template('browse.html',movies=MOVIES,saved=saved,list_only=False)

    @app.get('/my-list')
    @login_required
    def my_list():
        saved={row.movie_id:row for row in db.session.scalars(select(Watchlist).where(Watchlist.user_id==g.user.id))}
        return render_template('browse.html',movies=[m for m in MOVIES if m['id'] in saved],saved=saved,list_only=True)

    @app.post('/watchlist/<int:movie_id>')
    @login_required
    def update_watchlist(movie_id):
        if movie_id not in MOVIE_IDS: abort(404)
        action=request.form.get('action')
        if action not in {'add','remove','watched','unwatched'}: abort(400)
        item=db.session.get(Watchlist,(g.user.id,movie_id))
        if action=='add' and not item:
            db.session.add(Watchlist(user_id=g.user.id,movie_id=movie_id))
        elif action=='remove' and item: db.session.delete(item)
        elif action in {'watched','unwatched'}:
            if not item: abort(404)
            item.watched=action=='watched'
        try: db.session.commit()
        except IntegrityError: db.session.rollback() # Simultaneous repeated add is idempotent.
        flash({'add':'Added to My List.','remove':'Removed from My List.','watched':'Marked as watched.','unwatched':'Marked as unwatched.'}[action],'success')
        return redirect(url_for('my_list' if request.form.get('return_to')=='my_list' else 'browse'))

    @app.get('/health')
    def health():
        try:
            db.session.execute(select(User.id).limit(1))
            return jsonify(status='ok')
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify(status='unavailable'),503

    @app.errorhandler(CSRFError)
    def csrf_error(error): return render_template('error.html',code=400,message='This form has expired. Return to the page and try again.'),400

    @app.errorhandler(404)
    def not_found(error): return render_template('error.html',code=404,message='We couldn’t find that page.'),404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template('error.html',code=500,message='Something went wrong. Please try again shortly.'),500

    @app.cli.command('init-db')
    def init_db():
        """Create missing tables without deleting existing accounts or saved titles."""
        db.create_all()
        click.echo('Database tables are ready.')

    app.config['DUMMY_HASH']=generate_password_hash(secrets.token_urlsafe(24),method='scrypt')
    return app
