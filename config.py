import os

class Config:
    """Application configuration settings."""
    
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database
    # Use DATABASE_URL from environment (Render provides this for PostgreSQL)
    # Falls back to SQLite for local development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'daily_reports.db')}")
    
    # Fix for Render's postgres:// vs postgresql:// URL format
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for sessions (use environment variable in production)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'psa-report-tool-secret-key-2026')
    
    # Timezone
    TIMEZONE = 'Asia/Bangkok'
