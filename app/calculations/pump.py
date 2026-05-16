# ============================================================
# app/calculations/pump.py
# Centrifugal Pump Design & Selection
# Reference: Kaplan "Pump Handbook" 4th Ed, ANSI/HI Standards
# ============================================================
import math


def calculate_pump(inputs: dict) -> dict:
    """
    Design and size a centrifugal pump.

    Args:
        inputs:
            - flow_rate        (m³/h)
            - suction_head     (m)  static suction head
            - discharge_head   (m)  static discharge head
            - suction_pressure (kPa)
            - discharge_pressure (kPa)
            - pipe_diameter    (m)
            - pipe_length      (m)
            - fluid_density    (kg/m³)
            - fluid_viscosity  (Pa·s)
            - pump_efficiency  (%) — typical 65–85%
            - motor_efficiency (%) — typical 90–95%
            - vapor_pressure   (kPa) — fluid vapor pressure
            - pipe_roughness   (m)  — 4.6e-5 for commercial steel
            - material
    """
    steps = []
    errors = []

    try:
        Q       = float(inputs['flow_rate']) / 3600        # m³/s
        H_s     = float(inputs['suction_head'])            # m
        H_d     = float(inputs['discharge_head'])          # m
        P_s     = float(inputs['suction_pressure'])        # kPa
        P_d     = float(inputs['discharge_pressure'])      # kPa
        D_pipe  = float(inputs['pipe_diameter'])           # m
        L_pipe  = float(inputs['pipe_length'])             # m
        rho     = float(inputs.get('fluid_density', 1000)) # kg/m³
        mu      = float(inputs.get('fluid_viscosity', 0.001)) # Pa·s
        eta_p   = float(inputs.get('pump_efficiency', 75)) / 100
        eta_m   = float(inputs.get('motor_efficiency', 92)) / 100
        Pv      = float(inputs.get('vapor_pressure', 2.34)) # kPa (water @ 20°C)
        eps     = float(inputs.get('pipe_roughness', 4.6e-5)) # m
        material = inputs.get('material', 'Cast Iron')
        g       = 9.81  # m/s²

        if Q <= 0:
            errors.append('Flow rate must be positive.')
        if D_pipe <= 0:
            errors.append('Pipe diameter must be positive.')

        # ── Step 1: Pipe Velocity ─────────────────────────────
        A_pipe = math.pi * D_pipe**2 / 4
        v      = Q / A_pipe   # m/s
        steps.append({
            'step': 1, 'title': 'Flow Velocity',
            'formula': 'v = Q / A = Q / (π·D²/4)',
            'calc': f'Q={Q:.5f} m³/s, D={D_pipe} m, A={A_pipe:.5f} m²',
            'result': f'v = {v:.3f} m/s  (ideal range: 1.5–3.5 m/s)',
        })
        if v > 5:
            errors.append(f'Pipe velocity {v:.2f} m/s exceeds 5 m/s — increase pipe diameter.')

        # ── Step 2: Reynolds Number ───────────────────────────
        Re = rho * v * D_pipe / mu
        flow_regime = 'Turbulent' if Re > 4000 else ('Transitional' if Re > 2300 else 'Laminar')
        steps.append({
            'step': 2, 'title': 'Reynolds Number',
            'formula': 'Re = ρ·v·D / μ',
            'result': f'Re = {Re:.0f}  ({flow_regime})',
        })

        # ── Step 3: Friction Factor (Colebrook-White) ────────
        if Re < 2300:
            f_D = 64 / Re   # Hagen-Poiseuille (laminar)
        else:
            # Swamee-Jain explicit approximation of Colebrook-White
            f_D = 0.25 / (math.log10(eps / (3.7 * D_pipe) + 5.74 / Re**0.9))**2
        steps.append({
            'step': 3, 'title': 'Darcy Friction Factor',
            'formula': 'Swamee-Jain: f = 0.25/[log(ε/3.7D + 5.74/Re⁰·⁹)]²',
            'calc': f'ε={eps} m, ε/D={eps/D_pipe:.5f}',
            'result': f'f_D = {f_D:.5f}',
        })

        # ── Step 4: Head Losses ───────────────────────────────
        # Major (friction) loss: Darcy-Weisbach
        h_f_major = f_D * (L_pipe / D_pipe) * v**2 / (2 * g)
        # Minor losses — assume K_total = 10 (fittings, valves, etc.)
        K_minor = float(inputs.get('minor_loss_coefficient', 10.0))
        h_f_minor = K_minor * v**2 / (2 * g)
        h_f_total = h_f_major + h_f_minor
        steps.append({
            'step': 4, 'title': 'System Head Losses',
            'formula': 'h_f = f·(L/D)·v²/2g  +  ΣK·v²/2g',
            'calc': f'h_major={h_f_major:.3f} m, h_minor={h_f_minor:.3f} m',
            'result': f'h_f_total = {h_f_total:.3f} m',
        })

        # ── Step 5: Total Dynamic Head (TDH) ─────────────────
        # TDH = (H_d − H_s) + (P_d − P_s)/(ρg) + (v_d² − v_s²)/2g + h_f
        # Assume same pipe diameter suction/discharge → velocity terms cancel
        dP_head = (P_d - P_s) * 1000 / (rho * g)   # pressure head difference
        dZ      = H_d - H_s                          # elevation difference
        TDH     = dZ + dP_head + h_f_total
        steps.append({
            'step': 5, 'title': 'Total Dynamic Head (TDH)',
            'formula': 'TDH = ΔZ + ΔP/(ρg) + h_f',
            'calc': f'ΔZ={dZ:.2f} m, ΔP_head={dP_head:.3f} m, h_f={h_f_total:.3f} m',
            'result': f'TDH = {TDH:.3f} m',
        })

        # ── Step 6: Hydraulic Power ───────────────────────────
        P_hydraulic = rho * g * Q * TDH          # W
        P_shaft     = P_hydraulic / eta_p         # W  (shaft power to fluid)
        P_motor     = P_shaft / eta_m             # W  (power drawn from grid)
        steps.append({
            'step': 6, 'title': 'Power Requirements',
            'formula': 'P_hyd = ρgQH;  P_shaft = P_hyd/η_p;  P_motor = P_shaft/η_m',
            'calc': f'η_pump={eta_p*100:.0f}%, η_motor={eta_m*100:.0f}%',
            'result': (f'P_hydraulic={P_hydraulic/1000:.3f} kW, '
                       f'P_shaft={P_shaft/1000:.3f} kW, '
                       f'P_motor={P_motor/1000:.3f} kW'),
        })

        # ── Step 7: NPSH Available ────────────────────────────
        # NPSHa = (P_s − Pv) / (ρg) + H_s − h_f_suction
        # Estimate suction loss as 30% of total pipe loss
        h_f_suction = 0.3 * h_f_total
        NPSHa = (P_s - Pv) * 1000 / (rho * g) + H_s - h_f_suction
        # Required NPSH (NPSHr): typical 2–6 m for centrifugal pumps
        NPSHr = float(inputs.get('npsh_required', 3.0))
        NPSH_margin = NPSHa - NPSHr
        steps.append({
            'step': 7, 'title': 'Net Positive Suction Head (NPSH)',
            'formula': 'NPSH_a = (P_s−Pv)/(ρg) + H_s − h_f_suction',
            'calc': f'Pv={Pv} kPa, P_s={P_s} kPa',
            'result': (f'NPSHa={NPSHa:.2f} m, NPSHr={NPSHr:.2f} m, '
                       f'Margin={NPSH_margin:.2f} m '
                       f'{"✓ OK" if NPSH_margin > 0 else "⚠ CAVITATION RISK"}'),
        })
        if NPSH_margin < 0:
            errors.append(f'Cavitation risk! NPSHa ({NPSHa:.2f} m) < NPSHr ({NPSHr:.2f} m). Lower pump or raise suction level.')

        # ── Step 8: Specific Speed ────────────────────────────
        # Ns = N * Q^0.5 / TDH^0.75  (N in rpm, Q in m³/s)
        N_rpm = float(inputs.get('speed_rpm', 1450))
        Ns = N_rpm * (Q**0.5) / (TDH**0.75)
        pump_type_str = ('Axial Flow' if Ns > 8000 else
                         'Mixed Flow' if Ns > 3000 else
                         'Radial (Centrifugal)')
        steps.append({
            'step': 8, 'title': 'Specific Speed',
            'formula': 'Ns = N·√Q / TDH^0.75',
            'result': f'Ns = {Ns:.1f}  → {pump_type_str}',
        })

        # ── Step 9: Cost Estimation ───────────────────────────
        material_factors = {'Cast Iron': 1.0, 'Stainless Steel': 1.8, 'Bronze': 1.4, 'Alloy Steel': 2.0}
        Fm = material_factors.get(material, 1.0)
        P_kW = P_motor / 1000
        # Base cost: C = 900 * P_kW^0.61 * Fm
        base_cost = 900 * (P_kW ** 0.61) * Fm
        installed = base_cost * 3.5
        steps.append({
            'step': 9, 'title': 'Cost Estimation',
            'formula': 'C = 900 × P_kW^0.61 × Fm',
            'result': f'Purchased ≈ ${base_cost:,.0f} | Installed ≈ ${installed:,.0f}',
        })

        results = {
            'flow_rate_m3h':        round(Q * 3600, 2),
            'flow_rate_m3s':        round(Q, 5),
            'pipe_velocity_ms':     round(v, 3),
            'reynolds_number':      round(Re, 0),
            'flow_regime':          flow_regime,
            'friction_factor':      round(f_D, 5),
            'head_friction_m':      round(h_f_total, 3),
            'TDH_m':                round(TDH, 3),
            'hydraulic_power_kW':   round(P_hydraulic / 1000, 3),
            'shaft_power_kW':       round(P_shaft / 1000, 3),
            'motor_power_kW':       round(P_motor / 1000, 3),
            'pump_efficiency_pct':  round(eta_p * 100, 1),
            'NPSHa_m':              round(NPSHa, 3),
            'NPSHr_m':              NPSHr,
            'NPSH_margin_m':        round(NPSH_margin, 3),
            'specific_speed':       round(Ns, 1),
            'pump_type':            pump_type_str,
            'purchased_cost_USD':   round(base_cost, 0),
            'installed_cost_USD':   round(installed, 0),
            'material':             material,
            'safety_notes': [
                f'NPSH margin = {NPSH_margin:.2f} m — maintain > 1.0 m safety margin.',
                'Install mechanical seal with flush plan (API Plan 11).',
                'Verify motor is rated for ambient temperature + 10°C.',
                'Provide pressure gauge on suction and discharge.',
                'Install check valve on discharge to prevent backflow.',
                'Couple pump shaft with flexible coupling — check alignment.',
            ],
            'calculation_steps': steps,
            'errors': errors,
        }
        return results

    except Exception as e:
        return {'errors': [f'Pump calculation error: {str(e)}'], 'calculation_steps': steps}
