from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, send_file
from models import db, Customer, Product, Invoice, InvoiceItem
import pdfkit
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db.init_app(app)

from flask_migrate import Migrate
migrate = Migrate(app, db)

# Home page with buttons
@app.route('/')
def home():
    return render_template('home.html')

# Inventory Management - View Products
@app.route('/inventory')
def inventory():
    products = Product.query.all()
    return render_template('inventory.html', products=products)

# Add Product
@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    hsn = request.form['hsn']
    rate = float(request.form['rate'])
    
    new_product = Product(name=name, hsn=hsn, rate=rate)
    db.session.add(new_product)
    db.session.commit()
    
    return redirect(url_for('inventory'))

# Update Product
@app.route('/update_product/<int:id>', methods=['POST'])
def update_product(id):
    try:
        product = Product.query.get_or_404(id)
        data = request.get_json()

        if data:
            product.name = data.get('name', product.name)
            product.hsn = data.get('hsn', product.hsn)
            product.rate = float(data.get('rate', product.rate))

            db.session.commit()

            return jsonify({'message': 'Product updated successfully'}), 200
        else:
            return jsonify({'message': 'Invalid data'}), 400
    except Exception as e:
        # Log the error
        print(f"Error updating product: {e}")
        return jsonify({'message': 'Failed to update product'}), 500



@app.route('/inventory_manage')
def inventory_manage():
    products = Product.query.all()  # Fetch all products from the database
    return render_template('inventory_manage.html', products=products)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    # Get the product or return a 404 error if not found
    product = Product.query.get_or_404(product_id)

    # Check if there are any invoice items associated with this product
    if product.items:  # Use 'items' as defined in the Product model
        flash('Cannot delete product. There are invoices associated with it.', 'error')
        return redirect(url_for('inventory_manage'))

    # If there are no associated invoice items, delete the product
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully', 'success')
    return redirect(url_for('inventory'))  # Redirect back to the inventory management page

@app.route('/get_product/<int:id>')
def get_product(id):
    product = Product.query.get(id)
    if product:
        return {
            'name': product.name,
            'hsn': product.hsn,
            'rate': product.rate
        }
    return {}, 404


# Invoice Generation Page
@app.route('/generate_invoice_page')
def generate_invoice_page():
    products = Product.query.all()
    return render_template('generate_invoice.html', products=products)

# Generate Invoice
@app.route('/generate_invoice', methods=['GET', 'POST'])
def generate_invoice():
    customer_name = request.form['customer_name']
    customer_address = request.form['customer_address']
    customer_contact = request.form['customer_contact']
    product_ids = request.form.getlist('products[]')
    quantities = request.form.getlist('quantity[]')
    
    customer = Customer(name=customer_name, address=customer_address, contact=customer_contact)
    db.session.add(customer)
    db.session.commit()

    invoice = Invoice(customer_id=customer.id)
    db.session.add(invoice)
    db.session.commit()

    labour_charge = request.form.get('labour_charge', '0') 
    labour_charge = float(labour_charge) if labour_charge else 0 

    items = []
    total_amount = 0
    for idx, product_id in enumerate(product_ids):
        product = Product.query.get(product_id)
        quantity = float(quantities[idx])
        rate  =  product.rate
        gross_weight =  quantity
        net_weight = abs(gross_weight)  # Example logic
        item = InvoiceItem(invoice_id=invoice.id, product_id=product_id,product_rate = rate, 
                           quantity=quantity, gross_weight=gross_weight, 
                           net_weight=net_weight, purity="22K", labour_charges=labour_charge)
        db.session.add(item)
        items.append(item)
        total_amount = total_amount + product.rate * net_weight + labour_charge * net_weight 
    
    db.session.commit()

    cgst_value = request.form.get('cgst', '0')  
    cgst = float(cgst_value) if cgst_value else 0  

    sgst_value = request.form.get('sgst', '0')  
    sgst = float(sgst_value) if sgst_value else 0 

    if cgst > 0:
        cgst = total_amount*cgst/100
    if sgst > 0:
        sgst = total_amount*sgst/100

    # Add up total GST if required
    total_gst = cgst + sgst
    total_amount_with_gst = total_amount + total_gst

    rendered = render_template('invoice.html', invoice=invoice, items=items, 
                               total_amount=total_amount, cgst=cgst, sgst=sgst, 
                               total_amount_with_gst=total_amount_with_gst)
    
    pdf_folder = os.path.join(os.getcwd(), 'PDF')
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
    
    pdf_filename = os.path.join(pdf_folder, f'invoice_{invoice.id}.pdf')
    pdf = pdfkit.from_string(rendered, False)
    with open(pdf_filename, 'wb') as f:
        f.write(pdf)
    
    return send_file(pdf_filename)

if __name__ == '__main__':
    app.run(debug=True)
