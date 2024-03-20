from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import io

def _mark_bbox(pdf, boxers, output_pdf, pages, color=(1, 0, 0)):
    """
    Marks bounding boxes on the specified pages of a PDF document.

    Args:
        pdf (str): The path to the input PDF file.
        boxers (list): A list of bounding boxes to mark on the pages. Each bounding box is represented as a tuple
            containing the coordinates ((x, y), width, height) and the page height.
        output_pdf (str): The path to the output PDF file.
        pages (tuple): A tuple specifying the range of pages to mark. If None, all pages will be marked.
        color (tuple): The RGB color values (between 0 and 1) to use for marking the bounding boxes. Default is red (1, 0, 0).
    """
    reader = PdfReader(pdf)
    writer = PdfWriter()
    if pages is not None:
        pages_list = reader.pages[pages[0] - 1 : pages[1]]
    else:
        pages_list = reader.pages

    _c = 0
    for i, page in enumerate(pages_list):
        if len(boxers) == 0:
            writer.add_page(page)
            continue
        if _c >= len(boxers):
            break
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
            can.rect(x, y, width, height)
        can.showPage()
        can.save()
        packet.seek(0)
        new_pdf = PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

def find_coords(pdf_html, toExclude):
    """
    Find the coordinates of specific lines in a PDF HTML.

    Args:
        pdf_html (BeautifulSoup): The parsed HTML of the PDF.
        toExclude (list): A list of line numbers to exclude.

    Returns:
        list: A nested list of coordinates for each excluded line in each page.
              Each coordinate is represented as a tuple of the form (((xMin, yMin), width, height),page_height).
              The page height is also included in the tuple.
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
    Converts coordinates to lines based on the given HTML file and coordinates tables.

    Args:
        file_html (BeautifulSoup): The HTML file to extract coordinates from.
        coords_tables (list): A list of coordinates tables.

    Returns:
        tuple: A tuple containing two lists - `coords` and `numbers`.
            - `coords` (list): A list of coordinates for each page, where each page contains a list of coordinates for each table.
            - `numbers` (list): A list of numbers corresponding to each line.

    """
    coords = []
    numbers = []
    for _p,_page in enumerate(file_html.find_all('page')):
        coords_page = []
        tables = coords_tables[_p]
        for _t,table in enumerate(tables):
            ((x,y),w,h),_ = table
            for _l,_line in enumerate(_page.find_all('line')):
                number = int(_line.get('number'))
                xMin = round(float(_line.get('xmin')),2)
                yMin = round(float(_line.get('ymin')),2)
                xMax = round(float(_line.get('xmax')),2)
                yMax = round(float(_line.get('ymax')),2)
                width = xMax - xMin
                height = yMax - yMin
                page_height = float(_page.get('height'))
                if xMin>=round(x,2) and yMin>=round(y,2) and round(x+w,2)>=xMax and round(y+h,2)>=yMax:
                    coords_page.append((((xMin,yMin),width,height),page_height))
                    numbers.append(number)
        coords.append(coords_page)
    return coords,numbers

def coords_to_section(file_html, coords_lines_section):
    coords = []
    id_sections = []

    coords_anexo = []
    id_sections_anexo = []
    for _t,(coords_section,_type) in enumerate(coords_lines_section):
        number_l = []
        coords_page = []
        ((x,y),w,h),pg_height,page,block_section = coords_section
        # x,y = round(x,3),round(y,3)
        pages = list(file_html.find_all('page'))
        page_to_search = pages[page]
        for _l,_line in enumerate(page_to_search.find_all('line')):
            number = int(_line.get('number'))
            xMin = float(_line.get('xmin'))
            yMin = float(_line.get('ymin'))
            xMax = float(_line.get('xmax'))
            yMax = float(_line.get('ymax'))
            width = xMax - xMin
            height = yMax - yMin
            page_height = pg_height
            # if number == 85:
            #     # print(f"{_line}")
            #     print(xMin,yMin,xMax,yMax)
            #     print(x,y,w,h)
            #     print(xMin>=x,yMin>=y,w>=xMax,h>=yMax)
            if xMin>=x and yMin>=y and w>=xMax and h>=yMax:
                coords_page.append((((xMin,yMin),width,height),page_height))
                block_section.append(_line)
                number_l.append(number)
        if _type == 'secao':
            coords.append(coords_page)
            id_sections.append(number_l)
        elif _type == 'anexo':
            coords_anexo.append(coords_page)
            id_sections_anexo.append(number_l)
    return (coords,id_sections),(coords_anexo,id_sections_anexo)