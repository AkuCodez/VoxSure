"""Build the short submission report as a PDF (layout of a standard lab project report).

    python ml/scripts/build_submission_pdf.py --name "Your Name" --regno "23XXX0000" --live https://... --repo https://github.com/...
Without arguments, personal details and links stay as visible [placeholders]. Output: docs/VoxSure_Project_Report.pdf
The text and numbers come from submission_content.py (shared with the Word version).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Table, TableStyle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from submission_content import L, ROOT, build_blocks  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="[Your Name]")
    ap.add_argument("--regno", default="[Reg. No.]")
    ap.add_argument("--live", default="")
    ap.add_argument("--repo", default="")
    ap.add_argument("--out", default=str(ROOT / "docs" / "VoxSure_Project_Report.pdf"))
    a = ap.parse_args()
    links = L(ROOT / "docs" / "links.json") or {}
    live = a.live or links.get("live") or "[live link: add after deployment]"
    repo = a.repo or links.get("repo") or "[GitHub link: add after pushing the code]"
    blocks = build_blocks(a.name, a.regno, live, repo)

    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.6, leading=13, alignment=TA_JUSTIFY, spaceAfter=5)
    small = ParagraphStyle("s", parent=body, fontSize=8.2, leading=10.5, alignment=0, spaceAfter=0)
    cell = ParagraphStyle("c", parent=small, fontSize=8.4, leading=10.6)
    cellb = ParagraphStyle("cb", parent=cell, fontName="Helvetica-Bold")
    styles = {
        "title": ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=0, spaceAfter=2, textColor=colors.HexColor("#0f2a4a")),
        "sub": ParagraphStyle("sub", parent=body, fontSize=10.5, leading=14, alignment=0, spaceAfter=1),
        "h1": ParagraphStyle("h1", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=15, spaceBefore=9, spaceAfter=4, textColor=colors.HexColor("#0f2a4a")),
        "h2": ParagraphStyle("h2", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=10.3, leading=13, spaceBefore=6, spaceAfter=3, textColor=colors.HexColor("#163a63")),
        "p": body,
        "note": ParagraphStyle("n", parent=small, textColor=colors.HexColor("#444444"), spaceBefore=2, spaceAfter=3),
        "caption": ParagraphStyle("cap", parent=small, textColor=colors.HexColor("#444444"), spaceBefore=2),
    }
    W = A4[0] - 4 * cm

    def table(spec):
        data = [[Paragraph(str(c), cellb if i == 0 else cell) for c in row] for i, row in enumerate(spec["rows"])]
        t = Table(data, colWidths=[f * W for f in spec["widths"]], repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9aa7b8")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                               ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3eefa"))]))
        return t

    def render(block):
        kind, val = block
        if kind in styles:
            return Paragraph(val, styles[kind])
        if kind == "table":
            return table(val)
        if kind == "image":
            w = val["width_cm"] * cm
            return Image(val["path"], width=w, height=w * val["aspect"])
        raise ValueError(kind)

    story, i = [], 0
    while i < len(blocks):
        kind = blocks[i][0]
        if kind in ("h1", "h2"):          # keep a heading together with what follows it (intro line + table / image)
            group, j = [render(blocks[i])], i + 1
            while j < len(blocks) and blocks[j][0] in ("p", "table", "image") and len(group) < 3:
                group.append(render(blocks[j]))
                j += 1
                if blocks[j - 1][0] in ("table", "image"):
                    break
            story.append(KeepTogether(group))
            i = j
        else:
            story.append(render(blocks[i]))
            i += 1

    def deco(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(2 * cm, A4[1] - 1.2 * cm, f"{a.name} ({a.regno}) | VoxSure Voice-Enabled Chatbot Project Report")
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(a.out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.9 * cm, bottomMargin=1.6 * cm,
                            title="VoxSure Project Report", author=a.name)
    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
