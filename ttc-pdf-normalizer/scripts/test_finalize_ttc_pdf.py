#!/usr/bin/env python3
"""Focused self-test for TTC numbering and conservative Boss watermark cleanup."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


MODULE_PATH = Path(__file__).with_name("finalize_ttc_pdf.py")
SPEC = importlib.util.spec_from_file_location("finalize_ttc_pdf", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_pdf(path: Path, light_watermark: bool) -> None:
    width, height = A4
    pdf = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.drawString(48, height - 72, "Candidate Resume")
    pdf.setFont("Helvetica", 8)
    if light_watermark:
        pdf.setFillColorRGB(0.72, 0.72, 0.72)
    else:
        pdf.setFillColorRGB(0, 0, 0)
    pdf.drawRightString(width - 10, height - 12, "123456789012")
    pdf.showPage()
    pdf.save()


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        source = temp_dir / "source.pdf"
        make_pdf(source, light_watermark=True)
        result = MODULE.finalize(source, "测试候选人", temp_dir, False, "0820", 1, True)
        assert result["boss_watermarks_removed"] == 1, result
        assert result["boss_watermark_pages"] == [1], result
        assert Path(result["output"]).name == "测试候选人-TTC-082001.pdf", result

        dark_source = temp_dir / "dark-contact.pdf"
        make_pdf(dark_source, light_watermark=False)
        boxes, warnings = MODULE.detect_boss_numeric_watermarks(dark_source)
        assert not boxes, (boxes, warnings)
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
