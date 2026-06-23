"""Render polished candidate + recruiter PDF reports from an Assessment.

Self-contained reportlab renderer that reads directly from the Assessment ORM
(no external JSON). Produces the same house style as the manually-generated
reports: three-signal cards, GREEN/YELLOW/RED verdict banding, the
capability narrative, component breakdown, a governance "why flagged" box that
never leaks threshold numbers, JD-quality interpretation, a fairness note, a
multilingual-intake badge, and a reproducibility manifest.

Used by the auto-report worker on assessment completion; also importable for
on-demand rendering. English content only → built-in Helvetica is sufficient.
"""
from __future__ import annotations

import datetime
import io
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings

NAVY = colors.HexColor("#0F1729")
BLUE = colors.HexColor("#1F4E79")
BLUE2 = colors.HexColor("#2E5E8C")
ROW = colors.HexColor("#F2F6FB")
GREY = colors.HexColor("#52606D")
LINE = colors.HexColor("#C7D0DA")
GREEN = colors.HexColor("#047857")
AMBER = colors.HexColor("#B45309")
SLATE = colors.HexColor("#475569")
VIOLET = colors.HexColor("#6D28D9")
RED = colors.HexColor("#B91C1C")
CW = letter[0] - 2 * inch

_LANG = {
    "zh": "Mandarin Chinese", "ja": "Japanese", "ta": "Tamil", "ms": "Malay",
    "id": "Indonesian (Bahasa Indonesia)", "th": "Thai", "ko": "Korean", "hi": "Hindi",
    "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese", "ar": "Arabic",
}


def _md(t: Any) -> str:
    t = str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    # Restore a safe allowlist of inline tags that were escaped above, so strings
    # may contain <b>/<i>/<br/>/<font …> intentionally and still render.
    t = (t.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
          .replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
          .replace("&lt;br/&gt;", "<br/>").replace("&lt;/font&gt;", "</font>"))
    t = re.sub(r"&lt;font([^&]*?)&gt;", r"<font\1>", t)
    return t


def _styles() -> dict[str, ParagraphStyle]:
    s: dict[str, ParagraphStyle] = {}
    s["Title"] = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=24, textColor=NAVY, leading=28, spaceAfter=2)
    s["Sub"] = ParagraphStyle("Sub", fontName="Helvetica", fontSize=12, textColor=GREY, leading=16, spaceAfter=2)
    s["Kicker"] = ParagraphStyle("Kicker", fontName="Helvetica-Bold", fontSize=10, textColor=BLUE2, leading=13, spaceAfter=2)
    s["H1"] = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=14, textColor=BLUE, spaceBefore=15, spaceAfter=6, leading=18)
    s["Body"] = ParagraphStyle("Body", fontName="Helvetica", fontSize=10, leading=14.5, spaceAfter=6, alignment=4, textColor=colors.HexColor("#1f2933"))
    s["Cell"] = ParagraphStyle("Cell", fontName="Helvetica", fontSize=9, leading=12.5)
    s["CellH"] = ParagraphStyle("CellH", fontName="Helvetica-Bold", fontSize=9, leading=12.5, textColor=colors.white)
    s["Small"] = ParagraphStyle("Small", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=GREY)
    s["SmallI"] = ParagraphStyle("SmallI", fontName="Helvetica-Oblique", fontSize=8.5, leading=11.5, textColor=GREY)
    s["Score"] = ParagraphStyle("Score", fontName="Helvetica-Bold", fontSize=22, alignment=TA_CENTER, leading=24)
    s["ScoreLbl"] = ParagraphStyle("ScoreLbl", fontName="Helvetica", fontSize=8, alignment=TA_CENTER, textColor=GREY, leading=10)
    s["ScoreSub"] = ParagraphStyle("ScoreSub", fontName="Helvetica", fontSize=7.5, alignment=TA_CENTER, textColor=GREY, leading=9)
    return s


