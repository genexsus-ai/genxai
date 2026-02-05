#!/usr/bin/env python3
"""
Generate a comprehensive PDF comparison document for GenXAI vs competitors.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os


def create_comparison_pdf(output_path):
    """Generate the GenXAI comparison PDF document."""
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4a4a4a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # Title Page
    elements.append(Spacer(1, 1.5*inch))
    elements.append(Paragraph("GenXAI Framework", title_style))
    elements.append(Paragraph("Comprehensive Comparison Report", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(
        "Comparing GenXAI with CrewAI, AutoGen, BeeAI, and n8n",
        body_style
    ))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        ParagraphStyle('Date', parent=body_style, alignment=TA_CENTER, fontSize=9)
    ))
    elements.append(PageBreak())
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading1_style))
    elements.append(Paragraph(
        "GenXAI's core runtime is feature-complete for agent workflows, tool orchestration, "
        "multi-provider LLM support, and workflow triggers/connectors. It competes well with "
        "CrewAI and AutoGen in orchestration depth and tooling, but still trails n8n on breadth "
        "of plug-and-play integrations and GUI-first automation UX. Compared to BeeAI, GenXAI "
        "offers stronger multi-provider support, graph orchestration, and enterprise-grade "
        "observability/security.",
        body_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Framework Overview
    elements.append(Paragraph("Framework Overview", heading2_style))
    
    framework_data = [
        ["Framework", "Primary Focus", "Key Strength"],
        ["GenXAI", "Multi-agent orchestration with graph workflows", "Provider breadth & enterprise features"],
        ["CrewAI", "Agent collaboration & role-based teams", "Prompt engineering & templates"],
        ["AutoGen", "Conversational multi-agent systems", "Research-backed agent patterns"],
        ["BeeAI", "Lightweight agent automation", "Local-first model support"],
        ["n8n", "Workflow automation & integrations", "Connector ecosystem & GUI"],
    ]
    
    framework_table = Table(framework_data, colWidths=[1.2*inch, 2.5*inch, 2.5*inch])
    framework_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(framework_table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(PageBreak())
    
    # Feature Matrix Table
    elements.append(Paragraph("Feature Comparison Matrix", heading1_style))
    elements.append(Paragraph(
        "Legend: ✅ = Available, ⚠️ = Partial, ❌ = Missing, 🟡 = External/Experimental",
        ParagraphStyle('Legend', parent=body_style, fontSize=8, textColor=colors.grey)
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    feature_data = [
        ["Capability", "GenXAI", "CrewAI", "AutoGen", "BeeAI", "n8n"],
        ["Multi-agent orchestration", "✅", "✅", "✅", "✅", "⚠️"],
        ["Graph/Workflow engine", "✅", "⚠️", "⚠️", "⚠️", "✅"],
        ["Multi-LLM providers", "✅", "⚠️", "✅", "⚠️", "✅"],
        ["Tool registry & schemas", "✅", "✅", "✅", "⚠️", "✅"],
        ["Tool templates", "✅", "⚠️", "❌", "⚠️", "✅"],
        ["Memory systems", "✅", "⚠️", "✅", "⚠️", "⚠️"],
        ["Vector store abstraction", "✅", "⚠️", "✅", "⚠️", "🟡"],
        ["Persistence (JSON/SQLite)", "✅", "❌", "⚠️", "⚠️", "✅"],
        ["Observability hooks", "✅", "⚠️", "⚠️", "⚠️", "✅"],
        ["Rate limiting & cost controls", "✅", "⚠️", "⚠️", "⚠️", "✅"],
        ["Security/RBAC", "✅", "⚠️", "⚠️", "⚠️", "✅"],
        ["Offline/local inference", "✅", "⚠️", "✅", "✅", "✅"],
        ["CLI workflows", "✅", "✅", "✅", "⚠️", "✅"],
        ["Workflow triggers/connectors", "✅", "⚠️", "⚠️", "⚠️", "✅"],
        ["GUI workflow builder", "❌", "❌", "❌", "❌", "✅"],
        ["Marketplace/ecosystem", "⚠️", "✅", "✅", "⚠️", "✅"],
    ]
    
    feature_table = Table(feature_data, colWidths=[2*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch])
    feature_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(feature_table)
    elements.append(PageBreak())
    
    # Scored Rubric Table
    elements.append(Paragraph("Scored Rubric (1-5 Scale)", heading1_style))
    elements.append(Paragraph(
        "Scale: 1 = Missing, 3 = Partial, 5 = Best-in-class",
        ParagraphStyle('Scale', parent=body_style, fontSize=8, textColor=colors.grey)
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    score_data = [
        ["Dimension", "GenXAI", "CrewAI", "AutoGen", "BeeAI", "n8n"],
        ["Agent orchestration depth", "4", "4", "5", "3", "2"],
        ["Workflow/graph flexibility", "4", "3", "3", "2", "5"],
        ["Provider breadth", "5", "3", "4", "3", "4"],
        ["Tooling & schemas", "4", "4", "4", "3", "5"],
        ["Memory & persistence", "4", "2", "4", "2", "3"],
        ["Observability & governance", "4", "2", "3", "2", "5"],
        ["Enterprise readiness", "4", "2", "3", "2", "5"],
        ["Ecosystem/connectors", "3", "4", "4", "2", "5"],
        ["UX/automation experience", "2", "3", "3", "3", "5"],
        ["Extensibility/plug-ins", "3", "4", "4", "2", "5"],
    ]
    
    score_table = Table(score_data, colWidths=[2.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f8f5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Weighted Totals
    elements.append(Paragraph("Weighted Total Scores (0-100 Scale)", heading2_style))
    
    weighted_data = [
        ["Framework", "Default Weights", "Enterprise-First", "Developer-First"],
        ["GenXAI", "76.8", "77.0", "77.2"],
        ["CrewAI", "61.8", "56.8", "63.2"],
        ["AutoGen", "75.2", "72.2", "76.8"],
        ["BeeAI", "48.0", "44.0", "50.4"],
        ["n8n", "85.0", "88.0", "78.4"],
    ]
    
    weighted_table = Table(weighted_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    weighted_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fadbd8')]),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(weighted_table)
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph(
        "<b>Note:</b> Scores are normalized to a 0-100 scale. Different weighting scenarios "
        "emphasize different priorities (enterprise features vs. developer experience).",
        ParagraphStyle('Note', parent=body_style, fontSize=8, textColor=colors.HexColor('#7f8c8d'))
    ))
    elements.append(PageBreak())
    
    # Heat Map View
    elements.append(Paragraph("Heat Map View", heading1_style))
    elements.append(Paragraph(
        "🟥 = 1-2 (Weak), 🟨 = 3 (Moderate), 🟩 = 4-5 (Strong)",
        ParagraphStyle('HeatLegend', parent=body_style, fontSize=8, textColor=colors.grey)
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    heatmap_data = [
        ["Dimension", "GenXAI", "CrewAI", "AutoGen", "BeeAI", "n8n"],
        ["Agent orchestration depth", "🟩 4", "🟩 4", "🟩 5", "🟨 3", "🟥 2"],
        ["Workflow/graph flexibility", "🟩 4", "🟨 3", "🟨 3", "🟥 2", "🟩 5"],
        ["Provider breadth", "🟩 5", "🟨 3", "🟩 4", "🟨 3", "🟩 4"],
        ["Tooling & schemas", "🟩 4", "🟩 4", "🟩 4", "🟨 3", "🟩 5"],
        ["Memory & persistence", "🟩 4", "🟥 2", "🟩 4", "🟥 2", "🟨 3"],
        ["Observability & governance", "🟩 4", "🟥 2", "🟨 3", "🟥 2", "🟩 5"],
        ["Enterprise readiness", "🟩 4", "🟥 2", "🟨 3", "🟥 2", "🟩 5"],
        ["Ecosystem/connectors", "🟨 3", "🟩 4", "🟩 4", "🟥 2", "🟩 5"],
        ["UX/automation experience", "🟥 2", "🟨 3", "🟨 3", "🟨 3", "🟩 5"],
        ["Extensibility/plug-ins", "🟨 3", "🟩 4", "🟩 4", "🟥 2", "🟩 5"],
    ]
    
    heatmap_table = Table(heatmap_data, colWidths=[2.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    heatmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4ecf7')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(heatmap_table)
    elements.append(PageBreak())
    
    # Detailed Framework Analysis
    elements.append(Paragraph("Detailed Framework Analysis", heading1_style))
    
    # GenXAI
    elements.append(Paragraph("GenXAI (Core Framework)", heading2_style))
    elements.append(Paragraph("<b>Strengths:</b>", body_style))
    strengths = [
        "Robust graph execution with parallel/conditional routing and checkpoints",
        "Strong tooling system with schemas, registry, templates, and built-in tools",
        "Multi-LLM provider support with fallback routing and local Ollama",
        "Comprehensive memory systems (short-term, long-term, episodic, semantic, procedural)",
        "Enterprise-grade observability scaffolding and security modules",
        "Workflow triggers and connectors for event-driven automation"
    ]
    for strength in strengths:
        elements.append(Paragraph(f"• {strength}", body_style))
    
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("<b>Weaknesses:</b>", body_style))
    weaknesses = [
        "Limited connector ecosystem compared to n8n (SaaS/enterprise integrations still growing)",
        "No GUI workflow builder in core framework (Studio UI is separate)",
        "Smaller community and marketplace compared to established frameworks"
    ]
    for weakness in weaknesses:
        elements.append(Paragraph(f"• {weakness}", body_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # CrewAI
    elements.append(Paragraph("CrewAI", heading2_style))
    elements.append(Paragraph("<b>Strengths:</b>", body_style))
    crewai_strengths = [
        "Strong agent collaboration patterns and role-based team structures",
        "Prompt-engineering focused UX with intuitive configuration",
        "Growing ecosystem of templates and community examples",
        "Good documentation and learning resources"
    ]
    for strength in crewai_strengths:
        elements.append(Paragraph(f"• {strength}", body_style))
    
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("<b>Weaknesses:</b>", body_style))
    crewai_weaknesses = [
        "Less opinionated graph orchestration capabilities",
        "Fewer LLM provider options out-of-the-box",
        "Limited enterprise features (observability, security, governance)",
        "Basic memory system compared to competitors"
    ]
    for weakness in crewai_weaknesses:
        elements.append(Paragraph(f"• {weakness}", body_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # AutoGen
    elements.append(Paragraph("AutoGen (Microsoft)", heading2_style))
    elements.append(Paragraph("<b>Strengths:</b>", body_style))
    autogen_strengths = [
        "Rich multi-agent orchestration patterns backed by research",
        "Strong community traction and Microsoft backing",
        "Excellent for conversational agent systems",
        "Good memory and state management capabilities"
    ]
    for strength in autogen_strengths:
        elements.append(Paragraph(f"• {strength}", body_style))
    
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("<b>Weaknesses:</b>", body_style))
    autogen_weaknesses = [
        "Heavier setup required for production orchestration",
        "GUI/connector ecosystem is limited (outside of extensions)",
        "Steeper learning curve for complex workflows",
        "Less focus on enterprise features"
    ]
    for weakness in autogen_weaknesses:
        elements.append(Paragraph(f"• {weakness}", body_style))
    
    elements.append(PageBreak())
    
    # BeeAI
    elements.append(Paragraph("BeeAI", heading2_style))
    elements.append(Paragraph("<b>Strengths:</b>", body_style))
    beeai_strengths = [
        "Lightweight agent automation patterns",
        "Local-first model support in some workflows",
        "Simple setup and configuration",
        "Good for basic agent tasks"
    ]
    for strength in beeai_strengths:
        elements.append(Paragraph(f"• {strength}", body_style))
    
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("<b>Weaknesses:</b>", body_style))
    beeai_weaknesses = [
        "Smaller ecosystem and fewer enterprise-grade features",
        "Limited observability and security modules",
        "Less sophisticated orchestration capabilities",
        "Smaller community and fewer resources"
    ]
    for weakness in beeai_weaknesses:
        elements.append(Paragraph(f"• {weakness}", body_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # n8n
    elements.append(Paragraph("n8n", heading2_style))
    elements.append(Paragraph("<b>Strengths:</b>", body_style))
    n8n_strengths = [
        "Mature workflow automation with extensive connectors and triggers",
        "Production-grade scheduling and integrations",
        "Excellent GUI workflow builder for non-technical users",
        "Large marketplace and community ecosystem",
        "Strong enterprise features (observability, security, RBAC)"
    ]
    for strength in n8n_strengths:
        elements.append(Paragraph(f"• {strength}", body_style))
    
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("<b>Weaknesses:</b>", body_style))
    n8n_weaknesses = [
        "Less agent-specific orchestration by default",
        "Agentic features typically layered via plugins or custom nodes",
        "Not primarily designed for multi-agent AI systems",
        "Weaker in advanced agent collaboration patterns"
    ]
    for weakness in n8n_weaknesses:
        elements.append(Paragraph(f"• {weakness}", body_style))
    
    elements.append(PageBreak())
    
    # Use Case Recommendations
    elements.append(Paragraph("Use Case Recommendations", heading1_style))
    
    use_cases = [
        ("Choose GenXAI when:", [
            "You need complex graph-based agent workflows with parallel execution",
            "Multi-provider LLM support with fallback routing is critical",
            "Enterprise features (observability, security, governance) are required",
            "Advanced memory systems are needed for agent learning",
            "You want a balance between code-first and no-code approaches"
        ]),
        ("Choose CrewAI when:", [
            "You need simple role-based agent teams",
            "Prompt engineering and agent collaboration are primary focus",
            "You want quick setup with minimal configuration",
            "Community templates and examples are valuable"
        ]),
        ("Choose AutoGen when:", [
            "You need research-backed conversational agent patterns",
            "Microsoft ecosystem integration is important",
            "Complex multi-agent conversations are the primary use case",
            "You have development resources for custom orchestration"
        ]),
        ("Choose BeeAI when:", [
            "You need lightweight agent automation",
            "Local-first model support is preferred",
            "Simple agent tasks without complex orchestration",
            "Minimal setup and configuration is desired"
        ]),
        ("Choose n8n when:", [
            "GUI-first workflow automation is essential",
            "Extensive SaaS integrations are needed",
            "Non-technical users need to build workflows",
            "Traditional workflow automation is more important than agent AI",
            "Production-grade scheduling and triggers are critical"
        ])
    ]
    
    for title, items in use_cases:
        elements.append(Paragraph(title, heading2_style))
        for item in items:
            elements.append(Paragraph(f"• {item}", body_style))
        elements.append(Spacer(1, 0.15*inch))
    
    elements.append(PageBreak())
    
    # Conclusion
    elements.append(Paragraph("Conclusion", heading1_style))
    elements.append(Paragraph(
        "GenXAI positions itself as a comprehensive agentic AI framework that bridges the gap "
        "between specialized agent frameworks (CrewAI, AutoGen) and workflow automation platforms (n8n). "
        "Its core strengths lie in:",
        body_style
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    conclusions = [
        "<b>Graph-based orchestration:</b> Superior to CrewAI and AutoGen for complex workflows",
        "<b>Multi-provider support:</b> Best-in-class LLM provider breadth with fallback routing",
        "<b>Enterprise readiness:</b> Comprehensive observability, security, and governance features",
        "<b>Memory systems:</b> Advanced multi-layered memory architecture for agent learning",
        "<b>Balanced approach:</b> Code-first with planned no-code Studio UI"
    ]
    
    for conclusion in conclusions:
        elements.append(Paragraph(f"• {conclusion}", body_style))
    
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(
        "While n8n leads in connector ecosystem and GUI experience, and AutoGen excels in "
        "research-backed agent patterns, GenXAI offers the most balanced feature set for "
        "production-grade agentic AI applications. The framework is particularly well-suited "
        "for organizations that need sophisticated agent orchestration with enterprise features, "
        "while maintaining flexibility for both developers and future no-code users.",
        body_style
    ))
    
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(
        "<b>Key Gaps to Address:</b> To achieve full parity with n8n's ecosystem, GenXAI should "
        "focus on expanding its connector library, building a template marketplace, and completing "
        "the Studio UI for visual workflow building.",
        body_style
    ))
    
    # Build PDF
    doc.build(elements)
    print(f"✅ PDF generated successfully: {output_path}")


if __name__ == "__main__":
    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.join(project_root, "docs", "GenXAI_Comparison_Report.pdf")
    
    # Ensure docs directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate the PDF
    create_comparison_pdf(output_path)
