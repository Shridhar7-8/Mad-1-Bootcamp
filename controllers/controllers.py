from sqlalchemy.orm import _orm_constructors
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask import url_for
from flask import request, flash
from flask import session
from models.models import User, db, Post, Bookmark

controllers = Blueprint('controllers', __name__)

def authorize_role(allowed_roles):
    if 'user_id' not in session:
        return False
    return session.get('role') in allowed_roles


@controllers.route('/')
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('controllers.admin_dashboard'))
        elif role == 'staff':
            return redirect(url_for('controllers.staff_dasboard'))
        else:
            return redirect(url_for('controllers.user_dashboard'))
    return redirect(url_for('controllers.login'))




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



@controllers.route('/admin/dashboard')
def admin_dashboard():
    if not authorize_role(['admin']):
        flash('Access denied. Admin authorization required.')
        return redirect(url_for('controllers.login'))
        
    
    total_posts = Post.query.count()
    total_users = User.query.filter_by(roles='user').count()
    total_staff = User.query.filter_by(roles='staff', status='approved').count()
    total_bookmarks = Bookmark.query.count()
    
    pending_staff = User.query.filter_by(roles='staff', status='pending').all()
    approved_staff_list = User.query.filter_by(roles='staff', status='approved').all()
    all_bookmarks = Bookmark.query.all()
    
    
    search_query = request.args.get('search_query', '').strip()
    search_type = request.args.get('search_type', 'post')
    
    posts_list, users_list, staff_list = [], [], []
    
    if search_query:
        query_id = int(search_query) if search_query.isdigit() else None
        if search_type == 'post':
            posts_list = Post.query.filter((Post.title.ilike(f'%{search_query}%')) | (Post.id == query_id)).all()
        elif search_type == 'user':
            users_list = User.query.filter(User.roles == 'user').filter((User.username.ilike(f'%{search_query}%')) | (User.id == query_id)).all()
        elif search_type == 'staff':
            staff_list = User.query.filter(User.roles == 'staff').filter((User.username.ilike(f'%{search_query}%')) | (User.id == query_id)).all()
    else:
        posts_list = Post.query.all()
        users_list = User.query.filter_by(roles='user').all()
        staff_list = User.query.filter(User.roles == 'staff').all()
        
    return render_template(
        'admin_dashboard.html',
        total_posts=total_posts, total_users=total_users, total_staff=total_staff, total_bookmarks=total_bookmarks,
        pending_staff=pending_staff, approved_staff_list=approved_staff_list,
        posts_list=posts_list, users_list=users_list, staff_list=staff_list, all_bookmarks=all_bookmarks,
        search_query=search_query, search_type=search_type
    )


@controllers.route('/admin/approve/<int:user_id>', methods=['POST'])
def approve_staff(user_id):
    if not authorize_role(['admin']): abort(403)
    user = User.query.get_or_404(user_id)
    if user.roles == 'staff' and user.status == 'pending':
        user.status = 'approved'
        db.session.commit()
        flash(f'Staff member {user.username} approved successfully!')
    return redirect(url_for('controllers.admin_dashboard'))


@controllers.route('/admin/user/toggle_status/<int:user_id>', methods=['POST'])
def toggle_user_status(user_id):
    if not authorize_role(['admin']): abort(403)
    user = User.query.get_or_404(user_id)
    if user.roles == 'admin':
        flash('Cannot modify administrator status.')
        return redirect(url_for('controllers.admin_dashboard'))
    user.status = 'approved' if user.status == 'blacklisted' else 'blacklisted'
    db.session.commit()
    flash(f'User {user.username} status toggled.')
    return redirect(url_for('controllers.admin_dashboard'))


@controllers.route('/admin/post/create', methods=['POST'])
def create_post():
    if not authorize_role(['admin']): abort(403)
    title = request.form.get('title')
    content = request.form.get('content')
    if title and content:
        new_post = Post(title=title, content=content, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        flash('Post created!')
    return redirect(url_for('controllers.admin_dashboard'))

@controllers.route('/admin/post/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not authorize_role(['admin']): abort(403)
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.status = request.form.get('status')
        db.session.commit()
        flash('Post updated!')
        return redirect(url_for('controllers.admin_dashboard'))
    return render_template('edit_post.html', post=post)

@controllers.route('/admin/post/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if not authorize_role(['admin']): abort(403)
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted!')
    return redirect(url_for('controllers.admin_dashboard'))

@controllers.route('/admin/post/assign/<int:post_id>', methods=['POST'])
def assign_staff(post_id):
    if not authorize_role(['admin']): abort(403)
    post = Post.query.get_or_404(post_id)

    staff_id = request.form.get('staff_id')
    post.assigned_staff_id = int(staff_id) if staff_id else None
    db.session.commit()
    flash('Staff assigned to the post')
    return redirect(url_for('controllers.admin_dashboard'))


@controllers.route('/logout')
def logout():
    session.clear()
    flash('logged out')
    return redirect(url_for('controllers.login'))