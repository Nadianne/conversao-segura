const form = document.getElementById('formulario');
const barra = document.getElementById('barra');
const status = document.getElementById('status');

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const dados = new FormData(form);
  status.textContent = "📤 Enviando arquivos...";
  barra.style.width = "10%";

  try {
    const resp = await fetch("/juntar_api", {
      method: "POST",
      body: dados
    });

    if (!resp.ok) {
      const msg = await resp.text();
      throw new Error(msg || "Erro ao juntar PDFs");
    }

    status.textContent = "🛡️ Escaneando com antivírus...";
    barra.style.width = "30%";
    await new Promise(resolve => setTimeout(resolve, 500));

    status.textContent = "🧼 Removendo metadados...";
    barra.style.width = "60%";
    await new Promise(resolve => setTimeout(resolve, 500));

    status.textContent = "🧩 Juntando arquivos...";
    barra.style.width = "90%";
    await new Promise(resolve => setTimeout(resolve, 500));

    status.textContent = "✅ Download pronto!";
    barra.style.width = "100%";

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "unido.pdf";
    a.click();
    window.URL.revokeObjectURL(url);

  } catch (err) {
    status.textContent = "❌ Erro: " + err.message;
    barra.style.background = "red";
  }
});
