from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
from datetime import datetime
from functools import wraps
import pandas as pd
import plotly.express as px
import plotly.utils
import json
import pytz
import os

from config import Config
from models import db, DailyReport, get_bangkok_now

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
            
            # Create new report with all fields
            report = DailyReport(
                report_date=bangkok_now.date(),
                created_at=bangkok_now.replace(tzinfo=None),  # Store without timezone
                
                # Basic Information
                employee_name=request.form.get('employee_name', '').strip(),
                brand=request.form.get('brand', '').strip(),
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
                
                # Query reports for selected date
                reports = DailyReport.query.filter_by(report_date=selected_date)\
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
    brands = [b[0] for b in brands]
    
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
    brands = [b[0] for b in brands]
    
    # Get reports for selected brand
    reports = DailyReport.query.filter_by(brand=brand)\
        .order_by(DailyReport.report_date, DailyReport.created_at)\
        .all()
    
    charts_json = None
    if reports:
        charts_json = generate_brand_charts(reports, brand)
    
    return render_template('overall_report.html', 
                         brands=brands, 
                         selected_brand=brand,
                         charts_json=charts_json)


@app.route('/manager/export/csv')
@login_required
def export_csv():
    """Export all data as CSV."""
    # Query all reports
    reports = DailyReport.query.order_by(
        DailyReport.report_date, 
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
    
    # Generate CSV
    csv_data = df.to_csv(index=False)
    
    # Return as downloadable file
    return Response(
        csv_data,
        mimetype='text/csv',
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
    
    # Aggregate by brand
    agg_df = df.groupby('brand').agg({
        'current_balance': 'sum',
        'new_orders': 'sum',
        'ads_spend_total': 'sum',
        'ads_sales_today': 'sum',
        'acos': 'mean'
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
    
    # New Orders by Brand
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
    
    # Ads Sales Today by Brand
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
    
    # Convert report_date back to datetime for proper sorting
    df['date'] = pd.to_datetime(df['report_date'], format='%d/%m/%Y')
    
    # Aggregate by date (in case multiple entries per day)
    agg_df = df.groupby('date').agg({
        'current_balance': 'sum',
        'new_orders': 'sum',
        'ads_spend_total': 'sum',
        'acos': 'mean'
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
    
    return charts


# =============================================================================
# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

