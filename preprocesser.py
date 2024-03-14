from utils import generateGroups,_remountLine,exclude_lines,_remountLinesWithCoord,isUncopyable,merge_split_words
from header_detection import removeHeader
from footer_detection import removeFooter
from mark_functions import _mark_bbox,find_coords,coords_to_line
from extract_tables import find_tablesCamelot
from layout_functions import isPDFImage
import warnings,time

def removeHeaderAndFooter(
        groups, 
        pageMapping, 
        min_chain=5, 
        max_lines_header=10, 
        max_lines_footer=10, 
        cross_similarities_header=False, 
        cross_similarities_footer=False,
        verbose=True,
        slice_window=3,
        header=True,
        footer=True,
        reach = 1
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
    toExclude = []
    if header:
        toExclude_Header = removeHeader(groups, 
                                        min_chain=min_chain, 
                                        n_lines=max_lines_header, 
                                        cross_similarities_header=cross_similarities_header,
                                        pageMap=pageMapping,slice_window=slice_window,reach=reach)
        toExclude.extend(toExclude_Header)
    if footer:
        toExclude_Footer = removeFooter(groups, 
                                        min_chain=min_chain, 
                                        n_lines=max_lines_footer, 
                                        cross_similarities_footer=cross_similarities_footer,
                                        pageMap=pageMapping,slice_window=slice_window,reach=reach)
        toExclude.extend(toExclude_Footer)
    return sorted(list(set(toExclude)))

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


def removeTableCamelot(file, file_html, pages,**kwargs):
    """
    Removes tables from a PDF file using the Camelot library.

    Args:
        file (str): Path to the input PDF file.
        file_html (str): Path to the output HTML file.
        pages (str): Pages to extract tables from (e.g., '1-3', '5').

    Returns:
        list: A list of tables extracted from the PDF file.
    """
    return find_tablesCamelot(file, file_html, pages,**kwargs)

def preprocess_pdf(
        file:str,
        pages:list=None,
        isBbox=True,
        header=True,
        footer=True,
        tables=True,
        indentify_collumns=True,
        out_file_bbox:str=None,
        out_path_html:str=None,
        out_path_txt:str=None,
        out_path_csv:str=None,
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
    groups,soup_pdf,page_mapping = generateGroups(file,pages=pages,indentify_collumns=indentify_collumns)
    len_pages = len(groups[0])
    start = time.time()
    # from utils import find_borders
    # (x1,y1),(x2,y2) = find_borders(soup_pdf)
    # print(f'File {file} has borders: {x1,y1,x2,y2}')
    # _mark_bbox(file, [[(((x1,y1),x2-x1,y2-y1),842.00)]], out_file_bbox,pages=pages,color=(0,0,1))
    # exit()
    toExclude = []
    if isPDFImage(soup_pdf):
        print(f'File {file} is a PDF image')
        return False,'PDFImage'
    if isUncopyable(soup_pdf):
        print(f'File {file} is uncopyable')
        return False,'Uncopyable'
    origin_file = file
    toExcludeHeaderAndFooter = removeHeaderAndFooter(groups,page_mapping,header=header,footer=footer,**kwargs)
    if isBbox:
        if not out_file_bbox:
            out_file_bbox = file
        mark_bbox(soup_pdf,toExcludeHeaderAndFooter,file,out_file_bbox,pages=pages)
        origin_file = out_file_bbox
    else:
        toExcludeHeaderAndFooter = []

    if tables:
        coord_tables_camelot = removeTableCamelot(file,soup_pdf,pages,out_path_csv=out_path_csv)
        coords_inside_tables,toExcludeLinesTables = coords_to_line(soup_pdf,coord_tables_camelot)
        if isBbox:
            _mark_bbox(origin_file.__str__(), coord_tables_camelot, out_file_bbox.__str__(),pages=pages,color=(0.447, 0.055, 0.58))
            _mark_bbox(out_file_bbox.__str__(), coords_inside_tables, out_file_bbox.__str__(),pages=pages,color=(0.447, 0.055, 0.58))
    else:
        toExcludeLinesTables = []
    toExclude = toExcludeHeaderAndFooter+toExcludeLinesTables
    soup_pdf = exclude_lines(soup_pdf, toExclude)
    soup_pdf = merge_split_words(soup_pdf)
    if out_path_html:
        save_html(out_path_html,soup_pdf)
    if out_path_txt:
        save_txt(out_path_txt,soup_pdf)
    if out_path_html is None and out_path_txt is None:
        return _remountLine(soup_pdf.find_all('line'))[1]
    end = time.time()
    elapsed = end-start
    print(f'Total time per page: {elapsed/len_pages}')
    return True,'sucess'

if __name__ == '__main__': 
    import pathlib,json,time
    from tqdm import tqdm
    files = list(pathlib.Path('./.pdf_files').glob('*.pdf'))
    bar = tqdm(total=len(files),desc='Processing')
    errosFiles = {'Uncopyable':[],'PDFImage':[]}
    # Preprocess the files
    for file in files:
        # list_files = ['927744_1982021']
        # list_files = ['ARQ-00470127000174-2023-1']
        list_files = ['910811_572021_1693489961855.3052']
        # list_files = ['Diário Oficial de Teresina_04-01-2024_3672']
        if file.stem not in list_files:
            continue
        # Create the directories to save the files
        if not (file.parent.absolute().parent /pathlib.Path('bbox')).exists():
            (file.parent.absolute().parent /pathlib.Path('bbox')).mkdir()
        if not (file.parent.absolute().parent /pathlib.Path('html')).exists():
            (file.parent.absolute().parent /pathlib.Path('html')).mkdir()
        if not (file.parent.absolute().parent /pathlib.Path('txt')).exists():
            (file.parent.absolute().parent /pathlib.Path('txt')).mkdir()
        # Define the output paths
        out = file.parent.absolute().parent /pathlib.Path('bbox') / pathlib.Path(file.stem+'_bbox.pdf')
        html = file.parent.absolute().parent /pathlib.Path('html') / pathlib.Path(file.stem+'_html.html')
        txt = file.parent.absolute().parent /pathlib.Path('txt') / pathlib.Path(file.stem+'_txt.txt')
        tables = file.parent.absolute().parent /pathlib.Path('tables')
        # Preprocess the file
        pages = None
        start = time.time()
        ret = preprocess_pdf(
            file,
            header=True,
            footer=True,
            tables=True,
            isBbox=True,  
            indentify_collumns = False,
            out_file_bbox=out, 
            out_path_html=html, 
            out_path_txt=txt,
            out_path_csv=None, 
            pages=pages, 
            min_chain=3, 
            max_lines_header=5, 
            max_lines_footer=5, 
            cross_similarities_header=False, 
            cross_similarities_footer=False, 
            verbose=True, 
            slice_window=1,
            reach = 2
        )
        end = time.time()
        print(f'File {file} took {end-start} seconds')
        # Save the errors
        if ret[0] == False:
            errosFiles[ret[1]].append(file.__str__())
        with open('erros.json','w') as f:
            json.dump(errosFiles,f)
        bar.update(1)
    bar.close()
    