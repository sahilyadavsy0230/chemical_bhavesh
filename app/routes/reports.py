# ============================================================
# app/routes/reports.py  —  PDF Report Generation Blueprint
# ============================================================

import os
from flask import (Blueprint, send_file, flash, redirect,
                   url_for, current_app)
from flask_login import login_required, current_user

from app.models.equipment import EquipmentDesign
from app.reports.pdf_generator import generate_pdf_report

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/generate/<int:design_id>')
@login_required
def generate(design_id):
    """Generate and stream a PDF report for a given design."""
    design = EquipmentDesign.query.filter_by(
        id=design_id, user_id=current_user.id
    ).first_or_404()

    try:
        # Build report and get file path
        pdf_path = generate_pdf_report(design, current_app)

        # Update design record
        from app import db
        design.report_path      = pdf_path
        design.report_generated = True
        db.session.commit()

        # Stream to browser
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'{design.equipment_type}_report_{design.id}.pdf',
            mimetype='application/pdf',
        )

    except Exception as e:
        flash(f'Report generation failed: {e}', 'danger')
        return redirect(url_for('equipment.result_detail', design_id=design_id))


@reports_bp.route('/view/<int:design_id>')
@login_required
def view(design_id):
    """Stream PDF inline (view in browser)."""
    design = EquipmentDesign.query.filter_by(
        id=design_id, user_id=current_user.id
    ).first_or_404()

    if not design.report_generated or not design.report_path:
        return redirect(url_for('reports.generate', design_id=design_id))

    if not os.path.exists(design.report_path):
        return redirect(url_for('reports.generate', design_id=design_id))

    return send_file(design.report_path, mimetype='application/pdf')
