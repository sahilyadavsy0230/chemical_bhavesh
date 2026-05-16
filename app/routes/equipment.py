# ============================================================
# app/routes/equipment.py  —  Equipment Design Blueprint
# ============================================================

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, current_app)
from flask_login import login_required, current_user

from app import db
from app.models.equipment import EquipmentDesign
from app.models.project    import Project
from app.calculations      import EQUIPMENT_CALCULATORS
from app.ai.groq_client    import GroqAIClient
from app.utils.validators  import validate_equipment_inputs

equipment_bp = Blueprint('equipment', __name__)
ai_client = GroqAIClient()

# ── Equipment metadata ────────────────────────────────────────
EQUIPMENT_META = {
    'heat_exchanger': {
        'name': 'Heat Exchanger', 'icon': 'bi-thermometer-half',
        'description': 'Shell and tube heat exchanger sizing using LMTD and NTU methods.',
        'fields': [
            {'name': 'hot_inlet_temp',   'label': 'Hot Inlet Temp (°C)',   'type': 'number', 'default': 150, 'min': -200, 'max': 1000},
            {'name': 'hot_outlet_temp',  'label': 'Hot Outlet Temp (°C)',  'type': 'number', 'default': 80,  'min': -200, 'max': 1000},
            {'name': 'cold_inlet_temp',  'label': 'Cold Inlet Temp (°C)',  'type': 'number', 'default': 25,  'min': -200, 'max': 1000},
            {'name': 'cold_outlet_temp', 'label': 'Cold Outlet Temp (°C)', 'type': 'number', 'default': 65,  'min': -200, 'max': 1000},
            {'name': 'hot_flow_rate',    'label': 'Hot Flow Rate (kg/s)',   'type': 'number', 'default': 2.5, 'min': 0.001},
            {'name': 'cold_flow_rate',   'label': 'Cold Flow Rate (kg/s)',  'type': 'number', 'default': 3.0, 'min': 0.001},
            {'name': 'hot_cp',           'label': 'Hot Fluid Cp (J/kg·K)', 'type': 'number', 'default': 4184},
            {'name': 'cold_cp',          'label': 'Cold Fluid Cp (J/kg·K)','type': 'number', 'default': 4184},
            {'name': 'U_overall',        'label': 'U Overall (W/m²·K)',    'type': 'number', 'default': 500, 'min': 10},
            {'name': 'tube_od',          'label': 'Tube OD (m)',            'type': 'number', 'default': 0.019, 'step': 0.001},
            {'name': 'tube_id',          'label': 'Tube ID (m)',            'type': 'number', 'default': 0.016, 'step': 0.001},
            {'name': 'tube_length',      'label': 'Tube Length (m)',        'type': 'number', 'default': 4.0},
            {'name': 'n_passes',         'label': 'Number of Passes',       'type': 'select', 'options': [1, 2, 4]},
            {'name': 'material',         'label': 'Material',               'type': 'select',
             'options': ['Carbon Steel','Stainless Steel 304','Stainless Steel 316','Titanium','Copper']},
        ],
    },
    'reactor': {
        'name': 'Reactor', 'icon': 'bi-atom',
        'description': 'CSTR and PFR reactor design with reaction kinetics.',
        'fields': [
            {'name': 'reactor_type',     'label': 'Reactor Type',           'type': 'select', 'options': ['CSTR','PFR']},
            {'name': 'reaction_order',   'label': 'Reaction Order',         'type': 'select', 'options': [1, 2]},
            {'name': 'feed_flow_rate',   'label': 'Feed Flow Rate (m³/s)',  'type': 'number', 'default': 0.005, 'step': 0.0001},
            {'name': 'inlet_conc',       'label': 'Inlet Conc CA0 (mol/m³)','type': 'number', 'default': 1000},
            {'name': 'conversion',       'label': 'Desired Conversion X',   'type': 'number', 'default': 0.85, 'min': 0.01, 'max': 0.99, 'step': 0.01},
            {'name': 'rate_constant',    'label': 'Rate Constant k (s⁻¹)',  'type': 'number', 'default': 0.05, 'step': 0.001},
            {'name': 'temperature',      'label': 'Temperature (°C)',        'type': 'number', 'default': 80},
            {'name': 'pressure',         'label': 'Pressure (kPa)',          'type': 'number', 'default': 200},
            {'name': 'heat_of_reaction', 'label': 'ΔHrxn (J/mol)',          'type': 'number', 'default': -80000},
            {'name': 'activation_energy','label': 'Ea (J/mol)',              'type': 'number', 'default': 50000},
            {'name': 'material',         'label': 'Material',               'type': 'select',
             'options': ['Carbon Steel','Stainless Steel 316','Hastelloy']},
        ],
    },
    'distillation': {
        'name': 'Distillation Column', 'icon': 'bi-bar-chart-steps',
        'description': 'Binary distillation using McCabe-Thiele and Gilliland methods.',
        'fields': [
            {'name': 'feed_flow_rate',      'label': 'Feed Flow Rate (kmol/h)', 'type': 'number', 'default': 100},
            {'name': 'feed_composition',    'label': 'Feed Composition z_F',    'type': 'number', 'default': 0.40, 'step': 0.01},
            {'name': 'distillate_comp',     'label': 'Distillate x_D',          'type': 'number', 'default': 0.95, 'step': 0.01},
            {'name': 'bottoms_comp',        'label': 'Bottoms x_B',             'type': 'number', 'default': 0.05, 'step': 0.01},
            {'name': 'relative_volatility', 'label': 'Relative Volatility α',   'type': 'number', 'default': 2.5, 'step': 0.1},
            {'name': 'reflux_ratio',        'label': 'Reflux Ratio R',          'type': 'number', 'default': 3.0, 'step': 0.1},
            {'name': 'feed_quality',        'label': 'Feed Quality q',          'type': 'number', 'default': 1.0, 'step': 0.1},
            {'name': 'tray_efficiency',     'label': 'Tray Efficiency (%)',      'type': 'number', 'default': 70},
            {'name': 'pressure_kPa',        'label': 'Pressure (kPa)',           'type': 'number', 'default': 101.325},
            {'name': 'avg_temp',            'label': 'Avg Column Temp (°C)',     'type': 'number', 'default': 90},
            {'name': 'avg_mol_weight',      'label': 'Avg Mol Weight (g/mol)',   'type': 'number', 'default': 78},
            {'name': 'material',            'label': 'Material',                'type': 'select',
             'options': ['Carbon Steel','Stainless Steel 304','Stainless Steel 316']},
        ],
    },
    'evaporator': {
        'name': 'Evaporator', 'icon': 'bi-cloud-haze',
        'description': 'Single and multi-effect evaporator design.',
        'fields': [
            {'name': 'feed_flow_rate',       'label': 'Feed Flow Rate (kg/h)',     'type': 'number', 'default': 5000},
            {'name': 'feed_concentration',   'label': 'Feed Concentration (wt fr)','type': 'number', 'default': 0.10, 'step': 0.01},
            {'name': 'product_concentration','label': 'Product Concentration',     'type': 'number', 'default': 0.45, 'step': 0.01},
            {'name': 'feed_temp',            'label': 'Feed Temperature (°C)',     'type': 'number', 'default': 25},
            {'name': 'steam_pressure',       'label': 'Steam Pressure (kPa abs)', 'type': 'number', 'default': 300},
            {'name': 'operating_pressure',   'label': 'Operating Pressure (kPa)', 'type': 'number', 'default': 20},
            {'name': 'n_effects',            'label': 'Number of Effects',        'type': 'select', 'options': [1, 2, 3]},
            {'name': 'boiling_point_rise',   'label': 'Boiling Point Rise (°C)',  'type': 'number', 'default': 5},
            {'name': 'U_overall',            'label': 'U Overall (W/m²·K)',       'type': 'number', 'default': 2000},
            {'name': 'material',             'label': 'Material',                 'type': 'select',
             'options': ['Carbon Steel','Stainless Steel 304','Stainless Steel 316']},
        ],
    },
    'absorber': {
        'name': 'Absorber', 'icon': 'bi-funnel',
        'description': 'Packed absorption column design using NTU-HTU method.',
        'fields': [
            {'name': 'gas_flow_rate',      'label': 'Gas Flow Rate (m³/h)',     'type': 'number', 'default': 1000},
            {'name': 'liquid_flow_rate',   'label': 'Liquid Flow Rate (m³/h)',  'type': 'number', 'default': 200},
            {'name': 'inlet_gas_conc',     'label': 'Inlet Gas y₁ (mol fr)',   'type': 'number', 'default': 0.05, 'step': 0.001},
            {'name': 'outlet_gas_conc',    'label': 'Outlet Gas y₂ (mol fr)',  'type': 'number', 'default': 0.005,'step': 0.001},
            {'name': 'inlet_liquid_conc',  'label': 'Inlet Liquid x₂ (mol fr)','type': 'number', 'default': 0.0},
            {'name': 'henry_constant',     'label': "Henry's Constant H",       'type': 'number', 'default': 0.5, 'step': 0.01},
            {'name': 'pressure_kPa',       'label': 'Pressure (kPa)',           'type': 'number', 'default': 101.325},
            {'name': 'temperature_C',      'label': 'Temperature (°C)',         'type': 'number', 'default': 25},
            {'name': 'packing_type',       'label': 'Packing Type',            'type': 'select',
             'options': ['Pall Rings','Raschig Rings','Saddles']},
            {'name': 'material',           'label': 'Material',                'type': 'select',
             'options': ['Carbon Steel','Stainless Steel 304','FRP']},
        ],
    },
    'pump': {
        'name': 'Centrifugal Pump', 'icon': 'bi-droplet-half',
        'description': 'Pump sizing with TDH, NPSH, and power calculations.',
        'fields': [
            {'name': 'flow_rate',           'label': 'Flow Rate (m³/h)',         'type': 'number', 'default': 50},
            {'name': 'suction_head',        'label': 'Suction Head (m)',         'type': 'number', 'default': 3},
            {'name': 'discharge_head',      'label': 'Discharge Head (m)',       'type': 'number', 'default': 30},
            {'name': 'suction_pressure',    'label': 'Suction Pressure (kPa)',   'type': 'number', 'default': 101.325},
            {'name': 'discharge_pressure',  'label': 'Discharge Pressure (kPa)','type': 'number', 'default': 400},
            {'name': 'pipe_diameter',       'label': 'Pipe Diameter (m)',        'type': 'number', 'default': 0.1, 'step': 0.01},
            {'name': 'pipe_length',         'label': 'Pipe Length (m)',          'type': 'number', 'default': 100},
            {'name': 'fluid_density',       'label': 'Fluid Density (kg/m³)',    'type': 'number', 'default': 1000},
            {'name': 'fluid_viscosity',     'label': 'Fluid Viscosity (Pa·s)',   'type': 'number', 'default': 0.001, 'step': 0.0001},
            {'name': 'pump_efficiency',     'label': 'Pump Efficiency (%)',      'type': 'number', 'default': 75},
            {'name': 'vapor_pressure',      'label': 'Vapor Pressure (kPa)',     'type': 'number', 'default': 2.34},
            {'name': 'material',            'label': 'Material',                'type': 'select',
             'options': ['Cast Iron','Stainless Steel','Bronze','Alloy Steel']},
        ],
    },
    'compressor': {
        'name': 'Compressor', 'icon': 'bi-wind',
        'description': 'Centrifugal and reciprocating compressor design.',
        'fields': [
            {'name': 'compressor_type',      'label': 'Compressor Type',       'type': 'select', 'options': ['Centrifugal','Reciprocating']},
            {'name': 'gas_flow_rate',        'label': 'Gas Flow Rate (m³/h)',  'type': 'number', 'default': 5000},
            {'name': 'inlet_pressure',       'label': 'Inlet Pressure (kPa)',  'type': 'number', 'default': 101.325},
            {'name': 'outlet_pressure',      'label': 'Outlet Pressure (kPa)', 'type': 'number', 'default': 700},
            {'name': 'inlet_temperature',    'label': 'Inlet Temp (°C)',       'type': 'number', 'default': 25},
            {'name': 'gas_mol_weight',       'label': 'Gas Mol Weight (g/mol)','type': 'number', 'default': 29},
            {'name': 'specific_heat_ratio',  'label': 'γ = Cp/Cv',            'type': 'number', 'default': 1.4, 'step': 0.01},
            {'name': 'compressor_efficiency','label': 'Isentropic Eff (%)',    'type': 'number', 'default': 75},
            {'name': 'n_stages',             'label': 'Number of Stages',      'type': 'select', 'options': [1, 2, 3]},
            {'name': 'material',             'label': 'Material',              'type': 'select',
             'options': ['Carbon Steel','Stainless Steel','Alloy Steel']},
        ],
    },
}


