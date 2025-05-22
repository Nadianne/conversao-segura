FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    ghostscript \
    clamav \
    clamav-freshclam \
    libmagic1 \
    libmagic-dev \
    file \
    && rm -rf /var/lib/apt/lists/*

# Atualizar base de dados do ClamAV
RUN pkill freshclam || true && freshclam

# Copiar tudo
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor porta do Flask
EXPOSE 5000

# Rodar a aplicação
CMD ["python", "app.py"]

