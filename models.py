from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

def get_bangkok_now():
    """Get current datetime in Bangkok timezone."""
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(bangkok_tz)

class DailyReport(db.Model):
    """Model for daily employee reports."""
    
    __tablename__ = 'daily_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)
    
    # Required fields
    employee_name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False, index=True)
    current_balance = db.Column(db.Float, nullable=False, default=0.0)
    
    # Account Status (required) - Healthy/Unhealthy
    account_status_us = db.Column(db.String(20), nullable=False, default='Healthy')
    account_status_mexico = db.Column(db.String(20), nullable=False, default='Healthy')
    account_status_canada = db.Column(db.String(20), nullable=False, default='Healthy')
    
    # Store Status (required) - Active/Inactive
    store_status_us = db.Column(db.String(20), nullable=False, default='Active')
    store_status_mexico = db.Column(db.String(20), nullable=False, default='Active')
    store_status_canada = db.Column(db.String(20), nullable=False, default='Active')
    
    # Optional fields
    new_orders = db.Column(db.Integer, nullable=True, default=0)
    vine_total_orders = db.Column(db.Integer, nullable=True, default=0)
    new_reviews = db.Column(db.Integer, nullable=True, default=0)
    average_rating = db.Column(db.Float, nullable=True, default=0.0)
    main_niche_ranking = db.Column(db.Integer, nullable=True, default=0)
    sub_niche_ranking = db.Column(db.Integer, nullable=True, default=0)
    ads_spend_total = db.Column(db.Float, nullable=True, default=0.0)
    ads_sales_total = db.Column(db.Float, nullable=True, default=0.0)
    acos = db.Column(db.Float, nullable=True, default=0.0)
    impressions = db.Column(db.Integer, nullable=True, default=0)
    
    # Composite index for brand + report_date queries
    __table_args__ = (
        db.Index('ix_brand_report_date', 'brand', 'report_date'),
    )
    
    def __repr__(self):
        return f'<DailyReport {self.employee_name} - {self.brand} - {self.report_date}>'
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'report_date': self.report_date.strftime('%d/%m/%Y') if self.report_date else None,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M:%S') if self.created_at else None,
            'employee_name': self.employee_name,
            'brand': self.brand,
            'current_balance': self.current_balance,
            'new_orders': self.new_orders,
            'vine_total_orders': self.vine_total_orders,
            'new_reviews': self.new_reviews,
            'average_rating': self.average_rating,
            'main_niche_ranking': self.main_niche_ranking,
            'sub_niche_ranking': self.sub_niche_ranking,
            'ads_spend_total': self.ads_spend_total,
            'ads_sales_total': self.ads_sales_total,
            'acos': self.acos,
            'impressions': self.impressions,
            'account_status_us': self.account_status_us,
            'account_status_mexico': self.account_status_mexico,
            'account_status_canada': self.account_status_canada,
            'store_status_us': self.store_status_us,
            'store_status_mexico': self.store_status_mexico,
            'store_status_canada': self.store_status_canada
        }
