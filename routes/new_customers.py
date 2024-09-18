from flask import Blueprint, redirect, url_for, render_template, flash, request, Response
from flask_login import login_required, current_user
from woocommerce import API
import datetime
import requests
import csv
from io import StringIO


new_customers_bp = Blueprint('new_customers', __name__)

# Configure WooCommerce API
wcapi = API(
    url="http://54.227.71.10/review_system_wp/",  # Replace with your WooCommerce store URL
    consumer_key="ck_73e8efe2681689d47ded3bb87ce1ad00599c4907",  # Replace with your consumer key
    consumer_secret="cs_2597f8d4431f19c1f99bfbc3017709888f72a53a",  # Replace with your consumer secret
    wp_api=True,  # Enable the WP REST API integration
    version="wc/v3"  # WooCommerce API version
)

# Helper function to format date and time
def format_datetime(value):
    if not value:
        return 'N/A'  # Return 'N/A' if the value is None or empty

    try:
        date_obj = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        def ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return str(n) + suffix
        formatted_date = date_obj.strftime('%B ') + ordinal(date_obj.day) + date_obj.strftime(', %Y at %I:%M %p')
        return formatted_date
    except ValueError:
        return value  # Return original value if parsing fails

def parse_date(date_str):
    """
    Parse a date string that may be in multiple formats.
    """
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None  # Return None if no format matches


