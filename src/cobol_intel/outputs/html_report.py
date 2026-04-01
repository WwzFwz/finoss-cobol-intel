"""Self-contained HTML report generator with embedded CSS and Mermaid JS."""

from __future__ import annotations

from cobol_intel.contracts.graph_output import CallGraphOutput
from cobol_intel.contracts.manifest import Manifest
from cobol_intel.outputs.doc_generator import ProgramDocumentation

_CSS = (  # noqa: E501 — embedded CSS, line length not meaningful
    ":root{--bg:#f8f9fa;--card:#fff;--border:#dee2e6;"
    "--primary:#0d6efd;--text:#212529;--muted:#6c757d}"
    "*{box-sizing:border-box;margin:0;padding:0}"
    "body{font-family:-apple-system,BlinkMacSystemFont,"
    "'Segoe UI',Roboto,sans-serif;background:var(--bg);"
    "color:var(--text);line-height:1.6}"
    ".container{max-width:1200px;margin:0 auto;"
    "padding:24px;display:flex;gap:24px}"
    "nav.sidebar{position:sticky;top:24px;width:260px;"
    "flex-shrink:0;height:fit-content;"
    "background:var(--card);border:1px solid var(--border);"
    "border-radius:8px;padding:16px}"
    "nav.sidebar h3{font-size:14px;text-transform:uppercase;"
    "color:var(--muted);margin-bottom:8px;letter-spacing:.5px}"
    "nav.sidebar ul{list-style:none}"
    "nav.sidebar li{margin-bottom:4px}"
    "nav.sidebar a{color:var(--primary);"
    "text-decoration:none;font-size:14px}"
    "nav.sidebar a:hover{text-decoration:underline}"
    "nav.sidebar input{width:100%;padding:6px 10px;"
    "border:1px solid var(--border);border-radius:4px;"
    "font-size:14px;margin-bottom:12px}"
    "main{flex:1;min-width:0}"
    ".card{background:var(--card);"
    "border:1px solid var(--border);border-radius:8px;"
    "padding:24px;margin-bottom:24px}"
    "h1{font-size:28px;margin-bottom:16px}"
    "h2{font-size:22px;margin-bottom:12px;"
    "border-bottom:2px solid var(--border);padding-bottom:6px}"
    "h3{font-size:18px;margin:16px 0 8px}"
    "table{width:100%;border-collapse:collapse;"
    "font-size:14px;margin:12px 0}"
    "th{background:var(--bg);text-align:left;"
    "padding:8px 12px;border:1px solid var(--border);"
    "font-weight:600}"
    "td{padding:8px 12px;border:1px solid var(--border)}"
    "tr:hover{background:#f0f6ff}"
    ".badge{display:inline-block;padding:2px 8px;"
    "border-radius:12px;font-size:12px;font-weight:600}"
    ".badge-ok{background:#d1e7dd;color:#0f5132}"
    ".badge-warn{background:#fff3cd;color:#664d03}"
    ".badge-err{background:#f8d7da;color:#842029}"
    ".meta{color:var(--muted);font-size:14px}"
    "ul.dep-list{list-style:none;padding-left:0}"
    "ul.dep-list li::before{content:'→ ';"
    "color:var(--primary);font-weight:bold}"
    "details{margin:8px 0}"
    "details summary{cursor:pointer;"
    "font-weight:600;padding:8px 0}"
    "details[open] summary{margin-bottom:8px}"
    ".mermaid{background:var(--card);padding:16px;"
    "border-radius:8px;text-align:center}"
    "code{background:#e9ecef;padding:2px 6px;"
    "border-radius:4px;font-size:13px}"
    "p{margin:6px 0}"
)

_JS = """
function filterPrograms() {
  var q = document.getElementById('search').value.toLowerCase();
  var items = document.querySelectorAll('.program-section');
  var links = document.querySelectorAll('.nav-link');
  items.forEach(function(el) {
    el.style.display = el.dataset.pid.toLowerCase().includes(q) ? '' : 'none';
  });
  links.forEach(function(el) {
    el.parentElement.style.display = el.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}
"""


