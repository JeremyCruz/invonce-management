from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import cv2
import pytesseract
import fitz  # PyMuPDF
import re
from werkzeug.utils import secure_filename


# Configuración de Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg'}

# Crear la carpeta 'uploads/' si no existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configura la ruta de Tesseract OCR en tu sistema
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Cambia esta ruta según tu instalación

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def image_to_text(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text

def extract_invoice_data(text):
    invoice_data = {}
    invoice_number = re.search(r'Factura\s*#?:?\s*(\w+)', text)
    if invoice_number:
        invoice_data['Invoice Number'] = invoice_number.group(1)
    
    date = re.search(r'Fecha\s*:\s*(\d{2}/\d{2}/\d{4})', text)
    if date:
        invoice_data['Date'] = date.group(1)
    
    total_amount = re.search(r'Total\s*:\s*\$?([\d,]+\.\d{2})', text)
    if total_amount:
        invoice_data['Total Amount'] = total_amount.group(1)
    
    return invoice_data

def save_to_excel(data, excel_path='invoice_data.xlsx'):
    if os.path.exists(excel_path):
        df_existing = pd.read_excel(excel_path)
        df_new = pd.DataFrame([data])
        df = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df = pd.DataFrame([data])
    
    df.to_excel(excel_path, index=False)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            file_type = 'pdf' if filename.endswith('.pdf') else 'image'
            text = pdf_to_text(file_path) if file_type == 'pdf' else image_to_text(file_path)
            invoice_data = extract_invoice_data(text)

            save_to_excel(invoice_data)

            return render_template('index.html', invoice_data=invoice_data)
    
    return render_template('index.html')

@app.route('/add-manual', methods=['POST'])
def add_manual_invoice():
    invoice_data = {
        'Invoice Number': request.form['invoice_number'],
        'Date': request.form['date'],
        'Total Amount': request.form['total_amount']
    }
    
    save_to_excel(invoice_data)

    return redirect(url_for('upload_file'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
