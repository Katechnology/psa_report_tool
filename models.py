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
    
    # Basic Information
    employee_name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False, index=True)
    date_report = db.Column(db.String(20), nullable=True)  # User-typed date
    current_balance = db.Column(db.Float, nullable=False, default=0.0)
    release_date_balance = db.Column(db.String(20), nullable=True)  # Date money transferred
    
    # Account Status (required) - Healthy/Unhealthy
    account_status_us = db.Column(db.String(20), nullable=False, default='Healthy')
    account_status_mexico = db.Column(db.String(20), nullable=False, default='Healthy')
    account_status_canada = db.Column(db.String(20), nullable=False, default='Healthy')
    
    # Store Status (required) - Active/Inactive
    store_status_us = db.Column(db.String(20), nullable=False, default='Active')
    store_status_mexico = db.Column(db.String(20), nullable=False, default='Active')
    store_status_canada = db.Column(db.String(20), nullable=False, default='Active')
    
    # Orders & Reviews
    new_orders = db.Column(db.Integer, nullable=True, default=0)
    vine_total_orders = db.Column(db.Integer, nullable=True, default=0)
    current_inventory = db.Column(db.Integer, nullable=True, default=0)
    average_orders_30_days = db.Column(db.Float, nullable=True, default=0.0)
    total_unit_sales = db.Column(db.Integer, nullable=True, default=0)  # Total units sold
    new_reviews = db.Column(db.Integer, nullable=True, default=0)
    average_rating = db.Column(db.Float, nullable=True, default=0.0)
    
    # Rankings
    main_niche_ranking = db.Column(db.Integer, nullable=True, default=0)
    sub_niche_ranking = db.Column(db.Integer, nullable=True, default=0)
    
    # Advertising
    ads_spend_total = db.Column(db.Float, nullable=True, default=0.0)
    ads_sales_total = db.Column(db.Float, nullable=True, default=0.0)
    ads_sales_today = db.Column(db.Float, nullable=True, default=0.0)  # NEW
    acos = db.Column(db.Float, nullable=True, default=0.0)
    impressions = db.Column(db.Integer, nullable=True, default=0)
    
    # Shopify Attributes (NEW section)
    shopify_click_throughs = db.Column(db.Integer, nullable=True, default=0)
    shopify_total_dpv = db.Column(db.Integer, nullable=True, default=0)
    shopify_total_atc = db.Column(db.Integer, nullable=True, default=0)
    shopify_total_purchases = db.Column(db.Integer, nullable=True, default=0)
    shopify_total_product_sales = db.Column(db.Float, nullable=True, default=0.0)
    
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
            'date_report': self.date_report,
            'current_balance': self.current_balance,
            'release_date_balance': self.release_date_balance,
            'new_orders': self.new_orders,
            'vine_total_orders': self.vine_total_orders,
            'current_inventory': self.current_inventory,
            'average_orders_30_days': self.average_orders_30_days,
            'total_unit_sales': self.total_unit_sales,
            'new_reviews': self.new_reviews,
            'average_rating': self.average_rating,
            'main_niche_ranking': self.main_niche_ranking,
            'sub_niche_ranking': self.sub_niche_ranking,
            'ads_spend_total': self.ads_spend_total,
            'ads_sales_total': self.ads_sales_total,
            'ads_sales_today': self.ads_sales_today,
            'acos': self.acos,
            'impressions': self.impressions,
            'shopify_click_throughs': self.shopify_click_throughs,
            'shopify_total_dpv': self.shopify_total_dpv,
            'shopify_total_atc': self.shopify_total_atc,
            'shopify_total_purchases': self.shopify_total_purchases,
            'shopify_total_product_sales': self.shopify_total_product_sales,
            'account_status_us': self.account_status_us,
            'account_status_mexico': self.account_status_mexico,
            'account_status_canada': self.account_status_canada,
            'store_status_us': self.store_status_us,
            'store_status_mexico': self.store_status_mexico,
            'store_status_canada': self.store_status_canada
        }


class AmazonTransaction(db.Model):
    """Model for Amazon settlement transactions parsed from XML."""
    
    __tablename__ = 'amazon_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)
    
    # Transaction info
    amazon_order_id = db.Column(db.String(50), nullable=True)
    posted_date = db.Column(db.DateTime, nullable=True)
    transaction_type = db.Column(db.String(100), nullable=False)  # Order, OtherTransaction, Advertising
    marketplace = db.Column(db.String(50), nullable=True)
    
    # Item info (for orders)
    sku = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=True, default=0)
    
    # Amounts
    principal_amount = db.Column(db.Float, nullable=True, default=0.0)
    shipping_amount = db.Column(db.Float, nullable=True, default=0.0)
    tax_amount = db.Column(db.Float, nullable=True, default=0.0)
    commission_fee = db.Column(db.Float, nullable=True, default=0.0)
    fba_fee = db.Column(db.Float, nullable=True, default=0.0)
    other_fees = db.Column(db.Float, nullable=True, default=0.0)
    total_amount = db.Column(db.Float, nullable=True, default=0.0)
    
    # Description for non-order transactions
    description = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<AmazonTransaction {self.brand} - {self.transaction_type} - {self.total_amount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M:%S') if self.created_at else None,
            'amazon_order_id': self.amazon_order_id,
            'posted_date': self.posted_date.strftime('%d/%m/%Y %H:%M:%S') if self.posted_date else None,
            'transaction_type': self.transaction_type,
            'marketplace': self.marketplace,
            'sku': self.sku,
            'quantity': self.quantity,
            'principal_amount': self.principal_amount,
            'shipping_amount': self.shipping_amount,
            'tax_amount': self.tax_amount,
            'commission_fee': self.commission_fee,
            'fba_fee': self.fba_fee,
            'other_fees': self.other_fees,
            'total_amount': self.total_amount,
            'description': self.description
        }


class ShipmentCost(db.Model):
    """Model for manual shipment/order cost entries."""
    
    __tablename__ = 'shipment_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)
    
    # Cost details
    cost_date = db.Column(db.Date, nullable=False)
    product = db.Column(db.String(200), nullable=False)
    cost_type = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    
    def __repr__(self):
        return f'<ShipmentCost {self.brand} - {self.product} - {self.total_amount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M:%S') if self.created_at else None,
            'cost_date': self.cost_date.strftime('%d/%m/%Y') if self.cost_date else None,
            'product': self.product,
            'cost_type': self.cost_type,
            'total_amount': self.total_amount
        }
