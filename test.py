#Here are the lists of tests we have incorporated to test the authentication method

#Static testing 
#Through Manual code Review were conducted
#Static analysis through CodeQL to seek improvements in coding practices

#Dynamic testing
#Unit testing - rerunning test after every changes in the code
#implemented pytest for dynamic testing of the authentication feature

import pytest
from flask import session
from project import create_app, db
from project.models import Photo, User

#creating the app
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    yield app

@pytest.fixture
def client(app):
    return app.test_client()
#
@pytest.fixture
def init_database(app):
    with app.app_context():
        db.create_all()

        # Create a test user
        test_user = User(google_id='123', email='test@example.com', name='Test User', profile_pic='test.jpg')
        db.session.add(test_user)
        db.session.commit()

        yield  

def test_csrf_attack(client):
    # Simulating a malicious request without the actual CSRF token
    response = client.get('/login/authorized?state=randomstatesss')
    assert response.status_code == 400 

def test_flawed_redirect_uri(client, init_database):
    # Simulate a flawed redirect_uri
    response = client.get('/login/authorized?state=test_state&redirect_uri=https://randomwebsitesssssssssssssss.com')
    assert response.status_code == 400 

# Task 8 & 9: These tests are not completely implemented but the test comments explain the reasoning

def test_like_unauthenticated(client, init_package):
    """ Ensure unauthenticated users cannot toggle likes. """
    response = client.post('/toggle_like/1', follow_redirects=True)
    assert 'Please login to like this photo' in response.get_data(as_text=True)
    assert response.status_code == 302 

def test_toggle_like_authenticated(client, init_database):
    """ Ensure authenticated users can add and remove likes. """
    with client:
        with client.session_transaction() as sess:
            sess['current_user_id'] = 1  # Simulate user login

        # Toggle like to add
        response = client.post('/toggle_like/1', follow_redirects=True)
        assert 'Photo liked' in response.get_data(as_text=True)

        # Toggle like to remove
        response = client.post('/toggle_like/1', follow_redirects=True)
        assert 'Photo unliked' in response.get_data(as_text=True)

def test_csrf_protection(client, init_database):
    """ Ensure CSRF protection is enforced. """
    with client:
        with client.session_transaction() as sess:
            sess['current_user_id'] = 1  # Simulate user login

        # Attempt to post without CSRF token
        response = client.post('/toggle_like/1')
        assert response.status_code == 400  # Check for the CSRF error code
        assert 'The CSRF token is missing.' in response.get_data(as_text=True)   

# Task 8 and 9 Feature 1

def test_search_no_results(client):
    response = client.get('/filterSearch', query_string={'search': 'nonexistent'})
    assert response.status_code == 200
    assert b"No photos found" in response.data

def test_search_with_results(client):
    # Add a photo to the database
    with client.application.app_context():
        photo = Photo(name='test_user', caption='test_caption', description='test_description', file='test.jpg')
        db.session.add(photo)
        db.session.commit()

    response = client.get('/filterSearch', query_string={'search': 'test_caption'})
    assert response.status_code == 200
    assert b"test_caption" in response.data
# Check for SQL injection
def test_search_sql_injection(client):
    response = client.get('/filterSearch', query_string={'search': "'; DROP TABLE photo; --"})
    assert response.status_code == 200
    assert b"No photos found" in response.data

# Check for CSS with malicious scripts
def test_search_xss(client):
    response = client.get('/filterSearch', query_string={'search': "<script>alert('xss');</script>"})
    assert response.status_code == 200
    assert b"&lt;script&gt;alert(&#39;xss&#39;);&lt;/script&gt;" in response.data

