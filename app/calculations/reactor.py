# ============================================================
# app/calculations/reactor.py
# Continuous Stirred Tank Reactor (CSTR) & PFR Design
# Reference: Levenspiel "Chemical Reaction Engineering" 3rd Ed
# ============================================================

import math


def calculate_reactor(inputs: dict) -> dict:
    """
    Design a CSTR or PFR for a first-order or second-order reaction.

    Args:
        inputs:
            - reactor_type    (str)   'CSTR' | 'PFR'
            - reaction_order  (int)   1 | 2
            - feed_flow_rate  (m³/s)  volumetric feed flow
            - inlet_conc      (mol/m³) reactant inlet concentration CA0
            - conversion      (float) desired fractional conversion X (0–1)
            - rate_constant   (float) k  [s⁻¹ for 1st order; m³/mol·s for 2nd]
            - temperature     (°C)    operating temperature
            - pressure        (kPa)   operating pressure
            - activation_energy (J/mol) Ea (optional)
            - heat_of_reaction  (J/mol) ΔHrxn (optional, exothermic < 0)
            - material         (str)
    """
    steps = []
    errors = []

    try:
        rtype  = inputs.get('reactor_type', 'CSTR').upper()
        order  = int(inputs.get('reaction_order', 1))
        v0     = float(inputs['feed_flow_rate'])      # m³/s
        CA0    = float(inputs['inlet_conc'])           # mol/m³
        X      = float(inputs['conversion'])           # 0–1
        k      = float(inputs['rate_constant'])
        T_op   = float(inputs['temperature'])          # °C
        P_op   = float(inputs['pressure'])             # kPa
        Ea     = float(inputs.get('activation_energy', 50000))  # J/mol
        dHrxn  = float(inputs.get('heat_of_reaction', -80000))  # J/mol
        material = inputs.get('material', 'Stainless Steel 316')

        if X <= 0 or X >= 1:
            errors.append('Conversion X must be between 0 and 1 (exclusive).')
        if k <= 0:
            errors.append('Rate constant k must be positive.')

        CA = CA0 * (1 - X)   # exit concentration

        # ── Step 1: Space Time / Residence Time ───────────────
        if rtype == 'CSTR':
            if order == 1:
                # τ = X / (k*(1-X))  from CSTR design equation
                tau = X / (k * (1 - X))
                FA0 = v0 * CA0
                V_reactor = tau * v0
                r_formula = 'CSTR: V = F_A0·X / (−r_A) where −r_A = k·C_A'
            elif order == 2:
                # −r_A = k·CA² ; V = F_A0·X / (k·CA²)
                r_A = k * CA**2
                V_reactor = v0 * CA0 * X / r_A
                tau = V_reactor / v0
                r_formula = 'CSTR: V = F_A0·X / k·C_A²'
            else:
                errors.append('Only 1st and 2nd order reactions are supported.')
                return {'errors': errors, 'calculation_steps': steps}
        else:  # PFR
            if order == 1:
                # τ = −ln(1−X)/k
                tau = -math.log(1 - X) / k
                V_reactor = tau * v0
                r_formula = 'PFR: V/F_A0 = −∫dX/(−r_A) = −ln(1−X)/k'
            elif order == 2:
                # τ = X / (k·CA0·(1−X))
                tau = X / (k * CA0 * (1 - X))
                V_reactor = tau * v0
                r_formula = 'PFR: V = (1/k·CA0) × X/(1−X)'
            else:
                errors.append('Only 1st and 2nd order reactions supported.')
                return {'errors': errors, 'calculation_steps': steps}

        steps.append({
            'step': 1, 'title': 'Space Time (τ) Calculation',
            'formula': r_formula,
            'calc': f'τ = {tau:.4f} s = {tau/60:.3f} min',
            'result': f'Reactor Volume V = {V_reactor:.4f} m³ = {V_reactor*1000:.2f} L',
        })

        # ── Step 2: Reactor Geometry (cylindrical) ────────────
        # Assume L/D = 1.5 (CSTR) or 10 (PFR/tubular)
        LD_ratio = 1.5 if rtype == 'CSTR' else 10.0
        # V = π/4 * D² * L = π/4 * D² * LD * D → D = (4V/(π*LD))^(1/3)
        D_reactor = (4 * V_reactor / (math.pi * LD_ratio)) ** (1/3)
        L_reactor = LD_ratio * D_reactor
        steps.append({
            'step': 2, 'title': 'Reactor Geometry',
            'formula': 'V = (π/4)·D²·L,  L/D = assumed ratio',
            'calc': f'L/D = {LD_ratio}',
            'result': f'D = {D_reactor:.3f} m,  L = {L_reactor:.3f} m',
        })

        # ── Step 3: Heat Generation / Removal Rate ────────────
        # Q_rxn = F_A0 * X * |ΔHrxn|
        FA0   = v0 * CA0   # mol/s
        Q_rxn = FA0 * X * abs(dHrxn)  # W
        rxn_type = 'Exothermic' if dHrxn < 0 else 'Endothermic'
        steps.append({
            'step': 3, 'title': 'Heat of Reaction',
            'formula': 'Q = F_A0 · X · |ΔH_rxn|',
            'calc': f'F_A0 = {FA0:.4f} mol/s, ΔHrxn = {dHrxn:.0f} J/mol',
            'result': f'Q_rxn = {Q_rxn:.2f} W  ({rxn_type})',
        })

        # ── Step 4: Adiabatic Temperature Rise ───────────────
        # ΔT_ad = −ΔHrxn * CA0 * X / (ρ_mix * Cp_mix)
        # Assume dilute aqueous solution: ρ≈1000 kg/m³, Cp≈4184 J/kg·K
        rho_mix = float(inputs.get('density', 1000))
        Cp_mix  = float(inputs.get('cp_mix', 4184))
        dT_ad = abs(dHrxn) * CA0 * X / (rho_mix * Cp_mix)
        steps.append({
            'step': 4, 'title': 'Adiabatic Temperature Rise',
            'formula': 'ΔT_ad = |ΔH_rxn|·C_A0·X / (ρ·Cp)',
            'result': f'ΔT_adiabatic = {dT_ad:.2f} °C',
        })

        # ── Step 5: Damköhler Number ──────────────────────────
        Da = k * tau if order == 1 else k * CA0 * tau
        steps.append({
            'step': 5, 'title': 'Damköhler Number',
            'formula': 'Da = k·τ  (1st order)',
            'result': f'Da = {Da:.3f}  (>1 means reaction-limited design adequate)',
        })

        # ── Step 6: Activation Energy Check (Arrhenius) ───────
        R_gas = 8.314   # J/mol·K
        T_K   = T_op + 273.15
        # k at reference 25°C
        k_ref = k * math.exp(Ea / R_gas * (1/298.15 - 1/T_K))
        steps.append({
            'step': 6, 'title': 'Temperature Effect (Arrhenius)',
            'formula': 'k(T) = k_ref · exp[−Ea/R·(1/T − 1/T_ref)]',
            'calc': f'Ea = {Ea} J/mol, T = {T_op}°C',
            'result': f'k_ref(25°C) = {k_ref:.4e}  →  verify kinetics in literature',
        })

        # ── Step 7: Cost Estimation ───────────────────────────
        material_factors = {'Carbon Steel': 1.0, 'Stainless Steel 316': 2.0, 'Hastelloy': 4.0}
        Fm = material_factors.get(material, 1.5)
        # Vessel cost: C = 4000 * V^0.57 * Fm (USD, 2024 basis)
        base_cost = 4000 * (V_reactor ** 0.57) * Fm
        installed  = base_cost * 4.2  # typical for reactors
        steps.append({
            'step': 7, 'title': 'Cost Estimation',
            'formula': 'C = 4000 × V^0.57 × Fm',
            'result': f'Purchased ≈ ${base_cost:,.0f} | Installed ≈ ${installed:,.0f}',
        })

        results = {
            'reactor_type':      rtype,
            'reaction_order':    order,
            'volume_m3':         round(V_reactor, 4),
            'volume_L':          round(V_reactor * 1000, 2),
            'diameter_m':        round(D_reactor, 3),
            'length_m':          round(L_reactor, 3),
            'space_time_s':      round(tau, 4),
            'residence_time_min': round(tau / 60, 3),
            'inlet_conc':        CA0,
            'outlet_conc':       round(CA, 4),
            'conversion_pct':    round(X * 100, 1),
            'heat_generation_W': round(Q_rxn, 2),
            'adiabatic_dT':      round(dT_ad, 2),
            'damkohler_number':  round(Da, 3),
            'operating_temp_C':  T_op,
            'operating_press_kPa': P_op,
            'purchased_cost_USD': round(base_cost, 0),
            'installed_cost_USD': round(installed, 0),
            'material': material,
            'safety_notes': [
                f'Adiabatic temperature rise = {dT_ad:.1f}°C — design cooling jacket accordingly.',
                'Install pressure relief valve per ASME Sec. VIII.',
                'Ensure adequate mixing (impeller power: P = Np·ρ·N³·D_impeller⁵).',
                'Monitor for hot spots in exothermic reactions.',
                f'Maximum {material} service temperature: verify ASME tables.',
                'Runaway reaction protection: emergency quench or dump tank required.',
            ],
            'calculation_steps': steps,
            'errors': errors,
        }
        return results

    except Exception as e:
        return {'errors': [f'Reactor calculation error: {str(e)}'], 'calculation_steps': steps}