# ─── Equipment Form ───────────────────────────────────────────
@equipment_bp.route('/<eq_type>', methods=['GET', 'POST'])
@login_required
def design_form(eq_type):
    if eq_type not in EQUIPMENT_META:
        flash('Unknown equipment type.', 'danger')
        return redirect(url_for('dashboard.index'))

    meta   = EQUIPMENT_META[eq_type]
    errors = []
    results = None
    design_id = None

    if request.method == 'POST':
        # Collect form inputs
        raw_inputs = {}
        for field in meta['fields']:
            val = request.form.get(field['name'], '')
            if field['type'] in ('number',):
                try:
                    raw_inputs[field['name']] = float(val)
                except ValueError:
                    raw_inputs[field['name']] = val
            else:
                raw_inputs[field['name']] = val

        # Validate
        val_errors = validate_equipment_inputs(eq_type, raw_inputs)
        if val_errors:
            errors = val_errors
            # Ask AI to help debug
            try:
                ai_help = ai_client.debug_inputs(eq_type, val_errors, raw_inputs)
                flash(ai_help['content'], 'warning')
            except Exception:
                pass
        else:
            # Run calculation
            calculator = EQUIPMENT_CALCULATORS[eq_type]
            results    = calculator(raw_inputs)
            calc_errors = results.get('errors', [])

            # Persist to DB
            design = EquipmentDesign(
                user_id=current_user.id,
                equipment_type=eq_type,
                design_name=request.form.get('design_name', f'{meta["name"]} Design'),
                status='completed' if not calc_errors else 'error',
                estimated_cost=results.get('purchased_cost_USD'),
                efficiency_score=results.get('effectiveness_pct') or results.get('efficiency_pct'),
                energy_consumption=results.get('motor_power_kW') or results.get('shaft_power_kW'),
            )
            design.set_inputs(raw_inputs)
            design.set_results(results)
            db.session.add(design)
            db.session.commit()
            design_id = design.id

            if calc_errors:
                for e in calc_errors:
                    flash(e, 'danger')
            else:
                flash('Design calculated successfully!', 'success')

    projects = Project.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'equipment/design_form.html',
        eq_type=eq_type,
        meta=meta,
        results=results,
        errors=errors,
        design_id=design_id,
        projects=projects,
        all_meta=EQUIPMENT_META,
    )


