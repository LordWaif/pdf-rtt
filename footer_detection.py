from utils import merge_dicts,_remountLine
from similarity_functions import spacy_cossine_similarity
from tqdm import tqdm
import time,math
from collections import OrderedDict

def find_footer(pdf, n=10):
    """
    Find the footer lines in a PDF.

    Args:
        pdf (PDF): The PDF object to search for footer lines.
        n (int): The number of lines to consider as the footer. Default is 10.

    Returns:
        list: A list of footer lines found in the PDF.
    """
    def _getDistance(p1,p2):
        return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
    all_lines = pdf.find_all('line')
    output = []
    if len(all_lines) > n:
        footer = all_lines[-n:]
    else:
        footer = all_lines
    # true_footer = list()
    # for _i,line in enumerate(footer):
    #     if _i+1 >= len(footer):
    #         break 
    #     isVertical_actual = isVertical(footer[_i])
    #     isVertical_next = isVertical(footer[_i+1])
    #     # Calcular distancia entre dois pontos
    #     if isVertical_next and  not isVertical_actual:
    #         p1 = (float(line.get('xmax')),float(line.get('ymin')))
    #         p2 = (float(footer[_i+1].get('xmin')),float(footer[_i+1].get('ymax')))
    #         d1 = _getDistance(p1,p2)
    #         p1 = (float(line.get('xmin')),float(line.get('ymin')))
    #         d2 = _getDistance(p1,p2)
    #         distance = min(d1,d2)
    #     elif isVertical_actual and not isVertical_next:
    #         p1 = (float(line.get('xmin')),float(line.get('ymax')))
    #         p2 = (float(footer[_i+1].get('xmax')),float(footer[_i+1].get('ymin')))
    #         d1 = _getDistance(p1,p2)
    #         p2 = (float(footer[_i+1].get('xmin')),float(footer[_i+1].get('ymin')))
    #         d2 = _getDistance(p1,p2)
    #         distance = min(d1,d2)
    #     elif isVertical_actual and isVertical_next:
    #         p1 = (float(line.get('xmin')),float(line.get('ymax')))
    #         p2 = (float(footer[_i+1].get('xmin')),float(footer[_i+1].get('ymax')))
    #         distance = _getDistance(p1,p2)
    #     else:
    #         p1 = (float(line.get('xmin')),float(line.get('ymin')))
    #         p2 = (float(footer[_i+1].get('xmin')),float(footer[_i+1].get('ymin')))
    #         distance = _getDistance(p1,p2)
    #     if distance < 65:
    #         true_footer.append(line)
    #         true_footer.append(footer[_i+1])
    #     else:
    #         if (isVertical_actual or isVertical_next) and distance < 150:
    #             true_footer.append(line)
    #             true_footer.append(footer[_i+1])
    #         else:
    #             break
    #         # print(f'Line {_i+1} of {len(footer)}: {_remountLine([line])[1]}::{_remountLine([footer[_i+1]])[1]} - Distance: {distance}')
    # true_footer = list(OrderedDict.fromkeys(true_footer).keys())
    # # print(_remountLine(true_footer)[1])
    # footer = true_footer
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
            # print(footers[_i], footers[_i+_j+1])
            # print('\n\n')
            for key, value in similarity.items():
                lines = key.split('-')
                if key not in similarities:
                    similarities[key] = [value]
                else:
                    similarities[key].append(value)
            # print(similarities)
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