def _signal_cards(S, kw, sem, cap, delta):
    def card(val, lbl, sub, clr):
        return [Paragraph(str(val), ParagraphStyle("x", parent=S["Score"], textColor=clr)),
                Paragraph(lbl, S["ScoreLbl"]), Paragraph(sub, S["ScoreSub"])]
    cells = [
        card(kw, "KEYWORD / ATS", "what filters see", SLATE),
        card(sem, "SEMANTIC", "concept fit", BLUE2),
        card(cap, "CAPABILITY", "evidence-based", VIOLET),
        card(f"+{delta}" if delta >= 0 else str(delta), "DELTA", "cap - keyword", GREEN if delta >= 0 else AMBER),
    ]
    t = Table([[list(c) for c in cells]], colWidths=[CW / 4] * 4)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def _tbl(S, headers, rows, widths):
    data = [[Paragraph(_md(h), S["CellH"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(_md(str(x)), S["Cell"]) for x in r])
    t = Table(data, colWidths=[CW * w for w in widths], repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -1), 0.4, LINE),
          ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 6),
          ("RIGHTPADDING", (0, 0), (-1, -1), 6)]
    for i in range(1, len(data)):
        if i % 2 == 0:
            st.append(("BACKGROUND", (0, i), (-1, i), ROW))
    t.setStyle(TableStyle(st))
    return t


def _chip(text, clr):
    p = Paragraph(f'<font color="white"><b>{_md(text)}</b></font>',
                  ParagraphStyle("c", fontSize=8.5, leading=11, alignment=TA_CENTER))
    t = Table([[p]], colWidths=[2.4 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), clr),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def _verdict_band(kw, sem, cap, delta):
    if cap >= 75 and kw >= 70 and delta < 15:
        return ("GREEN · ADVANCE", GREEN, "Strong on every signal; keyword and capability agree. Proceed to interview.")
    if cap < 50:
        return ("RED · LIKELY DECLINE", RED, "Capability is low and gaps are material; decline unless other context applies.")
    if delta >= 15 or cap > kw + 10:
        return ("YELLOW · HUMAN REVIEW", AMBER,
                "Capability materially exceeds the keyword/ATS rank - the hidden-gem pattern. A conventional ATS "
                "would mis-rank this candidate; review on capability, not keywords.")
    return ("YELLOW · HUMAN REVIEW", AMBER, "Signals diverge; human judgement recommended before a decision.")


def _jd_quality_interp(s):
    if s is None:
        return None
    if s >= 70:
        lvl = "strong - clear, specific and well-scoped"
    elif s >= 45:
        lvl = "moderate - some ambiguity or inflated requirements"
    else:
        lvl = "below-average - vague, over-stuffed, or internally inconsistent; treat keyword matching with extra caution"
    return f"<b>JD quality {s}/100</b> - {lvl}."


def _how_we_score(S, candidate=True):
    rows = [
        ["Keyword / ATS", "Deterministic TF-IDF term overlap - what an automated filter literally credits. Fully reproducible, no AI."],
        ["Semantic", "Concept-level fit via a multilingual embedding model - how well the meaning of the experience maps to the role."],
        ["Capability", "A governed AI verdict over evidence, trajectory and credential substitutions - the considered judgement of real fit. The un-inflated anchor."],
        ["Delta", "Capability minus keyword. A large positive delta = a candidate the ATS under-ranks (a hidden gem)."],
    ]
    title = "How to read these scores" if candidate else "How we score - signal definitions"
    return [Paragraph(title, S["H1"]), _tbl(S, ["Signal", "What it measures"], rows, [0.20, 0.80]),
            Paragraph("<b>Evidence strength</b> on each claim: <b>HIGH</b> = independently corroborated; "
                      "<b>MEDIUM</b> = credible but self-asserted; <b>WEAK</b> = thin support. Unverified claims are "
                      "capped at MEDIUM - the verdict never inflates beyond the evidence.", S["Small"])]


