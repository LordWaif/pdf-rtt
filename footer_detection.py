from utils import merge_dicts,_remountLine
from similarity_functions import spacy_cossine_similarity

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

def removeFooter(groups, min_chain=3):
    """
    Removes footers from a given list of groups.

    Args:
        groups (list): A list of groups, where each group is a list of pages.
        min_chain (int, optional): The minimum number of consecutive lines in a footer to be considered. Defaults to 3.

    Returns:
        list: A list of line numbers to be excluded as footers.
    """

    def reverse_footer(footer):
        return footer[0][::-1], footer[1][::-1]

    footers = [find_footer(page) for group in groups for page in group]
    similarities = dict()
    footers = [reverse_footer(footer) for footer in footers]

    for _i, footer in enumerate(footers):
        print(f'Page {_i+1} of {len(footers)}')
        if _i < len(footers) - 1:
            similarity = spacy_cossine_similarity(footers[_i], footers[_i+1], footer=True)
            for key, value in similarity.items():
                lines = key.split('-')
                if key not in similarities:
                    similarities[key] = [value]
                else:
                    similarities[key].append(value)

    similarities = merge_dicts(similarities)
    toExclude = []

    if len(footers) <= 3:
        min_chain = float('-inf')

    for key, value in similarities.items():
        lines = key.split('-')
        if len(lines) <= min_chain:
            continue
        if sum(value) / len(value) > 0.9:
            toExclude.extend(list(map(int, lines)))

    return toExclude