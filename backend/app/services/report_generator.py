"""
Report Generator - Araştırma sonuçlarını farklı formatlara dönüştürür.
Markdown → HTML → PDF zinciri ve JSON ham çıktı.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from loguru import logger
import markdown2

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

JINJA_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ language }}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} - Nova Nexus Search</title>
<style>
  :root { --accent: #00d4ff; --bg: #0a0e1a; --surface: #111827; --text: #e2e8f0; --border: #1e293b; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; line-height: 1.8; padding: 40px; }
  .report-header { border-left: 4px solid var(--accent); padding: 20px 30px; background: var(--surface); border-radius: 8px; margin-bottom: 32px; }
  .report-header h1 { color: var(--accent); font-size: 1.8rem; margin-bottom: 8px; }
  .meta-tag { display: inline-block; background: #1e3a5f; color: var(--accent); padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; margin: 3px; }
  .warning-box { background: #1a1a00; border: 1px solid #ffa500; border-radius: 8px; padding: 16px; margin: 20px 0; }
  .warning-box p { color: #ffa500; }
  .section { background: var(--surface); border-radius: 8px; border: 1px solid var(--border); padding: 24px; margin: 20px 0; }
  .section h2 { color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 16px; font-size: 1.2rem; }
  .reliability-badge { display: inline-block; padding: 4px 16px; border-radius: 20px; font-weight: bold; }
  .score-high { background: #0d3321; color: #4ade80; }
  .score-med { background: #2d2000; color: #fbbf24; }
  .score-low { background: #2d0000; color: #f87171; }
  .source-item { border-left: 3px solid var(--accent); padding: 8px 16px; margin: 8px 0; background: #0d1117; border-radius: 4px; }
  .source-item a { color: var(--accent); text-decoration: none; }
  .source-item a:hover { text-decoration: underline; }
  .content-body h1, .content-body h2, .content-body h3 { color: var(--accent); margin: 16px 0 8px; }
  .content-body ul, .content-body ol { padding-left: 20px; }
  .content-body li { margin: 4px 0; }
  .content-body blockquote { border-left: 3px solid var(--accent); padding-left: 16px; color: #94a3b8; }
  .footer { text-align: center; color: #4b5563; font-size: 0.8rem; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); }
</style>
</head>
<body>
<div class="report-header">
  <h1>🔭 Nova Nexus Search — Araştırma Raporu</h1>
  <p>{{ title }}</p>
  <div style="margin-top: 12px">
    <span class="meta-tag">📅 {{ date }}</span>
    <span class="meta-tag">🌐 {{ depth }} araştırma</span>
    <span class="meta-tag">📚 {{ source_count }} kaynak tarandı</span>
    <span class="meta-tag">✅ {{ reliable_count }} güvenilir kaynak</span>
  </div>
</div>

<div class="warning-box">
  <p>⚠️ <strong>Sorumluluk Reddi:</strong> Bu rapor yapay zeka tarafından otomatik olarak oluşturulmuştur. Bilgilerin doğruluğu kullanıcı tarafından teyit edilmelidir. Kaynaklar listelenmiştir, lütfen kontrol ediniz.</p>
</div>

<div class="section">
  <h2>🛡️ Güvenilirlik Analizi (Çapraz Doğrulama)</h2>
  <p>
    Güvenilirlik Skoru:
    <span class="reliability-badge {{ score_class }}">{{ reliability_score }}/10 — {{ hallucination_risk }}</span>
  </p>
  {% if unsupported_claims %}<p style="margin-top:12px"><strong>⚠️ Desteksiz İddialar:</strong></p>
  <ul>{% for claim in unsupported_claims %}<li>{{ claim }}</li>{% endfor %}</ul>{% endif %}
  {% if contradictions %}<p style="margin-top:8px"><strong>🔴 Çelişkiler:</strong></p>
  <ul>{% for c in contradictions %}<li>{{ c }}</li>{% endfor %}</ul>{% endif %}
  <p style="margin-top:12px; color:#94a3b8"><em>{{ verdict }}</em></p>
</div>

<div class="section">
  <h2>📊 Araştırma Bulguları</h2>
  <div class="content-body">{{ synthesis_html }}</div>
</div>

<div class="section">
  <h2>📚 Kaynaklar ({{ source_count }} Toplam)</h2>
  {% for doc in sources %}
  <div class="source-item">
    <strong>[{{ loop.index }}]</strong>
    <a href="{{ doc.url }}" target="_blank">{{ doc.title }}</a>
    {% if doc.relevance_score %}
    <span class="meta-tag">Alaka: {{ doc.relevance_score }}/10</span>
    {% endif %}
  </div>
  {% endfor %}
</div>

<div class="footer">
  <p>Nova Nexus Search • Yapay Zeka Destekli Araştırma Platformu • {{ date }}</p>
</div>
</body>
</html>"""


