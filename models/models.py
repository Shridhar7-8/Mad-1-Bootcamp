from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    roles = db.Column(db.String(50), nullable=False, default='user')  # 'admin', 'staff', 'user'
    status = db.Column(db.String(50), nullable=False, default='approved')  # 'pending', 'approved', 'blacklisted'
    
    # Relationships
    posts = db.relationship('Post', foreign_keys='Post.user_id', backref='author', lazy=True, cascade='all, delete-orphan')

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    flagged = db.Column(db.Boolean, default=False)
    

    status = db.Column(db.String(50), nullable=False, default='Open')  # 'Open', 'Closed'
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    assigned_staff = db.relationship('User', foreign_keys=[assigned_staff_id], backref='assigned_posts')


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')  # 'active', 'cancelled'
    booking_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='bookmarks')
    post = db.relationship('Post', foreign_keys=[post_id], backref='bookmarks')
