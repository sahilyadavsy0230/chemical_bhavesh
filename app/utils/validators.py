# ============================================================
# app/utils/validators.py  —  Input Validation Utilities
# ============================================================


# ── Per-equipment required fields and ranges ──────────────────
EQUIPMENT_RULES = {
    'heat_exchanger': {
        'required': ['hot_inlet_temp','hot_outlet_temp','cold_inlet_temp',
                     'cold_outlet_temp','hot_flow_rate','cold_flow_rate',
                     'U_overall','tube_od','tube_id','tube_length'],
        'ranges': {
            'hot_inlet_temp':   (-200, 1000),
            'hot_outlet_temp':  (-200, 1000),
            'cold_inlet_temp':  (-200, 1000),
            'cold_outlet_temp': (-200, 1000),
            'hot_flow_rate':    (0.001, 10000),
            'cold_flow_rate':   (0.001, 10000),
            'U_overall':        (10, 50000),
            'tube_od':          (0.005, 1.0),
            'tube_id':          (0.003, 0.99),
            'tube_length':      (0.1, 30),
        },
    },
    'reactor': {
        'required': ['feed_flow_rate','inlet_conc','conversion','rate_constant','temperature','pressure'],
        'ranges': {
            'feed_flow_rate': (1e-8, 100),
            'inlet_conc':     (0.001, 1e7),
            'conversion':     (0.001, 0.999),
            'rate_constant':  (1e-10, 1e6),
            'temperature':    (-100, 800),
            'pressure':       (1, 100000),
        },
    },
    'distillation': {
        'required': ['feed_flow_rate','feed_composition','distillate_comp',
                     'bottoms_comp','relative_volatility','reflux_ratio'],
        'ranges': {
            'feed_flow_rate':      (0.001, 1e6),
            'feed_composition':    (0.001, 0.999),
            'distillate_comp':     (0.01,  0.999),
            'bottoms_comp':        (0.001, 0.99),
            'relative_volatility': (1.01, 100),
            'reflux_ratio':        (0.1, 100),
        },
    },
    'evaporator': {
        'required': ['feed_flow_rate','feed_concentration','product_concentration',
                     'steam_pressure','U_overall'],
        'ranges': {
            'feed_flow_rate':        (1, 1e7),
            'feed_concentration':    (0.001, 0.999),
            'product_concentration': (0.01, 0.999),
            'steam_pressure':        (5, 5000),
            'U_overall':             (100, 20000),
        },
    },
    'absorber': {
        'required': ['gas_flow_rate','liquid_flow_rate','inlet_gas_conc',
                     'outlet_gas_conc','henry_constant','pressure_kPa'],
        'ranges': {
            'gas_flow_rate':   (1, 1e7),
            'liquid_flow_rate':(0.1, 1e6),
            'inlet_gas_conc':  (1e-5, 0.999),
            'outlet_gas_conc': (1e-6, 0.999),
            'henry_constant':  (1e-5, 1000),
            'pressure_kPa':    (1, 10000),
        },
    },
    'pump': {
        'required': ['flow_rate','discharge_head','pipe_diameter','pipe_length'],
        'ranges': {
            'flow_rate':    (0.001, 1e6),
            'pipe_diameter':(0.005, 5.0),
            'pipe_length':  (0.1, 100000),
        },
    },
    'compressor': {
        'required': ['gas_flow_rate','inlet_pressure','outlet_pressure','inlet_temperature'],
        'ranges': {
            'gas_flow_rate':   (0.001, 1e7),
            'inlet_pressure':  (0.1, 100000),
            'outlet_pressure': (0.1, 100000),
            'inlet_temperature': (-100, 600),
        },
    },
}


def validate_equipment_inputs(eq_type: str, inputs: dict) -> list:
    """
    Validate inputs for a given equipment type.

    Returns:
        List of error strings (empty list = no errors).
    """
    errors = []
    rules  = EQUIPMENT_RULES.get(eq_type, {})

    # ── Required fields ───────────────────────────────────────
    for field in rules.get('required', []):
        val = inputs.get(field)
        if val is None or str(val).strip() == '':
            errors.append(f'Required field missing: {field.replace("_", " ").title()}')

    # ── Numeric ranges ────────────────────────────────────────
    for field, (lo, hi) in rules.get('ranges', {}).items():
        val = inputs.get(field)
        if val is None:
            continue
        try:
            fval = float(val)
            if not (lo <= fval <= hi):
                errors.append(
                    f'{field.replace("_", " ").title()}: value {fval} is out of '
                    f'allowed range [{lo}, {hi}].'
                )
        except (TypeError, ValueError):
            errors.append(f'{field.replace("_", " ").title()}: must be a number.')

    # ── Cross-field checks ────────────────────────────────────
    if eq_type == 'heat_exchanger':
        try:
            if float(inputs.get('tube_id', 0)) >= float(inputs.get('tube_od', 0)):
                errors.append('Tube ID must be less than Tube OD.')
        except (TypeError, ValueError):
            pass

    if eq_type == 'distillation':
        try:
            xb = float(inputs.get('bottoms_comp', 0))
            zf = float(inputs.get('feed_composition', 0))
            xd = float(inputs.get('distillate_comp', 1))
            if not (xb < zf < xd):
                errors.append('Must satisfy: x_B < z_F < x_D.')
        except (TypeError, ValueError):
            pass

    if eq_type == 'compressor':
        try:
            p1 = float(inputs.get('inlet_pressure', 0))
            p2 = float(inputs.get('outlet_pressure', 0))
            if p2 <= p1:
                errors.append('Outlet pressure must be greater than inlet pressure.')
        except (TypeError, ValueError):
            pass

    if eq_type == 'absorber':
        try:
            y1 = float(inputs.get('inlet_gas_conc', 0))
            y2 = float(inputs.get('outlet_gas_conc', 0))
            if y2 >= y1:
                errors.append('Outlet gas concentration must be less than inlet concentration.')
        except (TypeError, ValueError):
            pass

    if eq_type == 'evaporator':
        try:
            xf = float(inputs.get('feed_concentration', 0))
            xp = float(inputs.get('product_concentration', 0))
            if xp <= xf:
                errors.append('Product concentration must be greater than feed concentration.')
        except (TypeError, ValueError):
            pass

    return errors
