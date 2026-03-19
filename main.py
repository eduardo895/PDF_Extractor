from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import re
from typing import Any, Dict, List, Optional, Tuple

app = FastAPI(title="Local Invoice PDF Extractor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_HTML = """
<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Extrator de Faturas PDF</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: #121931;
      --panel-2: #1a2342;
      --line: #2d3763;
      --text: #eef2ff;
      --muted: #aeb8db;
      --accent: #7aa2ff;
      --ok: #7bf0b1;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .wrap {
      max-width: 1380px;
      margin: 0 auto;
      padding: 24px;
    }
    .hero { margin-bottom: 20px; }
    .hero h1 { margin: 0 0 8px; font-size: 30px; }
    .hero p { margin: 0; color: var(--muted); }

    .toolbar {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      margin-top: 20px;
    }

    .dropzone {
      width: 100%;
      min-height: 140px;
      border: 2px dashed var(--line);
      border-radius: 16px;
      background: rgba(122,162,255,.05);
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 18px;
      transition: .18s ease;
      cursor: pointer;
    }
    .dropzone:hover {
      border-color: var(--accent);
      background: rgba(122,162,255,.08);
    }
    .dropzone.dragover {
      border-color: var(--ok);
      background: rgba(123,240,177,.08);
      transform: scale(1.01);
    }
    .dropzone .inner {
      display: grid;
      gap: 8px;
    }
    .dropzone .title {
      font-size: 18px;
      font-weight: 700;
    }
    .dropzone .subtitle {
      color: var(--muted);
      font-size: 14px;
    }
    .dropzone .filename {
      color: var(--ok);
      font-size: 14px;
      font-weight: 700;
      word-break: break-word;
    }

    input[type=file] {
      display: none;
    }

    .btn {
      background: var(--accent);
      color: white;
      border: 0;
      border-radius: 10px;
      padding: 11px 16px;
      font-weight: 700;
      cursor: pointer;
    }
    .btn.secondary {
      background: transparent;
      border: 1px solid var(--line);
      color: var(--text);
    }
    .btn:disabled { opacity: .6; cursor: default; }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      width: 100%;
    }

    .status {
      color: var(--muted);
      margin-top: 12px;
      min-height: 20px;
    }

    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255,255,255,.25);
      border-top-color: white;
      border-radius: 50%;
      animation: spin .8s linear infinite;
      vertical-align: -2px;
      margin-right: 8px;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .grid {
      display: grid;
      grid-template-columns: 520px 1fr;
      gap: 20px;
      margin-top: 20px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      min-height: 200px;
    }
    .card h2 {
      margin: 0 0 14px;
      font-size: 18px;
    }
    .fields {
      display: grid;
      gap: 10px;
    }
    .field {
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
    }
    .field .label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .06em;
      margin-bottom: 6px;
    }
    .field .value {
      font-size: 18px;
      font-weight: 700;
      word-break: break-word;
    }
    .field .confidence {
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
    }
    .pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      background: rgba(51,194,127,.15);
      color: #7bf0b1;
      border: 1px solid rgba(51,194,127,.2);
      font-size: 12px;
      margin-left: 6px;
    }
    .warn {
      background: rgba(240,180,41,.15);
      color: #ffd57a;
      border-color: rgba(240,180,41,.2);
    }
    .text-box {
      background: #0d1429;
      color: #dbe4ff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      white-space: pre-wrap;
      word-wrap: break-word;
      line-height: 1.45;
      max-height: 72vh;
      overflow: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 14px;
    }
    .meta .mini {
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px;
    }
    .mini .k {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }
    .mini .v {
      font-weight: 700;
      word-break: break-word;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      text-align: left;
      padding: 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    @media (max-width: 1000px) {
      .grid { grid-template-columns: 1fr; }
      .meta { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>Extrator local de faturas PDF</h1>
      <p>Reconstrói texto por coordenadas do PDF, separa cabeçalho e linhas de artigo.</p>
    </div>

    <div class="toolbar">
      <input id="file" type="file" accept="application/pdf" />

      <div id="dropzone" class="dropzone">
        <div class="inner">
          <div class="title">Arrasta o PDF para aqui</div>
          <div class="subtitle">ou clica para escolher um ficheiro</div>
          <div id="selected-file" class="filename"></div>
        </div>
      </div>

      <div class="actions">
        <button class="btn" id="send">Extrair dados</button>
        <button class="btn secondary" id="copy-json" disabled>Copiar JSON</button>
        <button class="btn secondary" id="download-json" disabled>Exportar JSON</button>
        <button class="btn secondary" id="download-csv" disabled>Exportar CSV</button>
      </div>
    </div>

    <div id="status" class="status"></div>

    <div class="grid">
      <div class="card">
        <h2>Cabeçalho da fatura</h2>
        <div id="fields" class="fields"></div>

        <h2 style="margin-top:18px">Linhas de artigo</h2>
        <div id="items"></div>
      </div>

      <div class="card">
        <h2>Texto processado</h2>
        <div id="meta" class="meta"></div>
        <div id="text" class="text-box"></div>
      </div>
    </div>
  </div>

  <script>
    const btn = document.getElementById('send');
    const copyJsonBtn = document.getElementById('copy-json');
    const downloadJsonBtn = document.getElementById('download-json');
    const downloadCsvBtn = document.getElementById('download-csv');

    const fileInput = document.getElementById('file');
    const status = document.getElementById('status');
    const textBox = document.getElementById('text');
    const fieldsBox = document.getElementById('fields');
    const metaBox = document.getElementById('meta');
    const itemsBox = document.getElementById('items');
    const dropzone = document.getElementById('dropzone');
    const selectedFileBox = document.getElementById('selected-file');

    let lastResult = null;

    function confidenceBadge(conf) {
      const n = Number(conf || 0);
      if (n >= 0.8) return `<span class="pill">alta</span>`;
      if (n >= 0.6) return `<span class="pill warn">média</span>`;
      return `<span class="pill warn">baixa</span>`;
    }

    function renderFields(data) {
      const entries = Object.entries(data.header || {});
      if (!entries.length) {
        fieldsBox.innerHTML = '<div class="field"><div class="label">Sem resultados</div><div class="value">Nenhum campo identificado</div></div>';
        return;
      }

      fieldsBox.innerHTML = entries.map(([key, value]) => `
        <div class="field">
          <div class="label">${key.replaceAll('_', ' ')}</div>
          <div class="value">${value.value ?? ''} ${confidenceBadge(value.confidence)}</div>
          <div class="confidence">Confiança: ${value.confidence ?? ''}</div>
        </div>
      `).join('');
    }

    function renderItems(data) {
      const items = data.items || [];
      if (!items.length) {
        itemsBox.innerHTML = '<div class="field"><div class="label">Sem artigos</div><div class="value">Nenhuma linha de artigo identificada</div></div>';
        return;
      }

      itemsBox.innerHTML = `
        <div style="overflow:auto; margin-top:10px;">
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Código</th>
                <th>Descrição</th>
                <th>Qtd</th>
                <th>Un</th>
                <th>P. Unit.</th>
                <th>Desc.</th>
                <th>IVA</th>
                <th>Total linha</th>
              </tr>
            </thead>
            <tbody>
              ${items.map(item => `
                <tr>
                  <td>${item.type || ''}</td>
                  <td>${item.code || ''}</td>
                  <td>${item.description || ''}</td>
                  <td>${item.qty || ''}</td>
                  <td>${item.unit || ''}</td>
                  <td>${item.unit_price || ''}</td>
                  <td>${item.discount || ''}</td>
                  <td>${item.vat_rate || ''}</td>
                  <td>${item.line_total || ''}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderMeta(data) {
      metaBox.innerHTML = `
        <div class="mini"><div class="k">Ficheiro</div><div class="v">${data.filename || '-'}</div></div>
        <div class="mini"><div class="k">Linhas úteis</div><div class="v">${data.line_count || 0}</div></div>
        <div class="mini"><div class="k">Texto repetido removido</div><div class="v">${data.removed_repeated_lines || 0}</div></div>
        <div class="mini"><div class="k">Modo</div><div class="v">${data.extraction_mode || '-'}</div></div>
      `;
    }

    function showSelectedFile(file) {
      selectedFileBox.textContent = file ? `Selecionado: ${file.name}` : '';
    }

    function setActionButtonsEnabled(enabled) {
      copyJsonBtn.disabled = !enabled;
      downloadJsonBtn.disabled = !enabled;
      downloadCsvBtn.disabled = !enabled;
    }

    function setSinglePdfFile(file) {
      if (!file) return false;

      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        status.textContent = 'Só PDFs são suportados.';
        return false;
      }

      const dt = new DataTransfer();
      dt.items.add(file);
      fileInput.files = dt.files;
      showSelectedFile(file);
      status.textContent = 'PDF pronto para extrair.';
      return true;
    }

    function showLoading(message) {
      status.innerHTML = `<span class="spinner"></span>${message}`;
    }

    function escapeCsv(value) {
      const s = String(value ?? '');
      if (s.includes('"') || s.includes(';') || s.includes('\\n')) {
        return '"' + s.replaceAll('"', '""') + '"';
      }
      return s;
    }

    function buildCsv(items) {
      const headers = [
        'type', 'code', 'description', 'qty', 'unit',
        'unit_price', 'discount', 'vat_rate', 'line_total'
      ];

      const rows = [
        headers.join(';'),
        ...items.map(item => headers.map(h => escapeCsv(item[h] ?? '')).join(';'))
      ];

      return rows.join('\\n');
    }

    function downloadFile(content, filename, contentType) {
      const blob = new Blob([content], { type: contentType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }

    function baseFilename(name) {
      if (!name) return 'resultado';
      return name.replace(/\\.pdf$/i, '');
    }

    async function sendFile() {
      const f = fileInput.files[0];
      if (!f) {
        status.textContent = 'Escolhe um PDF primeiro.';
        return;
      }

      btn.disabled = true;
      setActionButtonsEnabled(false);
      showLoading('A processar PDF...');
      textBox.textContent = '';
      fieldsBox.innerHTML = '';
      itemsBox.innerHTML = '';
      metaBox.innerHTML = '';
      lastResult = null;

      const form = new FormData();
      form.append('file', f);

      try {
        const res = await fetch('/extract', { method: 'POST', body: form });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Erro ao processar PDF');

        lastResult = data;
        renderFields(data);
        renderItems(data);
        renderMeta(data);
        textBox.textContent = data.cleaned_text || data.raw_text || '';
        status.textContent = 'Concluído.';
        setActionButtonsEnabled(true);
      } catch (err) {
        status.textContent = 'Erro: ' + err.message;
      } finally {
        btn.disabled = false;
      }
    }

    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async () => {
      const f = fileInput.files[0];
      showSelectedFile(f);
      if (f) {
        status.textContent = 'PDF pronto para extrair.';
      }
    });

    ['dragenter', 'dragover'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'dragend'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');

      const files = e.dataTransfer?.files;
      if (!files || !files.length) return;

      const file = files[0];
      const ok = setSinglePdfFile(file);
      if (ok) {
        await sendFile();
      }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
      document.addEventListener(evt, (e) => e.preventDefault());
    });

    btn.onclick = sendFile;

    copyJsonBtn.onclick = async () => {
      if (!lastResult) return;
      const json = JSON.stringify(lastResult, null, 2);
      await navigator.clipboard.writeText(json);
      status.textContent = 'JSON copiado para a área de transferência.';
    };

    downloadJsonBtn.onclick = () => {
      if (!lastResult) return;
      const name = baseFilename(lastResult.filename) + '.json';
      downloadFile(JSON.stringify(lastResult, null, 2), name, 'application/json;charset=utf-8');
    };

    downloadCsvBtn.onclick = () => {
      if (!lastResult) return;
      const name = baseFilename(lastResult.filename) + '_items.csv';
      const csv = buildCsv(lastResult.items || []);
      downloadFile(csv, name, 'text/csv;charset=utf-8');
    };
  </script>
</body>
</html>
"""

FIELD_ALIASES = {
    "invoice_date": ["invoice date", "date", "data", "data da fatura"],
    "due_date": ["vencimento", "due date"],
    "customer_nif": ["v. contribuinte", "cliente", "customer vat", "customer vat number", "nif cliente"],
    "supplier_nif": ["contrib nº", "contribuinte", "vat", "nif", "tax id", "vat number", "vat no", "nipc"],
    "subtotal": ["valor liquido", "subtotal", "sub total", "valor sem iva", "ilíquido", "base"],
    "iva_amount": ["i.v.a.", "iva", "vat amount", "tax", "imposto", "montante taxa"],
    "total": ["total documento", "liquido", "líquido", "total", "total amount", "amount due", "valor total", "total a pagar", "montante total"],
}

MONEY_RE = re.compile(r"(?<!\d)(?:€\s?)?[-+]?\d{1,3}(?:[ .]\d{3})*(?:,\d{2}|\.\d{2,3})(?![./]\d)(?!\d)")
DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),
    re.compile(r"\b\d{2}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b"),
]
PT_VAT_RE = re.compile(r"\bPT\s?\d{9}\b|\b\d{9}\b")
INVOICE_NO_RE = re.compile(r"\b\d{4}\.[A-Z]{2}\.\d+/\d+\b")


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_for_compare(line: str) -> str:
    line = line.lower().strip()
    line = re.sub(r"\b(original|duplicado|triplicado|quadruplicado)\b", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def cleanup_lines(text: str) -> Tuple[List[str], int]:
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    seen: Dict[str, int] = {}
    cleaned: List[str] = []
    removed = 0

    for line in raw_lines:
        norm = normalize_for_compare(line)
        if not norm:
            continue

        count = seen.get(norm, 0)
        if count >= 1 and len(norm) > 8:
            removed += 1
            seen[norm] = count + 1
            continue

        seen[norm] = count + 1
        cleaned.append(line)

    return cleaned, removed


def join_broken_label_lines(lines: List[str]) -> List[str]:
    merged: List[str] = []
    i = 0

    while i < len(lines):
        current = lines[i]

        if i + 1 < len(lines):
            nxt = lines[i + 1]
            pair = f"{current} {nxt}"

            if any(k in pair.lower() for k in [
                "factura fn",
                "fatura fn",
                "data",
                "valor liquido",
                "total documento",
                "i.v.a.",
                "vencimento",
            ]):
                if len(current) < 40 or current.endswith(":") or current.isupper():
                    merged.append(pair)
                    i += 2
                    continue

        merged.append(current)
        i += 1

    return merged


def money_candidates_in_line(line: str) -> List[str]:
    vals = MONEY_RE.findall(line)
    cleaned: List[str] = []
    for v in vals:
        if re.search(r"\d{2}[./]\d{2}[./]\d{2,4}", v):
            continue
        cleaned.append(v.strip())
    return cleaned

def get_first_date(text: str) -> Optional[str]:
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def parse_money_value(value: str) -> Optional[float]:
    if value is None:
        return None
    s = value.strip().replace("€", "").replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def format_money_pt(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def reconstruct_lines_from_words_pdfplumber(data: bytes) -> List[str]:
    import pdfplumber

    final_lines: List[str] = []

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                use_text_flow=False,
                keep_blank_chars=False,
                x_tolerance=2,
                y_tolerance=3,
            ) or []

            if not words:
                page_text = page.extract_text(layout=True) or ""
                final_lines.extend([ln.strip() for ln in page_text.splitlines() if ln.strip()])
                continue

            words = sorted(words, key=lambda w: (round(float(w["top"]), 1), float(w["x0"])))

            grouped: List[List[Dict[str, Any]]] = []
            current_group: List[Dict[str, Any]] = []
            current_top: Optional[float] = None
            tolerance = 3.0

            for w in words:
                top = float(w["top"])
                if current_top is None:
                    current_top = top
                    current_group = [w]
                    continue

                if abs(top - current_top) <= tolerance:
                    current_group.append(w)
                else:
                    grouped.append(current_group)
                    current_group = [w]
                    current_top = top

            if current_group:
                grouped.append(current_group)

            for group in grouped:
                group = sorted(group, key=lambda w: float(w["x0"]))
                pieces: List[str] = []
                prev_x1: Optional[float] = None

                for w in group:
                    text = str(w["text"]).strip()
                    x0 = float(w["x0"])
                    x1 = float(w["x1"])

                    if not text:
                        continue

                    if prev_x1 is None:
                        pieces.append(text)
                    else:
                        gap = x0 - prev_x1
                        if gap > 25:
                            pieces.append("    " + text)
                        else:
                            pieces.append(" " + text)

                    prev_x1 = x1

                line = "".join(pieces).strip()
                if line:
                    final_lines.append(line)

    return final_lines


def extract_text_from_pdf_bytes(data: bytes) -> Tuple[str, str]:
    parts: List[str] = []

    try:
        lines = reconstruct_lines_from_words_pdfplumber(data)
        text = normalize_whitespace("\n".join(lines))
        if len(text) > 40:
            return text, "pdfplumber_words"
    except Exception:
        pass

    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(page_text)

        text = normalize_whitespace("\n".join(parts))
        if len(text) > 40:
            return text, "pypdf"
    except Exception:
        pass

    try:
        import pdfplumber
        plumber_parts: List[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(layout=True) or ""
                if page_text.strip():
                    plumber_parts.append(page_text)
        text = normalize_whitespace("\n".join(plumber_parts))
        if len(text) > 40:
            return text, "pdfplumber_layout"
    except Exception:
        pass

    return "", "none"


def extract_value_near_alias(lines: List[str], aliases: List[str], kind: str) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()

        for alias in aliases:
            if alias in low:
                if kind == "money":
                    vals = money_candidates_in_line(line)
                    if vals:
                        return vals[-1], 0.88
                    if i + 1 < len(lines):
                        vals = money_candidates_in_line(lines[i + 1])
                        if vals:
                            return vals[0], 0.76

                elif kind == "date":
                    date = get_first_date(line)
                    if date:
                        return date, 0.88
                    if i + 1 < len(lines):
                        date = get_first_date(lines[i + 1])
                        if date:
                            return date, 0.76

                elif kind == "vat":
                    m = PT_VAT_RE.search(line)
                    if m:
                        return m.group(0).replace(" ", ""), 0.82
                    if i + 1 < len(lines):
                        m = PT_VAT_RE.search(lines[i + 1])
                        if m:
                            return m.group(0).replace(" ", ""), 0.70

    return None


def infer_supplier_name(lines: List[str]) -> Optional[Tuple[str, float]]:
    blacklist = [
        "exmo.(s)", "faturado ao cliente", "documento nº", "documento no", "data ",
        "n/ contribuinte", "v/ contribuinte", "condições de pagamento", "condicoes de pagamento",
        "data de vencimento", "entrega em", "item nº do produto", "item no do produto",
        "descrição do produto", "descricao do produto", "quantidade", "preço unitário",
        "preco unitario", "preço total", "preco total", "iban", "atcud", "modo de expedição",
        "modo de expedicao", "cliente:", "nr. doc.:", "nif:", "transportador", "pag. ",
        "tel:", "fax:", "porto :", "lisboa :", "cond.pgt", "email:", "www.", "capital social", "licenciado a:"
    ]
    positive_hints = [
        "lda", "lda.", "s.a.", "sa", "unipessoal", "portugal", "computadores",
        "informáticos", "informaticos", "distribution", "distribuição", "distribuicao",
        "software", "material informático", "material informatico"
    ]
    def clean_supplier_candidate(s: str) -> str:
        s = re.sub(r"\bFatura\b", "", s, flags=re.IGNORECASE).strip(" -")
        s = re.sub(r"\s*[|*]\s.*$", "", s).strip()
        s = re.sub(r"\s+-\s+Rua .*$", "", s, flags=re.IGNORECASE).strip()
        s = re.sub(r"\s{2,}", " ", s)
        return s.strip(" -")
    def is_bad_supplier_candidate(s: str) -> bool:
        low = s.lower().strip()
        if len(s) < 4 or "microlagos" in low:
            return True
        if any(x in low for x in blacklist):
            return True
        if get_first_date(s):
            return True
        if re.search(r"\b(?:tel|fax)\b", low):
            return True
        if re.search(r"\b\d{4}-\d{3}\b", s):
            return True
        if ":" in s and not any(h in low for h in positive_hints):
            return True
        if re.search(r"\b(?:rua|av\.?|avenida|largo|edifício|edificio|piso|loja|apartado)\b", low) and not any(h in low for h in positive_hints):
            return True
        if low in {"portugal", "faro", "lagos", "porto", "lisboa", "loja b"}:
            return True
        return False
    for i, line in enumerate(lines[:10]):
        s = clean_supplier_candidate(line.strip())
        low = s.lower()
        if is_bad_supplier_candidate(s):
            continue
        if any(h in low for h in positive_hints):
            return s, max(0.97 - i * 0.04, 0.82)
    footer_priority = []
    for idx, line in enumerate(lines):
        s = clean_supplier_candidate(line.strip())
        low = s.lower()
        if is_bad_supplier_candidate(s):
            continue
        if "eticadata software" in low:
            s = re.sub(r"^.*?(eticadata software,?\s*lda\.?)(?:.*)?$", r"", s, flags=re.IGNORECASE)
            return s, 0.98
        if any(h in low for h in positive_hints):
            score = 0.91 + (0.03 if idx > len(lines)//2 else 0)
            if "sage portugal" in low or "wdmi" in low or "also portugal" in low:
                score += 0.05
            if re.search(r"\d[A-Za-z]|[A-Za-z]\d", s):
                score -= 0.08
            footer_priority.append((s, score))
    if footer_priority:
        footer_priority.sort(key=lambda x: x[1], reverse=True)
        return footer_priority[0]
    return None

def parse_generic_item_line_simple(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 6:
        return None
    if len(parts) >= 5:
        q, u = split_attached_unit_token(parts[-4])
        if q and u and is_money_token(parts[-3]) and is_money_token(parts[-2]) and is_money_token(parts[-1]):
            return None
    if not is_money_token(parts[-1]) or not is_money_token(parts[-2]) or not is_number_token(parts[-3]):
        return None
    line_total = parts[-1]
    unit_price = parts[-2]
    qty = parts[-3]
    left = parts[:-3]
    if len(left) < 2:
        return None
    origin = ""
    code = ""
    description_tokens = left[:]
    if description_tokens and re.fullmatch(r"\d{1,6}", description_tokens[0]):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    if description_tokens and looks_like_code_token(description_tokens[0]):
        code = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": "", "unit_price": unit_price, "discount": "", "vat_rate": "", "line_total": line_total}

def infer_invoice_number(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        m_doc = re.search(r"documento\s*n[ºo]\.?\s+\S+\s+([A-Z0-9./_-]+)", line, re.IGNORECASE)
        if m_doc:
            return m_doc.group(1), 0.97
        m_nr = re.search(r"nr\.\s*doc\.:\s*[A-Z0-9]+\s+([A-Z0-9./_-]+)", line, re.IGNORECASE)
        if m_nr:
            return m_nr.group(1), 0.97
        m_ft = re.search(r"fatura\s*n[ºo]\s*[A-Z]{1,4}\s+([A-Z0-9./_-]+)", line, re.IGNORECASE)
        if m_ft:
            return m_ft.group(1), 0.97
        m_fatee = re.search(r"\b(FATEE\s+\d{3,}/\d+)\b", line, re.IGNORECASE)
        if m_fatee:
            return m_fatee.group(1), 0.98
        low = line.lower()
        if ("factura" in low or "fatura" in low) and len(line) < 80:
            m = re.search(r"(?:factura|fatura)\s+[A-Z]{1,4}\s+([A-Z0-9./-]+)", line, re.IGNORECASE)
            if m:
                return m.group(1), 0.95
            m2 = INVOICE_NO_RE.search(line)
            if m2:
                return m2.group(0), 0.90
    return None

def infer_dates(lines: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    inv = None
    due = None
    for i, line in enumerate(lines):
        low = line.lower()
        if "data venc" in low and "data doc" in low and i + 1 < len(lines):
            ds = []
            for pat in DATE_PATTERNS:
                ds.extend(pat.findall(lines[i + 1]))
            if len(ds) >= 2:
                due = (ds[0], 0.95)
                inv = (ds[1], 0.95)
        if inv is None and ("data doc" in low or re.search(r"\bdata:\b", low) or low.startswith("data ")):
            d = get_first_date(line)
            if d:
                inv = (d, 0.92)
        if due is None and ("vencimento" in low or "data venc" in low or "data de venct" in low):
            d = get_first_date(line)
            if d:
                due = (d, 0.92)
    if inv is None:
        inv = extract_value_near_alias(lines, FIELD_ALIASES["invoice_date"], "date")
    if due is None:
        due = extract_value_near_alias(lines, FIELD_ALIASES["due_date"], "date")
    if inv:
        out["invoice_date"] = {"value": inv[0], "confidence": round(inv[1], 2)}
    if due:
        out["due_date"] = {"value": due[0], "confidence": round(due[1], 2)}
    return out

def infer_best_total(lines: List[str]) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if "total documento" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.96

            nearby = []
            for j in range(i + 1, min(i + 8, len(lines))):
                nearby.extend(money_candidates_in_line(lines[j]))

            if nearby:
                return nearby[-1], 0.90

    return extract_value_near_alias(lines, FIELD_ALIASES["total"], "money")


def infer_subtotal(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        low = line.lower()
        if "montante líquido total sem iva" in low or "montante liquido total sem iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.96
        if "mercadoria:" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "total ilíquido" in low or "total iliquido" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "base de incidência de i.v.a." in low or "base de incidencia de i.v.a." in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.94
    return extract_value_near_alias(lines, FIELD_ALIASES["subtotal"], "money")

def infer_vat_amount(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        low = line.lower()
        if "montante de iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "total de i.v.a." in low or "iva:" in low or "resumo do iva iva:" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "observações: i.v.a." in low or "observacoes: i.v.a." in low or re.search(r"\bi\.v\.a\.\b", low):
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.95
    for i, line in enumerate(lines):
        low = line.lower()
        if "base taxa valor eur" in low:
            for j in range(i + 1, min(i + 4, len(lines))):
                vals = money_candidates_in_line(lines[j])
                if len(vals) >= 2:
                    return vals[1], 0.90
    return None

def infer_total_document(lines: List[str]) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if "montante total incluindo iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.98
        if "total documento" in low:
            after = re.split(r"total documento", line, flags=re.IGNORECASE)[-1]
            vals = money_candidates_in_line(after)
            if vals:
                return vals[-1], 0.99
            for j in range(i + 1, min(i + 3, len(lines))):
                vals = money_candidates_in_line(lines[j])
                if vals:
                    return vals[-1], 0.95
        if "total em eur" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.98
        if re.match(r"^total:\s*", low):
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.98
    return None

def infer_vat_amount(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        low = line.lower()
        if "montante de iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "total de i.v.a." in low or "iva:" in low or "resumo do iva iva:" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "observações: i.v.a." in low or "observacoes: i.v.a." in low or re.search(r"\bi\.v\.a\.\b", low):
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.95
    for i, line in enumerate(lines):
        low = line.lower()
        if "base taxa valor eur" in low:
            for j in range(i + 1, min(i + 4, len(lines))):
                vals = money_candidates_in_line(lines[j])
                if len(vals) >= 2:
                    return vals[1], 0.90
    return None

def find_customer_nif(lines: List[str]) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if "cliente:" in low and "nif:" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.95
        if "v/ contribuinte" in low or "v. contribuinte" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.93
        if re.match(r"^contribuinte:", low):
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.92
        if "nº de contribuinte cliente" in low or "contribuinte cliente" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.90
        if "cliente" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.82
            if i + 1 < len(lines):
                m = PT_VAT_RE.search(lines[i + 1])
                if m:
                    return m.group(0).replace(" ", ""), 0.75
    return None

def find_supplier_nif(lines: List[str], customer_nif: Optional[str]) -> Optional[Tuple[str, float]]:
    candidates: List[Tuple[str, float]] = []
    for line in lines:
        low = line.lower()
        for m in PT_VAT_RE.finditer(line):
            nif = m.group(0).replace(" ", "")
            score = 0.45
            if customer_nif and nif == customer_nif:
                score -= 0.40
            if ".contribuinte nº" in low or "contribuinte nº" in low or "nif pt" in low or "nipc" in low:
                score += 0.35
            if "sage" in low or "eticadata" in low or "wdmi" in low or "also" in low:
                score += 0.10
            if "cliente" in low or "v/ contribuinte" in low or "v. contribuinte" in low:
                score -= 0.25
            candidates.append((nif, score))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0]

def extract_header_fields(lines: List[str], raw_text: str) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for line in lines:
        low = line.lower()
        if "factura" in low or "fatura" in low:
            result["document_type"] = {"value": "FACTURA", "confidence": 0.98}
            break
    supplier = infer_supplier_name(lines)
    if supplier:
        result["supplier_name"] = {"value": supplier[0], "confidence": round(supplier[1], 2)}
    invoice_number = infer_invoice_number(lines)
    if invoice_number:
        result["invoice_number"] = {"value": invoice_number[0], "confidence": round(invoice_number[1], 2)}
    result.update(infer_dates(lines))
    customer_nif = find_customer_nif(lines)
    customer_nif_value = None
    if customer_nif:
        customer_nif_value = customer_nif[0]
        result["customer_nif"] = {"value": customer_nif[0], "confidence": round(customer_nif[1], 2)}
    supplier_nif = find_supplier_nif(lines, customer_nif_value)
    if supplier_nif:
        result["supplier_nif"] = {"value": supplier_nif[0], "confidence": round(supplier_nif[1], 2)}
    subtotal = infer_subtotal(lines)
    if subtotal:
        result["subtotal"] = {"value": subtotal[0], "confidence": round(subtotal[1], 2)}
    vat_amount = infer_vat_amount(lines)
    if vat_amount:
        result["vat_amount"] = {"value": vat_amount[0], "confidence": round(vat_amount[1], 2)}
    total = infer_total_document(lines) or infer_best_total(lines)
    if total:
        result["total"] = {"value": total[0], "confidence": round(total[1], 2)}
    subtotal_num = parse_money_value(result.get("subtotal", {}).get("value"))
    vat_num = parse_money_value(result.get("vat_amount", {}).get("value"))
    total_num = parse_money_value(result.get("total", {}).get("value"))
    if subtotal_num is not None and vat_num is not None:
        expected_total = round(subtotal_num + vat_num, 2)
        if total_num is None or abs(total_num - expected_total) > 0.01:
            result["total"] = {"value": format_money_pt(expected_total), "confidence": 0.93}
    if "EUR" in raw_text.upper() or "€" in raw_text:
        result["currency"] = {"value": "EUR", "confidence": 0.95}
    return result

def is_item_header_line(line: str) -> bool:
    low = line.lower()
    return (
        ("código" in low and "designação" in low)
        or ("codigo" in low and "designacao" in low)
        or ("qtd" in low and "iva" in low)
        or ("origem" in low and "código" in low and "designação" in low)
        or ("origem" in low and "codigo" in low and "designacao" in low)
    )


def is_total_or_footer_line(line: str) -> bool:
    low = line.lower().strip()
    stop_terms = [
        "valor liquido",
        "valor líquido",
        "i.v.a.",
        "iva ",
        "iva\t",
        "total documento",
        "pagamento",
        "vencimento",
        "observações",
        "observacoes",
        "atcud",
        "iban",
        "local de carga",
        "local de descarga",
        "válido como recibo",
        "valido como recibo",
        "contrib nº",
        "cliente ",
        "expedição",
        "expedicao",
        "requisição",
        "requisicao",
        "peso picking",
        "pág",
        "pag :",
        "contribuinte",
        "processado por programa certificado",
    ]
    return any(term in low for term in stop_terms)


def is_blocked_admin_line(line: str) -> bool:
    low = line.lower().strip()
    blocked = [
        "factura",
        "fatura",
        "exmos srs",
        "original",
        "duplicado",
        "triplicado",
        "quadruplicado",
        "eur",
        "origem",
        "porto :",
        "lisboa :",
        "cpc",
        "local de carga",
        "local de descarga",
        "observações",
        "observacoes",
        "atcud",
        "dd6 -",
        "v. contribuinte",
        "cliente ",
        "pagamento",
        "expedição",
        "expedicao",
        "total em pte",
    ]
    return any(x in low for x in blocked)


def is_description_candidate(line: str) -> bool:
    s = line.strip()
    low = s.lower()

    if not s or len(s) < 2:
        return False
    if is_total_or_footer_line(s):
        return False
    if is_blocked_admin_line(s):
        return False
    if is_item_header_line(s):
        return False
    if re.fullmatch(r"[\d\s.,€:+/-]+", s):
        return False
    if low in {"un", "iva", "taxa", "valor"}:
        return False

    return True


def is_number_token(tok: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:[.,]\d+)?", tok))


def is_money_token(tok: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:[.,]\d{2,3})", tok))


def is_unit_token(tok: str) -> bool:
    return tok.upper() in {"UN", "UNI", "KG", "G", "L", "LT", "ML", "CX", "PC", "PÇ", "PCA", "ROL", "ROLO"}


def looks_like_code_token(tok: str) -> bool:
    if len(tok) < 2:
        return False
    if not re.fullmatch(r"[A-Z0-9#./_+-]+", tok, re.IGNORECASE):
        return False
    has_letter = bool(re.search(r"[A-Z]", tok, re.IGNORECASE))
    has_digit = bool(re.search(r"\d", tok))
    return has_letter or has_digit


def parse_item_numeric_line(line: str) -> Optional[Dict[str, Any]]:
    compact = re.sub(r"\s+", " ", line).strip()

    p3 = re.match(
        r"^(?P<code>[A-Z0-9./_-]{6,})\s+"
        r"(?P<qty>\d+(?:[.,]\d+)?)\s+"
        r"(?P<unit>[A-Z]{1,5})\s+"
        r"(?P<unit_price>\d+(?:[.,]\d{2,3})?)\s+"
        r"(?P<discount>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<vat_rate>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2}))$",
        compact
    )
    if p3:
        d = p3.groupdict()
        return {
            "type": "item",
            "origin": "",
            "code": d["code"],
            "description": "",
            "qty": d["qty"],
            "unit": d["unit"],
            "unit_price": d["unit_price"],
            "discount": d["discount"],
            "vat_rate": d["vat_rate"],
            "line_total": d["line_total"],
        }

    p2 = re.match(
        r"^(?P<code>[A-Z0-9./_-]{6,})\s+"
        r"(?P<qty>\d+(?:[.,]\d+)?)\s+"
        r"(?P<unit>[A-Z]{1,5})\s+"
        r"(?P<unit_price>\d+(?:[.,]\d{2,3})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2}))$",
        compact
    )
    if p2:
        d = p2.groupdict()
        return {
            "type": "item",
            "origin": "",
            "code": d["code"],
            "description": "",
            "qty": d["qty"],
            "unit": d["unit"],
            "unit_price": d["unit_price"],
            "discount": "",
            "vat_rate": "",
            "line_total": d["line_total"],
        }

    p1 = re.match(
        r"^(?P<code>[A-Z0-9./_-]{6,})\s+"
        r"(?P<qty>\d+(?:[.,]\d+)?)\s+"
        r"(?P<unit_price>\d+(?:[.,]\d{2,3})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2}))$",
        compact
    )
    if p1:
        d = p1.groupdict()
        return {
            "type": "item",
            "origin": "",
            "code": d["code"],
            "description": "",
            "qty": d["qty"],
            "unit": "",
            "unit_price": d["unit_price"],
            "discount": "",
            "vat_rate": "",
            "line_total": d["line_total"],
        }

    return None


def parse_structured_extra_line(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()

    m = re.match(
        r"^(?:(?P<code>[A-Z])\s+)?"
        r"(?P<description>portes|desconto|descontos|ecotaxa|ecotaxas|transporte)\s+"
        r"(?P<discount>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<vat_rate>\d{1,2}(?:[.,]\d{1,2})?)$",
        s,
        re.IGNORECASE
    )
    if not m:
        return None

    d = m.groupdict()

    return {
        "type": "extra",
        "origin": "",
        "code": d.get("code") or "",
        "description": (d.get("description") or "").strip().title(),
        "qty": "",
        "unit": "",
        "unit_price": "",
        "discount": d.get("discount") or "",
        "vat_rate": d.get("vat_rate") or "",
        "line_total": d.get("line_total") or "",
    }


def is_service_period_line(line: str) -> bool:
    low = line.lower().strip()
    return (
        "serviço de" in low
        or "servico de" in low
        or ("até" in low and re.search(r"\d{2}/\d{2}/\d{4}", line))
        or ("ate" in low and re.search(r"\d{2}/\d{2}/\d{4}", line))
    )


def collect_description_before(lines: List[str], idx: int, max_back: int = 6) -> str:
    parts: List[str] = []

    start = max(0, idx - max_back)
    for j in range(start, idx):
        candidate = lines[j].strip()

        if not is_description_candidate(candidate):
            continue
        if parse_item_numeric_line(candidate):
            continue
        if parse_extra_charge_line(candidate, []):
            continue

        parts.append(candidate)

    unique_parts: List[str] = []
    seen = set()
    for p in parts:
        key = p.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        unique_parts.append(p)

    return " ".join(unique_parts).strip()


def find_nearest_money_after(lines: List[str], start_idx: int, max_forward: int = 6) -> Optional[str]:
    for j in range(start_idx + 1, min(len(lines), start_idx + 1 + max_forward)):
        vals = money_candidates_in_line(lines[j])
        if vals:
            return vals[0]
    return None


def enrich_items_with_lonely_amounts(items: List[Dict[str, Any]], lines: List[str]) -> List[Dict[str, Any]]:
    for item in items:
        if item.get("type") != "extra":
            continue
        if item.get("line_total"):
            continue

        desc = item.get("description", "").strip().lower()
        if not desc:
            continue

        for i, line in enumerate(lines):
            if line.strip().lower() == desc:
                for nxt in lines[i + 1:i + 4]:
                    vals = money_candidates_in_line(nxt)
                    if vals:
                        item["line_total"] = vals[0]
                        break
                break

    return items


def find_items_section(lines: List[str]) -> List[str]:
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        low = line.lower()
        if (("código" in low and "designação" in low) or ("codigo" in low and "designacao" in low)
            or ("designação" in low and "qtd" in low) or ("designacao" in low and "qtd" in low)
            or ("qtd" in low and "iva" in low) or ("artigo" in low and "descrição" in low)
            or ("artigo" in low and "descricao" in low) or ("origem" in low and "código" in low and "designação" in low)
            or ("origem" in low and "codigo" in low and "designacao" in low)
            or ("item" in low and "descrição do produto" in low) or ("item" in low and "descricao do produto" in low)
            or ("item" in low and "preço total" in low) or ("item" in low and "preco total" in low)
            or ("referência" in low and "designação" in low and "qtd" in low)
            or ("referencia" in low and "designacao" in low and "qtd" in low)):
            start_idx = i + 1
            break
    if start_idx is None:
        return lines
    for i in range(start_idx, len(lines)):
        low = lines[i].lower()
        if any(term in low for term in [
            "valor liquido", "valor líquido", "subtotal", "total documento", "total a pagar",
            "montante líquido total sem iva", "montante liquido total sem iva", "montante de iva",
            "montante total incluindo iva", "observações", "observacoes", "atcud", "iban",
            "modo de pagamento", "condições de pagamento", "condicoes de pagamento", "vencimento",
            "transportador", "base taxa valor", "modo de expedição", "modo de expedicao",
            "taxa base de incidência", "taxa base de incidencia", "resumo do iva", "mercadoria:",
            "total ilíquido", "total iliquido", "desconto comercial:", "total de i.v.a.", "total:"]):
            end_idx = i
            break
    return lines[start_idx:end_idx] if end_idx is not None else lines[start_idx:]

def is_noise_item_line(line: str) -> bool:
    low = line.lower().strip()
    blocked_contains = [
        "base taxa valor", "montante taxa", "ecotaxas devidas", "não sujeitas a descontos",
        "nao sujeitas a descontos", "início de transporte", "inicio de transporte", "local de carga",
        "local de descarga", "exmos srs", "contribuinte", "v. contribuinte", "cliente", "atcud",
        "iban", "total documento", "valor liquido", "valor líquido", "observações", "observacoes",
        "resumo do iva", "desconto comercial:", "desconto financeiro:", "total de i.v.a.",
        "mercadoria:", "meio de expedição", "meio de expedicao", "entidade ", "referência designação",
        "referencia designacao"
    ]
    if any(x in low for x in blocked_contains):
        return True
    if len(line.strip()) > 110:
        return True
    if re.match(r"^base\s+taxa\s+valor", low):
        return True
    if "ecotaxas devidas para reciclagem" in low:
        return True
    if re.search(r"\bdata\s+\d{4}-\d{2}-\d{2}\b", low):
        return True
    if re.search(r"\blote\b", low) and re.search(r"\bloja\b", low):
        return True
    return False

def is_serial_reference_line(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()

    if re.match(r"^[A-Z0-9]{8,}\s+[A-Z0-9#./_-]{2,}\s+[A-Z0-9_-]{8,}(?:\s+[A-Z0-9_-]{8,})*$", s, re.IGNORECASE):
        return True

    return False


def looks_like_item_candidate(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()
    if not s or len(s) < 8:
        return False
    if is_item_header_line(s) or is_total_or_footer_line(s) or is_noise_item_line(s) or is_serial_reference_line(s) or is_group_header_line(s):
        return False
    if re.search(r"\d+(?:[.,]\d+)?\s+(?:UN|UNI|KG|G|L|LT|ML|CX|PC|PÇ|PCA|ROL|ROLO)\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{2,3})\s*$", s, re.IGNORECASE):
        return True
    if re.search(r"\d+(?:[.,]\d+)?[A-Z]{1,5}\s+\d+(?:[.,]\d{2,3})(?:\s+\d+(?:[.,]\d{2,3})){2,4}\s*$", s, re.IGNORECASE):
        return True
    if re.search(r"\d+(?:[.,]\d+)?\s+(?:UN|UNI|KG|G|L|LT|ML|CX|PC|PÇ|PCA|ROL|ROLO)\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{1,2})\s+\d+(?:[.,]\d{2})\s*$", s, re.IGNORECASE):
        return True
    if re.search(r"\d+(?:[.,]\d{2})\s+\d{1,2}(?:[.,]\d{1,2})?\s*$", s):
        return True
    if re.search(r"\b\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{2})\s*$", s):
        return True
    return False

def parse_generic_item_line(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 6:
        return None
    i = len(parts) - 1
    if i < 0 or not re.fullmatch(r"\d{1,2}(?:[.,]\d{1,2})?", parts[i]):
        return None
    vat_rate = parts[i]
    i -= 1
    if i < 0 or not is_money_token(parts[i]):
        return None
    line_total = parts[i]
    i -= 1
    if i < 0 or not is_money_token(parts[i]):
        return None
    discount = parts[i]
    i -= 1
    if i < 0 or not is_money_token(parts[i]):
        return None
    unit_price = parts[i]
    i -= 1
    if i < 0:
        return None
    q, u = split_attached_unit_token(parts[i])
    if q and u:
        qty, unit = q, u
        i -= 1
    elif i >= 1 and is_unit_token(parts[i]) and is_number_token(parts[i-1]):
        qty, unit = parts[i-1], parts[i].upper()
        i -= 2
    else:
        return None
    left = parts[:i + 1]
    if not left:
        return None
    code = left[0] if looks_like_code_token(left[0]) else ""
    description_tokens = left[1:] if code else left[:]
    origin = ""
    if description_tokens and re.fullmatch(r"[A-Z]{2,8}", description_tokens[0], re.IGNORECASE):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": unit, "unit_price": unit_price, "discount": discount, "vat_rate": vat_rate, "line_total": line_total}

def is_description_continuation_line(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()
    low = s.lower()
    if not s:
        return False
    if is_item_header_line(s) or is_total_or_footer_line(s) or is_noise_item_line(s):
        return False
    if looks_like_item_candidate(s) or parse_structured_extra_line(s) or is_serial_reference_line(s):
        return False
    if len(s) > 90 or re.fullmatch(r"[\d\s.,€:+/-]+", s):
        return False
    if re.fullmatch(r"[A-Za-zÀ-ÿ.-]+", s) and len(s.split()) <= 3:
        return False
    blocked = ["n.º de peça do fabricante", "n.o de peça do fabricante", "nº de peça do fabricante", "code ean/upc", "ean/upc", "remessa", "encomenda", "modo de expedição", "modo de expedicao", "incoterm", "disponibilizado em", "loja b", "faro", "portugal", "fatura", "duplicado", "original", "cliente:", "nr. doc.:", "licenciado a:", "valor em falta", "o próximo escalão", "facturas à cobrança", "facturas à cobranca", "software phc", "material usado/recondicionado", "o 3º ano de garantia", "pagamento por multibanco"]
    if any(x in low for x in blocked):
        return False
    return True

def split_attached_unit_token(tok: str) -> Tuple[Optional[str], Optional[str]]:
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)([A-Z]{1,5})", tok, re.IGNORECASE)
    if not m:
        return None, None
    return m.group(1), m.group(2).upper()

def is_group_header_line(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()
    if re.match(r"^ECR-[A-Z0-9/.-]+\s+\(\d{2}/\d{2}/\d{4}\)\s+-\s+\d+", s, re.IGNORECASE):
        return True
    if re.match(r"^ref\.\s+ao\s+doc\.", s, re.IGNORECASE):
        return True
    if re.match(r"^nota\s+encomenda\s+cliente", s, re.IGNORECASE):
        return True
    return False

def parse_generic_item_line_with_rowno(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 7:
        return None
    if not is_money_token(parts[-1]):
        return None
    row_no = parts[-1]
    row_val = parse_money_value(row_no)
    if row_val is None or row_val <= 0 or row_val > 200 or abs(row_val - round(row_val)) > 0.001:
        return None
    q, u = split_attached_unit_token(parts[-5]) if len(parts) >= 5 else (None, None)
    if not (q and u):
        return None
    if not is_money_token(parts[-4]) or not is_money_token(parts[-3]) or not is_money_token(parts[-2]):
        return None
    qty, unit = q, u
    unit_price = parts[-4]
    discount = parts[-3]
    line_total = parts[-2]
    left = parts[:-5]
    if len(left) < 2:
        return None
    code = left[0]
    if not looks_like_code_token(code):
        return None
    origin = ""
    description_tokens = left[1:]
    if description_tokens and re.fullmatch(r"[A-Z]{2,6}", description_tokens[0], re.IGNORECASE):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": unit, "unit_price": unit_price, "discount": discount, "vat_rate": "", "line_total": line_total, "line_no": row_no}

def parse_generic_item_line_with_vat_before_total(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 7:
        return None
    if not is_money_token(parts[-1]) or not re.fullmatch(r"\d{1,2}(?:[.,]\d{1,2})?", parts[-2]) or not is_money_token(parts[-3]):
        return None
    line_total = parts[-1]
    vat_rate = parts[-2]
    unit_price = parts[-3]
    if len(parts) < 5 or not is_unit_token(parts[-4]) or not is_number_token(parts[-5]):
        return None
    qty = parts[-5]
    unit = parts[-4].upper()
    left = parts[:-5]
    if len(left) < 2:
        return None
    code = left[0] if looks_like_code_token(left[0]) else ""
    description_tokens = left[1:] if code else left[:]
    origin = ""
    if description_tokens and re.fullmatch(r"[A-Z]{2,8}", description_tokens[0], re.IGNORECASE):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": unit, "unit_price": unit_price, "discount": "", "vat_rate": vat_rate, "line_total": line_total}


def parse_extra_charge_line(line: str, next_lines: List[str]) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    low = s.lower()
    if is_noise_item_line(s):
        return None
    structured = parse_structured_extra_line(s)
    if structured:
        return structured
    labels = ["portes", "desconto", "descontos", "ecotaxa", "ecotaxas", "transporte"]
    if not any(label in low for label in labels):
        return None
    if len(s) > 60:
        return None
    if any(x in low for x in ["base taxa", "montante taxa", "valor eur", "desconto comercial", "desconto financeiro"]):
        return None
    vals = money_candidates_in_line(s)
    if vals:
        desc = s
        desc = re.sub(r"\s+\d+(?:[.,]\d{2})?\s+\d+(?:[.,]\d{2})?\s+\d{1,2}(?:[.,]\d{1,2})?$", "", desc).strip()
        desc = re.sub(r"^[A-Z]\s+", "", desc).strip()
        return {"type": "extra", "origin": "", "code": "", "description": desc, "qty": "", "unit": "", "unit_price": "", "discount": "", "vat_rate": "", "line_total": vals[-1]}
    for nxt in next_lines[:2]:
        if is_noise_item_line(nxt):
            continue
        vals = money_candidates_in_line(nxt)
        if vals:
            return {"type": "extra", "origin": "", "code": "", "description": s, "qty": "", "unit": "", "unit_price": "", "discount": "", "vat_rate": "", "line_total": vals[0]}
    return None

def extract_item_lines(lines: List[str]) -> List[Dict[str, Any]]:
    section = find_items_section(lines)
    items: List[Dict[str, Any]] = []
    used_keys = set()
    last_item_idx: Optional[int] = None
    for idx, line in enumerate(section):
        s = re.sub(r"\s+", " ", line).strip()
        low = s.lower()
        if not s:
            continue
        if is_item_header_line(s) or is_total_or_footer_line(s) or is_noise_item_line(s) or is_serial_reference_line(s):
            continue
        if low.startswith("transportado da página anterior") or low.startswith("transportado da pagina anterior") or low.startswith("transporte para a página seguinte") or low.startswith("transporte para a pagina seguinte"):
            continue
        if is_group_header_line(s):
            continue
        if looks_like_item_candidate(s):
            item = parse_generic_item_line_with_rowno(s)
            if not item:
                item = parse_generic_item_line(s)
            if not item:
                item = parse_generic_item_line_with_vat_before_total(s)
            if not item:
                item = parse_generic_item_line_simple(s)
            if item:
                key = (item.get("code", ""), item.get("description", ""), item.get("qty", ""), item.get("line_total", ""))
                if key not in used_keys:
                    used_keys.add(key)
                    items.append(item)
                    last_item_idx = len(items) - 1
                continue
        parsed = parse_item_numeric_line(s)
        if parsed:
            desc = collect_description_before(section, idx, max_back=3)
            if is_noise_item_line(desc):
                desc = ""
            parsed["description"] = desc
            key = (parsed.get("type", ""), parsed.get("code", ""), parsed.get("description", ""), parsed.get("line_total", ""))
            if key not in used_keys:
                used_keys.add(key)
                items.append(parsed)
                last_item_idx = len(items) - 1
            continue
        if is_service_period_line(s):
            service_item = {"type": "service", "origin": "", "code": "", "description": s, "qty": "1", "unit": "", "unit_price": "", "discount": "", "vat_rate": "", "line_total": ""}
            key = (service_item["type"], service_item["description"])
            if key not in used_keys:
                used_keys.add(key)
                items.append(service_item)
                last_item_idx = len(items) - 1
            continue
        if not items or ("portes" in low or low.startswith("desconto ") or low.startswith("descontos ")):
            extra = parse_extra_charge_line(s, section[idx + 1: idx + 3])
            if extra:
                key = (extra.get("type", ""), extra.get("description", ""), extra.get("line_total", ""))
                if key not in used_keys:
                    used_keys.add(key)
                    items.append(extra)
                    last_item_idx = len(items) - 1
                continue
        if is_description_continuation_line(s) and last_item_idx is not None and items[last_item_idx].get("type") == "item":
            prev = items[last_item_idx].get("description", "").strip()
            if s.lower() not in prev.lower():
                items[last_item_idx]["description"] = (prev + " " + s).strip()
            continue
    items = enrich_items_with_lonely_amounts(items, section)
    cleaned: List[Dict[str, Any]] = []
    for item in items:
        desc = item.get("description", "").strip().lower()
        if not desc:
            continue
        if is_noise_item_line(desc):
            continue
        if desc in {"base taxa valor", "base taxa valor eur", "descarga transporte"}:
            continue
        cleaned.append(item)
    return cleaned

@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return INDEX_HTML


@app.get("/extract")
def extract_info():
    return {"message": "Este endpoint aceita apenas POST com um ficheiro PDF no campo 'file'. Usa a interface em /."}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Só PDFs são suportados."}
        )

    data = await file.read()
    raw_text, extraction_mode = extract_text_from_pdf_bytes(data)

    if not raw_text:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Não foi possível extrair texto. Este PDF pode ser um scan/imagem. O próximo passo é adicionar OCR local como fallback."
            }
        )

    cleaned_lines, removed_repeated_lines = cleanup_lines(raw_text)
    cleaned_lines = join_broken_label_lines(cleaned_lines)
    cleaned_text = "\n".join(cleaned_lines)

    header = extract_header_fields(cleaned_lines, cleaned_text)
    items = extract_item_lines(cleaned_lines)

    return {
        "filename": file.filename,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "line_count": len(cleaned_lines),
        "removed_repeated_lines": removed_repeated_lines,
        "extraction_mode": extraction_mode,
        "header": header,
        "items": items,
    }


