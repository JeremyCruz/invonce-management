# Paso 1: Usa una imagen base oficial de Python
FROM python:3.9

# Paso 2: Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Paso 3: Copia el archivo de requerimientos
COPY requirements.txt .

# Paso 4: Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Paso 6: Instala Tesseract OCR
RUN apt-get update && apt-get install -y tesseract-ocr && apt-get clean
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# Paso 5: Copia el resto de la aplicación en el contenedor
COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Paso 7: Expone el puerto en el que correrá la aplicación Flask
EXPOSE 5000

# Paso 8: Comando para ejecutar la aplicación
CMD ["python", "app.py"]