def _governance_box(S, a):
    band, _clr, _g = _verdict_band(a.traditional_score or 0, a.semantic_score or 0,
                                   a.capability_score or 0, a.score_delta or 0)
    reasons = []
    if a.counter_rec_triggered:
        reasons.append("the capability verdict materially exceeds the keyword rank (hidden-gem pattern)")
    if (a.jd_quality_score or 100) < 45:
        reasons.append("the job description scored below-average on clarity, so keyword matching is less reliable")
    if not reasons:
        reasons.append("the signals diverge enough that a human should confirm the decision")
    body = ("This assessment was routed to <b>human review</b> because " + "; ".join(reasons) +
            ". A person confirms the decision before any outcome - the system is advisory, never automated.")
    t = Table([[Paragraph("Why this was flagged for human review", S["CellH"])],
               [Paragraph(_md(body), S["Cell"])]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), AMBER), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#FFF7ED")),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7)]))
    return t


def _fairness_note(S):
    return Paragraph(
        "<b>Fairness controls.</b> Every verdict passes a mandatory <b>bias gate</b> that flags reasoning leaning on "
        "protected or proxy attributes; component scores are reasoned from evidence, not demographics, and the "
        "deterministic signals are identical run-to-run. A formal third-party adverse-impact audit complements - does "
        "not replace - this in-system gate.", S["Small"])


def _lang_badge(S, source_language):
    sl = (source_language or "en").lower()
    if sl in ("en", "und", ""):
        return None
    name = _LANG.get(sl, sl.upper())
    return Paragraph(
        f'<font color="#0B6E4F"><b>● Multilingual intake.</b></font> This résumé was submitted in <b>{name}</b> '
        f'(<font face="Courier">{sl}</font>) and machine-translated to an English pivot at intake. The deterministic '
        "keyword signal is language-invariant; the semantic and capability signals are language-responsive (they "
        "reflect how legibly the evidence reads in translation). The original is retained for provenance.", S["Small"])


def _manifest_appendix(S, a):
    rows = [
        ["Assessment ID", str(a.id)],
        ["Timestamp (UTC)", str(getattr(a, "created_at", "") or "")],
        ["Capability model", settings.anthropic_model],
        ["Extraction model", settings.anthropic_fast_model],
        ["Keyword signal", "deterministic TF-IDF term-overlap"],
        ["Semantic signal", "embedding · " + getattr(settings, "semantic_embedding_model", "multilingual")],
        ["Governance gates", "coherence · consistency · fidelity · bias"],
        ["Source language", (getattr(a, "_source_language", None) or "en")],
    ]
    return [Paragraph("Appendix · Reproducibility manifest", S["H1"]),
            Paragraph("Inputs (résumé + JD) are SHA-256 hashed at intake and retained in the immutable audit trail. "
                      "Deterministic signals reproduce byte-for-byte; the AI verdict is pinned to the prompt registry.",
                      S["Small"]),
            _tbl(S, ["Field", "Value"], rows, [0.30, 0.70])]


def _components_rows(a):
    comps = a.capability_components or {}
    rows = []
    for k, v in comps.items():
        score = v.get("score") if isinstance(v, dict) else v
        note = v.get("reasoning", "") if isinstance(v, dict) else ""
        rows.append([k.replace("_", " ").title(), str(score), str(note)[:160]])
    return rows


def _build(story, title, header_label):
    buf = io.BytesIO()
    date_str = datetime.date.today().strftime("%d %B %Y")

    def _page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, letter[1] - 0.55 * inch, letter[0], 0.55 * inch, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(0.9 * inch, letter[1] - 0.37 * inch, "TrueMatch")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(letter[0] - 0.9 * inch, letter[1] - 0.37 * inch, header_label)
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawCentredString(letter[0] / 2, 0.4 * inch, f"Confidential · Generated {date_str} · Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.85 * inch, bottomMargin=0.7 * inch,
                            leftMargin=1 * inch, rightMargin=1 * inch, title=title)
    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buf.getvalue()


