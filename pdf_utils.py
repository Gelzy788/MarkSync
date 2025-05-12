from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup
import base64
import tempfile
from reportlab.lib.pagesizes import A4
import os


if not hasattr(pdfmetrics, '_loadedFonts') or 'DejaVuSans' not in pdfmetrics.getFontNames():
    font_path = os.path.join(os.path.dirname(__file__), 'data', 'dejavu-sans', 'DejaVuSans.ttf')
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт DejaVuSans не найден по пути: {font_path}")
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

def generate_pdf(html_content):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    normal_style = ParagraphStyle(
        name='Normal',
        fontName='DejaVuSans',
        fontSize=12,
        leading=14,
        textColor='#FFFFFF',
        allowWidows=0,
        allowOrphans=0,
        wordWrap='CJK'
    )

    story = []
    soup = BeautifulSoup(html_content, 'html.parser')

    def add_element(element):
        if element.name is None:
            text = element.strip()
            if text:
                story.append(Paragraph(text, normal_style))
                story.append(Spacer(1, 6))
            return

        tag = element.name.lower()
        if tag.startswith('h') and len(tag) == 2 and tag[1].isdigit():
            level = int(tag[1])
            heading_style = ParagraphStyle(
                name=f'Heading{level}',
                parent=normal_style,
                fontSize=18 - level * 2,
                spaceAfter=12
            )
            content = ''.join(child.get_text(strip=True) if child.name is None else child.get_text(strip=True) for child in element.children)
            story.append(Paragraph(content, heading_style))
            story.append(Spacer(1, 12))
            return
        if tag == 'p':
            content = ''
            for child in element.children:
                if child.name is None:
                    content += child.strip()
                elif child.name == 'strong':
                    content += f'<b>{child.get_text()}</b>'
                elif child.name == 'em':
                    content += f'<i>{child.get_text()}</i>'
                else:
                    content += child.get_text(strip=True)
            if content:
                story.append(Paragraph(content, normal_style))
                story.append(Spacer(1, 12))
            return
        if tag == 'ul':
            for li in element.find_all('li', recursive=False):
                bullet_text = li.get_text(strip=True)
                if bullet_text:
                    story.append(Paragraph(f'• {bullet_text}', normal_style))
            story.append(Spacer(1, 6))
            return
        if tag == 'img' and element.get('src', '').startswith('data:image'):
            try:
                src = element['src']
                if ',' in src:
                    _, encoded = src.split(',', 1)
                else:
                    encoded = src

                image_data = base64.b64decode(encoded)
                with tempfile.NamedTemporaryFile(delete=True, suffix='.png') as tmp:
                    tmp.write(image_data)
                    tmp.flush()
                    img = RLImage(tmp.name, width=400, height=300)
                    story.append(img)
                    story.append(Spacer(1, 12))
            except Exception as e:
                story.append(Paragraph(f"[Ошибка изображения: {str(e)}]", normal_style))
            return
        for child in element.children:
            add_element(child)
    for element in soup.find_all(recursive=False):
        add_element(element)

    doc.build(story)
    return buffer.getvalue()