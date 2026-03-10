from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from database import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember)
        
        if user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        county = request.form.get('county')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.signup'))
        
        user_exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if user_exists:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('auth.signup'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            phone_number=phone,
            county=county,
            is_farmer=True,
            is_admin=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    counties = [
        'Nairobi', 'Kiambu', 'Kirinyaga', 'Muranga', 'Nyandarua',
        'Nakuru', 'Uasin Gishu', 'Trans Nzoia', 'Bungoma', 'Kakamega',
        'Kisumu', 'Siaya', 'Homabay', 'Migori', 'Kisii',
        'Meru', 'Embu', 'Tharaka Nithi', 'Machakos', 'Makueni',
        'Kitui', 'Mombasa', 'Kwale', 'Kilifi', 'Taita Taveta'
    ]
    
    return render_template('signup.html', counties=sorted(counties))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone_number = request.form.get('phone')
        current_user.county = request.form.get('county')
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    counties = [
        'Nairobi', 'Kiambu', 'Kirinyaga', 'Muranga', 'Nyandarua',
        'Nakuru', 'Uasin Gishu', 'Trans Nzoia', 'Bungoma', 'Kakamega',
        'Kisumu', 'Siaya', 'Homabay', 'Migori', 'Kisii',
        'Meru', 'Embu', 'Tharaka Nithi', 'Machakos', 'Makueni'
    ]
    
    return render_template('profile.html', counties=sorted(counties))