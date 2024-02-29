from utils import generateGroups,_remountLine,exclude_lines,_remountLinesWithCoord,isUncopyable
from header_detection import removeHeader
from footer_detection import removeFooter
from mark_functions import _mark_bbox,find_coords,coords_to_line
from extract_tables import find_tablesCamelot
import warnings

def removeHeaderAndFooter(
        groups, 
        pageMapping, 
        min_chain=5, 
        max_lines_header=10, 
        max_lines_footer=10, 
        cross_similarities_header=False, 
        cross_similarities_footer=False,
        verbose=True,
        slice_window=3
        ):
    """
    Removes the header and footer from a given file.

    ## Args:
        file (str): The file to process.
        pages (list, optional): The specific pages to process. If None, all pages will be processed. Default is None.
        min_chain (int, optional): The minimum number of similarity lines each and other that must be considered as part of the header or footer. Default is 5.
        max_lines_header (int, optional): The maximum number of lines allowed in the header. Default is 10.
        max_lines_footer (int, optional): The maximum number of lines allowed in the footer. Default is 10.
        cross_similarities_header (bool, optional): Whether to consider cross similarities in the header. Default is False.
        cross_similarities_footer (bool, optional): Whether to consider cross similarities in the footer. Default is False.
        verbose (bool, optional): Whether to display warnings. Default is True.
        slice_window (int, optional): The size of the window to slice the sentences. Default is 3.

    ## Attention:
        Activating the cross_similarities_header and cross_similarities_footer parameters may significantly slow down the function.
        
    ## Returns:
        tuple: A tuple containing the processed soup and the sections to exclude from the header and footer.
    """
    if verbose:
        warnings.simplefilter('always', ResourceWarning)
        if cross_similarities_footer:
            warnings.warn('Cross similarities in the footer may significantly slow down the function.',ResourceWarning)
        if cross_similarities_header:
            warnings.warn('Cross similarities in the header may significantly slow down the function.',ResourceWarning)
        warnings.warn('This may take a while...',ResourceWarning)  
        warnings.warn('To disable this warning, set verbose to False.')
        warnings.simplefilter('ignore', ResourceWarning)
    toExclude_Header = removeHeader(groups, 
                                    min_chain=min_chain, 
                                    n_lines=max_lines_header, 
                                    cross_similarities_header=cross_similarities_header,
                                    pageMap=pageMapping,slice_window=slice_window)
    toExclude_Footer = removeFooter(groups, 
                                    min_chain=min_chain, 
                                    n_lines=max_lines_footer, 
                                    cross_similarities_footer=cross_similarities_footer,
                                    pageMap=pageMapping,slice_window=slice_window)
    return sorted(list(set(toExclude_Header + toExclude_Footer)))

def save_html(file, soup):
    """
    Save the HTML content of a BeautifulSoup object to a file.

    Args:
        file (Path): The file path where the HTML content will be saved.
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.

    Returns:
        None
    """
    with open(file, 'w') as f:
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
    with open(file, 'w') as f:
        f.write('\n'.join(_remountLine(soup.find_all('line'))[1]))

def mark_bbox(pdf_html, toExclude, file, out,pages=None,color=(1,0,0)):
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
    _mark_bbox(file, coords, out,pages=pages,color=color)


def removeTableCamelot(file, file_html, pages):
    """
    Removes tables from a PDF file using the Camelot library.

    Args:
        file (str): Path to the input PDF file.
        file_html (str): Path to the output HTML file.
        pages (str): Pages to extract tables from (e.g., '1-3', '5').

    Returns:
        list: A list of tables extracted from the PDF file.
    """
    return find_tablesCamelot(file, file_html, pages)

def preprocess_pdf(
        file:str,
        pages:list=None,
        isBbox=True,
        out_file_bbox:str=None,
        out_path_html:str=None,
        out_path_txt:str=None,
        **kwargs
    ):
    """
    Preprocesses a PDF file by performing various operations such as generating groups, removing headers and footers,
    marking bounding boxes, removing tables, excluding lines, and saving the result as HTML or TXT.

    Args:
        file (str): The path to the PDF file.
        pages (list, optional): A list of page numbers to process. Defaults to None, which processes all pages.
        isBbox (bool, optional): Indicates whether to mark bounding boxes. Defaults to True.
        out_file_bbox (str, optional): The path to save the PDF file with marked bounding boxes. Defaults to None,
            which overwrites the original file.
        out_path_html (str, optional): The path to save the preprocessed PDF as HTML. Defaults to None, which
            does not save as HTML.
        out_path_txt (str, optional): The path to save the preprocessed PDF as TXT. Defaults to None, which
            does not save as TXT.
        **kwargs: Additional keyword arguments for customizing the preprocessing operations.
        See the removeHeaderAndFooter function for more details.

    Returns:
        str or None: If neither out_path_html nor out_path_txt is provided, returns the preprocessed PDF as a string.
            Otherwise, returns None.
    """
    groups,soup_pdf,page_mapping = generateGroups(file,pages=pages)
    if isUncopyable(soup_pdf):
        print(f'File {file} is uncopyable')
        return None
    toExcludeHeaderAndFooter = removeHeaderAndFooter(groups,page_mapping,**kwargs)
    if isBbox:
        if not out_file_bbox:
            out_file_bbox = file
        mark_bbox(soup_pdf,toExcludeHeaderAndFooter,file,out_file_bbox,pages=pages)
    coord_tables_camelot = removeTableCamelot(file,soup_pdf,pages)
    coords_inside_tables,toExcludeLinesTables = coords_to_line(soup_pdf,coord_tables_camelot)
    if isBbox:
        _mark_bbox(out_file_bbox.__str__(), coord_tables_camelot, out_file_bbox.__str__(),pages=pages,color=(0.447, 0.055, 0.58))
        _mark_bbox(out_file_bbox.__str__(), coords_inside_tables, out_file_bbox.__str__(),pages=pages,color=(0.447, 0.055, 0.58))
    soup_pdf = exclude_lines(soup_pdf, toExcludeHeaderAndFooter+toExcludeLinesTables)
    if out_path_html:
        save_html(out_path_html,soup_pdf)
    if out_path_txt:
        save_txt(out_path_txt,soup_pdf)
    if out_path_html is None and out_path_txt is None:
        return _remountLine(soup_pdf.find_all('line'))[1]
    return None
    