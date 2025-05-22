const form = document.getElementById('formulario');
const barra = document.getElementById('barra');
const status = document.getElementById('status');

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const dados = new FormData(form);
  status.textContent = "📤 Enviando arquivo...";
  barra.style.width = "10%";

  try {
    const resp = await fetch("/comprimir_api", {
      method: "POST",
      body: dados
    });

    if (!resp.ok) {
      const msg = await resp.text();
      throw new Error(msg || "Erro ao processar PDF");
    }

    status.textContent = "🛡️ Verificando com antivírus...";
    barra.style.width = "30%";

    await new Promise(resolve => setTimeout(resolve, 500));

    status.textContent = "🧼 Removendo metadados...";
    barra.style.width = "60%";

    await new Promise(resolve => setTimeout(resolve, 500));

    status.textContent = "🗜️ Comprimindo PDF...";
    barra.style.width = "80%";

    await new Promise(resolve => setTimeout(resolve, 500));

    status.textContent = "✅ PDF pronto. Baixando...";
    barra.style.width = "100%";

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "comprimido.pdf";
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    status.textContent = "❌ Erro: " + err.message;
    barra.style.background = "red";
  }
});