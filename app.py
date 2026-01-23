from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
from datetime import datetime
from functools import wraps
import pandas as pd
import plotly.express as px
import plotly.utils
import json
import pytz
import os
import xml.etree.ElementTree as ET

from config import Config
from models import db, DailyReport, AmazonTransaction, ShipmentCost, get_bangkok_now

# Brand list for dropdowns (removed FEMBURN)
BRANDS = [
    'ENERZAA', 'LUVOST', 'PEAKSHILAJIT', 'BOXOOS', 'CYLEOX', 'ROBURSTAGE',
    'CHICADDONS', 'ORANIC EXTRACT', 'ZOVOST', 'VITALIXHAIR', 'SYLIARIX'
]

# Employee → Brand mapping
EMPLOYEE_BRAND_MAP = {
    'Mai Phương': 'ENERZAA',
    'Việt Khanh': 'LUVOST',
    'Quỳnh Anh': 'PEAKSHILAJIT',
    'Nhi (Boxoos)': 'BOXOOS',
    'Thảo (Cyleox)': 'CYLEOX',
    'Hoàng Thư': 'ROBURSTAGE',
    'Diệu Anh': 'CHICADDONS',
    'Uyên Vi': 'ORANIC EXTRACT',
    'Phạm Thảo': 'ZOVOST',
    'Lan Anh': 'VITALIXHAIR',
    'Thảo Tiên': 'SYLIARIX'
}

# Brand → Products mapping
BRAND_PRODUCTS_MAP = {
    'ENERZAA': ['Creatine Complex Gummies Blue Razz', 'Creatine Complex Gummies Sour Watermelon'],
    'VITALIXHAIR': ['Vitalix Hair Oil (yellow)', 'Vitalix Hair Growth (pink)'],
    'SYLIARIX': ['Brain Booster'],
    'CHICADDONS': ['ChicAddOns Mullein'],
    'CYLEOX': ['Night time fat burner', 'Balance Gummies'],
    'ORANIC EXTRACT': ['Pure Shilajit Gummies', '3 in 1 Wellness Gummies'],
    'LUVOST': ['Luvost Liquid Drops', 'Luvost Sea Moss'],
    'BOXOOS': ['Estrogen Control'],
    'ROBURSTAGE': ['Pure NMN'],
    'PEAKSHILAJIT': ['SHILAJIT GUMMY PLATINUM'],
    'ZOVOST': ['Super Blend']
}

# All products list for charts
ALL_PRODUCTS = [p for products in BRAND_PRODUCTS_MAP.values() for p in products]

app = Flask(__name__)
app.config.from_object(Config)

# Manager password (use environment variable or default)
MANAGER_PASSWORD = os.environ.get('MANAGER_PASSWORD', 'psa2026')

# Initialize database
db.init_app(app)

# Create tables on first request
with app.app_context():
    db.create_all()


# =============================================================================
# LOGIN REQUIRED DECORATOR
# =============================================================================

