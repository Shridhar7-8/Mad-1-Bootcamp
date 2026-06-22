from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask import url_for
from flask import request, flash
from flask import session
from models.models import User, db, Post

controllers = Blueprint('controllers', __name__)

def authorize_roles(allowed_roles):
    if 'user_id' not in session:
        return False
    return session.get('role') in allowed_roles


@controllers.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or Email already registered.')
            return redirect(url_for('controllers.register'))
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
      
        status = 'pending' if role == 'staff' else 'approved'
        
        new_user = User(
            username=username, 
            email=email, 
            password=hashed_password, 
            roles=role,
            status=status
        )
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'staff':
            flash('Staff registration successful! Awaiting Admin approval.')
        else:
            flash('Registration successful! Please log in.')
            
        return redirect(url_for('controllers.login'))
        
    return render_template('registration.html')


@controllers.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            
            if user.roles == 'staff' and user.status == 'pending':
                flash('Your staff account is pending admin approval.')
                return redirect(url_for('controllers.login'))
                
            if user.status == 'blacklisted':
                flash('Your account has been deactivated/blacklisted.')
                return redirect(url_for('controllers.login'))
                
            
            session['user_id'] = user.id
            session['role'] = user.roles
            session['username'] = user.username
            
            flash('Login successful!')
            if user.roles == 'admin':
                return redirect(url_for('controllers.admin_dashboard'))
            elif user.roles == 'staff':
                return redirect(url_for('controllers.staff_dashboard'))
            else:
                return redirect(url_for('controllers.user_dashboard'))
        else:
            flash('Login failed. Invalid email or password.')
            
    return render_template('login.html')

