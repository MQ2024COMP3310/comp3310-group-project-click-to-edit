from . import db

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    caption = db.Column(db.String(250), nullable=False)
    file = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(600), nullable=True)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'           : self.id,
           'name'         : self.name,
           'caption'      : self.caption,
           'file'         : self.file,
           'desc'         : self.description,
       }
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Adding a primary key for the User model
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(250), nullable=True)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'google_id': self.google_id,
            'email': self.email,
            'name': self.name,
            'profile_pic': self.profile_pic,
        }