# Get all woocommerce order data
@new_customers_bp.route('/new-customers', methods=['GET'])
@login_required
def new_customers():
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('user_home'))

    # Country list (You can fetch this from an API or database if needed)
    countries = { 
        "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AS": "American Samoa", "AD": "Andorra", "AO": "Angola", "AI": "Anguilla", "AG": "Antigua and Barbuda", "AR": "Argentina", "AM": "Armenia",
        "AW": "Aruba", "AU": "Australia", "AT": "Austria", "AZ": "Azerbaijan", "BS": "Bahamas", "BH": "Bahrain", "BD": "Bangladesh", "BB": "Barbados", "BY": "Belarus", "BE": "Belgium",
        "BZ": "Belize", "BJ": "Benin", "BM": "Bermuda", "BT": "Bhutan", "BO": "Bolivia", "BA": "Bosnia and Herzegovina", "BW": "Botswana", "BR": "Brazil", "BN": "Brunei", "BG": "Bulgaria",
        "BF": "Burkina Faso", "BI": "Burundi", "CV": "Cabo Verde", "KH": "Cambodia", "CM": "Cameroon", "CA": "Canada", "KY": "Cayman Islands", "CF": "Central African Republic", "TD": "Chad", "CL": "Chile",
        "CN": "China", "CO": "Colombia", "KM": "Comoros", "CG": "Congo", "CD": "Congo (Democratic Republic)", "CR": "Costa Rica", "CI": "Côte d'Ivoire", "HR": "Croatia", "CU": "Cuba", "CY": "Cyprus",
        "CZ": "Czech Republic", "DK": "Denmark", "DJ": "Djibouti", "DM": "Dominica", "DO": "Dominican Republic", "EC": "Ecuador", "EG": "Egypt", "SV": "El Salvador", "GQ": "Equatorial Guinea", "ER": "Eritrea",
        "EE": "Estonia", "ET": "Ethiopia", "FJ": "Fiji", "FI": "Finland", "FR": "France", "GA": "Gabon", "GM": "Gambia", "GE": "Georgia", "DE": "Germany", "GH": "Ghana", "GR": "Greece",
        "GD": "Grenada", "GT": "Guatemala", "GN": "Guinea", "GW": "Guinea-Bissau", "GY": "Guyana", "HT": "Haiti", "HN": "Honduras", "HK": "Hong Kong", "HU": "Hungary", "IS": "Iceland",
        "IN": "India", "ID": "Indonesia", "IR": "Iran", "IQ": "Iraq", "IE": "Ireland", "IL": "Israel", "IT": "Italy", "JM": "Jamaica", "JP": "Japan", "JO": "Jordan", "KZ": "Kazakhstan",
        "KE": "Kenya", "KI": "Kiribati", "KP": "North Korea", "KR": "South Korea", "KW": "Kuwait", "KG": "Kyrgyzstan", "LA": "Laos", "LV": "Latvia", "LB": "Lebanon", "LS": "Lesotho",
        "LR": "Liberia", "LY": "Libya", "LI": "Liechtenstein", "LT": "Lithuania", "LU": "Luxembourg", "MO": "Macau", "MK": "North Macedonia", "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia",
        "MV": "Maldives", "ML": "Mali", "MT": "Malta", "MH": "Marshall Islands", "MR": "Mauritania", "MU": "Mauritius", "MX": "Mexico", "FM": "Micronesia", "MD": "Moldova", "MC": "Monaco",
        "MN": "Mongolia", "ME": "Montenegro", "MA": "Morocco", "MZ": "Mozambique", "MM": "Myanmar", "NA": "Namibia", "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands", "NZ": "New Zealand",
        "NI": "Nicaragua", "NE": "Niger", "NG": "Nigeria", "NO": "Norway", "OM": "Oman", "PK": "Pakistan", "PW": "Palau", "PA": "Panama", "PG": "Papua New Guinea", "PY": "Paraguay",
        "PE": "Peru", "PH": "Philippines", "PL": "Poland", "PT": "Portugal", "QA": "Qatar", "RO": "Romania", "RU": "Russia", "RW": "Rwanda", "KN": "Saint Kitts and Nevis", "LC": "Saint Lucia",
        "VC": "Saint Vincent and the Grenadines", "WS": "Samoa", "SM": "San Marino", "ST": "Sao Tome and Principe", "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia", "SC": "Seychelles",
        "SL": "Sierra Leone", "SG": "Singapore", "SK": "Slovakia", "SI": "Slovenia", "SB": "Solomon Islands", "SO": "Somalia", "ZA": "South Africa", "SS": "South Sudan", "ES": "Spain",
        "LK": "Sri Lanka", "SD": "Sudan", "SR": "Suriname", "SE": "Sweden", "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan", "TJ": "Tajikistan", "TZ": "Tanzania", "TH": "Thailand",
        "TL": "Timor-Leste", "TG": "Togo", "TO": "Tonga", "TT": "Trinidad and Tobago", "TN": "Tunisia", "TR": "Turkey", "TM": "Turkmenistan", "TV": "Tuvalu", "UG": "Uganda", "UA": "Ukraine",
        "AE": "United Arab Emirates", "GB": "United Kingdom", "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan", "VU": "Vanuatu", "VE": "Venezuela", "VN": "Vietnam", "YE": "Yemen",
        "ZM": "Zambia", "ZW": "Zimbabwe"
    }

    
    # Get filter parameters from the request
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    customer_country = request.args.get('customer_country')
    search_query = request.args.get('search_query', '').strip()  # New search query parameter

    # Validate search query length
    if len(search_query) > 0 and len(search_query) < 3:
        flash('Search query must be at least 3 characters long.', 'warning')
        search_query = ''  # Reset search_query if invalid

    try:
        # Get current page number, default is 1
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of orders per page

        # Fetch orders with pagination
        response = wcapi.get("orders", params={"per_page": per_page, "page": page})
        response.raise_for_status()  # Check for HTTP request errors
        order_list = response.json()

        # Total number of orders (from headers)
        total_orders = int(response.headers.get('X-WP-Total', 0))

        # Sort by date_created in descending order (newest first)
        order_list.sort(key=lambda x: x.get('date_created', ''), reverse=True)

        filtered_orders = []

        # Format date fields
        for order in order_list:
            payment_date = order.get('payment_details', {}).get('payment_date', '')
            date_created = order.get('date_created', '')
            order['payment_details']['payment_date_formatted'] = format_datetime(payment_date)
            order['date_created_formatted'] = format_datetime(date_created)

            order_date = parse_date(date_created)
            if from_date and order_date and order_date < datetime.datetime.strptime(from_date, '%Y-%m-%d'):
                continue
            if to_date and order_date and order_date > datetime.datetime.strptime(to_date, '%Y-%m-%d'):
                continue
            if customer_country and order.get('custom_meta', {}).get('billing_customer_country', '') != customer_country:
                continue

            # Apply search filter (if search query is at least 3 characters long)
            if len(search_query) >= 3:
                search_query_lower = search_query.lower()
                matched = False

                # Search through all relevant fields
                for key, value in order.items():
                    if isinstance(value, str) and search_query_lower in value.lower():
                        matched = True
                        break
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, str) and search_query_lower in sub_value.lower():
                                matched = True
                                break
                    if matched:
                        break

                if matched:
                    filtered_orders.append(order)
            else:
                filtered_orders.append(order)

        # Calculate the total number of pages
        total_pages = (total_orders + per_page - 1) // per_page

    except requests.RequestException as e:
        flash(f'Error fetching orders: {str(e)}', 'danger')
        return redirect(url_for('user_home'))

    return render_template(
        'new_customers.html', 
        order_list=filtered_orders,  # Render filtered orders instead of all orders
        search_query=search_query,  # Pass the search query back to the template
        total_pages=total_pages, 
        current_page=page,
        per_page=per_page,  # Add this for conditional rendering in template
        total_orders=total_orders,
        from_date=from_date, 
        to_date=to_date, 
        customer_country=customer_country, 
        countries=countries,
        user=current_user, 
        user_role=current_user.role
    )


