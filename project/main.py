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

main = Blueprint('main', __name__)
main.secret_key = os.urandom(24)

oauth = OAuth(current_app)
google = oauth.register(
    name='google',
    authorize_params=None,
    access_token_params=None,
    client_kwargs={'scope': 'openid profile email'},
    redirect_uri='http://localhost:8000/login/authorized',
    server_metadata_url= 'https://accounts.google.com/.well-known/openid-configuration',
)

# This is called when the home page is rendered. It fetches all images sorted by filename.
@main.route('/')
def homepage():
  photos = db.session.query(Photo).order_by(asc(Photo.file))
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
    redirect_uri = url_for('main.authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@main.route('/login/authorized')
def authorized():
    logging.debug('Authorized route accessed')
    token = google.authorize_access_token()
    if not token:
        logging.error('Token is missing')
        flash('Login failed.', 'error')
        return redirect(url_for('main.homepage'))

    logging.debug(f'Token received: {token}')
    session['google_token'] = token
    userinfo_url = 'https://openidconnect.googleapis.com/v1/userinfo'
    me = google.get(userinfo_url, token=token)
    if me.ok:
        try:
            user_info = me.json()
            logging.debug(f'User info: {user_info}')
            
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
            return redirect(url_for('main.homepage'))  # Redirect to the homepage
        except ValueError:
            logging.error("JSON decode error: Invalid JSON received")
            flash("Failed to decode user info from Google", "error")
    else:
        logging.error("Failed to fetch user info: %s", me.text)
        flash("Failed to fetch user info from Google", "error")

    return redirect(url_for('main.homepage')) 

@main.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('main.homepage'))


