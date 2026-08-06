from __future__ import annotations

import io
import os
import re
import sys
from datetime import datetime

# ---------------------------------------------------------
# STREAMLIT CLOUD IMPORT FIX
# ---------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# ---------------------------------------------------------
# REPORTLAB
# ---------------------------------------------------------

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import cm

from reportlab.pdfgen import canvas

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from xml.sax.saxutils import escape
# ---------------------------------------------------------
# CORPORATE BRAND COLORS
# ---------------------------------------------------------

BRAND_PRIMARY = colors.HexColor("#0F4C81")
BRAND_ACCENT = colors.HexColor("#16A085")
BRAND_WARNING = colors.HexColor("#F39C12")
BRAND_DANGER = colors.HexColor("#C0392B")
BRAND_TEXT = colors.HexColor("#1F2933")
BRAND_MUTED = colors.HexColor("#7F8C8D")
BRAND_LIGHT = colors.HexColor("#F8FAFC")
BRAND_BORDER = colors.HexColor("#E2E8F0")

# ---------------------------------------------------------
# ORGANIZATION DETAILS
# ---------------------------------------------------------

ORG_NAME = os.environ.get(
    "ORG_NAME",
    "VisionBoard"
)

ORG_TAGLINE = os.environ.get(
    "ORG_TAGLINE",
    "AI Powered Resume Auditor"
)

LOGO_PATH = os.environ.get(
    "LOGO_PATH",
    "assets/logo.png"
)

# ---------------------------------------------------------
# PAGE NUMBER CANVAS
# ---------------------------------------------------------

class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._saved_page_states = []

    def showPage(self):

        self._saved_page_states.append(dict(self.__dict__))

        self._startPage()

    def save(self):

        total_pages = len(self._saved_page_states)

        for state in self._saved_page_states:

            self.__dict__.update(state)

            self.draw_page(total_pages)

            super().showPage()

        super().save()

    def draw_page(self, total_pages):

        self.saveState()

        self.setFont(
            "Helvetica",
            8,
        )

        self.setFillColor(
            BRAND_MUTED
        )

        footer = (
            f"© {datetime.now().year} "
            f"{ORG_NAME} | Confidential Resume Audit"
        )

        self.drawString(
            1.8 * cm,
            1.0 * cm,
            footer,
        )

        self.drawRightString(
            self._pagesize[0] - 1.8 * cm,
            1.0 * cm,
            f"Page {self._pageNumber} of {total_pages}",
        )

        self.restoreState()

# ---------------------------------------------------------
# STYLES
# ---------------------------------------------------------

def _styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="H1Brand",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=24,
            textColor=BRAND_PRIMARY,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="H2Brand",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=BRAND_PRIMARY,
            spaceBefore=14,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Body2",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=BRAND_TEXT,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=BRAND_TEXT,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="Muted",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=BRAND_MUTED,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Bullet2",
            parent=styles["BodyText"],
            leftIndent=14,
            bulletIndent=6,
            leading=14,
            fontSize=10,
            textColor=BRAND_TEXT,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.white,
            alignment=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="OrgTitle",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=BRAND_PRIMARY,
            alignment=2,
        )
    )

    styles.add(
        ParagraphStyle(
            name="OrgTagline",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=BRAND_MUTED,
            alignment=2,
        )
    )

    return styles

# ---------------------------------------------------------
# DOCUMENT BUILDER 
# ---------------------------------------------------------

def _doc(buffer, title):

    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=title,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
    )
# ---------------------------------------------------------
# LOGO
# ---------------------------------------------------------

def _logo_image(width_cm=3.4, height_cm=1.3):

    if not LOGO_PATH:
        return None

    if not os.path.exists(LOGO_PATH):
        return None

    try:
        return Image(
            LOGO_PATH,
            width=width_cm * cm,
            height=height_cm * cm,
            kind="proportional",
        )
    except Exception:
        return None


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

def _branded_header(styles, title, subtitle=""):

    logo = _logo_image()

    left = logo if logo else Paragraph("", styles["Body2"])

    right = [
        Paragraph(f"<b>{ORG_NAME}</b>", styles["OrgTitle"]),
        Paragraph(ORG_TAGLINE, styles["OrgTagline"]),
    ]

    tbl = Table(
        [[left, right]],
        colWidths=[8.5 * cm, 8.9 * cm],
    )

    tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 1.3, BRAND_PRIMARY),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    return [
        tbl,
        Spacer(1, 0.30 * cm),
        Paragraph(title, styles["H1Brand"]),
        Paragraph(
            subtitle
            or datetime.now().strftime(
                "Generated on %d %b %Y %H:%M"
            ),
            styles["Muted"],
        ),
        Spacer(1, 0.55 * cm),
    ]