def login_required(f):
    """Decorator to require manager login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('manager_logged_in'):
            flash('Please login to access the manager section.', 'error')
            return redirect(url_for('manager_login'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# LANDING PAGE
# =============================================================================

@app.route('/')
def index():
    """Landing page with Employee/Manager selection."""
    return render_template('index.html')


# =============================================================================
# EMPLOYEE ROUTES
# =============================================================================

@app.route('/employee', methods=['GET', 'POST'])
def employee():
    """Employee report submission form."""
    if request.method == 'POST':
        try:
            # Get Bangkok time
            bangkok_now = get_bangkok_now()
            
            # Get employee name and lookup brand
            employee_name = request.form.get('employee_name', '').strip()
            brand = EMPLOYEE_BRAND_MAP.get(employee_name, request.form.get('brand', '').strip())
            product = request.form.get('product', '').strip()
            
            # Create new report with all fields
            report = DailyReport(
                report_date=bangkok_now.date(),
                created_at=bangkok_now.replace(tzinfo=None),  # Store without timezone
                
                # Basic Information
                employee_name=employee_name,
                brand=brand,
                product=product,
                date_report=request.form.get('date_report', '').strip(),
                current_balance=float(request.form.get('current_balance', 0) or 0),
                release_date_balance=request.form.get('release_date_balance', '').strip(),
                
                # Account Status (required)
                account_status_us=request.form.get('account_status_us', 'Healthy'),
                account_status_mexico=request.form.get('account_status_mexico', 'Healthy'),
                account_status_canada=request.form.get('account_status_canada', 'Healthy'),
                
                # Store Status (required)
                store_status_us=request.form.get('store_status_us', 'Active'),
                store_status_mexico=request.form.get('store_status_mexico', 'Active'),
                store_status_canada=request.form.get('store_status_canada', 'Active'),
                
                # Orders & Reviews
                new_orders=int(request.form.get('new_orders', 0) or 0),
                vine_total_orders=int(request.form.get('vine_total_orders', 0) or 0),
                current_inventory=int(request.form.get('current_inventory', 0) or 0),
                average_orders_30_days=float(request.form.get('average_orders_30_days', 0) or 0),
                total_unit_sales=int(request.form.get('total_unit_sales', 0) or 0),
                new_reviews=int(request.form.get('new_reviews', 0) or 0),
                average_rating=float(request.form.get('average_rating', 0) or 0),
                
                # Rankings
                main_niche_ranking=int(request.form.get('main_niche_ranking', 0) or 0),
                sub_niche_ranking=int(request.form.get('sub_niche_ranking', 0) or 0),
                
                # Advertising
                ads_spend_total=float(request.form.get('ads_spend_total', 0) or 0),
                ads_sales_total=float(request.form.get('ads_sales_total', 0) or 0),
                ads_sales_today=float(request.form.get('ads_sales_today', 0) or 0),
                acos=float(request.form.get('acos', 0) or 0),
                impressions=int(request.form.get('impressions', 0) or 0),
                
                # Shopify Attributes
                shopify_click_throughs=int(request.form.get('shopify_click_throughs', 0) or 0),
                shopify_total_dpv=int(request.form.get('shopify_total_dpv', 0) or 0),
                shopify_total_atc=int(request.form.get('shopify_total_atc', 0) or 0),
                shopify_total_purchases=int(request.form.get('shopify_total_purchases', 0) or 0),
                shopify_total_product_sales=float(request.form.get('shopify_total_product_sales', 0) or 0)
            )
            
            # Validate required fields
            if not report.employee_name:
                flash('Employee name is required.', 'error')
                return render_template('employee.html')
            
            if not report.brand:
                flash('Brand is required.', 'error')
                return render_template('employee.html')
            
            # Save to database
            db.session.add(report)
            db.session.commit()
            
            flash('Report submitted successfully!', 'success')
            return render_template('employee.html', success=True)
            
        except ValueError as e:
            flash(f'Invalid input: Please check your numeric values.', 'error')
            return render_template('employee.html')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving report: {str(e)}', 'error')
            return render_template('employee.html')
    
    return render_template('employee.html')


# =============================================================================
# MANAGER ROUTES
# =============================================================================

@app.route('/manager/login', methods=['GET', 'POST'])
def manager_login():
    """Manager login page."""
    if session.get('manager_logged_in'):
        return redirect(url_for('manager'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == MANAGER_PASSWORD:
            session['manager_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('manager'))
        else:
            flash('Incorrect password. Please try again.', 'error')
    
    return render_template('manager_login.html')


@app.route('/manager/logout')
def manager_logout():
    """Manager logout."""
    session.pop('manager_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/manager')
@login_required
def manager():
    """Manager menu page."""
    return render_template('manager.html')


@app.route('/manager/daily', methods=['GET', 'POST'])
@login_required
def manager_daily():
    """Manager daily report view."""
    reports = []
    selected_date = None
    charts_json = None
    
    if request.method == 'POST':
        date_str = request.form.get('report_date', '').strip()
        
        if date_str:
            try:
                # Parse date from HTML5 date picker (YYYY-MM-DD format)
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Query reports for selected date (using date_report field entered by user)
                reports = DailyReport.query.filter_by(date_report=date_str)\
                    .order_by(DailyReport.created_at.desc()).all()
                
                if reports:
                    # Generate charts
                    charts_json = generate_daily_charts(reports)
                else:
                    flash(f'No records found for {selected_date.strftime("%d/%m/%Y")}', 'info')
                    
            except ValueError:
                flash('Invalid date format.', 'error')
    
    return render_template('daily_report.html', 
                         reports=reports, 
                         selected_date=selected_date,
                         charts_json=charts_json)


@app.route('/manager/overall')
@login_required
def manager_overall():
    """Manager overall report view with brand buttons."""
    # Get all unique brands
    brands = db.session.query(DailyReport.brand)\
        .distinct()\
        .order_by(DailyReport.brand)\
        .all()
    brands = [b[0] for b in brands if b[0]]
    
    return render_template('overall_report.html', brands=brands)


@app.route('/manager/overall/<brand>')
@login_required
def manager_overall_brand(brand):
    """Manager overall report for a specific brand."""
    # Get all unique brands for navigation
    brands = db.session.query(DailyReport.brand)\
        .distinct()\
        .order_by(DailyReport.brand)\
        .all()
    brands = [b[0] for b in brands if b[0]]
    
    # Get reports for selected brand
    reports = DailyReport.query.filter_by(brand=brand)\
        .order_by(DailyReport.date_report, DailyReport.created_at)\
        .all()
    
    charts_json = None
    if reports:
        charts_json = generate_brand_charts(reports, brand)
    
    return render_template('overall_report.html', 
                         brands=brands, 
                         selected_brand=brand,
                         charts_json=charts_json)


@app.route('/manager/fulfilment')
@login_required
def manager_fulfilment():
    """Manager fulfilment view - categorizes products by inventory status."""
    # Get all unique products
    products = db.session.query(DailyReport.product).distinct().all()
    products = [p[0] for p in products if p[0]]
    
    safe_products = []
    urgent_products = []
    
    for product_name in products:
        # Get the latest report for this product
        latest_report = DailyReport.query.filter_by(product=product_name)\
            .order_by(DailyReport.created_at.desc())\
            .first()
        
        if latest_report:
            inventory = latest_report.current_inventory or 0
            avg_orders = latest_report.average_orders_30_days or 0
            
            # Calculate days of stock (flag index)
            if avg_orders > 0:
                days_of_stock = inventory / avg_orders
            else:
                days_of_stock = float('inf') if inventory > 0 else 0
            
            product_data = {
                'name': product_name,
                'brand': latest_report.brand,
                'inventory': inventory,
                'avg_orders': avg_orders,
                'days_of_stock': days_of_stock if days_of_stock != float('inf') else 999
            }
            
            # Categorize: <= 60 days = Urgent, > 60 days = Safe
            if days_of_stock <= 60:
                urgent_products.append(product_data)
            else:
                safe_products.append(product_data)
    
    # Sort urgent by days_of_stock (lowest first - most urgent)
    urgent_products.sort(key=lambda x: x['days_of_stock'])
    # Sort safe by days_of_stock (lowest first)
    safe_products.sort(key=lambda x: x['days_of_stock'])
    
    return render_template('fulfilment.html',
                         safe_products=safe_products,
                         urgent_products=urgent_products)


# =============================================================================
# REVENUE & COST ROUTES
# =============================================================================

@app.route('/manager/revenue-cost')
@login_required
def manager_revenue_cost():
    """Revenue & Cost main menu."""
    return render_template('revenue_cost.html')


@app.route('/manager/amazon')
@login_required
def amazon_transactions_select():
    """Select brand for Amazon transactions."""
    return render_template('amazon_select.html', brands=BRANDS)


@app.route('/manager/amazon/<brand>')
@login_required
def amazon_transactions(brand):
    """View Amazon transactions for a brand."""
    transactions = AmazonTransaction.query.filter_by(brand=brand)\
        .order_by(AmazonTransaction.posted_date.desc())\
        .limit(5).all()
    return render_template('amazon_transactions.html', brand=brand, transactions=transactions)


@app.route('/manager/amazon/<brand>/upload', methods=['POST'])
@login_required
def amazon_upload(brand):
    """Upload and parse Amazon XML file."""
    if 'xml_file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('amazon_transactions', brand=brand))
    
    file = request.files['xml_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('amazon_transactions', brand=brand))
    
    if not file.filename.endswith('.xml'):
        flash('Please upload an XML file.', 'error')
        return redirect(url_for('amazon_transactions', brand=brand))
    
    try:
        # Parse XML
        tree = ET.parse(file)
        root = tree.getroot()
        
        bangkok_now = get_bangkok_now().replace(tzinfo=None)
        transactions_added = 0
        
        # Find SettlementReport
        for settlement in root.iter('SettlementReport'):
            # Parse Orders
            for order in settlement.findall('.//Order'):
                order_id = order.findtext('AmazonOrderID', '')
                marketplace = order.findtext('MarketplaceName', '')
                
                for fulfillment in order.findall('.//Fulfillment'):
                    posted_date_str = fulfillment.findtext('PostedDate', '')
                    posted_date = None
                    if posted_date_str:
                        try:
                            posted_date = datetime.fromisoformat(posted_date_str.replace('+00:00', ''))
                        except:
                            pass
                    
                    for item in fulfillment.findall('.//Item'):
                        sku = item.findtext('SKU', '')
                        quantity = int(item.findtext('Quantity', '0') or 0)
                        
                        # Parse prices
                        principal = shipping = tax = 0.0
                        for component in item.findall('.//ItemPrice/Component'):
                            comp_type = component.findtext('Type', '')
                            amount = float(component.findtext('Amount', '0') or 0)
                            if comp_type == 'Principal':
                                principal = amount
                            elif comp_type == 'Shipping':
                                shipping = amount
                            elif 'Tax' in comp_type and 'Facilitator' not in comp_type:
                                tax = amount
                        
                        # Parse fees
                        fba_fee = commission = other_fees = 0.0
                        for fee in item.findall('.//ItemFees/Fee'):
                            fee_type = fee.findtext('Type', '')
                            amount = float(fee.findtext('Amount', '0') or 0)
                            if 'FBA' in fee_type:
                                fba_fee += amount
                            elif 'Commission' in fee_type:
                                commission += amount
                            else:
                                other_fees += amount
                        
                        total = principal + shipping + tax + fba_fee + commission + other_fees
                        
                        trans = AmazonTransaction(
                            brand=brand,
                            created_at=bangkok_now,
                            amazon_order_id=order_id,
                            posted_date=posted_date,
                            transaction_type='Order',
                            marketplace=marketplace,
                            sku=sku,
                            quantity=quantity,
                            principal_amount=principal,
                            shipping_amount=shipping,
                            tax_amount=tax,
                            fba_fee=fba_fee,
                            commission_fee=commission,
                            other_fees=other_fees,
                            total_amount=total
                        )
                        db.session.add(trans)
                        transactions_added += 1
            
            # Parse OtherTransaction
            for other_trans in settlement.findall('.//OtherTransaction'):
                trans_type = other_trans.findtext('TransactionType', '')
                amount = float(other_trans.findtext('Amount', '0') or 0)
                posted_date_str = other_trans.findtext('PostedDate', '')
                posted_date = None
                if posted_date_str:
                    try:
                        posted_date = datetime.fromisoformat(posted_date_str.replace('+00:00', ''))
                    except:
                        pass
                
                trans = AmazonTransaction(
                    brand=brand,
                    created_at=bangkok_now,
                    amazon_order_id=other_trans.findtext('AmazonOrderID', ''),
                    posted_date=posted_date,
                    transaction_type='OtherTransaction',
                    description=trans_type,
                    total_amount=amount
                )
                db.session.add(trans)
                transactions_added += 1
            
            # Parse AdvertisingTransactionDetails
            for ad_trans in settlement.findall('.//AdvertisingTransactionDetails'):
                trans_type = ad_trans.findtext('TransactionType', '')
                amount = float(ad_trans.findtext('TransactionAmount', '0') or 0)
                posted_date_str = ad_trans.findtext('PostedDate', '')
                posted_date = None
                if posted_date_str:
                    try:
                        posted_date = datetime.fromisoformat(posted_date_str.replace('+00:00', ''))
                    except:
                        pass
                
                trans = AmazonTransaction(
                    brand=brand,
                    created_at=bangkok_now,
                    posted_date=posted_date,
                    transaction_type='Advertising',
                    description=trans_type,
                    total_amount=amount
                )
                db.session.add(trans)
                transactions_added += 1
        
        db.session.commit()
        flash(f'Successfully imported {transactions_added} transactions.', 'success')
    except Exception as e:
        flash(f'Error parsing XML: {str(e)}', 'error')
    
    return redirect(url_for('amazon_transactions', brand=brand))


@app.route('/manager/amazon/<brand>/download')
@login_required
def amazon_download(brand):
    """Download Amazon transactions as CSV."""
    transactions = AmazonTransaction.query.filter_by(brand=brand)\
        .order_by(AmazonTransaction.posted_date.desc()).all()
    
    if not transactions:
        flash('No data to export.', 'info')
        return redirect(url_for('amazon_transactions', brand=brand))
    
    data = [t.to_dict() for t in transactions]
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False)
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={brand}_amazon_transactions.csv'}
    )


@app.route('/manager/shipment')
@login_required
def shipment_cost_select():
    """Select brand for shipment costs."""
    return render_template('shipment_select.html', brands=BRANDS)


@app.route('/manager/shipment/<brand>')
@login_required
def shipment_cost(brand):
    """View shipment costs for a brand."""
    costs = ShipmentCost.query.filter_by(brand=brand)\
        .order_by(ShipmentCost.cost_date.desc()).all()
    return render_template('shipment_cost.html', brand=brand, costs=costs)


@app.route('/manager/shipment/<brand>/submit', methods=['POST'])
@login_required
def shipment_submit(brand):
    """Submit new shipment cost."""
    try:
        cost_date_str = request.form.get('cost_date', '')
        cost_date = datetime.strptime(cost_date_str, '%Y-%m-%d').date() if cost_date_str else None
        
        cost = ShipmentCost(
            brand=brand,
            created_at=get_bangkok_now().replace(tzinfo=None),
            cost_date=cost_date,
            product=request.form.get('product', '').strip(),
            cost_type=request.form.get('cost_type', ''),
            total_amount=float(request.form.get('total_amount', 0) or 0)
        )
        
        db.session.add(cost)
        db.session.commit()
        flash('Cost saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving cost: {str(e)}', 'error')
    
    return redirect(url_for('shipment_cost', brand=brand))


@app.route('/manager/shipment/<brand>/download')
@login_required
def shipment_download(brand):
    """Download shipment costs as CSV."""
    costs = ShipmentCost.query.filter_by(brand=brand)\
        .order_by(ShipmentCost.cost_date.desc()).all()
    
    if not costs:
        flash('No data to export.', 'info')
        return redirect(url_for('shipment_cost', brand=brand))
    
    data = [c.to_dict() for c in costs]
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False)
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={brand}_shipment_costs.csv'}
    )


@app.route('/manager/export/csv')
@login_required
def export_csv():
    """Export all data as CSV."""
    # Query all reports sorted by date_report (user-entered date)
    reports = DailyReport.query.order_by(
        DailyReport.date_report, 
        DailyReport.created_at
    ).all()
    
    if not reports:
        flash('No data to export.', 'info')
        return redirect(url_for('manager_overall'))
    
    # Convert to DataFrame with all fields
    data = []
    for r in reports:
        data.append({
            'report_date': r.report_date.strftime('%d/%m/%Y'),
            'created_at': r.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'employee_name': r.employee_name,
            'brand': r.brand,
            'product': r.product,
            'date_report': r.date_report,
            'current_balance': r.current_balance,
            'release_date_balance': r.release_date_balance,
            'new_orders': r.new_orders,
            'vine_total_orders': r.vine_total_orders,
            'current_inventory': r.current_inventory,
            'average_orders_30_days': r.average_orders_30_days,
            'total_unit_sales': r.total_unit_sales,
            'new_reviews': r.new_reviews,
            'average_rating': r.average_rating,
            'main_niche_ranking': r.main_niche_ranking,
            'sub_niche_ranking': r.sub_niche_ranking,
            'ads_spend_total': r.ads_spend_total,
            'ads_sales_total': r.ads_sales_total,
            'ads_sales_today': r.ads_sales_today,
            'acos': r.acos,
            'impressions': r.impressions,
            'shopify_click_throughs': r.shopify_click_throughs,
            'shopify_total_dpv': r.shopify_total_dpv,
            'shopify_total_atc': r.shopify_total_atc,
            'shopify_total_purchases': r.shopify_total_purchases,
            'shopify_total_product_sales': r.shopify_total_product_sales,
            'account_status_us': r.account_status_us,
            'account_status_mexico': r.account_status_mexico,
            'account_status_canada': r.account_status_canada,
            'store_status_us': r.store_status_us,
            'store_status_mexico': r.store_status_mexico,
            'store_status_canada': r.store_status_canada
        })
    
    df = pd.DataFrame(data)
    
    # Generate CSV with UTF-8 BOM encoding for Vietnamese characters
    csv_data = '\ufeff' + df.to_csv(index=False, encoding='utf-8-sig')
    
    # Return as downloadable file
    return Response(
        csv_data.encode('utf-8-sig'),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=daily_reports_export.csv'}
    )


# =============================================================================
# CHART GENERATION FUNCTIONS
# =============================================================================

def generate_daily_charts(reports):
    """Generate bar charts for daily report aggregated by brand."""
    # Convert reports to DataFrame
    data = [r.to_dict() for r in reports]
    df = pd.DataFrame(data)
    
    # Aggregate by brand (Balance, ACOS, Ads Spend are brand-level)
    agg_df = df.groupby('brand').agg({
        'current_balance': 'first',  # Same for all products in brand
        'new_orders': 'sum',
        'ads_spend_total': 'first',  # Same for all products in brand
        'ads_sales_today': 'sum',
        'acos': 'first'  # Same for all products in brand
    }).reset_index()
    
    charts = {}
    
    # Color scheme
    colors = px.colors.qualitative.Set2
    
    # Current Balance by Brand
    fig1 = px.bar(agg_df, x='brand', y='current_balance', 
                  title='Current Balance by Brand ($)',
                  color='brand', color_discrete_sequence=colors)
    fig1.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        showlegend=False
    )
    charts['balance'] = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    
    # New Orders by Brand (sum of all products)
    fig2 = px.bar(agg_df, x='brand', y='new_orders', 
                  title='New Orders by Brand',
                  color='brand', color_discrete_sequence=colors)
    fig2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        showlegend=False
    )
    charts['orders'] = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Ads Spend by Brand
    fig3 = px.bar(agg_df, x='brand', y='ads_spend_total', 
                  title='Ads Spend Total by Brand ($)',
                  color='brand', color_discrete_sequence=colors)
    fig3.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        showlegend=False
    )
    charts['ads_spend'] = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Ads Sales Today by Brand (sum of all products)
    fig4 = px.bar(agg_df, x='brand', y='ads_sales_today', 
                  title='Ads Sales Today by Brand ($)',
                  color='brand', color_discrete_sequence=colors)
    fig4.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        showlegend=False
    )
    charts['ads_sales_today'] = json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)
    
    # ACOS by Brand
    fig5 = px.bar(agg_df, x='brand', y='acos', 
                  title='Average ACOS by Brand (%)',
                  color='brand', color_discrete_sequence=colors)
    fig5.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        showlegend=False
    )
    charts['acos'] = json.dumps(fig5, cls=plotly.utils.PlotlyJSONEncoder)
    
    return charts


def generate_brand_charts(reports, brand):
    """Generate line charts for brand trends over time."""
    # Convert reports to DataFrame
    data = [r.to_dict() for r in reports]
    df = pd.DataFrame(data)
    
    # Convert date_report to datetime for proper sorting (date_report is YYYY-MM-DD from HTML5 date picker)
    df['date'] = pd.to_datetime(df['date_report'], format='%Y-%m-%d', errors='coerce')
    
    # Aggregate by date (in case multiple entries per day)
    # Balance, Ads Spend, ACOS are brand-level (use 'first'), Orders are summed
    agg_df = df.groupby('date').agg({
        'current_balance': 'first',  # Brand-level value
        'new_orders': 'sum',
        'ads_spend_total': 'first',  # Brand-level value
        'acos': 'first'  # Brand-level value
    }).reset_index()
    
    agg_df = agg_df.sort_values('date')
    agg_df['date_str'] = agg_df['date'].dt.strftime('%d/%m/%Y')
    
    charts = {}
    
    # Line chart styling
    line_color = '#00d4ff'
    
    # Current Balance over time
    fig1 = px.line(agg_df, x='date_str', y='current_balance', 
                   title=f'{brand} - Balance Over Time ($)',
                   markers=True)
    fig1.update_traces(line_color=line_color, marker_color=line_color)
    fig1.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        xaxis_title='Date',
        yaxis_title='Balance ($)'
    )
    charts['balance'] = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    
    # New Orders over time
    fig2 = px.line(agg_df, x='date_str', y='new_orders', 
                   title=f'{brand} - Orders Over Time',
                   markers=True)
    fig2.update_traces(line_color='#6bcb77', marker_color='#6bcb77')
    fig2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        xaxis_title='Date',
        yaxis_title='Orders'
    )
    charts['orders'] = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Ads Spend over time
    fig3 = px.line(agg_df, x='date_str', y='ads_spend_total', 
                   title=f'{brand} - Ads Spend Over Time ($)',
                   markers=True)
    fig3.update_traces(line_color='#ffd93d', marker_color='#ffd93d')
    fig3.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        xaxis_title='Date',
        yaxis_title='Ads Spend ($)'
    )
    charts['ads_spend'] = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    
    # ACOS over time
    fig4 = px.line(agg_df, x='date_str', y='acos', 
                   title=f'{brand} - ACOS Over Time (%)',
                   markers=True)
    fig4.update_traces(line_color='#ff6b6b', marker_color='#ff6b6b')
    fig4.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        xaxis_title='Date',
        yaxis_title='ACOS (%)'
    )
    charts['acos'] = json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Main Niche Ranking - prepare table data
    if 'product' in df.columns and df['product'].nunique() > 1:
        # Multiple products - show table with product breakdown
        ranking_df = df[['date', 'product', 'main_niche_ranking', 'sub_niche_ranking']].copy()
        ranking_df = ranking_df.sort_values(['date', 'product'], ascending=[False, True])
        ranking_df['date_str'] = ranking_df['date'].dt.strftime('%d/%m/%Y')
        
        # Create table figure
        fig5 = px.scatter(ranking_df, x='date_str', y='main_niche_ranking',
                         color='product',
                         title=f'{brand} - Main Niche Ranking Over Time (by Product)',
                         size_max=15)
        fig5.update_traces(mode='lines+markers', marker=dict(size=10))
        fig5.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            xaxis_title='Date',
            yaxis_title='Ranking',
            yaxis={'autorange': 'reversed'},
            height=500
        )
    else:
        # Single product - show simple line chart
        ranking_agg = df.groupby('date').agg({
            'main_niche_ranking': 'first'
        }).reset_index()
        ranking_agg = ranking_agg.sort_values('date')
        ranking_agg['date_str'] = ranking_agg['date'].dt.strftime('%d/%m/%Y')
        
        fig5 = px.scatter(ranking_agg, x='date_str', y='main_niche_ranking',
                         title=f'{brand} - Main Niche Ranking Over Time',
                         size_max=15)
        fig5.update_traces(mode='lines+markers', marker=dict(size=10, color='#9b59b6'),
                          line=dict(color='#9b59b6'))
        fig5.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            xaxis_title='Date',
            yaxis_title='Ranking',
            yaxis={'autorange': 'reversed'},
            height=500
        )
    charts['main_ranking'] = json.dumps(fig5, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Sub Niche Ranking
    if 'product' in df.columns and df['product'].nunique() > 1:
        # Multiple products
        sub_ranking_df = df[['date', 'product', 'sub_niche_ranking']].copy()
        sub_ranking_df = sub_ranking_df.sort_values(['date', 'product'], ascending=[False, True])
        sub_ranking_df['date_str'] = sub_ranking_df['date'].dt.strftime('%d/%m/%Y')
        
        fig6 = px.scatter(sub_ranking_df, x='date_str', y='sub_niche_ranking',
                         color='product',
                         title=f'{brand} - Sub Niche Ranking Over Time (by Product)',
                         size_max=15)
        fig6.update_traces(mode='lines+markers', marker=dict(size=10))
        fig6.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            xaxis_title='Date',
            yaxis_title='Ranking',
            yaxis={'autorange': 'reversed'},
            height=500
        )
    else:
        # Single product
        sub_ranking_agg = df.groupby('date').agg({
            'sub_niche_ranking': 'first'
        }).reset_index()
        sub_ranking_agg = sub_ranking_agg.sort_values('date')
        sub_ranking_agg['date_str'] = sub_ranking_agg['date'].dt.strftime('%d/%m/%Y')
        
        fig6 = px.scatter(sub_ranking_agg, x='date_str', y='sub_niche_ranking',
                         title=f'{brand} - Sub Niche Ranking Over Time',
                         size_max=15)
        fig6.update_traces(mode='lines+markers', marker=dict(size=10, color='#e67e22'),
                          line=dict(color='#e67e22'))
        fig6.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            xaxis_title='Date',
            yaxis_title='Ranking',
            yaxis={'autorange': 'reversed'},
            height=500
        )
    charts['sub_ranking'] = json.dumps(fig6, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Impressions over time (by product if multiple)
    if 'product' in df.columns and df['product'].nunique() > 1:
        # Multiple products
        impressions_df = df[['date', 'product', 'impressions']].copy()
        impressions_df = impressions_df.sort_values(['date', 'product'], ascending=[False, True])
        impressions_df['date_str'] = impressions_df['date'].dt.strftime('%d/%m/%Y')
        
        fig7 = px.scatter(impressions_df, x='date_str', y='impressions',
                         color='product',
                         title=f'{brand} - Impressions Over Time (by Product)',
                         size_max=15)
        fig7.update_traces(mode='lines+markers', marker=dict(size=10))
        fig7.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            xaxis_title='Date',
            yaxis_title='Impressions',
            height=500
        )
    else:
        # Single product
        impressions_agg = df.groupby('date').agg({
            'impressions': 'sum'
        }).reset_index()
        impressions_agg = impressions_agg.sort_values('date')
        impressions_agg['date_str'] = impressions_agg['date'].dt.strftime('%d/%m/%Y')
        
        fig7 = px.scatter(impressions_agg, x='date_str', y='impressions',
                         title=f'{brand} - Impressions Over Time',
                         size_max=15)
        fig7.update_traces(mode='lines+markers', marker=dict(size=10, color='#3498db'),
                          line=dict(color='#3498db'))
        fig7.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            xaxis_title='Date',
            yaxis_title='Impressions',
            height=500
        )
    charts['impressions'] = json.dumps(fig7, cls=plotly.utils.PlotlyJSONEncoder)
    
    return charts


# =============================================================================
# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

