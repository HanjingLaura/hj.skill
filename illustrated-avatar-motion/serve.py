#!/usr/bin/env python3
"""Local illustrated-avatar demo server.

Bind 127.0.0.1 only. Serve the portable bundle or this scripts folder.
Do not start Electron. Do not deploy.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
from email import message_from_bytes
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
HOST = os.environ.get("ILLUSTRATED_AVATAR_HOST", "127.0.0.1")
PORT = int(os.environ.get("ILLUSTRATED_AVATAR_PORT", "8766"))
FOUR = ()

if (HERE / "runtime" / "ani-bot" / "player.js").is_file():
    RUNTIME = HERE / "runtime"
else:
    RUNTIME = HERE.parents[1] / "src/renderer/ani/kit/src/features/avatar/vendor"

CASES = HERE / "cases"
DEMO = HERE / "demo"
PROBES: dict[str, object] = {}

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
}


def send(handler: BaseHTTPRequestHandler, status: int, body: bytes | str, content_type: str) -> None:
    payload = body if isinstance(body, bytes) else body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", content_type)
    handler.send_header("cache-control", "no-store")
    handler.send_header("content-length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def list_packs() -> list[dict[str, object]]:
    seen: set[str] = set()
    ids: list[str] = []
    for pack_id in FOUR:
        ids.append(pack_id)
        seen.add(pack_id)
    if CASES.is_dir():
        for child in sorted(CASES.iterdir()):
            if child.name in seen or not (child / "pack.json").is_file():
                continue
            ids.append(child.name)
    return [
        {
            "id": pack_id,
            "ok": (CASES / pack_id / "pack.json").is_file() and (CASES / pack_id / "front.png").is_file(),
        }
        for pack_id in ids
    ]


def safe_file(relative: str) -> Path | None:
    path = (HERE / relative.lstrip("/")).resolve()
    try:
        path.relative_to(HERE)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


def pack_payload(pack_id: str) -> dict[str, object] | None:
    directory = CASES / pack_id
    pack_path = directory / "pack.json"
    front = directory / "front.png"
    if not pack_path.is_file() or not front.is_file():
        return None
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    source_name = pack.get("source") if isinstance(pack.get("source"), str) else ""
    canonical_name = pack.get("canonical") if isinstance(pack.get("canonical"), str) else ""
    source = directory / source_name if source_name else front
    canonical = directory / canonical_name if canonical_name else front
    return {
        "ok": True,
        "pack": pack,
        "artworkUrl": f"/cases/{pack_id}/front.png",
        "sourceUrl": f"/cases/{pack_id}/{source.name}" if source.is_file() else f"/cases/{pack_id}/front.png",
        "canonicalUrl": f"/cases/{pack_id}/{canonical.name}" if canonical.is_file() else f"/cases/{pack_id}/front.png",
    }


DISPOSITION_NAME = re.compile(r'(?:^|;\s*)name\s*=\s*(?:"([^"]*)"|([^;\r\n]+))', re.I)


def safe_basename(name: str) -> str:
    base = Path(str(name).replace("\\", "/")).name
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in base).strip(".-")
    if not cleaned:
        return "upload.png"
    if "." not in cleaned:
        cleaned += ".png"
    return cleaned[:80]


def part_name(part) -> str:
    header = str(part.get("Content-Disposition") or "")
    match = DISPOSITION_NAME.search(header)
    if not match:
        return ""
    return (match.group(1) or match.group(2) or "").strip()


def parse_multipart(body: bytes, boundary: str) -> tuple[str, str, bytes]:
    wrapper = b"Content-Type: multipart/form-data; boundary=" + boundary.encode("utf-8") + b"\r\n\r\n" + body
    message = message_from_bytes(wrapper, policy=email_policy)
    pack_id = "upload"
    filename = "upload.png"
    image: bytes | None = None
    for part in message.iter_parts():
        name = part_name(part)
        payload = part.get_payload(decode=True)
        if payload is None:
            raw = part.get_payload()
            payload = raw.encode("utf-8", "replace") if isinstance(raw, str) else b""
        if name == "id":
            pack_id = payload.decode("utf-8", "replace").strip() or pack_id
        if name == "image":
            filename = safe_basename(part.get_filename() or "upload.png")
            image = payload
    if image is None:
        raise ValueError("No image part.")
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in pack_id)
    return safe_id or "upload", filename, image


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length) if length else b""
        if parsed.path == "/probe":
            try:
                payload = json.loads(body.decode("utf-8"))
                pack_id = payload["pack"] if isinstance(payload.get("pack"), str) else "unknown"
                PROBES[pack_id] = payload
                send(self, 200, json.dumps({"ok": True, "id": pack_id}), TYPES[".json"])
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                send(self, 400, json.dumps({"ok": False, "error": str(error)}), TYPES[".json"])
            return
        if parsed.path == "/build":
            try:
                content_type = self.headers.get("content-type") or ""
                marker = "boundary="
                if marker not in content_type:
                    send(
                        self,
                        400,
                        json.dumps({"ok": False, "code": "bad-request", "error": "Need multipart form data."}),
                        TYPES[".json"],
                    )
                    return
                boundary = content_type.split(marker, 1)[1].strip().strip('"')
                pack_id, filename, image = parse_multipart(body, boundary)
                work = Path(tempfile.mkdtemp(prefix="illustrated-avatar-"))
                source = work / safe_basename(filename)
                source.write_bytes(image)
                out = CASES / pack_id
                child = subprocess.run(
                    [sys.executable, str(HERE / "build-pack.py"), str(source), "--out", str(out), "--id", pack_id, "--json"],
                    cwd=str(HERE),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                try:
                    report = json.loads((child.stdout or "").strip().splitlines()[-1])
                except (json.JSONDecodeError, IndexError):
                    report = {
                        "ok": False,
                        "code": "pack-failed",
                        "error": child.stderr or child.stdout or f"exit {child.returncode}",
                    }
                if not report.get("ok"):
                    send(self, 422, json.dumps(report), TYPES[".json"])
                    return
                pack = json.loads((out / "pack.json").read_text(encoding="utf-8"))
                send(
                    self,
                    200,
                    json.dumps({"ok": True, "id": pack_id, "pack": pack, "artworkUrl": f"/cases/{pack_id}/front.png", "report": report}),
                    TYPES[".json"],
                )
            except Exception as error:  # noqa: BLE001
                send(self, 500, json.dumps({"ok": False, "code": "build-failed", "error": str(error)}), TYPES[".json"])
            return
        send(self, 404, "Not found", "text/plain; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in {"/", "/demo"}:
            self.send_response(302)
            self.send_header("location", "/demo/")
            self.send_header("cache-control", "no-store")
            self.end_headers()
            return
        if path == "/catalog":
            send(self, 200, json.dumps({"packs": list_packs()}), TYPES[".json"])
            return
        if path.startswith("/probe/"):
            pack_id = path[len("/probe/") :]
            probe = PROBES.get(pack_id)
            if probe is None:
                send(self, 404, json.dumps({"ok": False, "error": f"No probe for {pack_id}"}), TYPES[".json"])
                return
            send(self, 200, json.dumps({"ok": True, "probe": probe}), TYPES[".json"])
            return
        if path.startswith("/pack/"):
            payload = pack_payload(path[len("/pack/") :])
            if payload is None:
                send(self, 404, json.dumps({"ok": False, "error": "Pack is not built."}), TYPES[".json"])
                return
            send(self, 200, json.dumps(payload), TYPES[".json"])
            return
        relative = path
        if path == "/demo/":
            target = DEMO / "index.html"
        elif path.startswith("/demo/"):
            target = safe_file("demo/" + path[len("/demo/") :])
            if target is None:
                send(self, 404, "Not found", "text/plain; charset=utf-8")
                return
        elif path.startswith("/cases/"):
            target = safe_file(path.lstrip("/"))
            if target is None:
                send(self, 404, "Not found", "text/plain; charset=utf-8")
                return
        elif path == "/src/assets/primary-gray-avatar.png":
            repo_asset = HERE.parents[1] / "src/renderer/src/assets/primary-gray-avatar.png"
            case_asset = CASES / "primary-gray" / "front.png"
            if repo_asset.is_file():
                target = repo_asset
            elif case_asset.is_file():
                target = case_asset
            else:
                send(self, 404, "Not found", "text/plain; charset=utf-8")
                return
        elif path.startswith("/runtime/"):
            rest = path[len("/runtime/") :]
            target = (RUNTIME / rest).resolve()
            try:
                target.relative_to(RUNTIME)
            except ValueError:
                send(self, 404, "Not found", "text/plain; charset=utf-8")
                return
            if not target.is_file():
                send(self, 404, "Not found", "text/plain; charset=utf-8")
                return
        else:
            target = safe_file(relative.lstrip("/"))
            if target is None:
                send(self, 404, "Not found", "text/plain; charset=utf-8")
                return
        content_type = TYPES.get(target.suffix.lower()) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        send(self, 200, target.read_bytes(), content_type)


def main() -> int:
    if HOST not in {"127.0.0.1", "localhost", "::1"}:
        sys.stderr.write("Refusing to bind a non-local host.\n")
        return 2
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    sys.stdout.write(f"illustrated-avatar demo http://{HOST}:{PORT}/\n")
    sys.stdout.flush()
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
