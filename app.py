from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from models import db, Customer, Product, Invoice, InvoiceItem
import pdfkit
import os
from flask_migrate import Migrate

app = Flask(__name__)

# Database configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Use MySQL/PostgreSQL in production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sagar12'

# Initialize the database with the app
db.init_app(app)

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)

# Create database tables (only required if you're not using migrations)
with app.app_context():
    db.create_all()

# Route for the homepage
@app.route('/')
def index():
    customers = Customer.query.all()
    products = Product.query.all()
    return render_template('index.html', customers=customers, products=products)


@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    hsn = request.form['hsn']
    rate = request.form['rate']

    new_product = Product(name=name, hsn=hsn, rate=float(rate))
    db.session.add(new_product)
    db.session.commit()
    
    flash('Product added successfully!', 'success')  # Success message
    return redirect(url_for('index'))


@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    # Retrieve customer details from the form
    customer_name = request.form['customer_name']
    customer_address = request.form['customer_address']
    customer_contact = request.form['customer_contact']
    
    # Check if the customer already exists; if not, add them
    customer = Customer.query.filter_by(name=customer_name, address=customer_address, contact=customer_contact).first()
    if not customer:
        customer = Customer(name=customer_name, address=customer_address, contact=customer_contact)
        db.session.add(customer)
        db.session.commit()
    
    # Now proceed with invoice generation
    product_ids = request.form.getlist('products')
    
    if not product_ids:
        return "At least one product must be selected", 400

    invoice = Invoice(customer_id=customer.id)
    db.session.add(invoice)
    db.session.commit()

    items = []
    total_amount = 0
    for product_id in product_ids:
        product = Product.query.get(product_id)
        quantity = 1  # Set quantity to 1 or allow users to specify it if needed
        gross_weight = product.rate * quantity
        net_weight = gross_weight * 0.95  # Example logic
        item = InvoiceItem(invoice_id=invoice.id, product_id=product_id, 
                           quantity=quantity, gross_weight=gross_weight, 
                           net_weight=net_weight, purity="22K", labour_charges=150)
        db.session.add(item)
        items.append(item)
        total_amount += gross_weight + 150  # Example calculation
    
    db.session.commit()

    # Tax calculations
    cgst = total_amount * 0.09
    sgst = total_amount * 0.09
    total_gst = cgst + sgst
    total_amount_with_gst = total_amount + total_gst
    
    # Render HTML to PDF
    rendered = render_template('invoice.html', invoice=invoice, items=items, 
                               total_amount=total_amount, cgst=cgst, sgst=sgst, 
                               total_amount_with_gst=total_amount_with_gst)
    
    pdf = pdfkit.from_string(rendered, False)
    pdf_filename = f'invoice_{invoice.id}.pdf'
    with open(pdf_filename, 'wb') as f:
        f.write(pdf)
    
    return send_file(pdf_filename)


if __name__ == '__main__':
    app.run(debug=True)