# ---------------------------------------------------------
# SAFE PARAGRAPH     "from xml.sax.saxutils import escape"
# ---------------------------------------------------------

from xml.sax.saxutils import escape

def _P(text, styles, style="Body2"):
    """
    Safely render ReportLab Paragraphs.
    Supports <b>, <br/> while escaping invalid XML characters.
    """

    if text is None:
        return Paragraph("—", styles[style])

    text = str(text).strip()

    if text == "":
        return Paragraph("—", styles[style])

    # Keep line breaks
    text = text.replace("\r\n", "\n")
    text = text.replace("\n", "<br/>")

    # Preserve supported tags
    text = text.replace("<b>", "__BOLD_START__")
    text = text.replace("</b>", "__BOLD_END__")
    text = text.replace("<br/>", "__BR__")

    # Escape XML characters
    text = escape(text)

    # Restore formatting tags
    text = text.replace("__BOLD_START__", "<b>")
    text = text.replace("__BOLD_END__", "</b>")
    text = text.replace("__BR__", "<br/>")

    return Paragraph(text, styles[style])


# ---------------------------------------------------------
# BULLETS
# ---------------------------------------------------------

def _bullets(items, styles):

    if not items:
        return [Paragraph("—", styles["Body2"])]

    flowables = []

    for item in items:

        if not item:
            continue

        flowables.append(

            Paragraph(

                f"• {escape(str(item))}",

                styles["Bullet2"]

            )

        )

    return flowables


# ---------------------------------------------------------
# KEY VALUE TABLE
# ---------------------------------------------------------

def _kv_table(rows, styles):

    data = []

    for k, v in rows:

        data.append([
            Paragraph(f"<b>{k}</b>", styles["Body2"]),
            _P(v, styles)
        ])

    table = Table(
        data,
        colWidths=[5 * cm, 12.2 * cm]
    )

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (0,-1), BRAND_LIGHT),

        ("TEXTCOLOR", (0,0), (-1,-1), BRAND_TEXT),

        ("VALIGN", (0,0), (-1,-1), "TOP"),

        ("BOTTOMPADDING", (0,0), (-1,-1), 8),

        ("TOPPADDING", (0,0), (-1,-1), 8),

        ("LEFTPADDING", (0,0), (-1,-1), 10),

        ("RIGHTPADDING", (0,0), (-1,-1), 10),

        ("LINEBELOW", (0,0), (-1,-1), 0.35, BRAND_BORDER),

    ]))

    return table


# ---------------------------------------------------------
# COMPLIANCE TABLE
# ---------------------------------------------------------

def _checklist_table(items, styles):

    rows = [

        [

            Paragraph("<b>Company Guideline</b>", styles["TableHeader"]),

            Paragraph("<b>Status</b>", styles["TableHeader"]),

            Paragraph("<b>Remarks</b>", styles["TableHeader"]),

        ]

    ]

    for item in items:

        title = (
            item.get("check")
            or item.get("section")
            or item.get("item")
            or item.get("requirement")
            or "—"
        )

        passed = (
            item.get("passed") is True
            or str(item.get("status", "")).upper() == "PASS"
            or "PASS" in str(item.get("status", "")).upper()
        )

        label = "PASS" if passed else "FAIL"

        colour = BRAND_ACCENT if passed else BRAND_DANGER

        note = (
            item.get("note")
            or item.get("comment")
            or item.get("remarks")
            or "—"
        )

        ##rows.append([
        #    _P(title, styles),
        #    Paragraph(
        #        f"<font color='{colour.hexval()}'><b>{label}</b></font>",
         #       styles["Body2"],
        #    ),
        #    _P(note, styles, "Body2Small"),
        #])
        rows.append(

            [

                _P(title, styles),

                Paragraph(

                    f"<font color='{colour.hexval()}'><b>{label}</b></font>",

                    styles["Body2"],

                ),

                _P(note, styles, "BodySmall"),

            ]

        )

    tbl = Table(

        rows,

        colWidths=[7.2 * cm, 2.1 * cm, 8.0 * cm],

    )

    tbl.setStyle(

        TableStyle(

            [

                ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),

                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

                ("ROWBACKGROUNDS",

                 (0, 1),

                 (-1, -1),

                 [colors.white, BRAND_LIGHT]),

                ("GRID",

                 (0, 0),

                 (-1, -1),

                 0.3,

                 BRAND_BORDER),

                ("BOTTOMPADDING",

                 (0, 0),

                 (-1, -1),

                 7),

                ("TOPPADDING",

                 (0, 0),

                 (-1, -1),

                 7),

                ("VALIGN",

                 (0, 0),

                 (-1, -1),

                 "TOP"),

            ]

        )

    )

    return tbl


