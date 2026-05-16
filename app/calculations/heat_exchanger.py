# ============================================================
# app/calculations/heat_exchanger.py
# Shell-and-Tube Heat Exchanger Design Calculations
# Reference: Kern (1950), Coulson & Richardson Vol.6
# ============================================================

import math


def calculate_heat_exchanger(inputs: dict) -> dict:
    """
    Perform complete shell-and-tube heat exchanger sizing.

    Args:
        inputs: dict with keys:
            - hot_inlet_temp   (°C)
            - hot_outlet_temp  (°C)
            - cold_inlet_temp  (°C)
            - cold_outlet_temp (°C)
            - hot_flow_rate    (kg/s)
            - cold_flow_rate   (kg/s)
            - hot_cp           (J/kg·K)  specific heat of hot fluid
            - cold_cp          (J/kg·K)  specific heat of cold fluid
            - U_overall        (W/m²·K)  overall heat transfer coefficient
            - tube_od          (m)       tube outer diameter
            - tube_id          (m)       tube inner diameter
            - tube_length      (m)       effective tube length
            - n_passes         (int)     number of tube passes (1 or 2)
            - material         (str)     construction material

    Returns:
        dict with all intermediate steps and final results.
    """
    steps = []
    errors = []

    try:
        # ── Unpack & validate inputs ──────────────────────────
        Th_in  = float(inputs['hot_inlet_temp'])
        Th_out = float(inputs['hot_outlet_temp'])
        Tc_in  = float(inputs['cold_inlet_temp'])
        Tc_out = float(inputs['cold_outlet_temp'])
        m_h    = float(inputs['hot_flow_rate'])
        m_c    = float(inputs['cold_flow_rate'])
        cp_h   = float(inputs['hot_cp'])
        cp_c   = float(inputs['cold_cp'])
        U      = float(inputs['U_overall'])
        d_o    = float(inputs['tube_od'])
        d_i    = float(inputs['tube_id'])
        L      = float(inputs['tube_length'])
        n_pass = int(inputs.get('n_passes', 1))
        material = inputs.get('material', 'Carbon Steel')

        # Basic sanity checks
        if Th_in <= Th_out:
            errors.append('Hot inlet temperature must be greater than hot outlet temperature.')
        if Tc_out <= Tc_in:
            errors.append('Cold outlet temperature must be greater than cold inlet temperature.')
        if Th_in <= Tc_in:
            errors.append('Hot inlet must be hotter than cold inlet (check temperatures).')

        # ── Step 1: Duty (Heat Load) ─────────────────────────
        # Q = m_h * cp_h * (Th_in - Th_out)
        Q_hot  = m_h * cp_h * (Th_in - Th_out)  # W
        Q_cold = m_c * cp_c * (Tc_out - Tc_in)  # W
        Q = (Q_hot + Q_cold) / 2  # average (should be ~equal for no heat loss)
        steps.append({
            'step': 1,
            'title': 'Heat Duty Calculation',
            'formula': 'Q = ṁ · Cp · ΔT',
            'calc': f'Q_hot = {m_h} × {cp_h} × ({Th_in} − {Th_out}) = {Q_hot:.2f} W',
            'result': f'Q ≈ {Q:.2f} W = {Q/1000:.3f} kW',
        })

        # ── Step 2: Log Mean Temperature Difference (LMTD) ───
        # Counter-current LMTD
        dT1 = Th_in  - Tc_out   # hot-end temperature difference
        dT2 = Th_out - Tc_in    # cold-end temperature difference

        if dT1 <= 0 or dT2 <= 0:
            errors.append('Temperature cross detected — check inlet/outlet temperatures.')
            LMTD = abs(dT1 - dT2) / 2 if abs(dT1 - dT2) > 0 else 1  # fallback
        elif abs(dT1 - dT2) < 1e-6:
            LMTD = dT1  # avoid log(1) → 0 division
        else:
            LMTD = (dT1 - dT2) / math.log(dT1 / dT2)

        steps.append({
            'step': 2,
            'title': 'Log Mean Temperature Difference',
            'formula': 'LMTD = (ΔT₁ − ΔT₂) / ln(ΔT₁/ΔT₂)',
            'calc': f'ΔT₁ = {dT1:.2f} °C, ΔT₂ = {dT2:.2f} °C',
            'result': f'LMTD = {LMTD:.3f} °C',
        })

        # ── Step 3: LMTD Correction Factor (F) ───────────────
        # For 1-2 shell-and-tube exchanger (Bowman, Mueller & Nagle)
        R = (Th_in - Th_out) / (Tc_out - Tc_in)  # temperature ratio
        P = (Tc_out - Tc_in) / (Th_in - Tc_in)   # effectiveness

        if n_pass > 1 and R != 1:
            try:
                S = math.sqrt(R**2 + 1) / (R - 1)
                F = (S * math.log((1 - P) / (1 - P * R))) / math.log(
                    (2/P - 1 - R + S + math.sqrt((2/P - 1 - R + S)**2 + R**2 - 1 - S*2)) /
                    (2/P - 1 - R + S - math.sqrt((2/P - 1 - R + S)**2 + R**2 - 1 - S*2))
                ) if (2/P - 1 - R + S) > 0 else 0.85
            except Exception:
                F = 0.85  # typical design value when formula fails
        else:
            F = 1.0  # pure counter-current or R=1 case

        F = max(0.75, min(F, 1.0))  # clamp to practical range
        steps.append({
            'step': 3,
            'title': 'LMTD Correction Factor',
            'formula': 'F = f(R, P) — Bowman-Mueller-Nagle correlation',
            'calc': f'R = {R:.3f}, P = {P:.3f}',
            'result': f'F = {F:.3f}',
        })

        # ── Step 4: Required Heat Transfer Area ──────────────
        # A = Q / (U · F · LMTD)
        A_required = Q / (U * F * LMTD)
        steps.append({
            'step': 4,
            'title': 'Required Heat Transfer Area',
            'formula': 'A = Q / (U · F · LMTD)',
            'calc': f'A = {Q:.2f} / ({U} × {F:.3f} × {LMTD:.3f})',
            'result': f'A = {A_required:.4f} m²',
        })

        # ── Step 5: Number of Tubes ───────────────────────────
        # Area per tube = π · d_o · L
        area_per_tube = math.pi * d_o * L
        N_tubes = math.ceil(A_required / area_per_tube)
        steps.append({
            'step': 5,
            'title': 'Number of Tubes',
            'formula': 'N_tubes = A_required / (π · d_o · L)',
            'calc': f'Area/tube = π × {d_o} × {L} = {area_per_tube:.4f} m²',
            'result': f'N_tubes = {N_tubes}',
        })

        # ── Step 6: Shell Diameter (Kern method) ──────────────
        # Tube pitch (triangular, 1.25 × d_o)
        p_t = 1.25 * d_o
        # Bundle diameter: Db = d_o * (N_tubes / K1)^(1/n1)
        # K1, n1 for triangular pitch, 1-pass (TEMA standards)
        K1 = 0.319 if n_pass == 1 else 0.249
        n1 = 2.142 if n_pass == 1 else 2.207
        D_bundle = d_o * (N_tubes / K1) ** (1 / n1)

        # Shell inside diameter = bundle + clearance (~12 mm for fixed tubesheet)
        clearance = 0.012  # m
        D_shell = D_bundle + clearance
        steps.append({
            'step': 6,
            'title': 'Shell & Bundle Diameter',
            'formula': 'D_b = d_o × (N/K₁)^(1/n₁)',
            'calc': f'D_bundle = {d_o} × ({N_tubes}/{K1})^(1/{n1}) = {D_bundle:.4f} m',
            'result': f'D_shell = {D_shell:.4f} m  ({D_shell*1000:.1f} mm)',
        })

        # ── Step 7: Shell-side Baffle Spacing ─────────────────
        # Typical baffle spacing = 0.3–0.5 × D_shell
        baffle_spacing = 0.4 * D_shell
        steps.append({
            'step': 7,
            'title': 'Baffle Spacing',
            'formula': 'B = 0.40 × D_shell  (TEMA guideline)',
            'result': f'B = {baffle_spacing:.4f} m  ({baffle_spacing*1000:.1f} mm)',
        })

        # ── Step 8: Tube-side Velocity ────────────────────────
        # Assume water-like density 1000 kg/m³ for tube fluid
        rho_tube = float(inputs.get('cold_density', 1000))  # kg/m³
        A_tube_flow = (math.pi / 4) * d_i**2 * (N_tubes / n_pass)
        v_tube = m_c / (rho_tube * A_tube_flow)
        steps.append({
            'step': 8,
            'title': 'Tube-side Velocity',
            'formula': 'v = ṁ / (ρ · A_flow)',
            'calc': f'A_flow = {A_tube_flow:.6f} m²',
            'result': f'v_tube = {v_tube:.3f} m/s  (ideal: 1–3 m/s)',
        })

        # ── Step 9: Heat Transfer Coefficient (tube-side) ─────
        # Dittus-Boelter: Nu = 0.023 × Re^0.8 × Pr^0.4
        mu_c  = float(inputs.get('cold_viscosity', 0.001))   # Pa·s
        k_c   = float(inputs.get('cold_conductivity', 0.6))  # W/m·K
        Pr_c  = cp_c * mu_c / k_c
        Re_c  = rho_tube * v_tube * d_i / mu_c
        Nu_c  = 0.023 * (Re_c ** 0.8) * (Pr_c ** 0.4)
        h_i   = Nu_c * k_c / d_i
        steps.append({
            'step': 9,
            'title': 'Tube-side Heat Transfer Coefficient',
            'formula': 'Nu = 0.023 × Re⁰·⁸ × Pr⁰·⁴  (Dittus-Boelter)',
            'calc': f'Re = {Re_c:.1f}, Pr = {Pr_c:.3f}, Nu = {Nu_c:.2f}',
            'result': f'h_i = {h_i:.2f} W/m²·K',
        })

        # ── Step 10: Pressure Drop (tube-side) ───────────────
        # Darcy-Weisbach: ΔP = f * (L/d_i) * (ρ*v²/2) * n_pass
        # f from Churchill correlation (simplified): f ≈ 0.316/Re^0.25 (Blasius)
        f_tube = 0.316 / (Re_c ** 0.25) if Re_c > 4000 else 64 / Re_c
        dP_tube = f_tube * (L / d_i) * (rho_tube * v_tube**2 / 2) * n_pass
        steps.append({
            'step': 10,
            'title': 'Tube-side Pressure Drop',
            'formula': 'ΔP = f · (L/d_i) · (ρv²/2) · n_pass',
            'calc': f'f = {f_tube:.5f}',
            'result': f'ΔP_tube = {dP_tube:.2f} Pa  ({dP_tube/1000:.3f} kPa)',
        })

        # ── Step 11: Efficiency / Effectiveness ──────────────
        # NTU-Effectiveness method
        # NTU = U·A / C_min
        C_hot  = m_h * cp_h
        C_cold = m_c * cp_c
        C_min  = min(C_hot, C_cold)
        C_max  = max(C_hot, C_cold)
        C_r    = C_min / C_max  # heat capacity ratio
        NTU    = U * A_required / C_min

        # Counter-flow effectiveness
        if C_r < 1:
            effectiveness = (1 - math.exp(-NTU * (1 - C_r))) / (1 - C_r * math.exp(-NTU * (1 - C_r)))
        else:
            effectiveness = NTU / (NTU + 1)

        effectiveness = min(effectiveness, 1.0)
        steps.append({
            'step': 11,
            'title': 'Thermal Effectiveness (NTU Method)',
            'formula': 'ε = (1 − e^(−NTU(1−Cr))) / (1 − Cr·e^(−NTU(1−Cr)))',
            'calc': f'NTU = {NTU:.3f}, Cr = {C_r:.3f}',
            'result': f'Effectiveness ε = {effectiveness*100:.2f}%',
        })

        # ── Step 12: Cost Estimation ─────────────────────────
        # Simplified purchased cost using Guthrie correlations (2024 CEPCI ~800)
        material_factors = {
            'Carbon Steel': 1.0, 'Stainless Steel 304': 1.8,
            'Stainless Steel 316': 2.1, 'Titanium': 4.5,
            'Copper': 1.6, 'Nickel Alloy': 3.5,
        }
        Fm = material_factors.get(material, 1.0)
        # Base cost for shell-and-tube (USD, 2024): C = a * A^b
        # a=1200, b=0.6 for A in m²
        base_cost = 1200 * (A_required ** 0.6) * Fm
        installed_cost = base_cost * 3.5  # typical installation factor
        steps.append({
            'step': 12,
            'title': 'Cost Estimation',
            'formula': 'C_base = 1200 × A^0.6 × Fm (Guthrie, 2024)',
            'calc': f'Fm = {Fm} for {material}',
            'result': f'Purchased cost ≈ ${base_cost:,.0f} | Installed ≈ ${installed_cost:,.0f}',
        })

        # ── Compile Results ───────────────────────────────────
        results = {
            # Thermal
            'heat_duty_kW':        round(Q / 1000, 3),
            'LMTD':                round(LMTD, 3),
            'F_correction':        round(F, 3),
            'effectiveness_pct':   round(effectiveness * 100, 2),
            'NTU':                 round(NTU, 3),
            # Geometry
            'area_required_m2':    round(A_required, 4),
            'number_of_tubes':     N_tubes,
            'tube_od_m':           d_o,
            'tube_id_m':           d_i,
            'tube_length_m':       L,
            'tube_pitch_m':        round(p_t, 4),
            'shell_diameter_m':    round(D_shell, 4),
            'bundle_diameter_m':   round(D_bundle, 4),
            'baffle_spacing_m':    round(baffle_spacing, 4),
            'n_passes':            n_pass,
            # Hydraulics
            'tube_velocity_ms':    round(v_tube, 3),
            'tube_Re':             round(Re_c, 1),
            'tube_Pr':             round(Pr_c, 3),
            'tube_Nu':             round(Nu_c, 2),
            'h_tube_W_m2K':        round(h_i, 2),
            'dP_tube_Pa':          round(dP_tube, 2),
            # Cost
            'purchased_cost_USD':  round(base_cost, 0),
            'installed_cost_USD':  round(installed_cost, 0),
            'material':            material,
            # Safety
            'safety_notes': [
                'Maintain tube-side velocity between 1–3 m/s to prevent fouling.',
                'Pressure drop should not exceed 70 kPa per pass.',
                'Verify thermal expansion allowances for fixed tubesheet design.',
                f'Maximum operating temperature for {material}: use ASME B31.3 tables.',
                'Install relief valve on shell-side if it can be isolated.',
            ],
            # Steps
            'calculation_steps': steps,
            'errors': errors,
        }

        return results

    except Exception as e:
        return {
            'errors': [f'Calculation error: {str(e)}'],
            'calculation_steps': steps,
        }
