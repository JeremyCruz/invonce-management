from flask import Flask, render_template, request, redirect, send_file, url_for, flash
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
app.config['SECRET_KEY'] = '51d6aedc6dc9cfbd238d3b6bf85ffc1e'  # Configura una clave secreta aquí

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
    ruc = re.search(r'RUC\s*#?:?\s*(\w+)', text)
    if ruc:
        invoice_data['ruc'] = ruc.group(1)
    
    date = re.search(r'Fecha de emisión\s*:\s*(\d{2}/\d{2}/\d{4})', text)
    if date:
        invoice_data['date'] = date.group(1)
    
    total_amount = re.search(r'Importe total:\s*S/\s*([\d,]+\.\d{2})', text)
    if total_amount:
        invoice_data['total_amount'] = total_amount.group(1)
    
    og = re.search(r'SUBTOTAL:\s*S/\s*([\d,]+\.\d{2})', text)
    if og:
        invoice_data['og'] = og.group(1)
    
    oi = re.search(r'Op. Inafecta:\s*S/\s*([\d,]+\.\d{2})', text)
    if oi:
        invoice_data['oi'] = oi.group(1)
    
    oe = re.search(r'Op. Exonerada:\s*S/\s*([\d,]+\.\d{2})', text)
    if og:
        invoice_data['oe'] = oe.group(1)

    igv = re.search(r'I.G.V:\s*S/\s*([\d,]+\.\d{2})', text)
    if og:
        invoice_data['igv'] = igv.group(1)

    razon_social_match = re.search(r'\b[A-Za-z\s]+(?:SA|SAC|SRL|S.A.C.|S.A)\b', text)
    if razon_social_match:
        invoice_data['ruc_name'] = razon_social_match.group(0).strip()
    
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
    invoice_data = {}
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                file_type = 'pdf' if filename.endswith('.pdf') else 'image'
                text = pdf_to_text(file_path) if file_type == 'pdf' else image_to_text(file_path)
                invoice_data = extract_invoice_data(text)
                                
                flash('File processed successfully', 'success')
            except Exception as e:
                flash(f"An error occurred: {str(e)}", 'error')
    
    return render_template('index.html', invoice_data=invoice_data)

@app.route('/add-manual', methods=['POST'])
def add_manual_invoice():
    invoice_data = {
        'Type': request.form['type'],
        'Category': request.form['category'],
        'Razon Social': request.form['ruc_name'],
        'Responsable': request.form['responsable'],
        'Payment Method': request.form['pay_method'],
        'RUC': request.form['ruc'],
        'Date': request.form['date'],
        'Invoice Number': request.form['invoice_number'],
        'Op Gravada': request.form['og'],
        'Op Inafecta': request.form['oi'],
        'Op Exonerada': request.form['oe'],
        'IGV': request.form['igv'],
        'Total Amount': request.form['total_amount']
    }
    
    save_to_excel(invoice_data)

    return redirect(url_for('upload_file'))

@app.route('/download-excel')
def download_excel():
    excel_path = 'invoice_data.xlsx'
    if os.path.exists(excel_path):
        return send_file(excel_path, as_attachment=True)
    else:
        return "Archivo no encontrado", 404

if __name__ == '__main__':
    app.run(debug=True)
