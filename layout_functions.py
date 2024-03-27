from mark_functions import coords_to_section
def isVertical(line):
    delta_y = float(line.get('ymax')) - float(line.get('ymin'))
    delta_x = float(line.get('xmax')) - float(line.get('xmin'))
    return  delta_x / delta_y < 0.5

def isPDFImage(soup_pdf):
    if len(soup_pdf.find_all('line')) < 3:
        return True
    return False

def isUncopyable(soup_pdf):
    words = soup_pdf.find_all('word')
    chars = set([word.text for word in words])
    total = len(chars)
    count = sum([1 for char in chars if char.find('%') != -1 or char.find('<') != -1 or char.find('&') != -1 or char.find('/') != -1])
    return (count/total) > 0.2

def find_borders(soup_pdf):
    lines = soup_pdf.find_all('line')
    x_coords = []
    y_coords = []
    for line in lines:
        x_coords.append(float(line.get('xmin')))
        x_coords.append(float(line.get('xmax')))
        y_coords.append(float(line.get('ymin')))
        y_coords.append(float(line.get('ymax')))
    return (min(x_coords), min(y_coords)), (max(x_coords), max(y_coords))

def removeVerticalLines(soup_pdf):
    for _p,_pg in enumerate(soup_pdf.find_all('page')):
        lines = _pg.find_all('line')
        for line in lines:
            if isVertical(line):
                line.decompose()
    return soup_pdf

def reOrder(soup_pdf, separators=None):
    """
    Reorders the lines in the given PDF soup based on the specified separators.

    Args:
        soup_pdf (BeautifulSoup): The BeautifulSoup object representing the PDF soup.
        separators (list, optional): A list of separators used to determine the order of lines. 
            Each separator is a list of tuples containing the top, bottom, and center coordinates 
            of the separator line. Defaults to None.

    Returns:
        BeautifulSoup: The reordered PDF soup.

    """
    soup_pdf = removeVerticalLines(soup_pdf)
    parents_changed = []
    for _i, _pg in enumerate(soup_pdf.find_all('page')):
        if separators is not None:
            separator_actual = separators[_i]
            def _sort_key(x):
                if separator_actual is not None:
                    for _i, (top, bottom, center) in enumerate(separator_actual):
                        if float(x.get('ymin')) > top and float(x.get('ymax')) < bottom:
                            if float(x.get('xmin')) > center:
                                return (1, float(x.get('ymin')))
                            elif float(x.get('xmax')) < center:
                                return (0, float(x.get('ymin')))
                    return (float(x.get('ymin')), float(x.get('xmin')))
                else:
                    return (float(x.get('ymin')), float(x.get('xmin')))
        else:
            def _sort_key(x):
                return (float(x.get('ymin')), float(x.get('xmin')))
        lines = _pg.find_all('line')
        lines_sorted = sorted(lines, key=_sort_key)
        oldParents = [line.parent for line in lines]
        for _i, line in enumerate(lines_sorted):
            oldParent = oldParents[_i]
            newElement = line
            oldParent.append(newElement)
            parents_changed.extend([oldParent])
    return soup_pdf

def restore_blocks(soup_pdf):
    for _flow in soup_pdf.find_all('flow'):
        childrens = _flow.find_all('line')
        if len(childrens) == 0:
            _flow.decompose()
    for _block in soup_pdf.find_all('block'):
        childrens = _block.find_all('line')
        if len(childrens) == 0:
            _block.decompose()
            continue
        xmin = min([float(child.get('xmin')) for child in childrens])
        xmax = max([float(child.get('xmax')) for child in childrens])
        ymin = min([float(child.get('ymin')) for child in childrens])
        ymax = max([float(child.get('ymax')) for child in childrens])
        attr = {'xmin':str(xmin),'xmax':str(xmax),'ymin':str(ymin),'ymax':str(ymax)}
        _block.attrs = attr
    return soup_pdf

