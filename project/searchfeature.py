
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

# Task 8 & 9 : Feature 1
@searchfeature.route('/search')
def search():
  return render_template('search.html')

# Task 8 & 9 : Feature 1
@searchfeature.route("/filterSearch", methods=['GET'])
def searchKeyword():
  # Get the keyword submitted by the user as a query parameter
  keyword = request.args.get('search')
  # Every keyword is logged, to detect malicious activities
  logging.info('User search input', keyword)
  # Prepare the search pattern for SQL LIKE operation, wrapping the keyword with wildcards
  search_pattern = f'%{keyword}%'
      # Parameterised Queries: SQLAlchemy ORM being used -> converts Python code to SQL statements through parameterized queries
      # Hence, any input from the client side is treated as data, rather than executable SQL code
      # Preventing SQL injections.
    # Query the Photo database table to find photos where the caption, name, or description matches the search pattern
  photos = db.session.query(Photo).filter((Photo.caption.like(search_pattern)) 
                                          |(Photo.name.like(search_pattern)) 
                                          |(Photo.description.like(search_pattern))).all()
  if not photos:
    flash("No photos found related to \"" + keyword + "\"")
    return redirect(url_for('main.homepage'))
  else :
    return render_template('index.html', photos=photos)