# ---------------------------------------------------------
# COMPANY COMPLIANCE
# ---------------------------------------------------------

def calculate_company_compliance(
    resume_text,
    audit_data,
):

    resume_text = resume_text or ""

    upper = resume_text.upper()

    normalized = (

        upper

        .replace("-", "")

        .replace("_", "")

        .replace(" ", "")

    )

    checks = []

    def add(name, passed, note):

        checks.append(

            {

                "check": name,

                "status": "PASS" if passed else "FAIL",

                "note": note,

            }

        )

    add(

        "Profile Photo",

        audit_data.get("has_profile_photo", False),

        "Professional photograph verification",

    )

    add(

        "Email",

        "@" in resume_text,

        "Email address detected",

    )

    add(

        "Phone",

        bool(re.search(r"\d{10}", resume_text)),

        "Phone number detected",

    )

    add(

        "LinkedIn",

        "LINKEDIN" in upper,

        "LinkedIn profile available",

    )

    add(

        "Azure Skills",

        any(

            x in normalized

            for x in [

                "AZURE",

                "ADF",

                "PYTHON",

                "PYSPARK",

                "SQL",

                "DATABRICKS",

            ]

        ),

        "Azure Data Engineering stack detected",

    )

    add(

        "Certification",

        bool(

            re.search(

                r"(DP[- ]?900|DP[- ]?700|DATABRICKS)",

                upper,

            )

        ),

        "Relevant certification check",

    )

    passed = sum(

        x["status"] == "PASS"

        for x in checks

    )

    total = len(checks)

    score = int((passed / total) * 100)

    return {

        "passed": passed,

        "total": total,

        "score": score,

        "items": checks,

    }
#----------------------------------------------------------
#Single PDF Builder Function
#---------------------------------------------------------

