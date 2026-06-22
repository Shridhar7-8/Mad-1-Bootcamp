from flask import Flask, render_template_string
from models.models import db, User, Post
from werkzeug.security import generate_password_hash
from controllers.controllers import controllers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///milestone1.sqlite'
app.config['SECRET_KEY'] = 'milestone1_secret_key'


db.init_app(app)
app.register_blueprint(controllers)


def create_admin_user():
    admin_email = 'admin@example.com'
    admin_user = User.query.filter_by(email=admin_email).first()
    
    if not admin_user:
        admin_username = 'admin'
        
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        admin_user = User(
            username=admin_username, 
            email=admin_email, 
            password=hashed_password, 
            roles='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")


with app.app_context():
    db.create_all()
    create_admin_user()



if __name__ == "__main__":

    app.run(debug=True)
