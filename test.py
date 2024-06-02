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
from project.models import User

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