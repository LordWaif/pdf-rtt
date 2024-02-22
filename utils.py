import bs4
import subprocess


def generateGroups(path):
    """
    Generate groups and soup object from a PDF file.

    Args:
        path (str): The path to the PDF file.

    Returns:
        tuple: A tuple containing the groups and soup object.
            - groups (list): A list of groups.
            - soup (BeautifulSoup): The soup object generated from the PDF HTML.
    """
    cmd = ['pdftotext', '-layout', path, '-bbox-layout', '/dev/stdout']
    pdf_html = subprocess.check_output(cmd).decode('utf-8')
    soup = bs4.BeautifulSoup(pdf_html, 'html.parser')
    for _i,ln in enumerate(soup.find_all('line')):
        ln['number'] = _i
    groups = group_pages_by_size(soup.find_all('page'))
    return groups, soup


def group_pages_by_size(pages, threshold=2):
    '''Group pages by size.

    Args:
        pages (list): A list of page objects.
        threshold (float, optional): The maximum difference allowed between page sizes to group them together. Defaults to 2.

    Returns:
        list: A list of groups, where each group is a list of page objects with similar sizes.
    '''
    groups = []
    for page in pages:
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
        _lines.append(' '.join([_.text for _ in line.find_all('word')]))
    return _pgN, _lines

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