from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='approved') # aprroved, pending and blacklisted
    posts = db.relationship('Post', backref = "author", lazy = True, cascade = 'all, delete-orphan')
    roles = db.Column(db.String(50), nullable=False, default='user')

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    flagged = db.Column(db.Boolean, default=False)