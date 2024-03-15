def isVertical(line):
    """
    Determines whether a line is vertical or not.

    Args:
        line (dict): A dictionary representing a line with 'xmin', 'ymin', 'xmax', and 'ymax' keys.

    Returns:
        bool: True if the line is vertical, False otherwise.
    """
    delta_y = float(line.get('ymax')) - float(line.get('ymin'))
    delta_x = float(line.get('xmax')) - float(line.get('xmin'))
    return delta_y > delta_x

import statistics
def isPDFCollumn(soup_pdf):
    """
    Determines if a PDF document has multiple columns.

    Args:
        soup_pdf (BeautifulSoup): The parsed HTML representation of the PDF document.

    Returns:
        tuple: A tuple containing two elements:
            - A boolean indicating whether the document has multiple columns.
            - A dictionary containing the separators between the columns for each page.

    """
    proportion_doc = 0
    pages = list(soup_pdf.find_all('page'))
    separators = {_:[] for _ in range(len(pages))}
    for _i,_page in enumerate(pages):
        height = int(float(_page.get('height')))
        groups = {_:[] for _ in range(0,height,15)}
        for _line in _page.find_all('line'):
            y = _line.get('ymin')
            y = int(float(y))
            for __i,(k,v) in enumerate(groups.items()):
                chaves = list(groups.keys())
                if chaves[__i] <= y < chaves[__i+1]:
                    groups[k].append(_line)
        for k,v in groups.items():
            groups[k] = sorted(v, key=lambda x: float(x.get('xmin')))
            if len(groups[k]) == 0:
                continue
            left_side = groups[k][0]
            right_side = groups[k][-1]
            distantece_sep = float(right_side.get('xmin')) - float(left_side.get('xmax'))
            if distantece_sep > 10:
                separator = (float(left_side.get('ymin')), float(right_side.get('ymax')),int(float(left_side.get('xmax'))+distantece_sep/2))
                separators[_i].append(separator)
        total_parts_len = len(groups)
        greatThen3 = sum([len(v) for k,v in groups.items() if len(v)>2])
        proportion = greatThen3/total_parts_len
        proportion_doc += proportion

        primeira_moda = statistics.mode([separator[2] for separator in separators[_i]])
        top_primeira_moda = min([separator[0] for separator in separators[_i] if separator[2] == primeira_moda])
        bottom_primeira_moda = max([separator[1] for separator in separators[_i] if separator[2] == primeira_moda])

        coluna1 = (top_primeira_moda,bottom_primeira_moda,primeira_moda)
        separators[_i] = [coluna1]
    proportion_doc = proportion_doc/len(pages)
    return proportion_doc > 1.3,separators

def isPDFImage(soup_pdf):
    """
    Checks if the given PDF soup contains an image.

    Args:
        soup_pdf (BeautifulSoup): The BeautifulSoup object representing the PDF.

    Returns:
        bool: True if the PDF contains an image, False otherwise.
    """
    from utils import _remountLine
    if len(_remountLine(soup_pdf.find_all('line'))[1]) < 3:
        return True
    return False

def find_borders(soup_pdf):
    """
    Finds the minimum and maximum coordinates of the borders in a PDF represented by a BeautifulSoup object.

    Args:
        soup_pdf (BeautifulSoup): The BeautifulSoup object representing the PDF.

    Returns:
        tuple: A tuple containing the minimum and maximum coordinates of the borders in the format ((min_x, min_y), (max_x, max_y)).
    """
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
    """
    Removes vertical lines from the given PDF soup.

    Args:
        soup_pdf (BeautifulSoup): The PDF soup to process.

    Returns:
        BeautifulSoup: The modified PDF soup with vertical lines removed.
    """
    for _pg in soup_pdf.find_all('page'):
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
    return soup_pdf

def numerateLines(soup_pdf):
    """
    Numerates the lines in the given soup_pdf object.

    Args:
        soup_pdf: The BeautifulSoup object representing the PDF.

    Returns:
        A tuple containing the modified soup_pdf object and a page_map dictionary.
        The page_map dictionary maps each page number to a list of line numbers on that page.
    """
    _n = 0
    page_map = {}
    for _i, pg in enumerate(soup_pdf.find_all('page')):
        for _j, ln in enumerate(pg.find_all('line')):
            ln['number'] = _n
            if page_map.get(_i) is None:
                page_map[_i] = [_n]
            else:
                page_map[_i].append(_n)
            _n += 1
    return soup_pdf, page_map

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