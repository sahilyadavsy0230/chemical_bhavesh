# ============================================================
# app/routes/auth.py  —  Authentication Blueprint
# ============================================================

import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session)
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')


# ─── Registration ─────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username    = request.form.get('username', '').strip()
        email       = request.form.get('email', '').strip().lower()
        password    = request.form.get('password', '')
        confirm_pwd = request.form.get('confirm_password', '')
        full_name   = request.form.get('full_name', '').strip()
        institution = request.form.get('institution', '').strip()

        # Validation
        errors = []
        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_pwd:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html',
                                   form_data=request.form)

        # Create user
        user = User(
            username=username, email=email,
            full_name=full_name, institution=institution,
            role='user', is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form_data={})


# ─── Login ────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password   = request.form.get('password', '')
        remember   = 'remember' in request.form

        # Accept username or email
        user = (User.query.filter_by(username=identifier).first() or
                User.query.filter_by(email=identifier.lower()).first())

        if not user or not user.check_password(password):
            flash('Invalid credentials. Please try again.', 'danger')
            return render_template('auth/login.html', identifier=identifier)

        if not user.is_active:
            flash('Your account is disabled. Contact admin.', 'warning')
            return render_template('auth/login.html')

        # Login
        login_user(user, remember=remember)
        user.last_login = datetime.datetime.utcnow()
        db.session.commit()

        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.index'))

    return render_template('auth/login.html', identifier='')


# ─── Logout ───────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ─── Change Password ──────────────────────────────────────────
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pwd = request.form.get('current_password', '')
        new_pwd     = request.form.get('new_password', '')
        confirm_pwd = request.form.get('confirm_password', '')

        if not current_user.check_password(current_pwd):
            flash('Current password is incorrect.', 'danger')
        elif len(new_pwd) < 8:
            flash('New password must be at least 8 characters.', 'danger')
        elif new_pwd != confirm_pwd:
            flash('New passwords do not match.', 'danger')
        else:
            current_user.set_password(new_pwd)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile.index'))

    return render_template('auth/change_password.html')
