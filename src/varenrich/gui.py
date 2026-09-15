"""Local-only graphical interface for CMHS VarEnrich."""

from __future__ import annotations

import json
import secrets
import shutil
import threading
import webbrowser
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from . import __version__
from .analysis import enrich
from .io import filter_variants, read_gene_list, read_gene_sets, read_variant_table, read_vcf
from .report import write_html_report, write_results_tsv, write_svg_figures, write_variants_tsv

MAX_UPLOAD_BYTES = 250 * 1024 * 1024


def _page(token: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>CMHS VarEnrich</title>
<style>
:root{{--ink:#142b3a;--teal:#087f8c;--deep:#073b4c;--gold:#e29a2d;--wash:#eef6f5}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);font:15px/1.5 system-ui;color:var(--ink)}}
header{{padding:38px max(5vw,22px);color:white;background:linear-gradient(120deg,var(--deep),var(--teal))}}
header h1{{margin:0}}main{{max-width:940px;margin:-22px auto 40px;padding:0 20px}}
.panel{{background:white;padding:24px;border-radius:15px;box-shadow:0 8px 26px #092f4117}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:17px}}
label{{display:block;font-weight:650}}small{{display:block;color:#617681;margin:4px 0 7px}}
input,select{{width:100%;padding:10px;border:1px solid #adc3c7;border-radius:8px}}
.checks label{{font-weight:400;display:flex;align-items:center;gap:8px}}.checks input{{width:auto}}
button{{border:0;border-radius:9px;padding:12px 20px;background:var(--teal);color:white;font-weight:700;cursor:pointer}}
button:disabled{{opacity:.55}}#status{{margin-top:18px;padding:13px;background:#f4f8f8;border-radius:8px;white-space:pre-wrap}}
.notice{{border-left:4px solid var(--gold);padding-left:12px}}a{{color:var(--teal)}}
</style></head><body><header><h1>CMHS VarEnrich</h1><p>Rare-variant enrichment and visual evidence, entirely on this computer.</p></header>
<main><form class="panel" id="analysis"><div class="grid">
<label>Query file<small>Gene list, CSV/TSV variant table, annotated VCF, or VCF.GZ</small><input type="file" name="query" required></label>
<label>Background universe<small>Every gene that could have been selected; one symbol per line</small><input type="file" name="universe" required></label>
<label>Annotation collection<small>GO/pathway/disease gene sets in GMT format</small><input type="file" name="gene_sets" required></label>
<label>Report title<small>Shown at the top of the exported report</small><input name="title" value="CMHS VarEnrich Report"></label>
<label>Minimum variant QUAL<small>Leave blank to retain missing/any QUAL</small><input name="min_quality" type="number" step="any"></label>
<label>Maximum allele frequency<small>Example: 0.01 for variants at or below 1%</small><input name="max_af" type="number" min="0" max="1" step="any"></label>
</div><div class="checks"><label><input name="pass_only" type="checkbox"> Retain only PASS variants</label></div>
<p class="notice">Patient data is processed locally and not transmitted. The background universe controls the statistical question. For a panel, use adequately tested panel genes—not the whole genome.</p>
<button id="run">Run analysis</button><div id="status" role="status">Ready. No files have been uploaded anywhere.</div></form></main>
<script>
const form=document.getElementById('analysis'),status=document.getElementById('status'),button=document.getElementById('run');
form.addEventListener('submit',async e=>{{e.preventDefault();button.disabled=true;status.textContent='Analysing locally…';
try{{let response=await fetch('/{token}/api/analyse',{{method:'POST',body:new FormData(form)}}),data=await response.json();
if(!response.ok)throw new Error(data.error||'Analysis failed');status.innerHTML=`Complete: ${{data.query_size}} genes, ${{data.results}} tested terms.<br><a target="_blank" href="${{data.report_url}}">Open interactive report</a><br>Saved to: ${{data.output_directory}}`;}}
catch(error){{status.textContent='Error: '+error.message}}finally{{button.disabled=false}}}});
</script></body></html>"""


def _multipart_fields(body: bytes, content_type: str) -> dict[str, tuple[str, bytes] | str]:
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
    )
    fields: dict[str, tuple[str, bytes] | str] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        fields[name] = (filename or "upload", payload) if filename else payload.decode("utf-8")
    return fields


def _save_upload(field: tuple[str, bytes], directory: Path, safe_name: str) -> Path:
    filename, content = field
    suffixes = "".join(Path(filename).suffixes[-2:])
    path = directory / f"{safe_name}{suffixes}"
    path.write_bytes(content)
    return path


def create_server(output_root: Path | None = None) -> tuple[ThreadingHTTPServer, str]:
    token = secrets.token_urlsafe(24)
    root = output_root or Path.home() / "Documents" / "CMHS-VarEnrich-Results"
    root.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        server_version = f"CMHS-VarEnrich/{__version__}"

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, data: dict[str, object]) -> None:
            self._send(status, "application/json; charset=utf-8", json.dumps(data).encode())

        def do_GET(self) -> None:
            path = unquote(urlsplit(self.path).path)
            if path in {"/", f"/{token}"}:
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", f"/{token}/")
                self.end_headers()
                return
            if path == f"/{token}/":
                self._send(HTTPStatus.OK, "text/html; charset=utf-8", _page(token).encode())
                return
            prefix = f"/{token}/results/"
            if path.startswith(prefix):
                relative = Path(path[len(prefix) :])
                candidate = (root / relative).resolve()
                if root.resolve() not in candidate.parents or not candidate.is_file():
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                content_type = (
                    "text/html; charset=utf-8" if candidate.suffix == ".html" else "image/svg+xml"
                )
                self._send(HTTPStatus.OK, content_type, candidate.read_bytes())
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if urlsplit(self.path).path != f"/{token}/api/analyse":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_UPLOAD_BYTES:
                    raise ValueError("Upload is empty or exceeds the 250 MB local limit")
                fields = _multipart_fields(
                    self.rfile.read(length), self.headers.get("Content-Type", "")
                )
                required = ("query", "universe", "gene_sets")
                if any(not isinstance(fields.get(name), tuple) for name in required):
                    raise ValueError("Query, universe, and annotation files are required")
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
                job = f"analysis-{stamp}-{secrets.token_hex(3)}"
                destination = root / job
                uploads = destination / "inputs"
                uploads.mkdir(parents=True)
                query_path = _save_upload(fields["query"], uploads, "query")  # type: ignore[arg-type]
                universe_path = _save_upload(fields["universe"], uploads, "universe")  # type: ignore[arg-type]
                sets_path = _save_upload(fields["gene_sets"], uploads, "gene-sets")  # type: ignore[arg-type]
                lower_name = query_path.name.lower()
                if lower_name.endswith((".vcf", ".vcf.gz")):
                    records = read_vcf(query_path)
                    input_type = "VCF"
                elif lower_name.endswith((".csv", ".tsv")):
                    try:
                        records = read_variant_table(query_path)
                        input_type = "variant table"
                    except ValueError:
                        records = []
                        input_type = "gene list"
                else:
                    records = []
                    input_type = "gene list"
                min_quality = float(fields["min_quality"]) if fields.get("min_quality") else None
                max_af = float(fields["max_af"]) if fields.get("max_af") else None
                records = filter_variants(
                    records,
                    min_quality=min_quality,
                    max_allele_frequency=max_af,
                    pass_only="pass_only" in fields,
                )
                query = (
                    {record.gene for record in records} if records else read_gene_list(query_path)
                )
                universe = read_gene_list(universe_path)
                gene_sets = read_gene_sets(sets_path)
                testable_gene_sets = sum(bool(gene_set.genes & universe) for gene_set in gene_sets)
                results = enrich(query, universe, gene_sets)
                metadata = {
                    "software": "CMHS VarEnrich",
                    "version": __version__,
                    "query_size": len(query),
                    "universe_size": len(universe),
                    "gene_sets_loaded": len(gene_sets),
                    "gene_sets_tested": testable_gene_sets,
                    "results_returned": len(results),
                    "input_type": input_type,
                    "variant_records": len(records),
                    "method": "one-sided hypergeometric survival test; Benjamini-Hochberg FDR",
                }
                write_results_tsv(results, destination / "enrichment-results.tsv")
                if records:
                    write_variants_tsv(records, destination / "filtered-variants.tsv")
                write_svg_figures(results, destination / "figures")
                title = str(fields.get("title") or "CMHS VarEnrich Report")
                write_html_report(
                    results, destination / "report.html", title=title, metadata=metadata
                )
                (destination / "analysis-metadata.json").write_text(
                    json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                shutil.copy2(sets_path, destination / "annotation-collection.gmt")
                shutil.rmtree(uploads)
                self._json(
                    HTTPStatus.OK,
                    {
                        "query_size": len(query),
                        "results": len(results),
                        "output_directory": str(destination),
                        "report_url": f"/{token}/results/{quote(job)}/report.html",
                    },
                )
            except (OSError, TypeError, ValueError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    return server, token


def run_gui(*, open_browser: bool = True, output_root: Path | None = None) -> None:
    server, token = create_server(output_root)
    url = f"http://127.0.0.1:{server.server_port}/{token}/"
    print(f"CMHS VarEnrich is running locally at {url}")
    print("Press Ctrl+C to stop it. Patient data is not transmitted.")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
