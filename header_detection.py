from utils import _remountLine,merge_dicts
from similarity_functions import spacy_cossine_similarity
import bs4,time
from typing import Tuple
from tqdm import tqdm

def find_header(
        pdf:bs4.BeautifulSoup,
        n=10) -> Tuple[list,list]:
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

import statistics
def removeHeader(groups,min_chain=3,n_lines=10,cross_similarities_header=False,pageMap=None,slice_window=3,reach=1):
    """
    Removes headers from a list of groups.

    Args:
        groups (list): A list of groups, where each group is a list of pages.
        min_chain (int, optional): The minimum number of consecutive lines that must have similar headers to be considered a header. Defaults to 3.
        n_lines (int, optional): The number of lines to consider when comparing headers. Defaults to 10.
        cross_similarities_header (bool, optional): Whether to consider cross similarities between headers. Defaults to False.

    Returns:
        list: A list of line numbers to exclude, representing the lines that contain headers.
    """
    headers = [find_header(page,n=n_lines) for group in groups for page in group]
    similarities = dict()
    bar = tqdm(total=len(headers),desc='Removing headers')
    timePerPage = 0
    start = time.time()
    for _i, header in enumerate(headers):
        # print(f'Page {_i+1} of {len(headers)}')
        for _j in range(reach):
            if _i+_j+1 >= len(headers):
                break
            similarity = spacy_cossine_similarity(headers[_i], headers[_i+_j+1],header=True,cross_similarities_header=cross_similarities_header,slice_window=slice_window)
            # print(headers[_i], headers[_i+1])
            for key, value in similarity.items():
                lines = key.split('-')
                if key not in similarities:
                    similarities[key] = [value]
                else:
                    similarities[key].append(value)
        bar.update(1)
    end = time.time()
    bar.clear()
    bar.close()
    timePerPage = end-start
    print(f'(Header) Average time per page: {timePerPage/len(headers)}')
    similarities = merge_dicts(similarities)
    toExclude = []

    if len(headers) <= min_chain:
        min_chain = float('-inf')
        # min_chain = int(len(headers)*0.75)

    for key, value in similarities.items():
        lines = key.split('-')
        media = statistics.mean(value)
        if len(lines) <= min_chain:
            continue
        for _i,_v in enumerate(value):
            if _v > 0.98:
                toExclude.append(int(lines[_i]))
                toExclude.append(int(lines[_i+1]))
        # print(key, value, sum(value)/len(value))
        if media > 0.85:
            toExclude.extend(list(map(int, lines)))
    return toExclude