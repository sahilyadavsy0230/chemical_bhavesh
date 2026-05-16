# ============================================================
# app/routes/api.py  —  REST API Blueprint (JSON)
# ============================================================

import time
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app import db, limiter
from app.models.equipment import EquipmentDesign
from app.models.chat       import ChatHistory
from app.models.project    import Project
from app.calculations      import EQUIPMENT_CALCULATORS
from app.ai.groq_client    import GroqAIClient
from app.utils.validators  import validate_equipment_inputs

api_bp    = Blueprint('api', __name__)
ai_client = GroqAIClient()


# ── Utility ───────────────────────────────────────────────────
def success(data: dict, code: int = 200):
    return jsonify({'success': True, **data}), code

def error(msg: str, code: int = 400):
    return jsonify({'success': False, 'error': msg}), code


# ── Equipment Calculation API ─────────────────────────────────
@api_bp.route('/calculate/<eq_type>', methods=['POST'])
@login_required
@limiter.limit('30 per minute')
def calculate(eq_type):
    """
    POST /api/v1/calculate/<equipment_type>
    Body: JSON dict of design inputs
    Returns: JSON calculation results
    """
    if eq_type not in EQUIPMENT_CALCULATORS:
        return error(f'Unknown equipment type: {eq_type}')

    inputs = request.get_json(silent=True)
    if not inputs:
        return error('Request body must be valid JSON.')

    # Validate
    val_errors = validate_equipment_inputs(eq_type, inputs)
    if val_errors:
        return error(f'Validation errors: {val_errors}', 422)

    # Calculate
    calculator = EQUIPMENT_CALCULATORS[eq_type]
    results    = calculator(inputs)
    calc_errors = results.get('errors', [])

    # Persist
    design = EquipmentDesign(
        user_id=current_user.id,
        equipment_type=eq_type,
        design_name=inputs.get('design_name', f'{eq_type} API run'),
        status='completed' if not calc_errors else 'error',
        estimated_cost=results.get('purchased_cost_USD'),
        efficiency_score=results.get('effectiveness_pct'),
        energy_consumption=results.get('motor_power_kW'),
    )
    design.set_inputs(inputs)
    design.set_results(results)
    db.session.add(design)
    db.session.commit()

    return success({'design_id': design.id, 'results': results})


# ── AI Chat API ───────────────────────────────────────────────
@api_bp.route('/chat', methods=['POST'])
@login_required
@limiter.limit('20 per minute')
def chat():
    """
    POST /api/v1/chat
    Body: { "message": str, "design_id": int|null, "context": str }
    """
    data       = request.get_json(silent=True) or {}
    user_msg   = data.get('message', '').strip()
    design_id  = data.get('design_id')
    context    = data.get('context', '')

    if not user_msg:
        return error('Message cannot be empty.')

    # Fetch recent history for this user
    history_rows = (ChatHistory.query
                    .filter_by(user_id=current_user.id)
                    .order_by(ChatHistory.created_at.desc())
                    .limit(10).all())
    history = [{'user_message': h.user_message, 'ai_response': h.ai_response}
               for h in reversed(history_rows)]

    # Call AI
    resp = ai_client.general_chat(user_msg, history, context)

    # Save exchange
    chat_entry = ChatHistory(
        user_id=current_user.id,
        design_id=design_id,
        user_message=user_msg,
        ai_response=resp['content'],
        context_type=context or 'general',
        tokens_used=resp.get('tokens', 0),
        response_time=resp.get('response_time', 0),
    )
    db.session.add(chat_entry)
    db.session.commit()

    return success({
        'response':      resp['content'],
        'tokens_used':   resp.get('tokens', 0),
        'response_time': resp.get('response_time', 0),
        'chat_id':       chat_entry.id,
    })


# ── AI Optimization API ───────────────────────────────────────
@api_bp.route('/optimize/<int:design_id>', methods=['POST'])
@login_required
def optimize(design_id):
    """Run AI optimization on a saved design."""
    design = EquipmentDesign.query.filter_by(
        id=design_id, user_id=current_user.id
    ).first_or_404()

    resp = ai_client.suggest_optimization(
        design.equipment_type,
        design.get_inputs(),
        design.get_results()
    )
    # Save suggestions back
    design.ai_suggestions = resp['content']
    db.session.commit()

    return success({'optimization': resp['content'], 'tokens': resp.get('tokens', 0)})


# ── AI Safety Analysis API ────────────────────────────────────
@api_bp.route('/safety/<int:design_id>', methods=['POST'])
@login_required
def safety(design_id):
    design = EquipmentDesign.query.filter_by(
        id=design_id, user_id=current_user.id
    ).first_or_404()

    resp = ai_client.safety_analysis(
        design.equipment_type,
        design.get_inputs(),
        design.get_results()
    )
    return success({'safety_analysis': resp['content']})


