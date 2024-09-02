# Paso 1: Usa una imagen base oficial de Python
FROM python:3.9

# Paso 2: Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Paso 3: Copia el archivo de requerimientos
COPY requirements.txt .

# Paso 4: Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Paso 5: Copia el resto de la aplicación en el contenedor
COPY . .

# Paso 6: Instala Tesseract OCR
RUN apt-get update && apt-get install -y tesseract-ocr && apt-get clean

# Paso 7: Expone el puerto en el que correrá la aplicación Flask
EXPOSE 5000

# Paso 8: Comando para ejecutar la aplicación
CMD ["python", "app.py"]
