Invoice System Flask Application
This is a Flask-based invoice generation and inventory management system that enables users to create, search, and manage invoices with integrated database migrations and PDF generation.

Steps to Run the Application
1. Navigate to Your Project Directory
Open Command Prompt or Terminal, and use the cd command to navigate to the directory where your Flask app is located. For example:
cd C:\Users\invoice system

2. Install Dependencies
Run the following command to install the necessary Python packages:
pip install -r requirements.txt

If you are manually installing packages, refer to the list below:

pip install Flask
pip install flask_sqlalchemy
pip install pdfkit
pip install Jinja2
pip install Flask-Migrate
pip install inflect
python -m pip install pytest-playwright
python -m playwright install chromium
pip install num2words

3. Set Up and Migrate Database
For a new database setup, use Flask-Migrate commands to initialize and apply migrations. Run the following commands:

flask db init
flask db migrate -m "Initial migration."
flask db upgrade

4. Run the Application
To start the app, use the following command:
python app.py


This will start the Flask application, and you can access it by opening a web browser and navigating to http://127.0.0.1:5000.



Automated Setup and Desktop Shortcut Creation (Batch Script)
For a more streamlined setup, use the batch script


Double-click the setup_migration.bat file to install dependencies, initialize the database, and create a desktop shortcut for easy access.

This batch script will:

Install all dependencies if they haven't been installed.
Initialize and migrate the database.
Create a desktop shortcut for run_app_waitress.bat to easily launch the app with Waitress server.



Requirements
This app relies on the following tools and libraries:

Flask: Web framework
Flask-SQLAlchemy: ORM for database interactions
Flask-Migrate: Handles database migrations
PDFKit: For generating PDF invoices
Jinja2: Templating engine
Inflect: To handle words (e.g., number to words)
Playwright (Chromium): For automated testing and PDF generation
Num2words: For converting numbers to words in PDF invoices