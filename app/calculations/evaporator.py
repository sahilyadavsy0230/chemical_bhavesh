# ============================================================
# app/calculations/evaporator.py
# Single & Multi-Effect Evaporator Design
# Reference: McCabe-Smith, Perry's Chemical Engineers' Handbook
# ============================================================

import math


def calculate_evaporator(inputs: dict) -> dict:
    """
    Design a single-effect or multi-effect evaporator.

    Args:
        inputs:
            - feed_flow_rate    (kg/h)
            - feed_concentration (wt fraction solute, x_F)
            - product_concentration (wt fraction solute, x_P)
            - feed_temp         (°C)
            - steam_pressure    (kPa abs) — heating steam
            - operating_pressure (kPa abs) — vapor space
            - n_effects         (int) 1, 2, or 3
            - boiling_point_rise (°C) BPR
            - U_overall         (W/m²·K)
            - material
    """
    steps = []
    errors = []

    try:
        F     = float(inputs['feed_flow_rate'])           # kg/h
        x_F   = float(inputs['feed_concentration'])       # wt fraction
        x_P   = float(inputs['product_concentration'])    # wt fraction
        T_F   = float(inputs['feed_temp'])                # °C
        P_s   = float(inputs['steam_pressure'])           # kPa
        P_op  = float(inputs.get('operating_pressure', 20))  # kPa
        n_eff = int(inputs.get('n_effects', 1))
        BPR   = float(inputs.get('boiling_point_rise', 5))   # °C
        U     = float(inputs['U_overall'])                # W/m²·K
        material = inputs.get('material', 'Stainless Steel 304')

        if x_F >= x_P:
            errors.append('Product concentration must be greater than feed concentration.')
        if x_F <= 0 or x_P >= 1:
            errors.append('Concentrations must be between 0 and 1.')

        # ── Step 1: Overall Mass Balance ─────────────────────
        # F = W + L  ;  F*x_F = L*x_P  → L = F*x_F/x_P
        L = F * x_F / x_P          # product (thick liquor) kg/h
        W = F - L                  # total water evaporated  kg/h
        steps.append({
            'step': 1, 'title': 'Overall Mass Balance',
            'formula': 'W = F − L = F(1 − x_F/x_P)',
            'calc': f'F={F} kg/h, x_F={x_F}, x_P={x_P}',
            'result': f'W (evaporation) = {W:.2f} kg/h,  L (product) = {L:.2f} kg/h',
        })

        # ── Step 2: Steam & Boiling Temperatures ─────────────
        # Antoine equation for water (simplified): T_boil = 60.65*ln(P_kPa) - 183.1  [approx]
        T_steam = 60.65 * math.log(P_s) - 183.1 if P_s > 0 else 151.8
        T_boil  = 60.65 * math.log(P_op) - 183.1 if P_op > 0 else 60.1
        T_boil  += BPR   # add boiling point rise
        dT_eff  = T_steam - T_boil   # effective ΔT per effect
        steps.append({
            'step': 2, 'title': 'Temperatures',
            'formula': 'T_steam ≈ Antoine; T_boil = T_sat(P_op) + BPR',
            'result': f'T_steam={T_steam:.1f}°C, T_boil={T_boil:.1f}°C, ΔT_eff={dT_eff:.1f}°C',
        })
        if dT_eff < 5:
            errors.append('Effective ΔT < 5°C — insufficient driving force. Increase steam pressure.')

        # ── Step 3: Latent Heats ─────────────────────────────
        # λ_steam = 2257 − 2.09*(T_steam−100) kJ/kg  (simplified)
        lambda_steam = max(2257 - 2.09 * (T_steam - 100), 1800)   # kJ/kg
        lambda_vapor = max(2257 - 2.09 * (T_boil  - 100), 1800)   # kJ/kg
        steps.append({
            'step': 3, 'title': 'Latent Heats',
            'formula': 'λ = 2257 − 2.09·(T−100) kJ/kg',
            'result': f'λ_steam={lambda_steam:.1f} kJ/kg, λ_vapor={lambda_vapor:.1f} kJ/kg',
        })

        # ── Step 4: Feed Enthalpy (preheat needed) ───────────
        cp_feed = float(inputs.get('feed_cp', 4000))  # J/kg·K
        Q_preheat = F * cp_feed * max(T_boil - T_F, 0) / 3600  # W
        steps.append({
            'step': 4, 'title': 'Feed Preheat Duty',
            'formula': 'Q_ph = F·Cp·(T_boil − T_F)',
            'result': f'Q_preheat = {Q_preheat/1000:.2f} kW',
        })

        # ── Step 5: Steam Consumption (single effect basis) ──
        # Q_total = W*λ_vapor/3600 + Q_preheat  [W]
        Q_evap  = W * lambda_vapor * 1000 / 3600   # W
        Q_total = Q_evap + Q_preheat
        S_single = Q_total / (lambda_steam * 1000 / 3.6)  # kg/h
        # Multi-effect: economy ≈ n_effects × 0.85
        economy  = n_eff * 0.85
        S_actual = W / economy   # steam kg/h
        steps.append({
            'step': 5, 'title': 'Steam Consumption',
            'formula': 'S = W / economy;  economy ≈ n_effects × 0.85',
            'calc': f'n_effects={n_eff}, economy={economy:.2f}',
            'result': f'S = {S_actual:.2f} kg/h  ({S_actual/W*100:.1f}% of evaporation)',
        })

        # ── Step 6: Heat Transfer Area ────────────────────────
        # Q = U * A * ΔT_eff
        A_per_effect = Q_total / (U * dT_eff) if dT_eff > 0 else 0
        A_total = A_per_effect * n_eff
        steps.append({
            'step': 6, 'title': 'Heat Transfer Area',
            'formula': 'A = Q / (U · ΔT_eff)',
            'calc': f'Q={Q_total/1000:.2f} kW, U={U} W/m²K, ΔT={dT_eff:.1f}°C',
            'result': f'A/effect = {A_per_effect:.2f} m², A_total = {A_total:.2f} m²',
        })

        # ── Step 7: Evaporator Body Dimensions ────────────────
        # Vapor space: v_vapor = W_per_effect/3600 / rho_vapor
        W_effect = W / n_eff  # kg/h per effect
        rho_v    = P_op * 18 / (8.314 * (T_boil + 273.15))  # ideal gas approx kg/m³
        rho_v    = max(rho_v, 0.1)
        Q_vap_vol = W_effect / (rho_v * 3600)   # m³/s
        # Vapor velocity in body ≈ 1 m/s (design)
        u_v      = 1.0
        A_vapor  = Q_vap_vol / u_v
        D_body   = math.sqrt(4 * A_vapor / math.pi)
        steps.append({
            'step': 7, 'title': 'Evaporator Body Diameter',
            'formula': 'D = √(4·Q_vap / (π·u_vapor))',
            'calc': f'ρ_vapor={rho_v:.3f} kg/m³',
            'result': f'D_body = {D_body:.3f} m per effect',
        })

        # ── Step 8: Cost ──────────────────────────────────────
        material_factors = {'Carbon Steel': 1.0, 'Stainless Steel 304': 1.6, 'Stainless Steel 316': 1.9}
        Fm = material_factors.get(material, 1.0)
        base_cost  = 5000 * (A_total ** 0.65) * Fm
        installed  = base_cost * 3.8
        steps.append({
            'step': 8, 'title': 'Cost Estimation',
            'result': f'Purchased ≈ ${base_cost:,.0f} | Installed ≈ ${installed:,.0f}',
        })

        results = {
            'feed_flow_kgh':         F,
            'evaporation_rate_kgh':  round(W, 2),
            'product_flow_kgh':      round(L, 2),
            'steam_consumption_kgh': round(S_actual, 2),
            'steam_economy':         round(economy, 2),
            'n_effects':             n_eff,
            'area_per_effect_m2':    round(A_per_effect, 2),
            'total_area_m2':         round(A_total, 2),
            'body_diameter_m':       round(D_body, 3),
            'boiling_temp_C':        round(T_boil, 1),
            'steam_temp_C':          round(T_steam, 1),
            'effective_dT':          round(dT_eff, 2),
            'heat_duty_kW':          round(Q_total / 1000, 2),
            'preheat_duty_kW':       round(Q_preheat / 1000, 2),
            'purchased_cost_USD':    round(base_cost, 0),
            'installed_cost_USD':    round(installed, 0),
            'material': material,
            'safety_notes': [
                'Non-condensable gases must be vented from steam chest.',
                f'Operating at {P_op} kPa vacuum — ensure vessel integrity (ASME VIII).',
                'Scale/fouling: plan for periodic CIP cleaning.',
                'Install entrainment separators to prevent product carryover.',
            ],
            'calculation_steps': steps,
            'errors': errors,
        }
        return results

    except Exception as e:
        return {'errors': [f'Evaporator error: {str(e)}'], 'calculation_steps': steps}
