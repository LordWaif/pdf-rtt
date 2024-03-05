from utils import merge_dicts,_remountLine
from similarity_functions import spacy_cossine_similarity
from tqdm import tqdm
import time

def find_footer(pdf, n=10):
    """
    Find the footer lines in a PDF.

    Args:
        pdf (PDF): The PDF object to search for footer lines.
        n (int): The number of lines to consider as the footer. Default is 10.

    Returns:
        list: A list of footer lines found in the PDF.
    """
    all_lines = pdf.find_all('line')
    output = []
    if len(all_lines) > n:
        footer = all_lines[-n:]
    else:
        footer = all_lines
    output.extend(footer)
    return _remountLine(output)

def removeFooter(groups, min_chain=3, n_lines=10, cross_similarities_footer=False, pageMap=None, slice_window=3,reach=1):
    """
    Removes footers from a given list of groups.

    Args:
        groups (list): A list of groups, where each group is a list of pages.
        min_chain (int, optional): The minimum number of consecutive lines in a footer to be considered. Defaults to 3.
        n_lines (int, optional): The number of lines to consider for each page when finding footers. Defaults to 10.
        cross_similarities_footer (bool, optional): Whether to calculate cross similarities between footers. Defaults to False.

    Returns:
        list: A list of line numbers to be excluded as footers.
    """

    def reverse_footer(footer):
        return footer[0][::-1], footer[1][::-1]

    footers = [find_footer(page, n=n_lines) for group in groups for page in group]
    similarities = dict()
    footers = [reverse_footer(footer) for footer in footers]
    bar = tqdm(total=len(footers), desc='Removing footers')
    timePerPage = 0
    start = time.time()
    for _i, footer in enumerate(footers):
        # print(f'Page {_i+1} of {len(footers)}')
        for _j in range(reach):
            if _i+_j+1 >= len(footers):
                break
            similarity = spacy_cossine_similarity(footers[_i], footers[_i+_j+1],footer=True,cross_similarities_footer=cross_similarities_footer,slice_window=slice_window)
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
    print(f'(Footer) Average time per page: {timePerPage/len(footers)}')
    similarities = merge_dicts(similarities)
    toExclude = []

    if len(footers) <= min_chain:
        min_chain = float('-inf')

    for key, value in similarities.items():
        lines = key.split('-')
        if len(lines) <= min_chain:
            continue
        if sum(value) / len(value) > 0.9:
            toExclude.extend(list(map(int, lines)))

    return toExclude