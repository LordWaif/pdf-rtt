from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import io

def _mark_bbox(pdf, boxers, output_pdf):
    """
    Mark bounding boxes on each page of a PDF document.

    Args:
        pdf (str): Path to the input PDF file.
        boxers (list): List of bounding boxes for each page.
        output_pdf (str): Path to the output PDF file.

    Returns:
        None
    """
    reader = PdfReader(pdf)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        box = boxers[i]
        packet = io.BytesIO()
        can = canvas.Canvas(packet)
        for _box in box:
            ((x, y), width, height), page_height = _box
            y = page_height - y - height
            # Set color of the bbox
            can.setStrokeColorRGB(1, 0, 0)
            can.rect(x, y, width, height)
        can.showPage()
        can.save()
        packet.seek(0)
        new_pdf = PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)
    with open(output_pdf, 'wb') as f:
        writer.write(f)

def find_coords(pdf_html, toExclude):
    """
    Find the coordinates of lines in a PDF HTML document, excluding specific line numbers.

    Args:
        pdf_html (BeautifulSoup): The parsed HTML document of the PDF.
        toExclude (list): A list of line numbers to exclude.

    Returns:
        list: A list of coordinates for each excluded line, grouped by page.

    """
    if len(toExclude) == 0:
        return []
    coords = []
    for _page in pdf_html.find_all('page'):
        coords_page = []
        for _line in _page.find_all('line'):
            if int(_line.get('number')) in toExclude:
                xMin = float(_line.get('xmin'))
                yMin = float(_line.get('ymin'))
                xMax = float(_line.get('xmax'))
                yMax = float(_line.get('ymax'))
                width = xMax - xMin
                height = yMax - yMin
                page_height = float(_page.get('height'))
                coords_page.append((((xMin, yMin), width, height), page_height,))
        coords.append(coords_page)
    return coords