def build_single_pdf(audit, chart_pngs, resume_text="", format_check=None):
    buf = io.BytesIO()
    doc = _doc(buf, f"Resume Audit — {audit.get('candidate_name','Candidate')}")
    styles = _styles()
    story = []
    
    if not isinstance(chart_pngs, dict):
        chart_pngs = {}

    # Polymorphic state alignment mapping loop
    extracted_items = []
    if isinstance(format_check, dict):
        extracted_items = format_check.get("items") or format_check.get("checkpoints") or []
    elif isinstance(format_check, list):
        extracted_items = format_check
        
    if not extracted_items:
        extracted_items = audit.get("section_compliance") or audit.get("format_check") or []
        if isinstance(extracted_items, dict):
            extracted_items = extracted_items.get("items") or []

    if not extracted_items:
        fallback_data = calculate_company_compliance(resume_text, audit)
        extracted_items = fallback_data["items"]
        passed = fallback_data["passed"]
        total = fallback_data["total"]
        score = fallback_data["score"]
    else:
        passed = sum(1 for i in extracted_items if "PASS" in str(i.get("status") or i.get("passed") or "").upper() or i.get("passed") is True)
        total = len(extracted_items)
        score = int((passed / total) * 100) if total else 0

    name = audit.get("candidate_name", "Candidate")
    story += _branded_header(styles, "Resume Audit Report", f"Candidate: {name}")

    story.append(_kv_table([
        ("Candidate Profile", name),
        ("Target Role Headline", audit.get("headline", "—")),
        ("Executive Verdict", audit.get("verdict", "—")),
        ("Overall Score", f"{audit.get('overall_score', 0)} / 100"),
        ("ATS Parsability Score", f"{audit.get('ats_score', 0)} / 100"),
        ("Job Description Match", f"{audit.get('jd_match_score', 0)} / 100"),
        ("Quality Audit Score", f"{audit.get('quality_score', 0)} / 100"),
        ("Experience Depth Score", f"{audit.get('experience_score', 0)} / 100"),
        ("Total Verified Experience", f"{audit.get('total_experience_years', 0)} Years"),
    ], styles))
    story.append(Spacer(1, 0.4 * cm))

    if chart_pngs.get("gauge") and chart_pngs.get("radar"):
        row = Table([[Image(io.BytesIO(chart_pngs["gauge"]), width=8.0 * cm, height=5.2 * cm),
                      Image(io.BytesIO(chart_pngs["radar"]), width=8.0 * cm, height=5.2 * cm)]],
                    colWidths=[8.7 * cm, 8.7 * cm])
        row.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, 0), "RIGHT"),
            ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(row)
        story.append(Spacer(1, 0.4 * cm))

    # --- RENDER COMPLETELY COMPLIANT SYNCHRONIZED MATRIX TABLE ---
    story.append(Paragraph(f"Company Guidelines Format Compliance — {passed}/{total} Requirements Met ({score}%)", styles["H2Brand"]))
    story.append(_checklist_table(extracted_items, styles))
    story.append(Spacer(1, 0.4 * cm))
   # story.append(Spacer(1, 0.4 * cm))

    story.append(
        Table(
            [[""]],
            colWidths=[17.2 * cm],
            style=[
                ("LINEABOVE", (0,0), (-1,-1), 0.5, BRAND_BORDER)
            ]
        )
    )

    story.append(
        Spacer(1, 0.25 * cm)
    )
    skills = audit.get("skills") or {}
    story.append(Paragraph("Skillset & Keyword Analysis", styles["H2Brand"]))
    skill_data = [
        [Paragraph("<b>Matched Competencies</b>", styles["TableHeader"]), 
         Paragraph("<b>Missing Target Gaps</b>", styles["TableHeader"]), 
         Paragraph("<b>Additional Credentials</b>", styles["TableHeader"])],
        [_P(", ".join(skills.get("matched") or []) or "—", styles),
         _P(", ".join(skills.get("missing") or []) or "—", styles),
         _P(", ".join(skills.get("additional") or []) or "—", styles)],
    ]
    skill_t = Table(skill_data, colWidths=[5.8 * cm, 5.8 * cm, 5.8 * cm])
    skill_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(skill_t)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Core Strategic Strengths", styles["H2Brand"]))
    story += _bullets(audit.get("strengths"), styles)
    
    story.append(Paragraph("Areas for Optimization (Weaknesses)", styles["H2Brand"]))
    story += _bullets(audit.get("weaknesses"), styles)
    
    story.append(Paragraph("Critical Evaluation Red Flags", styles["H2Brand"]))
    story += _bullets(audit.get("red_flags"), styles)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()

# ==========================================================
# BULK PDF BUILDER
# ==========================================================

