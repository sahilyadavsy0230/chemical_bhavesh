# ============================================================
# app/calculations/absorber.py
# Gas Absorption Column Design (Packed Tower)
# Reference: Treybal "Mass Transfer Operations" 3rd Ed
# ============================================================
import math


def calculate_absorber(inputs: dict) -> dict:
    """
    Design a packed absorption column.

    Args:
        inputs:
            - gas_flow_rate     (m³/h at operating conditions)
            - liquid_flow_rate  (m³/h)
            - inlet_gas_conc    (mol fraction of solute in gas, y1)
            - outlet_gas_conc   (mol fraction required, y2)
            - inlet_liquid_conc (mol fraction of solute in liquid, x2)
            - henry_constant    (H, dimensionless  y* = H*x)
            - pressure_kPa
            - temperature_C
            - packing_type      (str) 'Raschig Rings' | 'Pall Rings' | 'Saddles'
            - packing_size_m    (m)
            - material
    """
    steps = []
    errors = []

    try:
        G_vol   = float(inputs['gas_flow_rate'])          # m³/h
        L_vol   = float(inputs['liquid_flow_rate'])       # m³/h
        y1      = float(inputs['inlet_gas_conc'])         # bottom of column (rich gas in)
        y2      = float(inputs['outlet_gas_conc'])        # top (clean gas out)
        x2      = float(inputs.get('inlet_liquid_conc', 0.0))  # top (lean solvent in)
        H       = float(inputs['henry_constant'])         # y* = H*x
        P       = float(inputs['pressure_kPa'])           # kPa
        T       = float(inputs['temperature_C'])          # °C
        d_pack  = float(inputs.get('packing_size_m', 0.05))
        packing = inputs.get('packing_type', 'Pall Rings')
        material = inputs.get('material', 'Carbon Steel')

        if y2 >= y1:
            errors.append('Outlet gas concentration must be less than inlet.')
        if x2 < 0 or x2 >= 1:
            errors.append('Inlet liquid concentration must be 0 ≤ x2 < 1.')

        # ── Step 1: Gas & Liquid Molar Flows ─────────────────
        # Ideal gas: n = PV/RT
        R_gas = 8.314   # J/mol·K
        T_K   = T + 273.15
        MW_gas = float(inputs.get('gas_mol_weight', 29))   # g/mol (air-like)
        MW_liq = float(inputs.get('liquid_mol_weight', 18))  # g/mol (water-like)
        rho_gas = P * 1000 * MW_gas / (R_gas * T_K * 1000)  # kg/m³
        rho_liq = float(inputs.get('liquid_density', 1000))

        G_mass = G_vol * rho_gas / 3600   # kg/s
        L_mass = L_vol * rho_liq / 3600   # kg/s
        G_mol  = G_mass * 1000 / MW_gas   # mol/s
        L_mol  = L_mass * 1000 / MW_liq   # mol/s

        steps.append({
            'step': 1, 'title': 'Molar Flow Rates',
            'formula': 'G = ρ·Q/MW;  ρ_gas = PM/(RT)',
            'calc': f'ρ_gas={rho_gas:.3f} kg/m³',
            'result': f'G={G_mol:.4f} mol/s, L={L_mol:.4f} mol/s',
        })

        # ── Step 2: Operating Line & Exit Liquid Concentration ─
        # Mass balance: G(y1−y2) = L(x1−x2)
        x1 = x2 + G_mol * (y1 - y2) / L_mol   # exit liquid (bottom)
        if x1 > 1:
            errors.append('Exit liquid concentration > 1: increase liquid rate.')
            x1 = 0.99
        steps.append({
            'step': 2, 'title': 'Mass Balance / Operating Line',
            'formula': 'G·(y₁−y₂) = L·(x₁−x₂)',
            'result': f'x₁(exit liquid) = {x1:.5f} mol fraction',
        })

        # ── Step 3: Number of Transfer Units (NTU) ───────────
        # For dilute systems: NTU = (y1 - y2) / (y_lm)
        # where y*_avg = H * x_avg
        y_star_top    = H * x2
        y_star_bottom = H * x1
        # Log-mean driving force
        dy_top    = y2 - y_star_top
        dy_bottom = y1 - y_star_bottom

        if dy_top <= 0 or dy_bottom <= 0:
            errors.append('Negative driving force — solvent rate too low or Henry constant mismatch.')
            dy_top    = abs(dy_top) + 0.001
            dy_bottom = abs(dy_bottom) + 0.001

        if abs(dy_top - dy_bottom) < 1e-8:
            dy_lm = dy_top
        else:
            dy_lm = (dy_bottom - dy_top) / math.log(dy_bottom / dy_top)

        NTU = (y1 - y2) / dy_lm
        steps.append({
            'step': 3, 'title': 'Number of Transfer Units (NTU)',
            'formula': 'NTU = (y₁−y₂) / Δy_lm',
            'calc': f'Δy_bottom={dy_bottom:.5f}, Δy_top={dy_top:.5f}, Δy_lm={dy_lm:.5f}',
            'result': f'NTU = {NTU:.3f}',
        })

        # ── Step 4: Height of a Transfer Unit (HTU) ──────────
        # HTU = G_s / (K_ya * A_c) — use empirical K_ya
        # Simplified: HTU = 0.5 + 0.8 * (G/(L+G)) for typical packings
        HTU = 0.5 + 0.8 * (G_mol / (L_mol + G_mol))
        H_column = NTU * HTU
        steps.append({
            'step': 4, 'title': 'Height of Transfer Unit (HTU)',
            'formula': 'HTU_empirical; Z = NTU × HTU',
            'result': f'HTU = {HTU:.3f} m,  Z_packed = {H_column:.2f} m',
        })

        # ── Step 5: Column Diameter ───────────────────────────
        # Generalised Pressure Drop Correlation (GPDC):
        # Flooding velocity from Bain-Hougen/Eckert chart
        # Simplified: u_flood = C_flood / sqrt(rho_gas)
        packing_factors = {
            'Raschig Rings': {'C': 0.055, 'Fp': 300},
            'Pall Rings':    {'C': 0.085, 'Fp': 160},
            'Saddles':       {'C': 0.075, 'Fp': 200},
        }
        pf = packing_factors.get(packing, {'C': 0.075, 'Fp': 200})
        u_flood = pf['C'] * math.sqrt((rho_liq - rho_gas) / rho_gas)
        u_design = 0.70 * u_flood   # operate at 70% flood

        A_col = G_mass / (rho_gas * u_design)
        D_col = math.sqrt(4 * A_col / math.pi)
        steps.append({
            'step': 5, 'title': 'Column Diameter (GPDC)',
            'formula': 'D = √(4·G / (π·ρ·u_design))',
            'calc': f'u_flood={u_flood:.3f} m/s, u_design={u_design:.3f} m/s',
            'result': f'D_column = {D_col:.3f} m',
        })

        # ── Step 6: Column Height (total) ────────────────────
        # Add 1.5 m bottom sump + 1 m top disengagement
        H_total = H_column + 2.5
        steps.append({
            'step': 6, 'title': 'Total Column Height',
            'result': f'H_total = {H_total:.2f} m (packed + internals)',
        })

        # ── Step 7: Pressure Drop ────────────────────────────
        # Typical pressure drop for well-designed packed column: 200–400 Pa/m packing
        dP_per_m = 300  # Pa/m (typical design point)
        dP_total = dP_per_m * H_column
        steps.append({
            'step': 7, 'title': 'Column Pressure Drop',
            'formula': 'ΔP = ΔP/m × H_packed',
            'result': f'ΔP = {dP_total:.0f} Pa = {dP_total/1000:.2f} kPa',
        })

        # ── Step 8: Absorption Efficiency ────────────────────
        removal_efficiency = (y1 - y2) / y1 * 100
        steps.append({
            'step': 8, 'title': 'Solute Removal Efficiency',
            'result': f'η = {removal_efficiency:.2f}%',
        })

        # ── Step 9: Cost Estimation ───────────────────────────
        material_factors = {'Carbon Steel': 1.0, 'Stainless Steel 304': 1.7, 'FRP': 0.9}
        Fm = material_factors.get(material, 1.0)
        base_cost = 8000 * (D_col ** 1.2) * (H_total ** 0.85) * Fm
        installed = base_cost * 4.0
        steps.append({
            'step': 9, 'title': 'Cost Estimation',
            'result': f'Purchased ≈ ${base_cost:,.0f} | Installed ≈ ${installed:,.0f}',
        })

        results = {
            'NTU':                   round(NTU, 3),
            'HTU_m':                 round(HTU, 3),
            'packed_height_m':       round(H_column, 2),
            'total_height_m':        round(H_total, 2),
            'column_diameter_m':     round(D_col, 3),
            'flood_velocity_ms':     round(u_flood, 3),
            'design_velocity_ms':    round(u_design, 3),
            'pressure_drop_Pa':      round(dP_total, 0),
            'removal_efficiency_pct': round(removal_efficiency, 2),
            'exit_liquid_conc':      round(x1, 5),
            'gas_molar_flow_mols':   round(G_mol, 4),
            'liquid_molar_flow_mols': round(L_mol, 4),
            'purchased_cost_USD':    round(base_cost, 0),
            'installed_cost_USD':    round(installed, 0),
            'packing_type':          packing,
            'material': material,
            'safety_notes': [
                'Ensure L/G > minimum wetting rate to prevent dry packing.',
                f'Operating at 70% flood — monitor for flooding during turndown.',
                'Install demister at column top to prevent liquid entrainment.',
                f'Pressure drop {dP_total:.0f} Pa — check blower/fan specifications.',
                'Safety hazard: if absorbing toxic gases, install gas alarm system.',
            ],
            'calculation_steps': steps,
            'errors': errors,
        }
        return results

    except Exception as e:
        return {'errors': [f'Absorber error: {str(e)}'], 'calculation_steps': steps}
