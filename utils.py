import bs4
import subprocess
from layout_functions import numerateLines,isPDFCollumn
from PyPDF2 import PdfWriter, PdfReader
import tempfile


def generateGroups(path, pages,indentify_collumns=False):
    from layout_functions import reOrder
    """
    Generate groups and soup object from a PDF file.

    ## Args:
        path (str): The path to the PDF file.
        pages (tuple): A tuple containing the start and end page numbers to extract. If None, all pages will be extracted.

    ## Returns:
        tuple: A tuple containing the groups, soup object, and page map.
            - groups (list): A list of groups.
            - soup (BeautifulSoup): The soup object generated from the PDF HTML.
            - page_map (dict): A dictionary mapping page numbers to line numbers.

    ## Raises:
        subprocess.CalledProcessError: If the pdftotext command fails.

    """
    if pages is not None:
        cmd = ['pdftotext', '-layout', path, '-bbox-layout', '/dev/stdout', '-f', str(pages[0]), '-l', str(pages[1])]
    else:
        cmd = ['pdftotext', '-layout', path, '-bbox-layout', '/dev/stdout']
    pdf_html = subprocess.check_output(cmd).decode('utf-8')
    soup = bs4.BeautifulSoup(pdf_html, 'html.parser')
    if indentify_collumns:
        isCollumn , collumns = isPDFCollumn(soup)
    else:
        isCollumn = False
    # from mark_functions import _mark_bbox
    # coords_pages = []
    # for _p in collumns.keys():
    #     coords_p = []
    #     for _l in collumns[_p]:
    #         xMin = float(_l[2]-2)
    #         yMin = float(_l[0])
    #         xMax = float(_l[2]+2)
    #         yMax = float(_l[1])
    #         width = xMax - xMin
    #         height = yMax - yMin
    #         coords_p.append(
    #             (
    #                 (
    #                     (xMin,yMin),
    #                     width,height
    #                 ),
    #                 float(soup.find('page').get('height'))
    #             )
    #         )
    #     coords_pages.append(coords_p)
    # _mark_bbox(
    #     path,
    #     coords_pages,
    #     'pdf_marked.pdf',
    #     pages
    # )
    if isCollumn:
        soup = reOrder(soup,collumns)
    else:
        soup = reOrder(soup)
    soup, page_map = numerateLines(soup)
    from layout_functions import findBlocks
    # coords_blocks = findBlocks(soup)
    # from mark_functions import _mark_bbox
    # _mark_bbox(path, coords_blocks, 'pdf_marked.pdf',pages)
    # Salvar o arquivo html
    # with open('pdf.html', 'w') as f:
    #     f.write(soup.prettify())
    groups = group_pages_by_size(soup.find_all('page'))
    return groups, soup, page_map


def group_pages_by_size(pages, threshold=2):
    '''Group pages by size.

    Args:
        pages (list): A list of page objects.
        threshold (float, optional): The maximum difference allowed between page sizes to group them together. Defaults to 2.

    Returns:
        list: A list of groups, where each group is a list of page objects with similar sizes.
    '''
    groups = []
    for ind,page in enumerate(pages):
        if len(groups) == 0:
            groups.append([page])
        else:
            for group in groups:
                if abs(float(group[0].get('width')) - float(page.get('width'))) < threshold:
                    group.append(page)
                    break
            else:
                groups.append([page])
    return groups

def _remountLine(lines):
    '''Remounts a line to be used in the cosine similarity function.
    
    Args:
        lines (list): A list of lines containing dictionaries with 'number' and 'text' keys.
        
    Returns:
        tuple: A tuple containing two lists. The first list contains the 'number' values from the input lines,
               and the second list contains the concatenated 'text' values from the input lines.
    '''
    _pgN,_lines = [],[]
    for i, line in enumerate(lines):
        _pgN.append(int(line.get('number')))
        content = ' '.join([_.text for _ in line.find_all('word')])
        _lines.append(content)
    return _pgN, _lines

def _remountLinesWithCoord(lines):
    '''Remounts a line to be used in the cosine similarity function.
    
    Args:
        lines (list): A list of lines containing dictionaries with 'number' and 'bbox' keys.
        
    Returns:
        tuple: A tuple containing two lists. The first list contains the 'number' values from the input lines,
               and the second list contains the 'bbox' values from the input lines.
    '''
    _pgN,_lines,_coord = [],[],[]
    for i, line in enumerate(lines):
        _pgN.append(int(line.get('number')))
        content = ' '.join([_.text for _ in line.find_all('word')])
        _lines.append(content)
        _coord.append({'xmin':float(line.get('xmin')),
                       'ymin':float(line.get('ymin')),
                       'xmax':float(line.get('xmax')),
                       'ymax':float(line.get('ymax'))})
    return _pgN, _lines, _coord

def merge_dicts(original_dict):
    '''Merges the keys of a dictionary that are consecutive.

    Args:
        original_dict (dict): The dictionary to be merged.

    Returns:
        dict: The merged dictionary.
    '''
    keys = list(original_dict.keys())
    i = 0
    while i < len(keys):
        j = 0
        while j < len(keys):
            if keys[i].split('-')[-1] == keys[j].split('-')[0]:
                p2 = '-'.join(keys[j].split('-')[1:])
                new_key = f'{keys[i]}-{p2}'
                new_value = original_dict[keys[i]] + original_dict[keys[j]]
                original_dict[new_key] = new_value
                del original_dict[keys[i]]
                del original_dict[keys[j]]
                keys = list(original_dict.keys())
                i = 0
                j = 0
            j += 1
        i += 1
    return original_dict

def exclude_lines(pdf, toExclude):
    """
    Exclude lines from a PDF based on the line numbers provided.

    Args:
        pdf (PDF object): The PDF object to modify.
        toExclude (list): A list of line numbers to exclude.

    Returns:
        PDF object: The modified PDF object with excluded lines.
    """
    for page in pdf.find_all('page'):
        for line in page.find_all('line'):
            if int(line.get('number')) in toExclude:
                line.decompose()
    return pdf

def isUncopyable(soup_pdf):
    """
    Checks if the given soup_pdf is uncopyable.

    Parameters:
    soup_pdf (BeautifulSoup): The BeautifulSoup object representing the PDF.

    Returns:
    bool: True if the PDF is uncopyable, False otherwise.
    """
    words = soup_pdf.find_all('word')
    chars = set([word.text for word in words])
    total = len(chars)
    count = sum([1 for char in chars if char.find('%') != -1 or char.find('<') != -1 or char.find('&') != -1 or char.find('/') != -1])
    return (count/total) > 0.2

def merge_split_words(soup_pdf):
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

def extract_rectangle_from_pdf(input_pdf_path, coordinates):
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False,suffix='.pdf')
    # Create a PDF writer object
    writer = PdfWriter()

    # Read the input PDF
    reader = PdfReader(input_pdf_path)

    # Get the number of pages in the input PDF
    num_pages = len(reader.pages)

    # Loop over all the pages
    for page_number in range(num_pages):
        # Get the page
        page = reader.pages[page_number]
        
        # Set the crop box coordinates
        page.cropbox.upper_left = coordinates[0]
        page.cropbox.lower_right = coordinates[1]

        # Add the page to the writer object
        writer.add_page(page)

    # Write the output PDF
    with open(temp_file.name, 'wb') as output_pdf:
        writer.write(output_pdf)

    return temp_file.name