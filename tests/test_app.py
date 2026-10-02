"""Uses an isolated MySQL database when TEST_DATABASE_URL is set; SQLite fallback for fast checks.
Never point TEST_DATABASE_URL at a database containing real data: tables are recreated.
"""
import os
import re
import pytest
from sqlalchemy import select
from werkzeug.security import check_password_hash
from app import create_app, db, User, Watchlist, LoginSession

@pytest.fixture
def app(tmp_path):
    app=create_app({'TESTING':True,'SECRET_KEY':'test-only-secret-key-32-characters-long',
        'SQLALCHEMY_DATABASE_URI':os.getenv('TEST_DATABASE_URL', 'sqlite:///'+str(tmp_path/'test.db')),
        'SESSION_COOKIE_SECURE':False})
    with app.app_context():
        db.drop_all();db.create_all()
    yield app
    with app.app_context():
        db.session.remove();db.drop_all();db.engine.dispose()

@pytest.fixture
def client(app): return app.test_client()

def test_production_requires_external_mysql_configuration(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'production-test-secret-key-that-is-long-enough')
    monkeypatch.delenv('DATABASE_URL', raising=False)
    for name in ('MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE'):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match='MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE'):
        create_app()

    for name, value in {
        'MYSQL_HOST': '127.0.0.1',
        'MYSQL_USER': 'render_test_user',
        'MYSQL_PASSWORD': 'render_test_password',
        'MYSQL_DATABASE': 'render_test_database',
    }.items():
        monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match='not a loopback address'):
        create_app()

def token(client,path='/login'):
    response=client.get(path)
    return re.search(r'name="csrf_token" value="([^"]+)"',response.text).group(1)

def signup(client,email='alice@example.test'):
    return client.post('/signup',data={'csrf_token':token(client,'/signup'),'name':'Alice','email':email,'password':'test-password-123','confirm_password':'test-password-123'})

def logout(client):return client.post('/logout',data={'csrf_token':token(client,'/browse')})

def login(client,password='test-password-123'):
    return client.post('/login',data={'csrf_token':token(client),'email':'alice@example.test','password':password})

def change(client,action,movie=1):
    return client.post(f'/watchlist/{movie}',data={'csrf_token':token(client,'/browse'),'action':action})

def test_accounts_passwords_duplicate_and_sessions(app,client):
    assert signup(client).status_code==302
    with app.app_context():
        user=db.session.scalar(select(User))
        assert user.password_hash.startswith('scrypt:')
        assert user.password_hash!='test-password-123'
        assert check_password_hash(user.password_hash,'test-password-123')
        assert db.session.scalar(select(LoginSession))
    assert client.get('/browse').status_code==200
    assert logout(client).status_code==302
    assert client.get('/browse').status_code==302
    assert signup(client).status_code==400
    assert login(client,'incorrect').status_code==400
    assert login(client).status_code==302
    logout(client)
    with app.app_context(): assert db.session.scalar(select(LoginSession)) is None

def test_watchlist_persists_and_is_private(app,client):
    signup(client)
    assert change(client,'add').status_code==302
    change(client,'add')
    assert 'Stranger Things' in client.get('/my-list').text
    assert change(client,'watched').status_code==302
    with app.app_context():
        items=list(db.session.scalars(select(Watchlist)))
        assert len(items)==1 and items[0].watched
    logout(client)
    other=app.test_client();signup(other,'bob@example.test')
    assert 'Your next favourite belongs here.' in other.get('/my-list').text
    change(other,'remove')
    login(client)
    assert '✓ Watched' in client.get('/my-list').text
    change(client,'unwatched')
    with app.app_context(): assert not db.session.scalar(select(Watchlist)).watched
    change(client,'remove')
    assert 'Your next favourite belongs here.' in client.get('/my-list').text

def test_csrf_validation_and_unauthenticated_access(client):
    assert client.post('/signup',data={'email':'x@y.com'}).status_code==400
    assert client.get('/my-list').status_code==302
    response=client.post('/signup',data={'csrf_token':token(client,'/signup'),'name':'A','email':'bad','password':'short','confirm_password':'different'})
    assert response.status_code==400
    assert 'Enter a valid email' in response.text
    signup(client)
    assert change(client,'add',999).status_code==404
    assert change(client,'invalid').status_code==400

def test_rate_limit(client):
    for _ in range(10): assert login(client,'bad').status_code==400
    assert login(client,'bad').status_code==429

def test_pages_and_security_headers(client):
    for path in ['/','/signup','/login']:
        response=client.get(path)
        assert response.status_code==200
        assert response.headers['X-Frame-Options']=='DENY'
        assert 'Content-Security-Policy' in response.headers
    assert client.get('/health').json=={'status':'ok'}
    assert client.get('/missing').status_code==404

def test_catalog_search_and_movie_details(client):
    signup(client)
    response=client.get('/browse')
    assert response.status_code==200
    assert 'id="catalog-search"' in response.text
    assert 'data-catalog-search' in response.text
    assert 'data-movie-card' in response.text
    assert 'data-search-text="stranger things sci-fi series' in response.text
    assert 'IMDb <strong>★ 8.6</strong>' in response.text
    assert '5 seasons' in response.text
    assert '42 episodes' in response.text
    assert 'not live IMDb data' in response.text
    assert client.get('/static/app.js').status_code==200
    assert client.get('/static/artwork.css').status_code==200

def test_home_has_original_animated_monogram(client):
    response=client.get('/')
    assert response.status_code==200
    assert 'class="hero-monogram"' in response.text
    assert 'class="home-rating">★ 8.6</span>' in response.text
