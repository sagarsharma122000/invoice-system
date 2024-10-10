from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, send_file, send_from_directory
from models import Sales, db, Customer, Product, Invoice, InvoiceItem
from playwright.async_api import async_playwright
import os
from datetime import datetime
import inflect
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db.init_app(app)

from flask_migrate import Migrate
migrate = Migrate(app, db)

# Create an inflect engine
p = inflect.engine()

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
    total_quantity = float(request.form['total_quantity'])
    rate = float(request.form['rate'])
    
    new_product = Product(name=name, total_quantity=total_quantity, rate=rate)
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
            product.total_quantity = float(data.get('total_quantity', product.total_quantity))
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
            'total_quantity': product.total_quantity,
            'rate': product.rate
        }
    return {}, 404


# Invoice Generation Page
@app.route('/generate_invoice_page')
def generate_invoice_page():
    products = Product.query.all()
    return render_template('generate_invoice.html', products=products)



# Assuming your PDFs are saved in a 'PDF' folder in the project directory
PDF_FOLDER = os.path.join(os.getcwd(), 'PDF')

@app.route('/search_invoice', methods=['GET', 'POST'])
def search_invoice():
    search_results = []  # To store the extracted information from the filenames
    search_performed = False

    if request.method == 'POST':
        search_date = request.form.get('search_date', '').strip()
        search_mobile = request.form.get('search_mobile', '').strip()

        # Convert the search_date from YYYY-MM-DD to DDMMYYYY
        if search_date:
            try:
                search_date = datetime.strptime(search_date, '%Y-%m-%d').strftime('%d%m%Y')
            except ValueError:
                search_date = ''  # Ignore if the date format is incorrect

        # Search for matching PDFs in the folder
        if os.path.exists(PDF_FOLDER):
            for filename in os.listdir(PDF_FOLDER):
                # Ensure the filename is in the expected format
                try:
                    parts = filename.split('_')
                    file_date, mobile, customer_name, invoice_id_with_extension = parts[0], parts[1], parts[2], parts[3]
                    invoice_id = invoice_id_with_extension.split('.')[0]

                    # Check if the file matches the search date and/or mobile number
                    if (search_date in file_date) and (search_mobile in mobile):
                        search_results.append({
                            'filename': filename,
                            'customer_name': customer_name,
                            'mobile': mobile,
                            'date': datetime.strptime(file_date, '%d%m%Y').strftime('%d-%m-%Y'),
                            'invoice_id': invoice_id
                        })
                except IndexError:
                    continue  # Skip files that don't match the expected format

        search_performed = True

    return render_template('search_invoice.html', search_results=search_results, search_performed=search_performed)


@app.route('/sales_history', methods=['GET', 'POST'])
def sales_history():
    sales = Sales.query.all()  # Fetch all sales data for the history section
    
    # Date filter section
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        # Query to aggregate by product_type for the given date range
        filtered_sales = db.session.query(
            Sales.product_type,
            func.sum(Sales.quantity_sold).label('total_quantity'),
            func.sum(Sales.total_amount).label('total_amount')
        ).filter(Sales.date_of_selling.between(start_date, end_date)) \
         .group_by(Sales.product_type).all()
        
        return render_template('sales_history.html', sales=sales, filtered_sales=filtered_sales)
    
    # Default: only show the history section if no date filter is applied
    return render_template('sales_history.html', sales=sales)


# Route to open/view the PDF files
@app.route('/view_pdf/<filename>')
def view_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

async def generate_html_pdf(pdf_filename, html_filename):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)  # Launch headless Chromium browser
        page = await browser.new_page()

        # Open the local HTML file
        await page.goto(f'file://{html_filename}')
        await page.emulate_media(media="screen")
        await page.pdf(
            path=pdf_filename, 
            format="A4", 
            landscape=False,  # Specify landscape or portrait orientation
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},  # Set margin to zero
            print_background=True  # Ensure that background colors and images are printed
        )

        await browser.close()  # Ensure the browser closes properly

