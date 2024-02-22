from utils import _remountLine,merge_dicts
from similarity_functions import spacy_cossine_similarity

def find_header(pdf,n=10):
    '''
    Find the header of a pdf using pdftotext.

    Parameters:
    - pdf: The PDF object to extract the header from.
    - n: The number of lines to consider as the header. Default is 10.

    Returns:
    - A list of lines that make up the header.
    '''
    all_lines = pdf.find_all('line')
    output = []
    if len(all_lines) > n:
        header = all_lines[:n]
    else:
        header = all_lines
    output.extend(header)
    return _remountLine(output)

def removeHeader(groups):
    """
    Removes headers from a list of groups.

    Args:
        groups (list): A list of groups, where each group is a list of pages.

    Returns:
        list: A list of line numbers to exclude, representing the lines that contain headers.
    """
    headers = [find_header(page) for group in groups for page in group]
    similarities = dict()
    for _i, header in enumerate(headers):
        if _i < len(headers) - 1:
            similarity = spacy_cossine_similarity(headers[_i], headers[_i+1],header=True)
            # print(similarity)
            for key, value in similarity.items():
                lines = key.split('-')
                if key not in similarities:
                    similarities[key] = [value]
                else:
                    similarities[key].append(value)
    similarities = merge_dicts(similarities)
    toExclude = []
    for key, value in similarities.items():
        lines = key.split('-')
        if sum(value)/len(value) > 0.9:
            toExclude.extend(list(map(int, lines)))
    return toExclude