
import re
from xml.sax.saxutils import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    PageBreak,
)


def markdown_to_pdf_elements(text, styles):
    """Convert the report's basic Markdown into PDF elements."""

    elements = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            elements.append(Spacer(1, 4))
            continue

        if line == "---":
            elements.append(
                HRFlowable(
                    width="100%",
                    thickness=0.7,
                    color=colors.lightgrey,
                )
            )
            continue

        if line.startswith("# "):
            elements.append(Paragraph(
                escape(line[2:]),
                styles["ReportTitle"],
            ))
            continue

        if line.startswith("## "):
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(
                escape(line[3:]),
                styles["SectionHeading"],
            ))
            continue

        if line.startswith("### "):
            elements.append(Paragraph(
                escape(line[4:]),
                styles["SubHeading"],
            ))
            continue

        if line.startswith("- "):
            item = format_inline_markdown(line[2:])
            elements.append(
                Paragraph(
                    f"&bull;&nbsp;&nbsp;{item}",
                    styles["BodyTextCustom"],
                )
            )
            continue

        elements.append(
            Paragraph(
                format_inline_markdown(line),
                styles["BodyTextCustom"],
            )
        )

    return elements


def format_inline_markdown(text):
    """Format safe bold text and clickable HTTP(S) links."""

    # Escape ordinary text first so webpage content cannot inject
    # ReportLab paragraph markup.
    text = escape(text)

    # Convert Markdown links: [label](https://example.com)
    link_pattern = re.compile(
        r"\[([^\]]+)\]\((https?://[^ )]+)\)"
    )

    def replace_link(match):
        label = match.group(1)
        url = match.group(2)

        return (
            f'<link href="{url}" color="#1565C0">'
            f'<u>{label}</u></link>'
        )

    text = link_pattern.sub(replace_link, text)

    # Convert bold text: **text**
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
    )

    # Convert inline code.
    text = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier">\1</font>',
        text,
    )

    # Make bare URLs clickable.
    url_pattern = re.compile(
        r"(?<![=\"])(https?://[^\s<>]+)"
    )

    def replace_url(match):
        url = match.group(1)
        return (
            f'<link href="{url}" color="#1565C0">'
            f'<u>{url}</u></link>'
        )

    text = url_pattern.sub(replace_url, text)

    return text


def add_page_number(canvas, doc):
    """Add a page number and footer to each page."""

    canvas.saveState()

    width, _ = A4

    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.5)
    canvas.line(
        20 * mm,
        16 * mm,
        width - 20 * mm,
        16 * mm,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)

    canvas.drawString(
        20 * mm,
        10 * mm,
        "AI-Assisted Research Report",
    )

    canvas.drawRightString(
        width - 20 * mm,
        10 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def create_pdf_report(
    markdown_text,
    output_path="research_report.pdf",
):
    """Create a formatted PDF from the Markdown report."""

    output_path = Path(output_path)

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=18,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#17365D"),
            spaceBefore=12,
            spaceAfter=7,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading3"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#24527A"),
            spaceBefore=7,
            spaceAfter=4,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            spaceAfter=5,
            wordWrap="CJK",
        )
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=23 * mm,
        title="Research Report",
        author="Multi-Agent Research Assistant",
    )

    story = markdown_to_pdf_elements(
        markdown_text,
        styles,
    )

    story.insert(
        0,
        Paragraph(
            "MULTI-AGENT RESEARCH REPORT",
            styles["ReportTitle"],
        ),
    )

    story.insert(1, Spacer(1, 6))

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    print(f"[PDF] Report saved to: {output_path.resolve()}")

    return output_path
