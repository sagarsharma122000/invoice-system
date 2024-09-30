from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20), nullable=False)

    # Properly associate Invoices with the Customer
    invoices = db.relationship('Invoice', backref='customer', lazy=True, cascade="all, delete-orphan")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hsn = db.Column(db.String(20), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    
    # Cascade delete to invoice items when a product is deleted
    items = db.relationship('InvoiceItem', backref='product', cascade="all, delete-orphan", passive_deletes=True)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cascade delete invoice items when an invoice is deleted
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade="all, delete-orphan")


class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id', ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete="CASCADE"), nullable=False)
    product_rate = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    gross_weight = db.Column(db.Float, nullable=False)
    net_weight = db.Column(db.Float, nullable=False)
    purity = db.Column(db.String(10), nullable=False)
    labour_charges = db.Column(db.Float, nullable=False)
    # cgst = db.Column(db.Float, nullable=False)
    # sgst = db.Column(db.Float, nullable=False)
