from flask import (
  Blueprint, render_template, request, 
  flash, redirect, url_for, send_from_directory, session, jsonify, 
  current_app, make_response
)
import logging
from authlib.integrations.flask_client import OAuth
from .models import Like, Photo
from sqlalchemy import asc, text
from . import db
from .models import User
import os
from dotenv import load_dotenv
load_dotenv()

main = Blueprint('main', __name__)

# This is called when the home page is rendered. It fetches all images sorted by filename.
@main.route('/')
def homepage():
  photos = db.session.query(Photo).order_by(asc(Photo.file))
  liked_photo_ids = []
  if 'current_user_id' in session:
    liked_photo_ids_query = db.session.query(Like.photo_id).filter_by(user_id=session['current_user_id']).all()
    # Extract photo IDs from the query result
    liked_photo_ids = [photo_id[0] for photo_id in liked_photo_ids_query]
  return render_template('index.html', photos=photos, liked_photo_ids=liked_photo_ids)


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
                    file = file.filename,
                    user_id = session['current_user_id'])
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
  if 'current_user_id' not in session or editedPhoto.user_id != session['current_user_id']:
    flash('You do not have permission to edit this photo.', 'error')
    return redirect(url_for('main.homepage'))
  else: 
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
  photoToDelete = db.session.query(Photo).filter_by(id = photo_id).one()
  if 'current_user_id' not in session or photoToDelete.user_id != session['current_user_id']:
    flash('You do not have permission to delete this photo.', 'error')
    return redirect(url_for('main.homepage'))
  else: 
    # Previously: Used concatenated SQL, exposing the app to SQL injection attacks
    # Now: SQLAlchemy ORM used, which prevents SQL injection by using parameterized queries instead of unsafe string concatenation
    try:
      filename = photoToDelete.file
      filepath = os.path.join(current_app.config["UPLOAD_DIR"], filename)
      os.unlink(filepath)
      db.session.delete(photoToDelete)
      db.session.commit()
      
      flash('Photo id %s Successfully Deleted' % photo_id)
      return redirect(url_for('main.homepage'))
    except:
      flash('Photo id %s Could Not be Deleted' % photo_id)
      return redirect(url_for('main.homepage'))

@main.route('/toggle_like/<int:photo_id>', methods=['POST'])
def toggle_like(photo_id):
    if 'current_user_id' not in session:
        flash("Please login to like this photo", 'error')
        return redirect(url_for('main.homepage'))

    user_id = session['current_user_id']
    like = Like.query.filter_by(user_id=user_id, photo_id=photo_id).first()

    if like:
        db.session.delete(like)
        flash('Photo unliked', 'success')
    else:
        new_like = Like(user_id=user_id, photo_id=photo_id)
        db.session.add(new_like)
        flash('Photo liked', 'success')
    
    db.session.commit()
    return redirect(url_for('main.homepage'))