# ============================================================
# config.py - Application Configuration
# AI-Based Chemical Process Equipment Design Platform
# ============================================================

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with common settings."""

    # ─── Flask Core ───────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # ─── Database ─────────────────────────────────────────────
    # Check for a single DATABASE_URL (common in Heroku/Render/Railway/Supabase)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI:
        # Fix for Render/Heroku: postgres:// must be postgresql://
        if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
        # Fix for Railway/Generic: mysql:// must be mysql+pymysql://
        if SQLALCHEMY_DATABASE_URI.startswith('mysql://'):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('mysql://', 'mysql+pymysql://', 1)
    else:
        # Fallback to individual components
        DB_HOST     = os.environ.get('DB_HOST', 'localhost')
        DB_PORT     = os.environ.get('DB_PORT', '3306')
        DB_NAME     = os.environ.get('DB_NAME', 'chem_design_db')
        DB_USER     = os.environ.get('DB_USER', 'root')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Sahil123')
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True to log all SQL queries (debug)

    # ─── JWT ─────────────────────────────────────────────────
    JWT_SECRET_KEY        = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ─── Groq AI ─────────────────────────────────────────────
    GROQ_API_KEY    = os.environ.get('GROQ_API_KEY', '')
    GROQ_MODEL      = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
    GROQ_MAX_TOKENS = 4096
    GROQ_TEMPERATURE = 0.3  # Lower = more deterministic engineering answers

    # ─── File Upload ─────────────────────────────────────────
    UPLOAD_FOLDER    = os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads')
    REPORTS_FOLDER   = os.path.join(os.path.dirname(__file__), 'app', 'static', 'reports')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # ─── Session ─────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE    = False  # Set True in production (HTTPS)
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = 'Lax'

    # ─── Rate Limiting ───────────────────────────────────────
    RATELIMIT_DEFAULT          = '200 per day, 50 per hour'
    RATELIMIT_STORAGE_URL      = 'memory://'
    RATELIMIT_STRATEGY         = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED  = True

    # ─── Pagination ──────────────────────────────────────────
    ITEMS_PER_PAGE = 10

    # ─── App Info ────────────────────────────────────────────
    APP_NAME    = 'ChemDesignAI'
    APP_VERSION = '1.0.0'

    @staticmethod
    def init_app(app):
        """Hook for app-specific initialization (override in subclasses)."""
        # Ensure upload/report dirs exist at startup
        os.makedirs(Config.UPLOAD_FOLDER,  exist_ok=True)
        os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG         = True
    SQLALCHEMY_ECHO = False  # Flip True to debug queries during dev


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING              = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED     = False


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG                     = False
    SESSION_COOKIE_SECURE     = True
    SQLALCHEMY_ECHO           = False
    RATELIMIT_DEFAULT         = '100 per day, 20 per hour'


# ─── Configuration Selector ──────────────────────────────────
config = {
    'development': DevelopmentConfig,
    'testing':     TestingConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}

