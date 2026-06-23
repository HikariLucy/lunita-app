# Usamos una versión ligera de Python
FROM python:3.10-slim

# --- ESTA ES LA PARTE QUE FALTA ---
# Instalamos las dependencias de sistema que WeasyPrint necesita para los PDF
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
# ----------------------------------

# Le decimos al servidor dónde trabajar
WORKDIR /app

# Copiamos primero los requerimientos e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de tu código
COPY . .

# La instrucción mágica: llama a uvicorn a través de python -m y usa el puerto de Render
CMD sh -c "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"