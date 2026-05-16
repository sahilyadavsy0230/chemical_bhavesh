# ============================================================
# app/utils/seed_data.py  —  Sample Data Seeder
# ============================================================

from app import db
from app.models.user      import User
from app.models.project   import Project
from app.models.equipment import EquipmentDesign
from app.models.chat      import ChatHistory


def seed_database():
    """Insert demo users, projects, and design history."""

    # ── Admin user ────────────────────────────────────────────
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin', email='admin@chemdesignai.com',
            full_name='Platform Administrator', institution='ChemDesignAI',
            department='Engineering', role='admin', is_active=True,
        )
        admin.set_password('Admin@1234')
        db.session.add(admin)

    # ── Demo engineer ─────────────────────────────────────────
    if not User.query.filter_by(username='engineer1').first():
        eng = User(
            username='engineer1', email='engineer@example.com',
            full_name='Bhavesh Patel', institution='SVNIT Surat',
            department='Chemical Engineering', role='user', is_active=True,
        )
        eng.set_password('Engineer@1234')
        db.session.add(eng)
        db.session.flush()   # get eng.id before commit

        # ── Demo Project ──────────────────────────────────────
        proj = Project(
            user_id=eng.id,
            name='Crude Oil Refinery Unit',
            description='Design of heat exchangers and distillation columns for CDU.',
            industry='Petroleum Refining',
            tags='heat exchanger,distillation,crude oil',
            status='active',
        )
        db.session.add(proj)
        db.session.flush()

        # ── Sample heat exchanger design ─────────────────────
        hx_inputs = {
            'hot_inlet_temp': 150, 'hot_outlet_temp': 80,
            'cold_inlet_temp': 25, 'cold_outlet_temp': 65,
            'hot_flow_rate': 2.5,  'cold_flow_rate': 3.0,
            'hot_cp': 4184,         'cold_cp': 4184,
            'U_overall': 500,       'tube_od': 0.019,
            'tube_id': 0.016,       'tube_length': 4.0,
            'n_passes': 1,          'material': 'Stainless Steel 304',
        }
        from app.calculations.heat_exchanger import calculate_heat_exchanger
        hx_results = calculate_heat_exchanger(hx_inputs)

        hx_design = EquipmentDesign(
            user_id=eng.id, project_id=proj.id,
            equipment_type='heat_exchanger',
            design_name='Crude Preheat HX-101',
            status='completed',
            estimated_cost=hx_results.get('purchased_cost_USD', 25000),
            efficiency_score=hx_results.get('effectiveness_pct', 78.5),
            energy_consumption=hx_results.get('heat_duty_kW', 420),
            report_generated=False,
        )
        hx_design.set_inputs(hx_inputs)
        hx_design.set_results(hx_results)
        db.session.add(hx_design)

        # ── Sample reactor design ─────────────────────────────
        rx_inputs = {
            'reactor_type': 'CSTR', 'reaction_order': 1,
            'feed_flow_rate': 0.005, 'inlet_conc': 1000,
            'conversion': 0.85,     'rate_constant': 0.05,
            'temperature': 80,      'pressure': 200,
            'heat_of_reaction': -80000, 'activation_energy': 50000,
            'material': 'Stainless Steel 316',
        }
        from app.calculations.reactor import calculate_reactor
        rx_results = calculate_reactor(rx_inputs)

        rx_design = EquipmentDesign(
            user_id=eng.id, project_id=proj.id,
            equipment_type='reactor',
            design_name='Esterification CSTR R-201',
            status='completed',
            estimated_cost=rx_results.get('purchased_cost_USD', 65000),
            efficiency_score=85.0,
            energy_consumption=rx_results.get('heat_generation_W', 0) / 1000,
        )
        rx_design.set_inputs(rx_inputs)
        rx_design.set_results(rx_results)
        db.session.add(rx_design)

        # ── Sample Chat ───────────────────────────────────────
        chat = ChatHistory(
            user_id=eng.id,
            user_message='What is LMTD and why is it used in heat exchanger design?',
            ai_response=(
                'LMTD (Log Mean Temperature Difference) is the driving force for heat '
                'transfer in a heat exchanger. It accounts for the varying temperature '
                'difference along the exchanger length using logarithmic averaging:\n\n'
                'LMTD = (ΔT₁ − ΔT₂) / ln(ΔT₁/ΔT₂)\n\n'
                'It is used because heat transfer driving force changes along the '
                'exchanger, and a simple arithmetic mean would overestimate the '
                'driving force for most configurations.'
            ),
            context_type='heat_exchanger',
            tokens_used=180,
            response_time=1.2,
        )
        db.session.add(chat)

    db.session.commit()
    print('✅ Database seeded with demo data.')
