# ============================================================
# app/routes/dashboard.py  —  Dashboard Blueprint
# ============================================================

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models.equipment import EquipmentDesign
from app.models.project    import Project
from app.models.chat       import ChatHistory
import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def landing():
    """Public landing page — redirect to dashboard if logged in."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main engineering dashboard."""
    user = current_user

    # ── Recent Designs (last 5) ───────────────────────────────
    recent_designs = (EquipmentDesign.query
                      .filter_by(user_id=user.id)
                      .order_by(EquipmentDesign.created_at.desc())
                      .limit(5).all())

    # ── Stats ────────────────────────────────────────────────
    total_designs  = EquipmentDesign.query.filter_by(user_id=user.id).count()
    total_projects = Project.query.filter_by(user_id=user.id).count()
    total_chats    = ChatHistory.query.filter_by(user_id=user.id).count()

    # ── Equipment type distribution ──────────────────────────
    all_designs = EquipmentDesign.query.filter_by(user_id=user.id).all()
    type_counts = {}
    cost_total  = 0.0
    energy_total = 0.0
    for d in all_designs:
        type_counts[d.equipment_type] = type_counts.get(d.equipment_type, 0) + 1
        cost_total   += d.estimated_cost   or 0
        energy_total += d.energy_consumption or 0

    # ── Monthly activity (last 6 months) ─────────────────────
    six_months_ago = datetime.datetime.utcnow() - datetime.timedelta(days=180)
    monthly = {}
    for d in EquipmentDesign.query.filter(
        EquipmentDesign.user_id == user.id,
        EquipmentDesign.created_at >= six_months_ago
    ).all():
        key = d.created_at.strftime('%b %Y')
        monthly[key] = monthly.get(key, 0) + 1

    # ── Recent Projects ───────────────────────────────────────
    recent_projects = (Project.query.filter_by(user_id=user.id)
                       .order_by(Project.updated_at.desc()).limit(3).all())

    # ── Equipment Cards Info ──────────────────────────────────
    equipment_cards = [
        {'id': 'heat_exchanger', 'name': 'Heat Exchanger',
         'icon': 'bi-thermometer-half', 'color': 'danger',
         'desc': 'Shell & tube sizing, LMTD, NTU method'},
        {'id': 'reactor',        'name': 'Reactor',
         'icon': 'bi-atom',            'color': 'warning',
         'desc': 'CSTR / PFR design, kinetics, heat effects'},
        {'id': 'distillation',   'name': 'Distillation Column',
         'icon': 'bi-bar-chart-steps', 'color': 'info',
         'desc': 'McCabe-Thiele, Fenske, column sizing'},
        {'id': 'evaporator',     'name': 'Evaporator',
         'icon': 'bi-cloud-haze',      'color': 'primary',
         'desc': 'Multi-effect evaporator, steam economy'},
        {'id': 'absorber',       'name': 'Absorber',
         'icon': 'bi-funnel',          'color': 'success',
         'desc': 'Packed column NTU/HTU, GPDC flooding'},
        {'id': 'pump',           'name': 'Pump',
         'icon': 'bi-droplet-half',    'color': 'secondary',
         'desc': 'Centrifugal pump, TDH, NPSH, power'},
        {'id': 'compressor',     'name': 'Compressor',
         'icon': 'bi-wind',            'color': 'dark',
         'desc': 'Centrifugal/reciprocating, isentropic work'},
    ]

    return render_template(
        'dashboard/index.html',
        recent_designs=recent_designs,
        recent_projects=recent_projects,
        total_designs=total_designs,
        total_projects=total_projects,
        total_chats=total_chats,
        type_counts=type_counts,
        cost_total=round(cost_total, 0),
        energy_total=round(energy_total, 2),
        monthly_activity=monthly,
        equipment_cards=equipment_cards,
    )


@dashboard_bp.route('/history')
@login_required
def history():
    """Full design history page with pagination."""
    page     = int(request.args.get('page', 1))
    eq_type  = request.args.get('type', '')

    query = EquipmentDesign.query.filter_by(user_id=current_user.id)
    if eq_type:
        query = query.filter_by(equipment_type=eq_type)
    query = query.order_by(EquipmentDesign.created_at.desc())

    designs = query.paginate(page=page, per_page=10, error_out=False)

    return render_template('dashboard/history.html',
                           designs=designs, eq_type=eq_type)
