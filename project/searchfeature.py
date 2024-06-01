
from flask import (
  Blueprint, request, 
  flash, redirect, render_template, url_for
)
import logging
from authlib.integrations.flask_client import OAuth
from .models import Photo
from sqlalchemy import asc, text
from . import db
from dotenv import load_dotenv
load_dotenv()

searchfeature = Blueprint('searchfeature', __name__)
@searchfeature.route('/search')
def search():
  return render_template('search.html')

# @limiter.limit("10 per minute")
@searchfeature.route("/filterSearch", methods=['GET'])
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
