from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import io

def _mark_bbox(pdf, boxers, output_pdf,pages,color=(1,0,0)):
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
    # if pages is None:
    #     pages = [1,len(boxers)]
    _c = 0
    for i, page in enumerate(reader.pages):
        if pages != None and (i+1 < pages[0] or i+1 > pages[1]):
            # writer.add_page(page)
            continue
        if len(boxers) == 0:
            # writer.add_page(page)
            continue
        box = boxers[_c]
        _c += 1
        packet = io.BytesIO()
        can = canvas.Canvas(packet)
        for _box in box:
            ((x, y), width, height), page_height = _box
            y = page_height - y - height
            # Set color of the bbox
            can.setStrokeColorRGB(*color)
            can.setLineWidth(2)
            # print(x, y, width, height)
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

def coords_to_line(file_html, coords_tables):
    """
    Converts coordinates to lines based on HTML file and coordinates tables.

    Args:
        file_html (BeautifulSoup): The HTML file.
        coords_tables (list): The list of coordinates tables.

    Returns:
        list: A list of coordinates for each line, grouped by page.
        list: A list of line numbers.
    """
    coords = []
    numbers = []
    for _p,_page in enumerate(file_html.find_all('page')):
        coords_page = []
        tables = coords_tables[_p]
        for _t,table in enumerate(tables):
            # print(f'Page {_p+1}/{len(file_html.find_all("page"))} - Table {_t+1}/{len(tables)}\n')
            ((x,y),w,h),_ = table
            for _l,_line in enumerate(_page.find_all('line')):
                number = int(_line.get('number'))
                xMin = float(_line.get('xmin'))
                yMin = float(_line.get('ymin'))
                xMax = float(_line.get('xmax'))
                yMax = float(_line.get('ymax'))
                width = xMax - xMin
                height = yMax - yMin
                page_height = float(_page.get('height'))
                if xMin>=x and y>=yMin and x+w>=xMax and y+h<=yMax:
                    coords_page.append((((xMin,yMin),width,height),page_height))
                    numbers.append(number)
        coords.append(coords_page)
    return coords,numbers