# ── Formula Explanation API ───────────────────────────────────
@api_bp.route('/explain-formula', methods=['POST'])
@login_required
def explain_formula():
    data    = request.get_json(silent=True) or {}
    formula = data.get('formula', '')
    context = data.get('context', '')
    if not formula:
        return error('Formula name required.')
    resp = ai_client.explain_formula(formula, context)
    return success({'explanation': resp['content']})


# ── Material Recommendation API ───────────────────────────────
@api_bp.route('/material-recommendation', methods=['POST'])
@login_required
def material_recommendation():
    data = request.get_json(silent=True) or {}
    eq_type    = data.get('equipment_type', 'general')
    conditions = data.get('conditions', {})
    resp = ai_client.material_recommendation(eq_type, conditions)
    return success({'recommendations': resp['content']})


# ── Unit Conversion API ───────────────────────────────────────
UNIT_CONVERSIONS = {
    'temperature': {
        'C_to_K':  lambda v: v + 273.15,
        'K_to_C':  lambda v: v - 273.15,
        'C_to_F':  lambda v: v * 9/5 + 32,
        'F_to_C':  lambda v: (v - 32) * 5/9,
    },
    'pressure': {
        'kPa_to_bar':  lambda v: v / 100,
        'bar_to_kPa':  lambda v: v * 100,
        'kPa_to_psi':  lambda v: v * 0.145038,
        'psi_to_kPa':  lambda v: v / 0.145038,
        'atm_to_kPa':  lambda v: v * 101.325,
        'kPa_to_atm':  lambda v: v / 101.325,
    },
    'flow': {
        'm3h_to_ls':  lambda v: v / 3.6,
        'ls_to_m3h':  lambda v: v * 3.6,
        'kgh_to_kgs': lambda v: v / 3600,
        'kgs_to_kgh': lambda v: v * 3600,
    },
    'length': {
        'm_to_ft':  lambda v: v * 3.28084,
        'ft_to_m':  lambda v: v / 3.28084,
        'm_to_in':  lambda v: v * 39.3701,
        'in_to_m':  lambda v: v / 39.3701,
    },
}

@api_bp.route('/convert', methods=['POST'])
@login_required
def convert_units():
    data      = request.get_json(silent=True) or {}
    category  = data.get('category', '')
    conv_key  = data.get('conversion', '')
    value     = data.get('value')

    if value is None:
        return error('Value required.')
    cat = UNIT_CONVERSIONS.get(category, {})
    fn  = cat.get(conv_key)
    if fn is None:
        return error(f'Unknown conversion: {category}.{conv_key}')

    try:
        result = fn(float(value))
        return success({'result': round(result, 6), 'conversion': conv_key})
    except Exception as e:
        return error(str(e))


# ── User Designs List API ─────────────────────────────────────
@api_bp.route('/designs', methods=['GET'])
@login_required
def list_designs():
    eq_type = request.args.get('type', '')
    query   = EquipmentDesign.query.filter_by(user_id=current_user.id)
    if eq_type:
        query = query.filter_by(equipment_type=eq_type)
    designs = query.order_by(EquipmentDesign.created_at.desc()).limit(50).all()
    return success({'designs': [d.to_dict() for d in designs]})


# ── Chat History API ──────────────────────────────────────────
@api_bp.route('/chat-history', methods=['GET'])
@login_required
def chat_history():
    rows = (ChatHistory.query.filter_by(user_id=current_user.id)
            .order_by(ChatHistory.created_at.desc()).limit(50).all())
    return success({'history': [r.to_dict() for r in rows]})


# ── Dashboard Stats API ───────────────────────────────────────
@api_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    designs = EquipmentDesign.query.filter_by(user_id=current_user.id).all()
    type_counts = {}
    costs, energies, efficiencies = [], [], []
    for d in designs:
        type_counts[d.equipment_type] = type_counts.get(d.equipment_type, 0) + 1
        if d.estimated_cost:     costs.append(d.estimated_cost)
        if d.energy_consumption: energies.append(d.energy_consumption)
        if d.efficiency_score:   efficiencies.append(d.efficiency_score)

    return success({
        'total_designs':      len(designs),
        'equipment_counts':   type_counts,
        'avg_cost_USD':       round(sum(costs) / len(costs), 0)       if costs else 0,
        'avg_energy_kW':      round(sum(energies) / len(energies), 2) if energies else 0,
        'avg_efficiency_pct': round(sum(efficiencies) / len(efficiencies), 1) if efficiencies else 0,
    })