def build_bulk_pdf(
    audits,
    pngs=None,
    resume_texts=None,
    format_checks=None,
) -> dict[str, bytes]:

    import io
    import re
    import charts

    pdf_files = {}

    styles = _styles()

    # ------------------------------------------------------
    # Backward compatibility
    # ------------------------------------------------------
    if isinstance(pngs, list):
        resume_texts = pngs
        pngs = None

    if resume_texts is None:
        resume_texts = [
            a.get("_resume_text", "")
            for a in audits
        ]

    if format_checks is None:
        format_checks = [
            a.get("_format_check")
            for a in audits
        ]

    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------

    candidates = sorted(
        zip(audits, resume_texts, format_checks),
        key=lambda x: x[0].get("overall_score", 0),
        reverse=True,
    )

    # ------------------------------------------------------
    # SUMMARY PDF
    # ------------------------------------------------------

    summary_buffer = io.BytesIO()
    pdf_files = {}
    summary_doc = _doc(
        summary_buffer,
        "Bulk Resume Audit Summary",
    )

    story = []

    story += _branded_header(
        styles,
        "Bulk Resume Audit Summary",
        f"{len(candidates)} Candidates Evaluated",
    )

    overall_scores = [
        a.get("overall_score", 0)
        for a, _, _ in candidates
    ]

    avg_score = round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0
    top_score = max(overall_scores) if overall_scores else 0
    strong_candidates = sum(score >= 75 for score in overall_scores)

    story.append(
        _kv_table(
            [
                ("Candidates Evaluated", len(candidates)),
                ("Average Overall Score", avg_score),
                ("Highest Overall Score", top_score),
                ("Strong Candidates (≥75)", strong_candidates),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 0.35 * cm))

    headers = [
        Paragraph("<b>Rank</b>", styles["TableHeader"]),
        Paragraph("<b>Candidate</b>", styles["TableHeader"]),
        Paragraph("<b>Overall</b>", styles["TableHeader"]),
        Paragraph("<b>ATS</b>", styles["TableHeader"]),
        Paragraph("<b>JD</b>", styles["TableHeader"]),
        Paragraph("<b>Experience</b>", styles["TableHeader"]),
        Paragraph("<b>Quality</b>", styles["TableHeader"]),
        Paragraph("<b>Verdict</b>", styles["TableHeader"]),
    ]

    table_data = [headers]

    for rank, (audit, _, _) in enumerate(candidates, start=1):

        table_data.append([
            _P(rank, styles),
            _P(audit.get("candidate_name", "-"), styles),
            _P(audit.get("overall_score", 0), styles),
            _P(audit.get("ats_score", 0), styles),
            _P(audit.get("jd_match_score", 0), styles),
            _P(audit.get("experience_score", 0), styles),
            _P(audit.get("quality_score", 0), styles),
            _P(audit.get("verdict", ""), styles, "BodySmall"),
        ])

    table = Table(
        table_data,
        colWidths=[
            1 * cm,
            5 * cm,
            1.5 * cm,
            1.5 * cm,
            1.5 * cm,
            1.8 * cm,
            1.8 * cm,
            4 * cm,
        ],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, BRAND_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(table)

    summary_doc.build(
        story,
        canvasmaker=NumberedCanvas,
    )

    pdf_files["SUMMARY_OVERVIEW"] = summary_buffer.getvalue()
# ------------------------------------------------------
# INDIVIDUAL REPORTS
# ------------------------------------------------------

    for idx, (audit, resume_text, format_check) in enumerate(candidates, start=1):

        candidate = re.sub(
            r"[^A-Za-z0-9_-]",
            "",
            audit.get("candidate_name", "Candidate").replace(" ", "_"),
        )

        charts_png = {}

        try:
            charts_png["gauge"] = charts.fig_to_png_bytes(
                charts.gauge(audit.get("overall_score", 0))
            )
        except Exception:
            pass

        try:
            charts_png["radar"] = charts.fig_to_png_bytes(
                charts.radar({
                    "Overall": audit.get("overall_score", 0),
                    "ATS": audit.get("ats_score", 0),
                    "JD Match": audit.get("jd_match_score", 0),
                    "Experience": audit.get("experience_score", 0),
                    "Quality": audit.get("quality_score", 0),
                })
            )
        except Exception:
            pass

        try:
            filename = f"{idx}_{candidate}_Report.pdf"

            pdf_files[filename] = build_single_pdf(
                audit=audit,
                chart_pngs=charts_png,
                resume_text=resume_text,
                format_check=format_check,
            )

        except Exception as e:
            print("=" * 80)
            print("FAILED FOR:", candidate)
            print(e)
            print("=" * 80)

    return pdf_files
# ==========================================================
# COMPARE PDF BUILDER
# ==========================================================

def build_compare_pdf(compare_result, pngs=None, format_checks=None):
    """
    Generate PDF report for Resume Comparison.
    Returns PDF bytes.
    """

    import io
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib import colors
    pdf_files = {}
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = _styles()
    story = []

    # ------------------------------------------------------
    # TITLE
    # ------------------------------------------------------
    #story.append(
     #   Paragraph(
   #         "Resume Comparison Report",
            #styles["TitleBrand"],
   #         styles["H1Brand"],
    #    )
  #  )
    #story.append(Spacer(1, 0.5 * cm))

    # ------------------------------------------------------
    # WINNER
    # ------------------------------------------------------
    story.append(
        Paragraph(
            "Final Recommendation",
            styles["H2Brand"],
        )
    )

    story.append(
        _kv_table(
            [
                (
                    "Selected Candidate",
                    compare_result.get("winner", "-"),
                ),
                (
                    "Selection Reason",
                    compare_result.get("why_winner", "-"),
                ),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------
    # RANKING TABLE
    # ------------------------------------------------------
    story.append(
        Paragraph(
            "Candidate Ranking",
            styles["H2Brand"],
        )
    )

    header = [
        Paragraph("<b>Rank</b>", styles["TableHeader"]),
        Paragraph("<b>Candidate</b>", styles["TableHeader"]),
        Paragraph("<b>Overall</b>", styles["TableHeader"]),
        Paragraph("<b>JD Match</b>", styles["TableHeader"]),
        Paragraph("<b>Experience</b>", styles["TableHeader"]),
        Paragraph("<b>Quality</b>", styles["TableHeader"]),
        Paragraph("<b>Verdict</b>", styles["TableHeader"]),
    ]

    rows = [header]

    ranking = compare_result.get("ranking", [])

    for row in ranking:
        rows.append(
            [
                _P(row.get("rank", ""), styles),
                _P(row.get("candidate_name", ""), styles),
                _P(row.get("overall_score", 0), styles),
                _P(row.get("jd_match_score", 0), styles),
                _P(row.get("experience_score", 0), styles),
                _P(row.get("quality_score", 0), styles),
                _P(row.get("verdict", ""), styles, "BodySmall"),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            1.2 * cm,
            5.2 * cm,
            1.8 * cm,
            1.8 * cm,
            1.8 * cm,
            1.8 * cm,
            4.0 * cm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, BRAND_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    # ------------------------------------------------------
    # CHARTS (Optional)
    # ------------------------------------------------------
    if pngs:
        if pngs.get("bar"):
            story.append(Paragraph("Metric Comparison", styles["H2Brand"]))
            story.append(_img_from_bytes(pngs["bar"], width=17 * cm))
            story.append(Spacer(1, 0.3 * cm))

        if pngs.get("ranking"):
            story.append(Paragraph("Ranking Chart", styles["H2Brand"]))
            story.append(_img_from_bytes(pngs["ranking"], width=17 * cm))
            story.append(Spacer(1, 0.5 * cm))

    # ------------------------------------------------------
    # INDIVIDUAL ANALYSIS
    # ------------------------------------------------------
    for row in ranking:

        story.append(
            Paragraph(
                row.get("candidate_name", ""),
                styles["H2Brand"],
            )
        )

        story.append(
            _kv_table(
                [
                    ("Overall Score", f"{row.get('overall_score',0)}/100"),
                    ("JD Match", f"{row.get('jd_match_score',0)}/100"),
                    ("Experience", f"{row.get('experience_score',0)}/100"),
                    ("Quality", f"{row.get('quality_score',0)}/100"),
                    ("Verdict", row.get("verdict", "")),
                ],
                styles,
            )
        )

        story.append(Spacer(1, 0.2 * cm))

        story.append(
            Paragraph(
                "<b>Key Strengths</b>",
                styles["BodySmall"],
            )
        )

        story.extend(
            _bullets(
                row.get("key_strengths", []),
                styles,
            )
        )

        story.append(Spacer(1, 0.15 * cm))

        story.append(
            Paragraph(
                "<b>Key Gaps</b>",
                styles["BodySmall"],
            )
        )

        story.extend(
            _bullets(
                row.get("key_gaps", []),
                styles,
            )
        )

        story.append(Spacer(1, 0.35 * cm))

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------
    story.append(
        Paragraph(
            "Comparison Summary",
            styles["H2Brand"],
        )
    )

    story.append(
        _P(
            compare_result.get(
                "comparison_summary",
                "",
            ),
            styles,
        )
    )

    doc.build(
    story,
    canvasmaker=NumberedCanvas,
    )

    pdf_files["COMPARE_SUMMARY"] = buffer.getvalue()

    buffer.close()
    
    # ------------------------------------------------------
    # INDIVIDUAL CANDIDATE REPORTS
    # ------------------------------------------------------

    import re
    import charts

    ranking = compare_result.get("ranking", [])
    for candidate in ranking:

            audit = candidate.get("_audit")

            if not audit:
                continue

            chart_pngs = {}

            try:
                chart_pngs["gauge"] = charts.fig_to_png_bytes(
                    charts.gauge(
                        audit.get("overall_score", 0)
                    )
                )
            except Exception:
                pass

            try:
                chart_pngs["radar"] = charts.fig_to_png_bytes(
                    charts.radar({
                        "Overall": audit.get("overall_score", 0),
                        "ATS": audit.get("ats_score", 0),
                        "JD Match": audit.get("jd_match_score", 0),
                        "Experience": audit.get("experience_score", 0),
                        "Quality": audit.get("quality_score", 0),
                    })
                )
            except Exception:
                pass

            candidate_name = re.sub(
                r"[^A-Za-z0-9_-]",
                "",
                audit.get("candidate_name", "Candidate").replace(" ", "_"),
            )

            try:

                pdf_files[f"{candidate_name}_Report.pdf"] = build_single_pdf(
                    audit=audit,
                    chart_pngs=chart_pngs,
                    resume_text=candidate.get("_resume_text", ""),
                    format_check=candidate.get("_format_check"),
                )

            except Exception as e:

                print("=" * 80)
                print("COMPARE PDF FAILED:", candidate_name)
                print(e)
                print("=" * 80)
    return pdf_files