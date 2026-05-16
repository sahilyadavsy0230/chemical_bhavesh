# ============================================================
# app/routes/admin.py  —  Admin Dashboard Blueprint
# ============================================================

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user      import User
from app.models.equipment import EquipmentDesign
from app.models.project   import Project
from app.models.chat      import ChatHistory

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator: require admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin overview dashboard."""
    stats = {
        'total_users':   User.query.count(),
        'active_users':  User.query.filter_by(is_active=True).count(),
        'total_designs': EquipmentDesign.query.count(),
        'total_projects':Project.query.count(),
        'total_chats':   ChatHistory.query.count(),
    }
    # Equipment type distribution
    designs = EquipmentDesign.query.all()
    type_dist = {}
    for d in designs:
        type_dist[d.equipment_type] = type_dist.get(d.equipment_type, 0) + 1

    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    return render_template('admin/index.html',
                           stats=stats,
                           type_dist=type_dist,
                           recent_users=recent_users)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself.', 'warning')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        state = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.username} {state}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/make-admin', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'admin' if user.role != 'admin' else 'user'
    db.session.commit()
    flash(f'{user.username} role set to {user.role}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/designs')
@login_required
@admin_required
def designs():
    all_designs = (EquipmentDesign.query
                   .order_by(EquipmentDesign.created_at.desc()).limit(100).all())
    return render_template('admin/designs.html', designs=all_designs)