def render_reports(assessment, *, candidate_name: str, target_title: str,
                   source_language: str | None = None) -> dict[str, bytes]:
    """Return {'candidate': pdf_bytes, 'recruiter': pdf_bytes} for one assessment."""
    a = assessment
    a._source_language = source_language  # stashed for the manifest appendix
    S = _styles()
    kw = a.traditional_score or 0
    sem = a.semantic_score or 0
    cap = a.capability_score or 0
    delta = a.score_delta if a.score_delta is not None else (cap - kw)
    band, bclr, guidance = _verdict_band(kw, sem, cap, delta)
    badge = _lang_badge(S, source_language)

    # ---------- Candidate ----------
    cs = [Paragraph("TrueMatch · Capability Assessment", S["Kicker"]),
          Paragraph(_md(candidate_name), S["Title"]),
          Paragraph(f"Your result for: <b>{_md(target_title)}</b>  ·  {datetime.date.today():%d %B %Y}", S["Sub"]),
          Spacer(1, 8)]
    if badge:
        cs += [badge, Spacer(1, 6)]
    cs += [Paragraph("This report shows how today's hiring software reads you - and, more importantly, what your "
                     "evidenced capability actually is. Where the two differ is your opportunity. Nothing here is "
                     "invented: every score is computed from your résumé.", S["Body"]),
           Paragraph("Your three signals", S["H1"]), _signal_cards(S, kw, sem, cap, delta)]
    cs += _how_we_score(S, candidate=True)
    if a.capability_narrative:
        cs += [Paragraph("What this means", S["H1"]), Paragraph(_md(a.capability_narrative), S["Body"])]
    cs += [Spacer(1, 8),
           Paragraph("This assessment was reviewed by a human before any decision (it is advisory, not automated).", S["Small"]),
           _fairness_note(S),
           Paragraph(f"Generated by TrueMatch · capability model {settings.anthropic_model}. This report re-expresses "
                     "your real, evidenced capability; it never fabricates experience.", S["SmallI"])]
    candidate_pdf = _build(cs, f"TrueMatch — {candidate_name} — Candidate Report", "Candidate copy")

    # ---------- Recruiter ----------
    ctr = a.counter_rec_triggered
    match = "HIDDEN GEM" if (ctr and delta >= 15) else ("STRONG MATCH" if cap >= kw and sem >= 70 else "KEYWORD-ALIGNED")
    rs = [Paragraph("TrueMatch · Recruiter Assessment  ·  Confidential", S["Kicker"]),
          Paragraph(_md(candidate_name), S["Title"]),
          Paragraph(f"Evaluated for: <b>{_md(target_title)}</b>  ·  {datetime.date.today():%d %B %Y}", S["Sub"]),
          Spacer(1, 8), _chip(f"{band}   ·   match: {match}", bclr), Spacer(1, 8)]
    if badge:
        rs += [badge, Spacer(1, 6)]
    rs += [_signal_cards(S, kw, sem, cap, delta), Spacer(1, 8),
           Paragraph("Verdict & recommendation", S["H1"]), Paragraph(_md(guidance), S["Body"]),
           _governance_box(S, a)]
    jq = _jd_quality_interp(a.jd_quality_score)
    if jq:
        rs += [Spacer(1, 6), Paragraph(_md(jq), S["Small"])]
    comp_rows = _components_rows(a)
    if comp_rows:
        rs += [Paragraph("Capability components", S["H1"]),
               _tbl(S, ["Component", "Score", "Evidence reasoning"], comp_rows, [0.22, 0.10, 0.68])]
    if a.counter_rec_triggered and a.counter_rec_reasoning:
        rs += [Paragraph("Counter-recommendation (hidden gem)", S["H1"]),
               Paragraph(_md(a.counter_rec_reasoning), S["Body"])]
    rs += _how_we_score(S, candidate=False)
    rs += [Paragraph("Fairness & governance", S["H1"]), _fairness_note(S), PageBreak()]
    rs += _manifest_appendix(S, a)
    recruiter_pdf = _build(rs, f"TrueMatch — {candidate_name} — Recruiter Report", "Recruiter copy")

    return {"candidate": candidate_pdf, "recruiter": recruiter_pdf}