def numerateLines(soup_pdf):
    _n = 0
    for _i, pg in enumerate(soup_pdf.find_all('page')):
        for _j, ln in enumerate(pg.find_all('line')):
            ln['number'] = _n
            ln['page'] = _i
            _n += 1
    return soup_pdf

def findBlocks(soup_pdf):
    """
    Find and extract blocks from a PDF using BeautifulSoup.

    Args:
        soup_pdf (BeautifulSoup): The BeautifulSoup object representing the parsed PDF.

    Returns:
        list: A list of blocks, where each block is represented as a tuple containing the block coordinates,
        block dimensions, and page height.

    """
    blocks = []
    for _pg in soup_pdf.find_all('page'):
        _block_page = []
        _blocks = _pg.find_all('block')
        for _b in _blocks:
            xMin = float(_b.get('xmin'))
            yMin = float(_b.get('ymin'))
            xMax = float(_b.get('xmax'))
            yMax = float(_b.get('ymax'))
            width = xMax - xMin
            height = yMax - yMin
            _block_page.append((((xMin, yMin), width, height), float(_pg.get('height'))))
        blocks.append(_block_page)
    return blocks

def merge_split_words(soup_pdf):
    """
    Merges adjacent words in a PDF document if their x-coordinates are close enough.

    Args:
        soup_pdf (BeautifulSoup): The parsed HTML representation of the PDF document.

    Returns:
        BeautifulSoup: The modified HTML representation of the PDF document with merged words.
    """
    for __i,_line in enumerate(soup_pdf.find_all('line')):
        _words = list(_line.find_all('word'))
        _i = 0
        word = ''
        attrs = {}
        _initial_indice = float('-inf')
        isInside = False
        while _i < len(_words):
            try:
                if _i+1 == len(_words):
                    string_prox = _words[_i-1]
                    xmin_prox = float(_words[_i-1].get('xmin'))
                else:
                    string_prox = _words[_i+1]
                    xmin_prox = float(_words[_i+1].get('xmin'))
            except:
                _i += 1
                continue
            xmax_act = float(_words[_i].get('xmax'))
            if abs(xmin_prox-xmax_act)< 1.5:
                if not isInside:
                    _initial_indice = _i
                    attrs = _words[_i].attrs
                    word = _words[_i].string + string_prox.string
                    isInside = True
                else:
                    attrs['xmax'] = str(max(float(_words[_i].get('xmax')),float(string_prox.get('xmax'))))
                    word += string_prox.string
            else:
                if word != '':
                    _words[_initial_indice].string = word
                    _words[_initial_indice].attrs = attrs
                    for _ in range(_initial_indice+1,_i+1):
                        _words[_].decompose()
                attrs = {}
                _initial_indice = float('-inf')
                isInside = False
                word = ''

            _i += 1
    return soup_pdf

def merge_split_lines(soup_pdf):
    for _p,_page in enumerate(soup_pdf.find_all('page')):
        last_line = None
        inside_line = False
        for _l,_line in enumerate(_page.find_all('line')):
            if not inside_line:
                last_line = _line
                inside_line = True
                continue
            else:
                actual = _line
                lenght = float(actual.get('ymax')) - float(actual.get('ymin'))
                distanceymin = abs(float(actual.get('ymin')) - float(last_line.get('ymin')))
                distanceymax = abs(float(actual.get('ymax')) - float(last_line.get('ymax')))
                isInside = float(actual.get('ymin')) > float(last_line.get('ymin')) and \
                            float(actual.get('ymax')) < float(last_line.get('ymax')) or \
                            float(actual.get('ymin')) < float(last_line.get('ymin')) and \
                            float(actual.get('ymax')) > float(last_line.get('ymax'))
                isInside = isInside or \
                            (distanceymin < 1 and \
                            distanceymax < lenght/2) or \
                            (distanceymax < 1 and \
                            distanceymin < lenght/2)
                # t = ' '.join([_w.get_text() for _w in last_line.find_all('word')])
                # if _p == 2:
                #     print(
                #             actual.get('ymin') < last_line.get('ymin'),actual.get('ymax') > last_line.get('ymax'),'\n',
                #             actual.attrs,'\n',
                #             ' '.join([_w.get_text() for _w in actual.find_all('word')]),'\n'
                #         ,
                        
                #             last_line.attrs,'\n',
                #             ' '.join([_w.get_text() for _w in last_line.find_all('word')]),'\n'
                #     )
                if isInside:
                    attrs = last_line.attrs
                    if float(actual.get('xmin')) < float(last_line.get('xmin')):
                        last_line,actual = actual,last_line
                        attrs['xmin'] = str(float(actual.get('xmin')))
                    else:
                        attrs['xmax'] = str(float(actual.get('xmax')))
                    for _w in actual.find_all('word'):
                        last_line.append(_w)
                    last_line.attrs = attrs
                    attrs_parent = last_line.parent.attrs
                    attrs_parent['xmax'] = max([_.get('xmax') for _ in last_line.parent.find_all('line')])
                    actual.decompose()
                else:
                    last_line = actual
    return soup_pdf

