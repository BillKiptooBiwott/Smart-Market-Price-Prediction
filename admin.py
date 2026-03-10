from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from database import db, User, PredictionHistory
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_farmers = User.query.filter_by(is_farmer=True).count()
    total_predictions = PredictionHistory.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_predictions = PredictionHistory.query.order_by(
        PredictionHistory.created_at.desc()
    ).limit(10).all()
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    
    return render_template('admin.html',
                         total_users=total_users,
                         total_farmers=total_farmers,
                         total_predictions=total_predictions,
                         new_users=new_users,
                         recent_users=recent_users,
                         recent_predictions=recent_predictions)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search)) |
            (User.full_name.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_users.html', users=users, search=search)

@admin_bp.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot change your own admin status', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin privileges {status} for {user.username}', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/predictions')
@login_required
@admin_required
def admin_predictions():
    page = request.args.get('page', 1, type=int)
    
    predictions = PredictionHistory.query.order_by(
        PredictionHistory.created_at.desc()
    ).paginate(page=page, per_page=30, error_out=False)
    
    return render_template('admin_predictions.html', predictions=predictions)

@admin_bp.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    total_users = User.query.count()
    active_today = User.query.filter(
        User.last_login >= datetime.utcnow() - timedelta(days=1)
    ).count()
    
    total_preds = PredictionHistory.query.count()
    avg_pred_per_user = total_preds / total_users if total_users > 0 else 0
    
    crop_stats = db.session.query(
        PredictionHistory.crop, 
        db.func.count(PredictionHistory.crop).label('count')
    ).group_by(PredictionHistory.crop).order_by(db.desc('count')).all()
    
    return render_template('admin_stats.html',
                         total_users=total_users,
                         active_today=active_today,
                         total_preds=total_preds,
                         avg_pred_per_user=round(avg_pred_per_user, 2),
                         crop_stats=crop_stats)