def render_html_report(
    manifest: Manifest,
    program_docs: list[ProgramDocumentation],
    call_graph: CallGraphOutput | None = None,
) -> str:
    """Render a self-contained HTML report from analysis artifacts."""
    status_badge = _status_badge(manifest.status.value)
    nav_items = "\n".join(
        f'<li><a class="nav-link" href="#prog-{_slug(d.program_id)}">{_esc(d.program_id)}</a></li>'
        for d in program_docs
    )

    summary_rows = [
        ("Run ID", f"<code>{_esc(manifest.run_id)}</code>"),
        ("Status", status_badge),
        ("Programs", str(len(program_docs))),
        ("Warnings", str(len(manifest.warnings))),
        ("Errors", str(len(manifest.errors))),
    ]
    if manifest.governance.approved_backend:
        summary_rows.append(("Backend", _esc(manifest.governance.approved_backend)))
    if manifest.governance.token_usage.total_tokens:
        summary_rows.append(("Tokens", str(manifest.governance.token_usage.total_tokens)))

    summary_html = "\n".join(
        f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>" for k, v in summary_rows
    )

    mermaid_section = ""
    if call_graph and call_graph.edges:
        mermaid_code = call_graph.to_mermaid()
        mermaid_section = f"""
        <div class="card">
            <h2>Call Graph</h2>
            <div class="mermaid">{_esc(mermaid_code)}</div>
        </div>
        """

    program_sections = "\n".join(
        _render_program_section(doc) for doc in program_docs
    )

    inventory_rows = "".join(
        f'<tr><td><a href="#prog-{_slug(d.program_id)}">'
        f'{_esc(d.program_id)}</a></td>'
        f'<td><code>{_esc(d.file_path)}</code></td></tr>'
        for d in program_docs
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>cobol-intel Report — {_esc(manifest.project_name)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
    <nav class="sidebar">
        <h3>Programs</h3>
        <input type="text" id="search" placeholder="Filter..." oninput="filterPrograms()">
        <ul>{nav_items}</ul>
    </nav>
    <main>
        <div class="card">
            <h1>Project Report: {_esc(manifest.project_name)}</h1>
            <table>{summary_html}</table>
        </div>

        {mermaid_section}

        <div class="card">
            <h2>Program Inventory</h2>
            <table>
                <thead><tr><th>Program</th><th>File</th></tr></thead>
                <tbody>
                {inventory_rows}
                </tbody>
            </table>
        </div>

        {program_sections}
    </main>
</div>
<script>{_JS}</script>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
</script>
</body>
</html>"""


def _render_program_section(doc: ProgramDocumentation) -> str:
    """Convert a ProgramDocumentation's markdown into an HTML card section."""
    pid = doc.program_id
    slug = _slug(pid)

    # Parse markdown into simple HTML sections
    sections: list[str] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in doc.markdown.split("\n"):
        if line.startswith("# "):
            # Top-level heading — skip, we use our own
            if current_lines:
                sections.append(_render_md_block(current_heading, current_lines))
                current_lines = []
            current_heading = ""
        elif line.startswith("## "):
            if current_lines:
                sections.append(_render_md_block(current_heading, current_lines))
            current_heading = line[3:].strip()
            current_lines = []
        elif line.startswith("### "):
            current_lines.append(f"<h3>{_esc(line[4:].strip())}</h3>")
        elif line.startswith("| "):
            current_lines.append(_md_table_row_to_html(line))
        elif line.startswith("|---"):
            continue  # Skip table separator
        elif line.startswith("- **"):
            # Bold list item
            text = line[2:]
            html_text = text.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            current_lines.append(f"<li>{html_text}</li>")
        elif line.startswith("- `"):
            current_lines.append(f"<li>{_inline_code(line[2:])}</li>")
        elif line.startswith("- "):
            current_lines.append(f"<li>{_esc(line[2:])}</li>")
        elif line.startswith("```mermaid"):
            current_lines.append('<div class="mermaid">')
        elif line.startswith("```"):
            if current_lines and current_lines[-1] != '<div class="mermaid">':
                current_lines.append("</div>")
        elif line.strip():
            current_lines.append(f"<p>{_inline_code(_esc(line))}</p>")

    if current_lines:
        sections.append(_render_md_block(current_heading, current_lines))

    body = "\n".join(sections)
    return f"""
    <div class="card program-section" id="prog-{slug}" data-pid="{_esc(pid)}">
        <h2>{_esc(pid)}</h2>
        {body}
    </div>"""


def _render_md_block(heading: str, lines: list[str]) -> str:
    content = "\n".join(lines)
    has_table = any("<td>" in ln or "<th>" in ln for ln in lines)
    has_list = any("<li>" in ln for ln in lines)

    if has_table:
        rows = [ln for ln in lines if "<td>" in ln or "<th>" in ln]
        non_rows = [ln for ln in lines if "<td>" not in ln and "<th>" not in ln]
        table_html = "<table>\n" + "\n".join(rows) + "\n</table>"
        content = "\n".join(non_rows) + "\n" + table_html
    if has_list:
        list_items = [ln for ln in lines if "<li>" in ln]
        non_list = [ln for ln in lines if "<li>" not in ln]
        list_html = "<ul class='dep-list'>\n" + "\n".join(list_items) + "\n</ul>"
        content = "\n".join(non_list) + "\n" + list_html

    if heading:
        return f"<details open><summary>{_esc(heading)}</summary>\n{content}\n</details>"
    return content


def _md_table_row_to_html(line: str) -> str:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    tag = "th" if all(c.startswith("**") for c in cells if c) else "td"
    cell_html = "".join(f"<{tag}>{_inline_code(_esc(c.strip('*')))}</{tag}>" for c in cells)
    return f"<tr>{cell_html}</tr>"


def _inline_code(text: str) -> str:
    """Convert backtick-wrapped text to <code> elements."""
    parts = text.split("`")
    result: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(f"<code>{part}</code>")
        else:
            result.append(part)
    return "".join(result)


def _status_badge(status: str) -> str:
    if status == "completed":
        cls = "badge-ok"
    elif status == "partial":
        cls = "badge-warn"
    else:
        cls = "badge-err"
    return f'<span class="badge {cls}">{_esc(status)}</span>'


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )
