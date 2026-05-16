# ============================================================
# app/calculations/distillation.py
# Binary Distillation Column Design
# Reference: McCabe-Smith-Harriott "Unit Operations" 7th Ed
# ============================================================

import math


def calculate_distillation(inputs: dict) -> dict:
    """
    Binary distillation column sizing using McCabe-Thiele method.

    Args:
        inputs:
            - feed_flow_rate   (kmol/h)
            - feed_composition (mol fraction light key, z_F)
            - distillate_comp  (mol fraction light key, x_D)
            - bottoms_comp     (mol fraction light key, x_B)
            - relative_volatility (α)
            - feed_quality     (q) — 1=sat liquid, 0=sat vapor
            - reflux_ratio     (R) — actual; should be > R_min
            - tray_efficiency  (%) — Murphree overall
            - pressure_kPa
            - material
    """
    steps = []
    errors = []

    try:
        F   = float(inputs['feed_flow_rate'])          # kmol/h
        z_F = float(inputs['feed_composition'])
        x_D = float(inputs['distillate_comp'])
        x_B = float(inputs['bottoms_comp'])
        alpha = float(inputs['relative_volatility'])
        q   = float(inputs.get('feed_quality', 1.0))
        R   = float(inputs['reflux_ratio'])
        E_o = float(inputs.get('tray_efficiency', 70)) / 100  # fractional
        P   = float(inputs.get('pressure_kPa', 101.325))
        material = inputs.get('material', 'Carbon Steel')

        # Validate
        if not (0 < x_B < z_F < x_D < 1):
            errors.append('Must satisfy x_B < z_F < x_D; all between 0 and 1.')
        if alpha <= 1:
            errors.append('Relative volatility α must be > 1 for separation.')
        if R <= 0:
            errors.append('Reflux ratio R must be positive.')

        # ── Step 1: Overall Mass Balance ─────────────────────
        # F = D + B  and  F*z_F = D*x_D + B*x_B
        D = F * (z_F - x_B) / (x_D - x_B)   # distillate flow
        B = F - D                              # bottoms flow
        steps.append({
            'step': 1, 'title': 'Overall Material Balance',
            'formula': 'F = D + B;  F·z_F = D·x_D + B·x_B',
            'calc': f'F={F}, z_F={z_F}, x_D={x_D}, x_B={x_B}',
            'result': f'D = {D:.3f} kmol/h,  B = {B:.3f} kmol/h',
        })

        # ── Step 2: Minimum Reflux Ratio (Underwood) ──────────
        # Equilibrium: y* = α*x / (1 + (α-1)*x)
        # For feed: y_F = α*z_F / (1 + (α-1)*z_F)
        y_F_eq = alpha * z_F / (1 + (alpha - 1) * z_F)
        # Underwood: R_min = (x_D - y_F_eq) / (y_F_eq - z_F) for q=1
        if y_F_eq != z_F:
            R_min = (x_D - y_F_eq) / (y_F_eq - z_F)
        else:
            R_min = 1.2  # fallback
        R_min = max(R_min, 0.5)  # physical lower bound
        steps.append({
            'step': 2, 'title': 'Minimum Reflux Ratio (Underwood)',
            'formula': 'R_min = (x_D − y_F*) / (y_F* − z_F)',
            'calc': f'y_F* = {y_F_eq:.4f}',
            'result': f'R_min = {R_min:.3f}   (actual R = {R:.3f}, R/R_min = {R/R_min:.2f})',
        })
        if R < R_min * 1.05:
            errors.append(f'Reflux ratio {R:.2f} is below or near minimum {R_min:.2f}. Increase R.')

        # ── Step 3: Internal Flows (L, V, L', V') ────────────
        L  = R * D           # liquid flow rectifying  (kmol/h)
        V  = L + D           # vapor flow rectifying   (kmol/h)
        L_prime = L + q * F  # liquid flow stripping   (kmol/h)
        V_prime = V - (1 - q) * F  # vapor flow stripping
        steps.append({
            'step': 3, 'title': 'Internal Column Flows',
            'formula': 'L = R·D;  V = L+D;  L\' = L+q·F;  V\' = V−(1−q)·F',
            'result': f'L={L:.2f}, V={V:.2f}, L\'={L_prime:.2f}, V\'={V_prime:.2f}  kmol/h',
        })

        # ── Step 4: Number of Theoretical Stages (Fenske) ────
        # Fenske equation for minimum stages at total reflux
        N_min = math.log((x_D / (1 - x_D)) * ((1 - x_B) / x_B)) / math.log(alpha)
        # Gilliland correlation for actual reflux
        X_gill = (R - R_min) / (R + 1)
        Y_gill = 1 - math.exp((1 + 54.4 * X_gill) / (11 + 117.2 * X_gill) * (X_gill - 1) / X_gill**0.5)
        N_theoretical = (N_min + Y_gill) / (1 - Y_gill)
        N_actual = math.ceil(N_theoretical / E_o)
        steps.append({
            'step': 4, 'title': 'Number of Stages',
            'formula': 'Fenske (N_min) + Gilliland correlation',
            'calc': f'N_min={N_min:.2f}, Gilliland Y={Y_gill:.3f}',
            'result': f'N_theoretical = {N_theoretical:.1f}, N_actual = {N_actual} (at E_o={E_o*100:.0f}%)',
        })

        # ── Step 5: Feed Tray Location (Kirkbride) ────────────
        # log(N_rect/N_strip) = 0.206 log[(B/D)*(z_F/x_D)²*(x_B/(1−x_D))]
        ratio = (B / D) * (z_F / (1 - x_D)) ** 2 * (x_D / x_B)
        try:
            log_ratio = 0.206 * math.log10(ratio)
            NR_NS = 10 ** log_ratio
            N_rect = round(N_theoretical * NR_NS / (1 + NR_NS))
        except Exception:
            N_rect = round(N_theoretical / 2)
        steps.append({
            'step': 5, 'title': 'Feed Tray Location (Kirkbride)',
            'formula': 'log(N_rect/N_strip) = 0.206·log[...]',
            'result': f'Feed tray ≈ stage {N_rect} from top',
        })

        # ── Step 6: Column Diameter (Fair method) ────────────
        # Vapor velocity from flooding — simplified Fair flooding approach
        # Assume tray spacing = 0.6 m, system factor = 0.8
        # Vapor density: assume ideal gas at T_avg, P
        T_avg_K = float(inputs.get('avg_temp', 100)) + 273.15  # K
        MW_avg  = float(inputs.get('avg_mol_weight', 80))       # g/mol
        rho_V   = P * 1000 * MW_avg / (8314 * T_avg_K)  # kg/m³  (ideal gas)
        rho_L   = float(inputs.get('liquid_density', 750))      # kg/m³

        # Fair flood velocity (simplified)
        C_sbf   = 0.07 * math.sqrt((rho_L - rho_V) / rho_V)  # m/s
        u_flood = C_sbf  # m/s at flooding

        # Design at 80% of flooding
        u_design = 0.80 * u_flood

        # Vapor volumetric flow (m³/s) = V[kmol/h] * MW * 1000 / (rho_V * 3600)
        Q_V = V * MW_avg / (rho_V * 3600)  # m³/s
        A_column = Q_V / u_design
        D_column = math.sqrt(4 * A_column / math.pi)
        steps.append({
            'step': 6, 'title': 'Column Diameter (Fair Method)',
            'formula': 'D = √(4·Q_V / (π·u_design))',
            'calc': f'ρ_V={rho_V:.2f} kg/m³, u_flood={u_flood:.3f} m/s, u_design={u_design:.3f} m/s',
            'result': f'D_column = {D_column:.3f} m  ({D_column*1000:.0f} mm)',
        })

        # ── Step 7: Column Height ─────────────────────────────
        tray_spacing = float(inputs.get('tray_spacing', 0.6))  # m
        H_column = N_actual * tray_spacing + 3.0  # +3 m for top/bottom sections
        steps.append({
            'step': 7, 'title': 'Column Height',
            'formula': 'H = N_actual × tray_spacing + overhead/boot allowance',
            'result': f'H = {H_column:.2f} m',
        })

        # ── Step 8: Condenser & Reboiler Duty ─────────────────
        # Latent heat assumption: λ = 35 000 J/mol
        lambda_vap = float(inputs.get('latent_heat', 35000))  # J/mol
        Q_cond   = V * lambda_vap * 1000 / 3600    # W  (V in kmol/h → mol/s)
        Q_reb    = V_prime * lambda_vap * 1000 / 3600
        steps.append({
            'step': 8, 'title': 'Condenser & Reboiler Duties',
            'formula': 'Q_cond = V·λ;  Q_reb = V\'·λ',
            'result': f'Q_cond = {Q_cond/1000:.2f} kW, Q_reb = {Q_reb/1000:.2f} kW',
        })

        # ── Step 9: Cost Estimation ───────────────────────────
        material_factors = {'Carbon Steel': 1.0, 'Stainless Steel 304': 1.7, 'Stainless Steel 316': 2.0}
        Fm = material_factors.get(material, 1.0)
        # Tower shell cost: C = 10000 * D^1.066 * H^0.802 * Fm
        base_cost  = 10000 * (D_column ** 1.066) * (H_column ** 0.802) * Fm
        installed  = base_cost * 4.5
        steps.append({
            'step': 9, 'title': 'Cost Estimation',
            'formula': 'C = 10000 × D^1.066 × H^0.802 × Fm',
            'result': f'Purchased ≈ ${base_cost:,.0f} | Installed ≈ ${installed:,.0f}',
        })

        results = {
            'feed_flow_kmolh':        F,
            'distillate_flow_kmolh':  round(D, 3),
            'bottoms_flow_kmolh':     round(B, 3),
            'reflux_ratio':           R,
            'reflux_ratio_min':       round(R_min, 3),
            'internal_L_kmolh':       round(L, 2),
            'internal_V_kmolh':       round(V, 2),
            'n_theoretical_stages':   round(N_theoretical, 1),
            'n_actual_stages':        N_actual,
            'feed_stage_from_top':    N_rect,
            'tray_efficiency_pct':    round(E_o * 100, 1),
            'column_diameter_m':      round(D_column, 3),
            'column_height_m':        round(H_column, 2),
            'condenser_duty_kW':      round(Q_cond / 1000, 2),
            'reboiler_duty_kW':       round(Q_reb / 1000, 2),
            'vapor_density_kgm3':     round(rho_V, 3),
            'purchased_cost_USD':     round(base_cost, 0),
            'installed_cost_USD':     round(installed, 0),
            'material': material,
            'safety_notes': [
                'Ensure reflux ratio > 1.2 × R_min for stable operation.',
                'Install tray load tests — design for 70–80% flooding.',
                f'Column diameter {D_column:.2f} m: verify wind/seismic loads (ASME VIII).',
                'Condenser cooling water temperature rise < 10°C.',
                'Use demister pads at overhead vapor outlet.',
            ],
            'calculation_steps': steps,
            'errors': errors,
        }
        return results

    except Exception as e:
        return {'errors': [f'Distillation error: {str(e)}'], 'calculation_steps': steps}
