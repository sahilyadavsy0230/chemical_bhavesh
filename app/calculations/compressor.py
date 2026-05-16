# ============================================================
# app/calculations/compressor.py
# Centrifugal / Reciprocating Compressor Design
# Reference: GPSA Engineering Data Book, Perry's Handbook
# ============================================================
import math


def calculate_compressor(inputs: dict) -> dict:
    """
    Design and size a gas compressor (centrifugal or reciprocating).

    Args:
        inputs:
            - compressor_type   (str) 'Centrifugal' | 'Reciprocating'
            - gas_flow_rate     (m³/h at inlet conditions)
            - inlet_pressure    (kPa abs)
            - outlet_pressure   (kPa abs)
            - inlet_temperature (°C)
            - gas_mol_weight    (g/mol)
            - specific_heat_ratio (γ = Cp/Cv)  e.g. 1.4 for air
            - compressor_efficiency (%) isentropic
            - mechanical_efficiency (%)
            - n_stages          (int) 1, 2, or 3
            - material
    """
    steps = []
    errors = []

    try:
        ctype  = inputs.get('compressor_type', 'Centrifugal')
        Q_in   = float(inputs['gas_flow_rate'])            # m³/h
        P1     = float(inputs['inlet_pressure'])            # kPa abs
        P2     = float(inputs['outlet_pressure'])           # kPa abs
        T1     = float(inputs['inlet_temperature']) + 273.15  # K
        MW     = float(inputs.get('gas_mol_weight', 29))   # g/mol
        gamma  = float(inputs.get('specific_heat_ratio', 1.4))
        eta_is = float(inputs.get('compressor_efficiency', 75)) / 100
        eta_m  = float(inputs.get('mechanical_efficiency', 95)) / 100
        n_stg  = int(inputs.get('n_stages', 1))
        material = inputs.get('material', 'Carbon Steel')
        R_gas  = 8314  # J/kmol·K

        if P2 <= P1:
            errors.append('Outlet pressure must be greater than inlet pressure.')
        if P1 <= 0 or P2 <= 0:
            errors.append('Pressures must be positive absolute values.')

        # ── Step 1: Compression Ratio ─────────────────────────
        r_total = P2 / P1          # overall compression ratio
        r_stage = r_total ** (1 / n_stg)  # per-stage ratio
        steps.append({
            'step': 1, 'title': 'Compression Ratio',
            'formula': 'r = P₂/P₁;  r_stage = r^(1/n_stages)',
            'calc': f'P1={P1} kPa, P2={P2} kPa',
            'result': f'r_total = {r_total:.3f}, r_stage = {r_stage:.3f}',
        })
        if r_stage > 4.0:
            errors.append(f'Stage compression ratio {r_stage:.2f} > 4.0 — add more stages.')

        # ── Step 2: Inlet Gas Density ─────────────────────────
        # ρ = PM / (RT)  — ideal gas, M in kg/kmol
        rho1 = P1 * 1000 * MW / (R_gas * T1)   # kg/m³
        steps.append({
            'step': 2, 'title': 'Inlet Gas Density',
            'formula': 'ρ = PM / (RT)  [ideal gas]',
            'calc': f'P={P1} kPa, M={MW} g/mol, T={T1:.1f} K',
            'result': f'ρ₁ = {rho1:.4f} kg/m³',
        })

        # ── Step 3: Mass Flow Rate ────────────────────────────
        Q_m3s  = Q_in / 3600       # m³/s
        m_dot  = rho1 * Q_m3s      # kg/s
        steps.append({
            'step': 3, 'title': 'Mass Flow Rate',
            'formula': 'ṁ = ρ₁ · Q',
            'result': f'ṁ = {m_dot:.4f} kg/s = {m_dot*3600:.2f} kg/h',
        })

        # ── Step 4: Isentropic Outlet Temperature (per stage) ─
        # T2s = T1 * r^((γ-1)/γ)
        T2s_stage = T1 * (r_stage ** ((gamma - 1) / gamma))
        T2_actual = T1 + (T2s_stage - T1) / eta_is   # actual outlet T (with inefficiency)
        steps.append({
            'step': 4, 'title': 'Outlet Temperature (Isentropic)',
            'formula': 'T₂s = T₁ · r^((γ−1)/γ)',
            'calc': f'γ={gamma}, r_stage={r_stage:.3f}, T₁={T1:.1f} K',
            'result': (f'T₂s (isentropic) = {T2s_stage:.1f} K = {T2s_stage-273.15:.1f}°C\n'
                       f'T₂_actual = {T2_actual:.1f} K = {T2_actual-273.15:.1f}°C'),
        })
        if T2_actual - 273.15 > 200:
            errors.append(f'Actual discharge temperature {T2_actual-273.15:.1f}°C is high — consider inter-cooling.')

        # ── Step 5: Isentropic Work per Stage ────────────────
        # W_is = [γ/(γ-1)] * R * T1 * (r^((γ-1)/γ) - 1)  per kg
        # R_specific = R_gas / MW (in J/kg·K)
        R_specific = R_gas / MW   # J/kg·K
        W_is_stage = (gamma / (gamma - 1)) * R_specific * T1 * (r_stage**((gamma-1)/gamma) - 1)
        W_actual   = W_is_stage / eta_is   # actual work per kg, per stage
        W_total    = W_actual * n_stg      # total actual work per kg
        steps.append({
            'step': 5, 'title': 'Isentropic Work (per stage)',
            'formula': 'W_is = [γ/(γ−1)]·R_sp·T₁·(r^((γ−1)/γ)−1)',
            'calc': f'R_sp={R_specific:.2f} J/kg·K',
            'result': (f'W_is/stage = {W_is_stage/1000:.3f} kJ/kg\n'
                       f'W_actual/stage = {W_actual/1000:.3f} kJ/kg\n'
                       f'W_total = {W_total/1000:.3f} kJ/kg'),
        })

        # ── Step 6: Shaft Power ───────────────────────────────
        P_shaft = m_dot * W_total      # W
        P_input = P_shaft / eta_m      # W (including mechanical losses)
        steps.append({
            'step': 6, 'title': 'Power Requirements',
            'formula': 'P_shaft = ṁ · W_total;  P_input = P_shaft / η_mech',
            'result': (f'P_shaft = {P_shaft/1000:.3f} kW\n'
                       f'P_input (motor) = {P_input/1000:.3f} kW'),
        })

        # ── Step 7: Volumetric Flow at Outlet ─────────────────
        # Use ideal gas: Q2 = Q1 * (P1/P2) * (T2/T1)
        Q_out = Q_m3s * (P1 / P2) * (T2_actual / T1)
        rho2  = P2 * 1000 * MW / (R_gas * T2_actual)
        steps.append({
            'step': 7, 'title': 'Outlet Volumetric Flow',
            'formula': 'Q₂ = Q₁·(P₁/P₂)·(T₂/T₁)',
            'result': f'Q_out = {Q_out*3600:.3f} m³/h,  ρ₂ = {rho2:.4f} kg/m³',
        })

        # ── Step 8: Impeller / Piston Sizing ─────────────────
        if ctype == 'Centrifugal':
            # Head coefficient ψ = 0.5 (typical)
            # Euler head: H_euler = W_is / g
            g = 9.81
            H_euler = W_is_stage / g   # m (per stage, isentropic)
            psi = 0.5  # typical head coefficient
            # Tip speed: u2 = sqrt(W_is / ψ)
            u2 = math.sqrt(W_is_stage / psi)
            # Impeller diameter: u2 = π * D * N/60
            N_rpm = float(inputs.get('speed_rpm', 3000))
            D_impeller = 60 * u2 / (math.pi * N_rpm)
            steps.append({
                'step': 8, 'title': 'Impeller Sizing (Centrifugal)',
                'formula': 'u₂ = √(W_is/ψ);  D = 60·u₂/(π·N)',
                'calc': f'ψ=0.5, N={N_rpm} rpm',
                'result': f'u₂={u2:.2f} m/s, D_impeller={D_impeller:.3f} m',
            })
            dim_result = {'impeller_diameter_m': round(D_impeller, 3), 'tip_speed_ms': round(u2, 2)}
        else:
            # Reciprocating — bore/stroke sizing
            N_cyl = n_stg
            vol_eff = 0.85  # volumetric efficiency
            rpm = float(inputs.get('speed_rpm', 360))
            # Piston displacement per minute = Q_in / vol_eff
            Vd_total = Q_in / (vol_eff * rpm)   # m³/rev
            Vd_cyl   = Vd_total / N_cyl
            # Stroke = 1.2 * Bore (typical)
            bore = (4 * Vd_cyl / (math.pi * 1.2)) ** (1/3)
            stroke = 1.2 * bore
            steps.append({
                'step': 8, 'title': 'Cylinder Sizing (Reciprocating)',
                'formula': 'V_disp = Q/(η_vol·rpm);  bore = (4V/(π·1.2))^(1/3)',
                'result': f'Bore={bore*1000:.1f} mm, Stroke={stroke*1000:.1f} mm/cylinder',
            })
            dim_result = {'bore_mm': round(bore*1000, 1), 'stroke_mm': round(stroke*1000, 1)}

        # ── Step 9: Inter-cooling Load (if multi-stage) ───────
        Q_intercool = 0
        if n_stg > 1:
            # Cool back to T1 between stages
            Cp = gamma * R_specific / (gamma - 1)   # J/kg·K
            Q_intercool = m_dot * Cp * (T2_actual - T1) * (n_stg - 1)  # W
            steps.append({
                'step': 9, 'title': 'Inter-cooling Duty',
                'formula': 'Q_ic = ṁ·Cp·(T₂−T₁)·(n−1)',
                'result': f'Q_intercooler = {Q_intercool/1000:.3f} kW per inter-cooler',
            })

        # ── Step 10: Cost Estimation ──────────────────────────
        material_factors = {'Carbon Steel': 1.0, 'Stainless Steel': 1.9, 'Alloy Steel': 2.5}
        Fm = material_factors.get(material, 1.0)
        P_kW = P_input / 1000
        # Centrifugal: C = 2500*P^0.55; Reciprocating: C = 3500*P^0.55
        a = 2500 if ctype == 'Centrifugal' else 3500
        base_cost = a * (P_kW ** 0.55) * Fm
        installed = base_cost * 4.0
        steps.append({
            'step': 10, 'title': 'Cost Estimation',
            'formula': f'C = {a}×P^0.55×Fm',
            'result': f'Purchased ≈ ${base_cost:,.0f} | Installed ≈ ${installed:,.0f}',
        })

        results = {
            'compressor_type':        ctype,
            'n_stages':               n_stg,
            'compression_ratio_total': round(r_total, 3),
            'compression_ratio_stage': round(r_stage, 3),
            'inlet_density_kgm3':     round(rho1, 4),
            'mass_flow_kgs':          round(m_dot, 4),
            'mass_flow_kgh':          round(m_dot * 3600, 2),
            'outlet_temp_isentropic_C': round(T2s_stage - 273.15, 1),
            'outlet_temp_actual_C':   round(T2_actual - 273.15, 1),
            'isentropic_work_kJkg':   round(W_is_stage / 1000, 3),
            'actual_work_kJkg':       round(W_actual / 1000, 3),
            'shaft_power_kW':         round(P_shaft / 1000, 3),
            'motor_power_kW':         round(P_input / 1000, 3),
            'outlet_flow_m3h':        round(Q_out * 3600, 3),
            'intercooler_duty_kW':    round(Q_intercool / 1000, 3),
            'isentropic_efficiency_pct': round(eta_is * 100, 1),
            'purchased_cost_USD':     round(base_cost, 0),
            'installed_cost_USD':     round(installed, 0),
            'material':               material,
            **dim_result,
            'safety_notes': [
                f'Discharge temperature {T2_actual-273.15:.1f}°C — verify material compatibility.',
                'Install safety relief valve on each stage discharge.',
                'Surge control: install anti-surge bypass valve (centrifugal).',
                'Vibration monitoring required per API 670.',
                'Lube oil system: maintain pressure > 150 kPa at bearings.',
                'Pressure test per ASME Sec VIII at 1.5× design pressure.',
            ],
            'calculation_steps': steps,
            'errors': errors,
        }
        return results

    except Exception as e:
        return {'errors': [f'Compressor error: {str(e)}'], 'calculation_steps': steps}
