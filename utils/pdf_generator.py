"""
PDF Generation Module
Converts notes to well-formatted PDF documents
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
import io
import re


def generate_pdf(notes_data, video_title="YouTube Lecture Notes"):
    """
    Generate a PDF from notes data
    
    Args:
        notes_data: Dictionary containing notes structure
        video_title: Title of the video
        
    Returns:
        bytes: PDF file as bytes
    """
    # Create a BytesIO buffer
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
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
        textColor=HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['BodyText'],
        fontSize=11,
        leftIndent=20,
        spaceAfter=6,
        leading=14
    )
    
    # Add title
    elements.append(Paragraph(video_title, title_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Add summary
    if 'summary' in notes_data:
        elements.append(Paragraph("Summary", heading_style))
        summary_text = notes_data['summary'].replace('\n', '<br/>')
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 0.2 * inch))
    
    # Add key concepts
    if 'key_concepts' in notes_data and notes_data['key_concepts']:
        elements.append(Paragraph("Key Concepts", heading_style))
        for concept in notes_data['key_concepts']:
            # Escape special characters and format
            concept_clean = escape_xml(concept)
            bullet_text = f"• {concept_clean}"
            elements.append(Paragraph(bullet_text, bullet_style))
        elements.append(Spacer(1, 0.2 * inch))
    
    # Add topics covered
    if 'topics_covered' in notes_data and notes_data['topics_covered']:
        elements.append(Paragraph("Topics Covered", heading_style))
        for topic in notes_data['topics_covered']:
            topic_clean = escape_xml(topic)
            bullet_text = f"• {topic_clean}"
            elements.append(Paragraph(bullet_text, bullet_style))
        elements.append(Spacer(1, 0.2 * inch))
    
    # Add detailed notes
    if 'detailed_notes' in notes_data:
        elements.append(PageBreak())
        elements.append(Paragraph("Detailed Notes", heading_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Process detailed notes
        detailed_text = notes_data['detailed_notes']
        
        # Split by sections (looking for numbered sections or headers)
        sections = re.split(r'\n(?=\d+\.|#{1,3}\s)', detailed_text)
        
        for section in sections:
            if not section.strip():
                continue
                
            # Check if it's a header (starts with # or numbered)
            lines = section.split('\n')
            first_line = lines[0].strip()
            
            # Format headers
            if first_line.startswith('#'):
                # Remove # symbols
                header_text = first_line.lstrip('#').strip()
                header_clean = escape_xml(header_text)
                elements.append(Paragraph(header_clean, subheading_style))
                # Process remaining lines
                remaining = '\n'.join(lines[1:]).strip()
                if remaining:
                    remaining_clean = escape_xml(remaining).replace('\n', '<br/>')
                    elements.append(Paragraph(remaining_clean, body_style))
            
            elif re.match(r'^\d+\.', first_line):
                # Numbered section
                section_clean = escape_xml(section).replace('\n', '<br/>')
                elements.append(Paragraph(section_clean, body_style))
            
            else:
                # Regular paragraph
                section_clean = escape_xml(section).replace('\n', '<br/>')
                elements.append(Paragraph(section_clean, body_style))
            
            elements.append(Spacer(1, 0.1 * inch))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def escape_xml(text):
    """Escape special XML characters for reportlab"""
    if not text:
        return ""
    
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    
    return text
