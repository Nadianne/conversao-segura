import os, uuid, logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file, flash

from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utils import (
    validar_pdf,
    juntar_pdfs,
    limpar_temp,
    comprimir_pdf_ghostscript,
    escanear_arquivo,
    limpar_metadados_pdf
)

# 🔐 Variáveis de ambiente
load_dotenv()

# 🗂️ Diretório para uploads temporários
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🚀 Inicialização do Flask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_inseguro")
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB

# 🔐 Content Security Policy + Talisman
csp = {
    'default-src': ["'self'"],
    'style-src': ["'self'", 'https://fonts.googleapis.com'],
    'style-src-elem': ["'self'", 'https://fonts.googleapis.com'],
    'font-src': ['https://fonts.gstatic.com'],
    'img-src': ["'self'", 'data:'],
    'script-src': ["'self'"]
}
Talisman(app, content_security_policy=csp, force_https=False)
# 🚦 Limitação de requisições (anti-DoS)
limiter = Limiter(get_remote_address, app=app, default_limits=["20 per minute"])

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/seguranca.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🏠 Página principal (juntar PDF)
@app.route("/", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def index():
    if request.method == "POST":
        arquivos = request.files.getlist("pdfs")
        if not arquivos or len(arquivos) < 2:
            flash("Envie ao menos dois arquivos PDF.")
            return render_template("index.html")

        arquivos_salvos = []
        for arq in arquivos:
            if not validar_pdf(arq):
                flash(f"Arquivo inválido: {arq.filename}")
                logging.warning(f"[REJEITADO] IP {request.remote_addr} - Arquivo inválido.")
                return render_template("index.html")

            nome = f"{uuid.uuid4()}.pdf"
            caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome)
            arq.save(caminho)
            arquivos_salvos.append(caminho)

        pdf_final = juntar_pdfs(arquivos_salvos)
        limpar_temp(app.config["UPLOAD_FOLDER"])
        logging.info(f"[JUNTAR] IP {request.remote_addr} - PDFs unidos com sucesso.")
        return send_file(pdf_final, as_attachment=True, download_name="unido.pdf")

    return render_template("index.html")

# 📄 Página com formulário de compressão
@app.route("/comprimir", methods=["GET"])
def comprimir():
    return render_template("comprimir.html")

# ⚙️ API para compressão de PDF (via JavaScript)
@app.route("/comprimir_api", methods=["POST"])
@limiter.limit("5 per minute")
def comprimir_api():
    arquivo = request.files.get("pdf")
    qualidade = request.form.get("qualidade", "screen")

    if not arquivo or not validar_pdf(arquivo):
        logging.warning(f"[REJEITADO] IP {request.remote_addr} - Arquivo inválido.")
        return "Arquivo inválido", 400

    nome_entrada = f"/tmp/{uuid.uuid4()}.pdf"
    nome_saida = f"/tmp/comprimido_{uuid.uuid4()}.pdf"
    arquivo.save(nome_entrada)

    if os.path.getsize(nome_entrada) > 100 * 1024 * 1024:
        logging.warning(f"[EXCEDIDO] IP {request.remote_addr} - Arquivo > 100MB.")
        os.remove(nome_entrada)
        return "Arquivo muito grande", 413

    if not escanear_arquivo(nome_entrada):
        logging.warning(f"[CLAMAV] IP {request.remote_addr} - Vírus detectado.")
        os.remove(nome_entrada)
        return "Arquivo infectado", 403

    # Limpa metadados e comprime
    arquivo_limpo = f"/tmp/limpo_{uuid.uuid4()}.pdf"
    limpar_metadados_pdf(nome_entrada, arquivo_limpo)
    sucesso = comprimir_pdf_ghostscript(arquivo_limpo, nome_saida, qualidade)

    os.remove(nome_entrada)
    os.remove(arquivo_limpo)

    if not sucesso:
        logging.error(f"[ERRO] IP {request.remote_addr} - Falha na compressão.")
        return "Erro na compressão", 500

    logging.info(f"[COMPRIMIR] IP {request.remote_addr} - PDF comprimido com qualidade {qualidade}.")
    return send_file(nome_saida, as_attachment=True, download_name="comprimido.pdf")

@app.route("/juntar_api", methods=["POST"])
@limiter.limit("5 per minute")
def juntar_api():
    arquivos = request.files.getlist("pdfs")
    if not arquivos or len(arquivos) < 2:
        logging.warning(f"[REJEITADO] IP {request.remote_addr} - Menos de 2 arquivos.")
        return "Envie pelo menos dois PDFs.", 400

    arquivos_salvos = []
    for arq in arquivos:
        if not validar_pdf(arq):
            logging.warning(f"[REJEITADO] IP {request.remote_addr} - Arquivo inválido: {arq.filename}")
            return f"Arquivo inválido: {arq.filename}", 400

        nome_temp = f"/tmp/{uuid.uuid4()}.pdf"
        arq.save(nome_temp)

        # Tamanho individual
        if os.path.getsize(nome_temp) > 100 * 1024 * 1024:
            os.remove(nome_temp)
            logging.warning(f"[EXCEDIDO] IP {request.remote_addr} - {arq.filename} > 100MB.")
            return "Arquivo muito grande", 413

        # Verificação com ClamAV
        if not escanear_arquivo(nome_temp):
            os.remove(nome_temp)
            logging.warning(f"[CLAMAV] IP {request.remote_addr} - Vírus detectado em {arq.filename}")
            return "Arquivo infectado", 403

        # Limpeza de metadados
        caminho_limpo = f"/tmp/limpo_{uuid.uuid4()}.pdf"
        limpar_metadados_pdf(nome_temp, caminho_limpo)
        os.remove(nome_temp)

        arquivos_salvos.append(caminho_limpo)

    # Junta os arquivos
    pdf_final = juntar_pdfs(arquivos_salvos)

    # Limpa temporários
    for arq in arquivos_salvos:
        os.remove(arq)

    logging.info(f"[JUNTAR] IP {request.remote_addr} - {len(arquivos)} PDFs unidos com sucesso.")
    return send_file(pdf_final, as_attachment=True, download_name="unido.pdf")

@app.route("/juntar", methods=["GET"])
def juntar_pdf():
    return render_template("juntar_pdf.html")
# 🛑 Limite de requisições atingido
@app.errorhandler(429)
def ratelimit_handler(e):
    logging.warning(f"[LIMITE] IP {request.remote_addr} - Excesso de requisições.")
    return "🚫 Você fez muitas requisições. Aguarde um momento e tente novamente.", 429

# ▶️ Executa o app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