# ─── Results Detail ──────────────────────────────────────────
@equipment_bp.route('/result/<int:design_id>')
@login_required
def result_detail(design_id):
    design = EquipmentDesign.query.filter_by(
        id=design_id, user_id=current_user.id
    ).first_or_404()

    results = design.get_results()
    inputs  = design.get_inputs()
    meta    = EQUIPMENT_META.get(design.equipment_type, {})

    # Get AI explanation
    ai_explanation = None
    try:
        resp = ai_client.explain_calculation(design.equipment_type, results)
        ai_explanation = resp.get('content', '')
    except Exception:
        ai_explanation = 'AI explanation unavailable. Check your API key.'

    return render_template(
        'equipment/result_detail.html',
        design=design,
        results=results,
        inputs=inputs,
        meta=meta,
        ai_explanation=ai_explanation,
        all_meta=EQUIPMENT_META,
    )


# ─── Delete Design ────────────────────────────────────────────
@equipment_bp.route('/delete/<int:design_id>', methods=['POST'])
@login_required
def delete_design(design_id):
    design = EquipmentDesign.query.filter_by(
        id=design_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(design)
    db.session.commit()
    flash('Design deleted.', 'info')
    return redirect(url_for('dashboard.history'))


# ─── Compare Designs ─────────────────────────────────────────
@equipment_bp.route('/compare')
@login_required
def compare():
    ids = request.args.getlist('ids')
    designs = []
    for did in ids[:4]:  # max 4 at a time
        d = EquipmentDesign.query.filter_by(
            id=int(did), user_id=current_user.id
        ).first()
        if d:
            designs.append(d)
    return render_template('equipment/compare.html',
                           designs=designs, all_meta=EQUIPMENT_META)
