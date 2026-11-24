"""
SkillMatch – Career Report Generator Module
Generates a comprehensive, downloadable PDF Career Report using ReportLab.
Includes student profile, skill assessment, recommended careers, skill gaps, and learning roadmap.
Handles XML special characters (&, <, >) safely to guarantee reliable PDF rendering.
"""

import io
import html
from datetime import datetime
from typing import Dict, List, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _safe(text: Any) -> str:
    """Safely convert value to string and escape XML entities for ReportLab Paragraphs."""
    if text is None:
        return "N/A"
    s = str(text).strip()
    if not s:
        return "N/A"
    return html.escape(s)


def generate_career_report_pdf(
    student: Dict[str, Any],
    skills: List[Dict[str, Any]],
    assessment: Dict[str, float],
    recommendations: List[Dict[str, Any]],
    selected_career: str,
    pathway: List[Dict[str, Any]],
    progress: Dict[str, bool],
) -> bytes:
    """
    Generate a complete, professionally formatted PDF report bytes object using student's actual data.
    Guarantees no XML parsing crashes from unescaped '&', '<', or '>'.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Professional palette
    navy = colors.HexColor("#0D47A1")
    blue = colors.HexColor("#1976D2")
    light_blue = colors.HexColor("#E3F2FD")
    dark_gray = colors.HexColor("#263238")
    light_gray = colors.HexColor("#F5F7FA")
    green = colors.HexColor("#2E7D32")
    red = colors.HexColor("#C62828")
    amber = colors.HexColor("#E65100")

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=navy,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=blue,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=navy,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=dark_gray,
        leading=12,
    )
    bold_body = ParagraphStyle(
        "BoldBody",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    elements = []

    # Title header
    elements.append(Paragraph("SkillMatch – Student Career &amp; Skill Guidance Report", title_style))
    elements.append(Paragraph("Personalized Academic Evaluation, Machine Learning Career Matching &amp; Learning Roadmap", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=navy, spaceAfter=8))

    # Metadata
    date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    meta_text = f"Report Date: <b>{_safe(date_str)}</b> | Student ID: <b>#{_safe(student.get('id', 'N/A'))}</b> | Status: <b>Official Academic Dossier</b>"
    elements.append(Paragraph(meta_text, body_style))
    elements.append(Spacer(1, 6))

    # ── Section 1: Student Profile ────────────────────────────────────────────
    elements.append(Paragraph("1. Student Profile &amp; Educational Background", h2_style))
    student_table_data = [
        [
            Paragraph("<b>Full Name:</b>", body_style),
            Paragraph(_safe(student.get("name")), body_style),
            Paragraph("<b>Email Address:</b>", body_style),
            Paragraph(_safe(student.get("email")), body_style),
        ],
        [
            Paragraph("<b>Education Level:</b>", body_style),
            Paragraph(_safe(student.get("education_level")), body_style),
            Paragraph("<b>Department:</b>", body_style),
            Paragraph(_safe(student.get("department")), body_style),
        ],
        [
            Paragraph("<b>Degree / Program:</b>", body_style),
            Paragraph(_safe(student.get("degree")) if student.get("degree") else "B.Tech Engineering", body_style),
            Paragraph("<b>Year of Study:</b>", body_style),
            Paragraph(_safe(student.get("year_of_study")), body_style),
        ],
        [
            Paragraph("<b>Career Interests:</b>", body_style),
            Paragraph(_safe(student.get("interests")), body_style),
            Paragraph("<b>Total Skills Tracked:</b>", body_style),
            Paragraph(f"<b>{len(skills)} skills</b>", body_style),
        ],
    ]
    st_table = Table(student_table_data, colWidths=[105, 160, 105, 170])
    st_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(st_table)
    elements.append(Spacer(1, 8))

    # ── Section 2: Skills Profile & Assessment ────────────────────────────────
    elements.append(Paragraph("2. Skills Profile &amp; Proficiency Diagnostic", h2_style))
    combined_skills = {}
    for s in skills:
        combined_skills[s["skill_name"]] = (s.get("skill_type", "technical").title(), float(s.get("proficiency", 3)))
    for sname, score in assessment.items():
        cat = "Soft" if sname.lower() in ["communication", "problem solving", "teamwork", "leadership", "time management"] else "Technical"
        combined_skills[sname] = (cat, float(score))

    if combined_skills:
        skill_rows = [["Skill Name", "Category", "Proficiency Score", "Readiness Level"]]
        for sname, (cat, score) in list(combined_skills.items())[:14]:
            label = "Expert" if score >= 4.5 else "Advanced" if score >= 3.5 else "Intermediate" if score >= 2.5 else "Beginner"
            skill_rows.append([
                Paragraph(f"<b>{_safe(sname)}</b>", body_style),
                Paragraph(_safe(cat), body_style),
                Paragraph(f"{score:.1f} / 5.0", body_style),
                Paragraph(f"<b>{label}</b>", body_style),
            ])

        sk_table = Table(skill_rows, colWidths=[150, 110, 130, 150])
        sk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_gray]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(sk_table)
    else:
        elements.append(Paragraph("No skills recorded yet. Complete registration or skill assessment.", body_style))
    elements.append(Spacer(1, 8))

    # ── Section 3: Machine Learning Career Recommendations ────────────────────
    elements.append(Paragraph("3. Top Machine Learning Career Recommendations", h2_style))
    elements.append(Paragraph("<i>Matched dynamically via TF-IDF Vectorization and Cosine Similarity against occupational requirements:</i>", body_style))
    elements.append(Spacer(1, 4))

    if recommendations:
        rec_rows = [["Rank", "Recommended Career", "Domain", "Match Score", "Matched Skills", "Skill Gap"]]
        for idx, rec in enumerate(recommendations[:5], start=1):
            matching_cnt = len(rec.get("matching_skills", []))
            missing_cnt = len(rec.get("missing_skills", []))
            rec_rows.append([
                Paragraph(f"<b>#{idx}</b>", body_style),
                Paragraph(f"<b>{_safe(rec['career_title'])}</b>", body_style),
                Paragraph(_safe(rec.get("category", "Technology")), body_style),
                Paragraph(f"<b>{rec['match_pct']}%</b>", body_style),
                Paragraph(f"{matching_cnt} skills", body_style),
                Paragraph(f"{missing_cnt} missing", body_style),
            ])

        rec_table = Table(rec_rows, colWidths=[40, 160, 120, 80, 70, 70])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_blue]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(rec_table)
        elements.append(Spacer(1, 6))

        # Top Career Rationale
        top_rec = recommendations[0]
        elements.append(Paragraph(f"<b>Primary Career Match Rationale ({_safe(top_rec['career_title'])}):</b>", bold_body))
        elements.append(Paragraph(_safe(top_rec.get("explanation", "High alignment between your skill vector and occupational profile.")), body_style))
        elements.append(Spacer(1, 6))

        # Skill Gap Breakdown for Top Match
        matching_str = ", ".join([_safe(s) for s in top_rec.get("matching_skills", [])]) or "None"
        missing_str = ", ".join([_safe(s) for s in top_rec.get("missing_skills", [])]) or "None"
        gap_summary_data = [
            [Paragraph("<b>Matching Competencies:</b>", body_style), Paragraph(f"<font color='#2E7D32'>{matching_str}</font>", body_style)],
            [Paragraph("<b>Missing Skills Gap:</b>", body_style), Paragraph(f"<font color='#C62828'>{missing_str}</font>", body_style)],
        ]
        gap_tbl = Table(gap_summary_data, colWidths=[140, 400])
        gap_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(gap_tbl)
    else:
        elements.append(Paragraph("Recommendations not yet generated. Complete the skill assessment and career recommendation module.", body_style))
    elements.append(Spacer(1, 8))

    # ── Section 4: Personalized Learning Pathway ──────────────────────────────
    target_career_name = selected_career or (recommendations[0]["career_title"] if recommendations else "Target Career")
    elements.append(Paragraph(f"4. Personalized 3-Tier Learning Pathway: {_safe(target_career_name)}", h2_style))

    if pathway:
        completed_cnt = sum(1 for item in pathway if progress.get(item.get("topic", ""), False))
        total_steps = len(pathway)
        pct_comp = round(completed_cnt / total_steps * 100, 1) if total_steps > 0 else 0.0

        elements.append(Paragraph(
            f"Curriculum Status: <b>{completed_cnt} of {total_steps} topics completed ({pct_comp}%)</b> | "
            f"Structure: <b>Beginner &rarr; Intermediate &rarr; Advanced</b>",
            body_style
        ))
        elements.append(Spacer(1, 4))

        path_rows = [["Step", "Level", "Learning Topic & Description", "Status"]]
        for item in pathway:
            topic = item.get("topic", "")
            is_done = progress.get(topic, False)
            status_str = "COMPLETED" if is_done else "PENDING"
            level_str = item.get("level", "Beginner")
            desc_text = item.get("description", "")
            topic_cell = f"<b>{_safe(topic)}</b><br/><font color='#546E7A'>{_safe(desc_text)}</font>"

            path_rows.append([
                Paragraph(str(item.get("step", "?")), body_style),
                Paragraph(_safe(level_str), body_style),
                Paragraph(topic_cell, body_style),
                Paragraph(f"<font color='{'#2E7D32' if is_done else '#C62828'}'><b>{status_str}</b></font>", body_style),
            ])

        path_table = Table(path_rows, colWidths=[35, 80, 345, 80])
        path_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_gray]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(path_table)
    else:
        elements.append(Paragraph("No pathway generated yet. Select a career in the Learning Pathway module to view roadmap.", body_style))

    # ── Footer ────────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#90CAF9"), spaceAfter=6))
    elements.append(Paragraph(
        "SkillMatch Academic System | B.Tech Academic Project Demonstration | Data Source: U.S. DOL O*NET Database | ML Engine: TF-IDF + Cosine Similarity",
        ParagraphStyle("Footer", parent=body_style, fontSize=7, textColor=colors.HexColor("#78909C"), alignment=TA_CENTER)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
