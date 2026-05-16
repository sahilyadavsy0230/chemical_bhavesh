# ============================================================
# run.py - Application Entry Point
# AI-Based Chemical Process Equipment Design Platform
# ============================================================

import os
from app import create_app, db

# Select configuration based on FLASK_ENV environment variable
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)


@app.shell_context_processor
def make_shell_context():
    """
    Expose db and models to flask shell for quick debugging.
    Usage: flask shell  → then type 'db', 'User', etc.
    """
    from app.models.user        import User
    from app.models.project     import Project
    from app.models.equipment   import EquipmentDesign
    from app.models.chat        import ChatHistory

    return {
        'db':              db,
        'User':            User,
        'Project':         Project,
        'EquipmentDesign': EquipmentDesign,
        'ChatHistory':     ChatHistory,
    }


@app.cli.command('init-db')
def init_db():
    """Create all database tables (run once after setup)."""
    with app.app_context():
        db.create_all()
        print('✅  Database tables created successfully.')


@app.cli.command('seed-db')
def seed_db():
    """Insert sample / demo data into the database."""
    from app.utils.seed_data import seed_database
    with app.app_context():
        seed_database()
        print('✅  Sample data seeded successfully.')


if __name__ == '__main__':
    port = int(os.environ.get('APP_PORT', 5000))
    host = os.environ.get('APP_HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=(config_name == 'development'))
