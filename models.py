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
    employee_name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False, index=True)
    new_sales = db.Column(db.Float, nullable=False, default=0.0)
    acos = db.Column(db.Float, nullable=False, default=0.0)
    ads_spend = db.Column(db.Float, nullable=False, default=0.0)
    current_inventory = db.Column(db.Integer, nullable=False, default=0)
    account_status = db.Column(db.String(20), nullable=False, default='Healthy')
    
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
            'new_sales': self.new_sales,
            'acos': self.acos,
            'ads_spend': self.ads_spend,
            'current_inventory': self.current_inventory,
            'account_status': self.account_status
        }
