# ============================================================
# app/routes/profile.py  —  User Profile Blueprint
# ============================================================

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/')
@login_required
def index():
    from app.models.equipment import EquipmentDesign
    from app.models.chat      import ChatHistory
    total_designs = EquipmentDesign.query.filter_by(user_id=current_user.id).count()
    total_chats   = ChatHistory.query.filter_by(user_id=current_user.id).count()
    return render_template('profile/index.html',
                           total_designs=total_designs,
                           total_chats=total_chats)


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        current_user.full_name   = request.form.get('full_name', '').strip()
        current_user.institution = request.form.get('institution', '').strip()
        current_user.department  = request.form.get('department', '').strip()
        current_user.bio         = request.form.get('bio', '').strip()
        current_user.theme_preference = request.form.get('theme', 'dark')
        current_user.unit_system = request.form.get('unit_system', 'SI')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))

    return render_template('profile/edit.html')


@profile_bp.route('/projects')
@login_required
def projects():
    from app.models.project import Project
    all_projects = (Project.query.filter_by(user_id=current_user.id)
                    .order_by(Project.updated_at.desc()).all())
    return render_template('profile/projects.html', projects=all_projects)


@profile_bp.route('/projects/new', methods=['POST'])
@login_required
def new_project():
    from app.models.project import Project
    name  = request.form.get('name', '').strip()
    desc  = request.form.get('description', '').strip()
    if not name:
        flash('Project name required.', 'danger')
        return redirect(url_for('profile.projects'))
    proj = Project(user_id=current_user.id, name=name, description=desc)
    db.session.add(proj)
    db.session.commit()
    flash(f'Project "{name}" created!', 'success')
    return redirect(url_for('profile.projects'))
