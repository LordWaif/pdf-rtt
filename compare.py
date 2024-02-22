from utils import generateGroups,_remountLine,exclude_lines
from header_detection import removeHeader
from footer_detection import removeFooter
from mark_functions import _mark_bbox,find_coords

def removeHeaderAndFooter(file):
    """
    Removes the header and footer from a given file.

    Args:
        file (str): The file to process.

    Returns:
        tuple: A tuple containing the processed soup and the sections to exclude from the header and footer.
    """
    groups, soup = generateGroups(file)
    toExclude_Header = removeHeader(groups)
    toExclude_Footer = removeFooter(groups)
    return soup, sorted(list(set(toExclude_Header + toExclude_Footer)))

def save_html(file, soup):
    """
    Save the HTML content of a BeautifulSoup object to a file.

    Args:
        file (Path): The file path where the HTML content will be saved.
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.

    Returns:
        None
    """
    with open(f'./html/{file.stem}.html', 'w') as f:
        f.write(str(soup.prettify()))

def save_txt(file, soup):
    """
    Save the contents of a BeautifulSoup object as a text file.

    Args:
        file (Path): The file path to save the text file.
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.

    Returns:
        None
    """
    with open(f'./html/{file.stem}.txt', 'w') as f:
        f.write('\n'.join(_remountLine(soup.find_all('line'))[1]))

def mark_bbox(pdf_html, toExclude, file, out):
    """
    Marks the bounding boxes of specified coordinates on a PDF file.

    Args:
        pdf_html (str): The PDF HTML content.
        toExclude (list): List of coordinates to exclude from marking.
        file (str): The input PDF file path.
        out (str): The output PDF file path.

    Returns:
        None
    """
    coords = find_coords(pdf_html, toExclude)
    _mark_bbox(file, coords, out)



if __name__ == '__main__':
    import pathlib
    from tqdm import tqdm
    files = list(pathlib.Path('./.pdf_files').glob('*.pdf'))
    bar = tqdm(total=len(files))
    for file in files:
        # # toAnalisys = ['ARQ-01303619000138-2023-61','ARQ-76416940000128-2023-332','ARQ-83102319000155-2023-140']
        # toAnalisys = ['ARQ-87572079000103-2021-12']
        # if file.stem not in toAnalisys:
        #     bar.update(1)
        #     continue
        print(file)
        out = file.parent.absolute().parent /pathlib.Path('bbox') / pathlib.Path(file.stem+'_bbox.pdf')
        pdf_html,toExclude = removeHeaderAndFooter(file)
        if len(toExclude) != 0:
            mark_bbox(pdf_html,toExclude,file,out)
            pdf_html = exclude_lines(pdf_html, toExclude)
            save_html(file,pdf_html)
            save_txt(file,pdf_html)
        bar.update(1)
    bar.close()
            
