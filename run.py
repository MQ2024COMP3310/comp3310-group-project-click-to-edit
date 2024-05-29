from project import create_app
from flask import Flask
from dotenv import load_dotenv
import os

if __name__ == '__main__':
  app = create_app()
  app.run(host = '0.0.0.0', port = 8000, debug=True)
  
app.secret_key = os.getenv('SECRET_KEY')

from authlib.integrations.flask_client import OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    authorize_params=None,
    access_token_params=None,
    client_kwargs={'scope': 'openid profile email'},
    redirect_uri='http://localhost:8000/login/authorized',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)