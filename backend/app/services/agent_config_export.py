"""Export services for agent configurations (PDF, CSV, etc.)."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentConfig, AgentConfigVersion
from app.services.agent_config_service import AgentConfigService
from app.services.agent_config_governance import AgentConfigGovernance


class AgentConfigExportService:
    """Export agent configurations to various formats."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_service = AgentConfigService(db)
        self.governance = AgentConfigGovernance(db)

    async def export_to_pdf(
        self, config_id: str, include_audit: bool = True
    ) -> bytes:
        """Export approval checklist to PDF.

        Returns PDF bytes that can be sent as file download.

        Uses reportlab for PDF generation (lightweight, no external dependencies).
        """
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib import colors

        # Fetch config and validation
        config = await self.config_service.get_config_by_id(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        version = await self.config_service.get_version_by_number(
            config_id, config.version_number
        )
        if not version:
            raise ValueError(f"Version not found")

        checklist = await self.governance.get_approval_checklist(config, version)

        # Create PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#374151"),
            spaceAfter=8,
            spaceBefore=8,
        )

        # Build document
        elements = []

        # Title
        elements.append(
            Paragraph(
                f"{checklist['agent_type'].title()} Agent Configuration - Approval Checklist",
                title_style,
            )
        )
        elements.append(Spacer(1, 0.2 * inch))

        # Metadata
        metadata_data = [
            ["Configuration Name:", checklist["config_id"]],
            ["Version:", str(checklist["version_number"])],
            ["Agent Type:", checklist["agent_type"]],
            ["Role:", checklist["role"]],
            ["Created By:", checklist["created_by"]],
            ["Submitted At:", checklist["submitted_at"] or "Not submitted"],
            ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
        ]
        metadata_table = Table(metadata_data, colWidths=[2 * inch, 4 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2937")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
                ]
            )
        )
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Validation Summary
        elements.append(Paragraph("Validation Summary", heading_style))
        validation = checklist["validation"]
        summary_data = [
            [
                "Safety Check:",
                "✓ PASSED" if validation["safety_passed"] else "✗ FAILED",
            ],
            ["Fairness Score:", f"{validation['fairness_score']}/100"],
            [
                "Recommendation:",
                checklist["recommendation"].upper(),
            ],
        ]
        summary_table = Table(summary_data, colWidths=[2 * inch, 4 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2937")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
                ]
            )
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Approval Items
        elements.append(Paragraph("Approval Checklist", heading_style))
        items_data = [["Item", "Status", "Details"]]
        for item in checklist["approval_items"]:
            status_symbol = {
                "passed": "✓",
                "failed": "✗",
                "warning": "⚠",
                "missing": "○",
                "incomplete": "○",
            }.get(item["status"], "?")
            items_data.append(
                [item["item"], f"{status_symbol} {item['status'].upper()}", item["details"]]
            )

        items_table = Table(items_data, colWidths=[1.8 * inch, 1.2 * inch, 3 * inch])
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
                ]
            )
        )
        elements.append(items_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Errors/Warnings
        if validation["errors"]:
            elements.append(Paragraph("Errors", heading_style))
            for error in validation["errors"]:
                elements.append(Paragraph(f"• {error}", styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))

        if validation["warnings"]:
            elements.append(Paragraph("Warnings", heading_style))
            for warning in validation["warnings"]:
                elements.append(Paragraph(f"• {warning}", styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))

        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        footer_text = "This approval checklist is generated automatically. Review validation results and approve/reject the configuration in the admin panel."
        elements.append(
            Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey))
        )

        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    async def export_to_csv(self) -> str:
        """Export all pending configs to CSV for bulk review."""
        import csv
        import io

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)

        # Header
        writer.writerow(
            [
                "Config ID",
                "Name",
                "Agent Type",
                "Version",
                "Status",
                "Fairness Score",
                "Safety Passed",
                "Recommendation",
                "Created",
                "Submitted",
            ]
        )

        # Data rows (would fetch from DB in production)
        # For now, just the header with example
        csv_buffer.seek(0)
        return csv_buffer.getvalue()

    def generate_filename(self, config: AgentConfig) -> str:
        """Generate a descriptive filename for exports."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name = config.name.lower().replace(" ", "_")
        return f"agent_config_{name}_v{config.version_number}_{timestamp}"


__all__ = ["AgentConfigExportService"]
