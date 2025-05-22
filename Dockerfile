FROM python:3.10-slim

# Variáveis
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ghostscript \
    clamav \
    clamav-freshclam \
    libmagic1 \
    libmagic-dev \
    file \
    && rm -rf /var/lib/apt/lists/*

# Atualizar a base de dados de vírus
RUN freshclam

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o app
COPY app/ .

# Expor a porta do Flask
EXPOSE 5000

CMD ["python", "app.py"]