# Generate Invoice
@app.route('/generate_invoice', methods=['GET', 'POST'])
async def generate_invoice():
    customer_name = request.form['customer_name']
    customer_address = request.form['customer_address']
    customer_contact = request.form['customer_contact']
    product_ids = request.form.getlist('products[]')
    gross_weights = request.form.getlist('gross_weight[]')
    net_weights = request.form.getlist('net_weight[]')
    invoice_name = request.form.getlist('invoice_name[]')
    labour_chargess = request.form.getlist('labour_charge[]')
    
    customer = Customer(name=customer_name, address=customer_address, contact=customer_contact)
    db.session.add(customer)
    db.session.commit()

    invoice = Invoice(customer_id=customer.id)
    db.session.add(invoice)
    db.session.commit()

    # labour_charge = request.form.get('labour_charge', '0') 
    # labour_charge = float(labour_charge) if labour_charge else 0 

    items = []
    total_amount = 0
    for idx, product_id in enumerate(product_ids):
        product = Product.query.get(product_id)
        rate  =  product.rate
        product_type = product.name
        product_name = invoice_name[idx]
        gross_weight = float(gross_weights[idx])
        net_weight = float(net_weights[idx])
        labour_charge = float(labour_chargess[idx]) if labour_chargess[idx] else 0 
        item = InvoiceItem(invoice_name = product_name, invoice_id=invoice.id, product_id=product_id,
                           product_type = product_type, product_rate = rate, gross_weight=gross_weight, 
                           net_weight=net_weight, labour_charges=labour_charge)
        db.session.add(item)
        items.append(item)
        
        total_item_amount = (rate * net_weight)
        sale = Sales(date_of_selling=datetime.now(),
                 product_type=product.name,
                 quantity_sold=net_weight,
                 rate=rate,
                 total_amount=total_item_amount)
    
        db.session.add(sale)

        # Update the product's total quantity
        if product.total_quantity >= net_weight:
            product.total_quantity -= net_weight
            product.total_quantity = round(product.total_quantity,2)
        else:
            flash(f"Insufficient stock for {product.name}. Available: {product.total_quantity}, Required: {net_weight}", "error")
            db.session.rollback()  # Rollback the session if not enough stock
            return redirect(url_for('generate_invoice_page'))  # Redirect to the invoice page
        
        total_amount = total_amount + product.rate * net_weight + labour_charge * net_weight
    
    db.session.commit()

    cgst_value = request.form.get('cgst', '0')  
    cgst_value = float(cgst_value) if cgst_value else 0  

    sgst_value = request.form.get('sgst', '0')  
    sgst_value = float(sgst_value) if sgst_value else 0 
    
    cgst = 0
    sgst = 0
    if cgst_value > 0:
        cgst = total_amount*cgst_value/100
    if sgst_value > 0:
        sgst = total_amount*sgst_value/100

    # Add up total GST if required
    total_gst = cgst + sgst
    total_amount_with_gst = total_amount + total_gst

    cgst = round(cgst, 2)
    sgst = round(sgst, 2)
    total_amount_with_gst = int(round(total_amount_with_gst, 0))
    words = p.number_to_words(total_amount_with_gst)
    result = f"{words.replace(',', '').title()} Rupees"

    rendered = render_template('invoice.html', invoice=invoice, items=items, 
                               total_amount=total_amount, cgst=cgst, sgst=sgst,
                               cgst_value = cgst_value, sgst_value = sgst_value,
                               total_amount_with_gst=total_amount_with_gst, result = result)
    
    pdf_folder = os.path.join(os.getcwd(), 'PDF')
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)

    today = datetime.now().strftime('%d%m%Y')
    pdf_filename = os.path.join(pdf_folder, f'{today}_{customer_contact}_{customer_name}_{invoice.id}.pdf')

    html_filename = os.path.join(pdf_folder, f'{today}_{customer_contact}_{customer_name}_{invoice.id}.html')
    with open(html_filename, 'w') as f:
        f.write(rendered)

    await generate_html_pdf(pdf_filename,html_filename)
    os.remove(html_filename)
    return send_file(pdf_filename)
    

if __name__ == '__main__':
    app.run(debug=True)
