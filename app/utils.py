import os, uuid, magic
from pypdf import PdfReader, PdfWriter
import subprocess

def validar_pdf(arquivo):
    tipo = magic.from_buffer(arquivo.read(2048), mime=True)
    arquivo.seek(0)
    return tipo == "application/pdf"

def juntar_pdfs(lista_caminhos):
    writer = PdfWriter()
    for caminho in lista_caminhos:
        reader = PdfReader(caminho)
        for pagina in reader.pages:
            writer.add_page(pagina)
    saida = f"/tmp/{uuid.uuid4()}.pdf"
    with open(saida, "wb") as f:
        writer.write(f)
    return saida

def limpar_temp(pasta):
    for arq in os.listdir(pasta):
        os.remove(os.path.join(pasta, arq))

def comprimir_pdf_ghostscript(entrada, saida, qualidade="screen"):
    comando = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{qualidade}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={saida}",
        entrada
    ]

    try:
        subprocess.run(comando, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    
def escanear_arquivo(path):
    try:
        resultado = subprocess.run(["clamscan", path], capture_output=True, text=True)
        return "OK" in resultado.stdout
    except Exception:
        return False
    
def limpar_metadados_pdf(entrada, destino):
    reader = PdfReader(entrada)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata({})  # Remove todos os metadados
    with open(destino, "wb") as f:
        writer.write(f)
        
def remover_metadados_pdf(caminho_pdf):
    try:
        subprocess.run(['exiftool', '-all=', caminho_pdf], check=True)
        # Remove o backup gerado pelo exiftool (arquivo_original.pdf_original)
        backup = caminho_pdf + '_original'
        subprocess.run(['rm', '-f', backup])
        print(f"Metadados removidos de {caminho_pdf}")
    except subprocess.CalledProcessError:
        print("Erro ao remover metadados.")