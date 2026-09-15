import threading
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

from varenrich.gui import create_server

EXAMPLES = Path(__file__).parents[1] / "examples"


def multipart(files: dict[str, Path], values: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----VarEnrich{uuid.uuid4().hex}"
    parts: list[bytes] = []
    for name, value in values.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    for name, path in files.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n".encode()
            + path.read_bytes()
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def test_gui_binds_to_loopback_and_requires_token(tmp_path):
    server, token = create_server(tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert server.server_address[0] == "127.0.0.1"
        with urlopen(f"http://127.0.0.1:{server.server_port}/{token}/") as response:
            page = response.read().decode()
        assert "CMHS VarEnrich" in page
        assert "not transmitted" in page
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_gui_runs_end_to_end_local_analysis(tmp_path):
    server, token = create_server(tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        body, content_type = multipart(
            {
                "query": EXAMPLES / "demo-variants.tsv",
                "universe": EXAMPLES / "demo-universe.txt",
                "gene_sets": EXAMPLES / "demo-gene-sets.gmt",
            },
            {"title": "Synthetic GUI test"},
        )
        request = Request(
            f"http://127.0.0.1:{server.server_port}/{token}/api/analyse",
            data=body,
            headers={"Content-Type": content_type},
        )
        with urlopen(request) as response:
            result = response.read().decode()
        assert '"query_size": 3' in result
        reports = list(tmp_path.glob("analysis-*/report.html"))
        assert len(reports) == 1
        assert not list(tmp_path.glob("analysis-*/inputs"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
