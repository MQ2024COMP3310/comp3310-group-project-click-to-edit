from flask import (
  Blueprint, render_template, request, 
  flash, redirect, url_for,  session, 
  current_app
)
from authlib.integrations.flask_client import OAuth
from .models import Like, Photo
from sqlalchemy import asc, text
import secrets
from . import db
from .models import User
import os
from dotenv import load_dotenv
load_dotenv()

auth = Blueprint('auth', __name__)

#loads the sensitive information from .env file, hence they do not need to be hard coded into the source code and risk possible leak if source code is exposed.
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID') 
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

oauth = OAuth(current_app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_params=None,
    access_token_params=None,
    client_kwargs={'scope': 'openid profile email'},
    redirect_uri='http://localhost:8000/login/authorized',
    server_metadata_url= 'https://accounts.google.com/.well-known/openid-configuration',
)

@auth.route('/login')
def login():
    # State parameter is introduced to prevent possible CSRF attack.
    # Generates a random state token using python secret module
    state = secrets.token_urlsafe(16)
    # Saves the state token in the session
    session['oauth_state'] = state
    # Creates the mew authorization URL using the state parameter
    redirect_uri = url_for('auth.authorized', _external=True)
    return google.authorize_redirect(redirect_uri, state=state)

@auth.route('/login/authorized')
def authorized():
    # Verify the state parameter
    state = request.args.get('state')
    if state != session.pop('oauth_state', None):
        flash('Invalid state parameter.', 'error')
        return redirect(url_for('main.homepage'))
    
    #using authorisation flow to prevent leakage of access token
    token = google.authorize_access_token()
    if not token:
        flash('Login failed.', 'error')
        return redirect(url_for('main.homepage'))

    session['google_token'] = token
    userinfo_url = 'https://openidconnect.googleapis.com/v1/userinfo'
    me = google.get(userinfo_url, token=token)
    if me.ok:
        user_info = me.json()
        
        # Save user info to the database
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        profile_pic = user_info.get('picture')

        user = User.query.filter_by(google_id=google_id).first()
        if user is None:
            flash("New user time")
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                profile_pic=profile_pic
            )
            db.session.add(user)
            db.session.commit()
        session['current_user_id'] = user.id
        flash('Login successful!', 'success')
        return redirect(url_for('main.homepage'))  
    else:
        #proper error handling needs to be applied although the codes here could not catch the error when the user permission was not given
        flash('Login unsuccessful', 'error')
        return redirect(url_for('main.homepage'))


@auth.route('/logout')
def logout():
    session.pop('google_token', None)
    session.clear()
    return redirect(url_for('main.homepage'))
