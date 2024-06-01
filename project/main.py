from flask import (
  Blueprint, render_template, request, 
  flash, redirect, url_for, send_from_directory, session, jsonify, 
  current_app, make_response
)
import logging
from authlib.integrations.flask_client import OAuth
from .models import Photo
from sqlalchemy import asc, text
from . import db
from .models import User
import os
import secrets
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

main = Blueprint('main', __name__)
main.secret_key = os.urandom(24)
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
limiter = Limiter(
    get_remote_address,
    app=main,
    default_limits=[],
    storage_uri="memory://",
)

# This is called when the home page is rendered. It fetches all images sorted by filename.
@main.route('/')
def homepage():
  photos = db.session.query(Photo).order_by(asc(Photo.file))
  return render_template('index.html', photos=photos)

@main.route('/search')
def search():
  return render_template('search.html')

@limiter.limit("10 per minute")
@main.route("/filterSearch", methods=['GET'])
def searchKeyword():
  keyword = request.args.get('search')
  logging.info('User search input', keyword)
  search_pattern = f'%{keyword}%'
  photos = db.session.query(Photo).filter((Photo.caption.like(search_pattern)) 
                                          |(Photo.name.like(search_pattern)) 
                                          |(Photo.description.like(search_pattern))).all()
  if not photos:
    flash("No photos found related to \"" + keyword + "\"")
    return redirect(url_for('main.homepage'))
  else :
    return render_template('index.html', photos=photos)

@main.route('/uploads/<name>')
def display_file(name):
  return send_from_directory(current_app.config["UPLOAD_DIR"], name)

# Upload a new photo
@main.route('/upload/', methods=['GET','POST'])
def newPhoto():
  if request.method == 'POST':
    file = None
    if "fileToUpload" in request.files:
      file = request.files.get("fileToUpload")
    else:
      flash("Invalid request!", "error")

    if not file or not file.filename:
      flash("No file selected!", "error")
      return redirect(request.url)

    filepath = os.path.join(current_app.config["UPLOAD_DIR"], file.filename)
    file.save(filepath)

    newPhoto = Photo(name = request.form['user'], 
                    caption = request.form['caption'],
                    description = request.form['description'],
                    file = file.filename)
    db.session.add(newPhoto)
    flash('New Photo %s Successfully Created' % newPhoto.name)
    db.session.commit()
    return redirect(url_for('main.homepage'))
  else:
    return render_template('upload.html')

# This is called when clicking on Edit. Goes to the edit page.
@main.route('/photo/<int:photo_id>/edit/', methods = ['GET', 'POST'])
def editPhoto(photo_id):
  editedPhoto = db.session.query(Photo).filter_by(id = photo_id).one()
  if request.method == 'POST':
    if request.form['user']:
      editedPhoto.name = request.form['user']
      editedPhoto.caption = request.form['caption']
      editedPhoto.description = request.form['description']
      db.session.add(editedPhoto)
      db.session.commit()
      flash('Photo Successfully Edited %s' % editedPhoto.name)
      return redirect(url_for('main.homepage'))
  else:
    return render_template('edit.html', photo = editedPhoto)


# This is called when clicking on Delete. 
@main.route('/photo/<int:photo_id>/delete/', methods = ['GET','POST'])
def deletePhoto(photo_id):
  fileResults = db.session.execute(text('select file from photo where id = ' + str(photo_id)))
  filename = fileResults.first()[0]
  filepath = os.path.join(current_app.config["UPLOAD_DIR"], filename)
  os.unlink(filepath)
  db.session.execute(text('delete from photo where id = ' + str(photo_id)))
  db.session.commit()
  
  flash('Photo id %s Successfully Deleted' % photo_id)
  return redirect(url_for('main.homepage'))


  
@main.route('/login')
def login():
    # State parameter is introduced to prevent possible CSRF attack.
    # Generates a random state token using python secret module
    state = secrets.token_urlsafe(16)
    # Saves the state token in the session
    session['oauth_state'] = state
    # Creates the mew authorization URL using the state parameter
    redirect_uri = url_for('main.authorized', _external=True)
    return google.authorize_redirect(redirect_uri, state=state)

@main.route('/login/authorized')
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
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                profile_pic=profile_pic
            )
            db.session.add(user)
            db.session.commit()
        
        flash('Login successful!', 'success')
        return redirect(url_for('main.homepage'))  
    else:
        #proper error handling needs to be applied although the codes here could not catch the error when the user permission was not given
        flash('Login unsuccessful', 'error')
        return redirect(url_for('main.homepage'))


@main.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('main.homepage'))