# Export order data as csv format
@new_customers_bp.route('/new-customers/export-csv', methods=['GET'])
@login_required
def export_customers_csv():
    if current_user.role != 'administrator':
        flash('Access denied. Administrators only.', 'danger')
        return redirect(url_for('user_home'))
    
    try:
        # Fetch all orders
        response = wcapi.get("orders")
        response.raise_for_status()  # Check for HTTP request errors
        order_list = response.json()
        
        # Prepare the CSV file in memory
        si = StringIO()
        csv_writer = csv.writer(si)

        # Write CSV header
        csv_writer.writerow([
            "Order ID", "Payment Date", "Customer Name", "Customer Phone",
            "Customer Email", "Customer Country", "Business Name",
            "Business Phone", "Business Address", "Business Email", "Google Map URL"
        ])
        
        # Write CSV data rows
        for order in order_list:
            payment_date = order.get('payment_details', {}).get('payment_date', 'N/A')
            customer_name = order.get('custom_meta', {}).get('billing_customer_name', 'N/A')
            customer_phone = order.get('custom_meta', {}).get('billing_customer_phone', 'N/A')
            customer_email = order.get('custom_meta', {}).get('billing_customer_email', 'N/A')
            customer_country = order.get('custom_meta', {}).get('billing_customer_country', 'N/A')
            business_name = order.get('custom_meta', {}).get('billing_business_name', 'N/A')
            business_phone = order.get('custom_meta', {}).get('billing_business_phone', 'N/A')
            business_address = order.get('custom_meta', {}).get('billing_business_address', 'N/A')
            business_email = order.get('custom_meta', {}).get('billing_business_email', 'N/A')
            google_map_url = order.get('custom_meta', {}).get('billing_google_map_url', 'N/A')

            if payment_date != '':
                payment_date = order.get('date_created')

            csv_writer.writerow([
                order.get('order_id'), payment_date, customer_name, customer_phone, 
                customer_email, customer_country, business_name, business_phone, 
                business_address, business_email, google_map_url
            ])

        # Create a response with the CSV data
        output = si.getvalue()
        response = Response(output, mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=new_customers.csv'
        return response

    except Exception as e:
        flash(f'Error exporting orders: {str(e)}', 'danger')
        return redirect(url_for('new_customers.new_customers'))