import tempfile
from PyPDF2 import PdfWriter, PdfReader
def extract_rectangle_from_pdf(input_pdf_path, coordinates):
    temp_file = tempfile.NamedTemporaryFile(delete=False,suffix='.pdf')
    writer = PdfWriter()
    reader = PdfReader(input_pdf_path)
    num_pages = len(reader.pages)
    for page_number in range(num_pages):
        page = reader.pages[page_number]
        page.cropbox.upper_left = coordinates[0]
        page.cropbox.lower_right = coordinates[1]
        writer.add_page(page)
    with open(temp_file.name, 'wb') as output_pdf:
        writer.write(output_pdf)
    return temp_file.name

def found_sections_with_more_then_one_line(sections, soup_pdf, toExcludeSummarization):
    """
    Finds sections with more than one line.

    Args:
        sections (list): A list of sections.
        soup_pdf: The soup_pdf object.
        toExcludeSummarization (list): A list of sections to exclude from summarization.

    Returns:
        tuple: A tuple containing two lists. The first list contains the sections found, and the second list contains the coordinates of the parents.

    """
    sections_without_summarization = []
    page_id = []
    page_heights = []
    sections_lines = []
    _type = []
    for sec in sections:
        number = int(sec[2].get('number'))
        if len(toExcludeSummarization) != 0 and number <= toExcludeSummarization[-1]:
            continue
        line = sec[2]
        sections_without_summarization.append(line)
        page_heights.append(float(sec[1]))
        page_id.append(sec[0])
        sections_lines.append(number)
        _type.append(sec[3])
    parents = [
        (sec.parent,h,pg,_t) 
        for sec,h,pg,_t in zip(sections_without_summarization,page_heights,page_id,_type)
            if int(sec.get('number')) in sections_lines and sec.parent.name == 'block'
    ]
    coords_parents = []
    after_anexo = False
    for _parent,_h,_pg,_t in parents:
        if _t == 'anexo':
            after_anexo = True
        xmin = float(_parent.get('xmin'))
        ymin = float(_parent.get('ymin'))
        xmax = float(_parent.get('xmax'))
        ymax = float(_parent.get('ymax'))
        coord = (((xmin, ymin), xmax, ymax),_h,_pg,_parent)
        if not after_anexo: 
            coords_parents.append((coord,'secao'))
        else:
            coords_parents.append((coord,'anexo'))
    (coords_parents, sections_founded),(coords_parents_anexo,sections_founded_anexo) = coords_to_section(soup_pdf,coords_parents)
    for _i in range(len(sections_founded)):
        sections_founded[_i].append(sections_lines[_i])
        sections_founded[_i] = sorted(list(set(sections_founded[_i])))
    for _i in range(len(sections_founded_anexo)):
        sections_founded_anexo[_i].append(sections_lines[_i+len(sections_founded)])
        sections_founded_anexo[_i] = sorted(list(set(sections_founded_anexo[_i])))
    return (coords_parents, sections_founded),(coords_parents_anexo,sections_founded_anexo)