class ReportGenerator:
    def generate_markdown(self, research_result: dict) -> str:
        query = research_result.get("query", "Araştırma")
        synthesis = research_result.get("synthesis", "")
        validation = research_result.get("validation", {})
        documents = research_result.get("documents", [])
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        md = f"""# 🔭 Nova Nexus Search — Araştırma Raporu
**Konu:** {query}
**Tarih:** {now}
**Derinlik:** {research_result.get('depth', 'medium')}
**Taranan Kaynak:** {research_result.get('source_count', 0)} / Güvenilir: {research_result.get('reliable_source_count', 0)}

---
> ⚠️ **Sorumluluk Reddi:** Bu rapor yapay zeka tarafından otomatik olarak oluşturulmuştur. Bilgilerin doğruluğu kullanıcı tarafından teyit edilmelidir.

---

## 🛡️ Güvenilirlik Analizi
- **Skor:** {validation.get('reliability_score', 'N/A')}/10
- **Halüsinasyon Riski:** {validation.get('hallucination_risk', 'N/A')}
- **Değerlendirme:** {validation.get('verdict', '')}

"""
        if validation.get("unsupported_claims"):
            md += "### ⚠️ Desteksiz İddialar\n"
            for claim in validation["unsupported_claims"]:
                md += f"- {claim}\n"
            md += "\n"

        if validation.get("contradictions"):
            md += "### 🔴 Çelişkiler\n"
            for c in validation["contradictions"]:
                md += f"- {c}\n"
            md += "\n"

        md += f"""---

## 📊 Araştırma Bulguları

{synthesis}

---

## 📚 Kaynaklar

"""
        for i, doc in enumerate(documents, 1):
            score = doc.get('relevance_score', '')
            score_str = f" | Alaka: {score}/10" if score else ""
            md += f"{i}. [{doc['title']}]({doc['url']}){score_str}\n"

        return md

    def generate_html(self, research_result: dict) -> str:
        from jinja2 import Template
        validation = research_result.get("validation", {})
        documents = research_result.get("documents", [])
        synthesis = research_result.get("synthesis", "")
        synthesis_html = markdown2.markdown(synthesis, extras=["fenced-code-blocks", "tables"])

        score = validation.get('reliability_score', 5)
        score_class = "score-high" if score >= 7 else "score-med" if score >= 4 else "score-low"

        template = Template(JINJA_TEMPLATE)
        return template.render(
            title=research_result.get("query", "Araştırma"),
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            depth=research_result.get("depth", "medium"),
            language=research_result.get("language", "tr"),
            source_count=research_result.get("source_count", 0),
            reliable_count=research_result.get("reliable_source_count", 0),
            synthesis_html=synthesis_html,
            reliability_score=score,
            hallucination_risk=validation.get("hallucination_risk", "N/A"),
            unsupported_claims=validation.get("unsupported_claims", []),
            contradictions=validation.get("contradictions", []),
            verdict=validation.get("verdict", ""),
            score_class=score_class,
            sources=documents,
        )

    def generate_json(self, research_result: dict) -> str:
        return json.dumps(research_result, ensure_ascii=False, indent=2)

    def save_report(self, research_result: dict, formats: list = None) -> dict:
        if formats is None:
            formats = ["md", "html", "json"]

        query_slug = re.sub(r'[^\w\s-]', '', research_result.get("query", "report"))
        query_slug = re.sub(r'\s+', '_', query_slug)[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{query_slug}_{timestamp}"
        
        saved = {}

        if "md" in formats:
            md_content = self.generate_markdown(research_result)
            md_path = REPORTS_DIR / f"{base_name}.md"
            md_path.write_text(md_content, encoding="utf-8")
            saved["markdown"] = str(md_path)

        if "html" in formats:
            html_content = self.generate_html(research_result)
            html_path = REPORTS_DIR / f"{base_name}.html"
            html_path.write_text(html_content, encoding="utf-8")
            saved["html"] = str(html_path)

        if "json" in formats:
            json_content = self.generate_json(research_result)
            json_path = REPORTS_DIR / f"{base_name}.json"
            json_path.write_text(json_content, encoding="utf-8")
            saved["json"] = str(json_path)

        if "pdf" in formats:
            try:
                from xhtml2pdf import pisa
                html_content = self.generate_html(research_result)
                pdf_path = REPORTS_DIR / f"{base_name}.pdf"
                
                with open(str(pdf_path), "w+b") as result_file:
                    pisa_status = pisa.CreatePDF(html_content, dest=result_file)
                
                if pisa_status.err:
                    logger.warning(f"PDF generation encountered errors: {pisa_status.err}")
                    saved["pdf"] = None
                else:
                    saved["pdf"] = str(pdf_path)
            except Exception as e:
                logger.warning(f"PDF generation failed: {e}")
                saved["pdf"] = None

        return saved
