from utils import generateGroups,_remountLine,exclude_lines,_remountLinesWithCoord,isUncopyable
from extract_rectangles import find_rectangles
from header_detection import removeHeader
from footer_detection import removeFooter
from mark_functions import _mark_bbox,find_coords,coords_to_line
from extract_tables import find_tablesCamelot
from layout_functions import isPDFImage,merge_split_words,found_sections_with_more_then_one_line,restore_blocks
from extract_sections import identify_sections
import shutil

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
        reach = 1,
        **kwargs
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

def removeRectangles(file):
    """
    Removes rectangles (gray shades) from a PDF file.

    Args:
        file (str): Path to the input PDF file.

    Returns:
        list: A list of coordinates of the rectangles found in the PDF file.
    """
    return find_rectangles(file)

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

def process_tables(file, soup_pdf, pages, isBbox, out_file_bbox,**kwargs):
    """
    Process tables in a PDF file.

    Args:
        file (str): The path to the PDF file.
        soup_pdf (str): The parsed PDF content.
        pages (list): The list of pages to process.
        isBbox (bool): Flag indicating whether to mark bounding boxes.
        origin_file (str): The path to the original file.
        out_file_bbox (str): The path to the output file with bounding boxes.
        **kwargs: Additional keyword arguments.

    Returns:
        tuple: A tuple containing the following elements:
            - coord_tables_camelot (list): The coordinates of tables detected by Camelot.
            - coords_inside_tables (list): The coordinates of lines inside tables.
            - toExcludeLinesTables (list): The coordinates of lines to exclude from tables.
    """
    coord_tables_camelot = removeTableCamelot(file, soup_pdf, pages,**kwargs)
    coords_inside_tables, toExcludeLinesTables = coords_to_line(soup_pdf, coord_tables_camelot)
    if isBbox:
        _mark_bbox(out_file_bbox.__str__(), coord_tables_camelot, out_file_bbox.__str__(), pages=pages, color=(0.447, 0.055, 0.58))
        _mark_bbox(out_file_bbox.__str__(), coords_inside_tables, out_file_bbox.__str__(), pages=pages, color=(0.447, 0.055, 0.58))
    return coord_tables_camelot, coords_inside_tables, toExcludeLinesTables

def process_header_footer(groups,soup_pdf, page_mapping, header, footer, isBbox, out_file_bbox, **kwargs):
    """
    Process the header and footer of a document.

    Args:
        groups (list): List of groups.
        page_mapping (dict): Mapping of pages.
        header (str): Header string.
        footer (str): Footer string.
        isBbox (bool): Flag indicating if bounding box should be marked.
        origin_file (str): Path to the original file.
        **kwargs: Additional keyword arguments.

    Returns:
        tuple: A tuple containing the processed content without header and footer, and the updated origin file path.
    """
    toExcludeHeaderAndFooter = removeHeaderAndFooter(groups, page_mapping, header=header, footer=footer, **kwargs)
    if isBbox:
        mark_bbox(soup_pdf, toExcludeHeaderAndFooter, out_file_bbox, out_file_bbox, pages=pages)
    return toExcludeHeaderAndFooter

def process_summarization(soup_pdf, out_file_bbox, isBbox, pages,**kwargs):
    """
    Process the summarization of a PDF document.

    Args:
        soup_pdf (BeautifulSoup): The parsed HTML representation of the PDF document.
        out_file_bbox (str): The output file path for the bounding box.
        pages (int): The number of pages in the PDF document.

    Returns:
        list: The lines to be excluded from the summarization.

    """
    sections_for_more_then_one_line = kwargs.get('sections_for_more_then_one_line',False)
    anexo_after = False
    coords_sections,coords_anexo = [],[]
    lines_section,lines_anexo = [],[]
    sections, summary_lines = identify_sections(soup_pdf)
    # print([_l[2].get('number') for _l in sections])
    _ic = 0
    while _ic < len(sections):
        (_i,_page_height,_line,_type) = sections[_ic]
        ymin = float(_line.get('ymin'))
        xmin = float(_line.get('xmin'))
        xmax = float(_line.get('xmax'))
        ymax = float(_line.get('ymax'))
        range_y = ymin - 3.5
        # print(' '.join([_w.get_text() for _w in _line.find_all('word')]))
        # existe alguma linha que esta dentro do range_y)
        if int(_line.get('number')) == 0 or int(_line.get('number')) in summary_lines:
            _ic += 1
            continue
        anterior_line = soup_pdf.find('line',attrs={'number':str(int(_line.get('number'))-1)})
        if int(_line.get('number')) == 28:
            print(anterior_line)
            print(' '.join([_w.get_text() for _w in _line.find_all('word')]))
            print(float(anterior_line.get('ymax')),range_y)
        if _i == int(anterior_line.get('page')) and float(anterior_line.get('ymax')) > range_y:
            sections.pop(_ic)
            continue
            # print('Não é uma linha de seção')
        if not sections_for_more_then_one_line:
            if _type == 'anexo':
                anexo_after = True
            if not anexo_after:
                lines_section.append([int(_line.get('number'))])
                coords_sections.append((((xmin, ymin), xmax, ymax),_page_height,_i,_line))
            else:
                lines_anexo.append([int(_line.get('number'))])
                coords_anexo.append((((xmin, ymin), xmax, ymax),_page_height,_i,_line))
        _ic += 1
    toExcludeSummarization = summary_lines
    if sections_for_more_then_one_line:
        (coords_parents, sections_founded),(coords_parents_anexo,sections_founded_anexo) = found_sections_with_more_then_one_line(sections,soup_pdf,toExcludeSummarization)
        print(f'Founded {len(sections_founded)} sections and {len(sections_founded_anexo)} anexos')
    else:
        print(f'Founded {len(lines_section)} sections and {len(lines_anexo)} anexos')
    if isBbox:
        mark_bbox(soup_pdf, toExcludeSummarization, out_file_bbox, out_file_bbox, pages=pages, color=(0.5, 0.5, 1))
        if sections_for_more_then_one_line:
            mark_bbox(soup_pdf, [_ for _l in sections_founded for _ in _l], out_file_bbox, out_file_bbox, pages=pages, color=(0, 0, 1))
            mark_bbox(soup_pdf, [_ for _l in sections_founded_anexo for _ in _l], out_file_bbox, out_file_bbox, pages=pages, color=(0, 1, 0))
            return toExcludeSummarization,sections_founded,sections_founded_anexo
        else:
            # print([_ for _l in lines_section for _ in _l])
            mark_bbox(soup_pdf, [_ for _l in lines_section for _ in _l], out_file_bbox, out_file_bbox, pages=pages, color=(0, 0, 1))
            mark_bbox(soup_pdf, [_ for _l in lines_anexo for _ in _l], out_file_bbox, out_file_bbox, pages=pages, color=(0, 1, 0))
            return toExcludeSummarization,lines_section,lines_anexo
def preprocess_pdf(
        file:str,
        pages:list=None,
        isBbox=True,
        rectangles=True,
        header=True,
        footer=True,
        tables=True,
        identify_sections=True,
        segment_txt_by_section=False,
        indentify_collumns=True,
        out_file_bbox:str=None,
        out_path_html:str=None,
        out_path_txt:str=None,
        out_path_csv:str=None,
        out_path_json:str=None,
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
    groups,soup_pdf,page_mapping,coordsMargin = generateGroups(file,pages=pages,indentify_collumns=indentify_collumns,**kwargs)
    len_pages = len(groups[0])
    start = time.time()
    if not identify_sections:
        segment_txt_by_section = False
    data_json = {'secoes':{},'anexos':{}}
    toExclude = []
    if isPDFImage(soup_pdf):
        print(f'File {file} is a PDF image')
        return False,'PDFImage'
    if isUncopyable(soup_pdf):
        print(f'File {file} is uncopyable')
        return False,'Uncopyable'
    origin_file = file
    
    if isBbox:
        if not out_file_bbox:
            out_file_bbox = file
        else:
            shutil.copy(origin_file,out_file_bbox)

    # Remove rectangles
    if rectangles:
        coord_rectangles = removeRectangles(file)
        coords_inside_rectangles, toExcludeRectangles = coords_to_line(soup_pdf,coord_rectangles)
        if isBbox:
            _mark_bbox(file, coord_rectangles, out_file_bbox,pages=pages,color=(0,0,1))
            _mark_bbox(out_file_bbox.__str__(), coords_inside_rectangles, out_file_bbox.__str__(),pages=pages,color=(0,1,0))
    else:
       toExcludeRectangles = []

    delimite_margin = kwargs.get('delimite_margin',False)
    if delimite_margin:
        print('Delimiting margin')
        if isBbox:
            _mark_bbox(out_file_bbox.__str__(), coordsMargin, out_file_bbox.__str__(),pages=pages,color=(250/255, 237/255, 0/255))

    # Remove header and footer
    if header or footer:
        toExcludeHeaderAndFooter = process_header_footer(groups,soup_pdf,page_mapping,header,footer,isBbox,out_file_bbox,**kwargs)
    else:
        toExcludeHeaderAndFooter = []

    # Remove tables
    if tables:
        _,_,toExcludeLinesTables = process_tables(file,soup_pdf,pages,isBbox,out_file_bbox,out_path_csv=out_path_csv,**kwargs)
    else:
        toExcludeLinesTables = []

    # Remove summarization
    if identify_sections:
        toExcludeSummarization,lines_section,lines_anexo = process_summarization(soup_pdf,out_file_bbox,isBbox,pages,**kwargs)
    else:
        toExcludeSummarization = []
            
    toExclude = toExcludeRectangles+toExcludeHeaderAndFooter+toExcludeLinesTables+toExcludeSummarization
    
    soup_pdf = restore_blocks(soup_pdf)
    soup_pdf = exclude_lines(soup_pdf, toExclude)
    if segment_txt_by_section:
        def find_section(soup_pdf,section_init,section_end):
            content = []
            name = None
            # print(section_init[0])
            for _l in soup_pdf.find_all('line'):
                if _l.get('number') == section_init[0]:
                    name = _remountLine([_l])[1][0]
                    continue
                if int(_l.get('number')) > section_init[-1] and int(_l.get('number')) < section_end[0]:
                    content.append(_l)
            content = '\n'.join(_remountLine(content)[1])
            return content,name
        def segment_and_save(soup_pdf,data_json,lines_section,lines_anexo,out_path_txt,out_path_json=None):
            i = 1
            secoes_e_anexos = {'secoes':[],'anexos':[]}
            for _i in range(len(lines_section)):
                if _i == len(lines_section)-1 and len(lines_anexo) > 0:
                    _s_init = lines_section[_i]
                    _s_end = lines_anexo[0]
                elif _i == len(lines_section)-1 and len(lines_anexo) == 0:
                    _s_init = lines_section[_i]
                    _s_end = [len(soup_pdf.find_all('line'))]
                else:
                    _s_init = lines_section[_i]
                    _s_end = lines_section[_i+1]
                # print(_s_init,_s_end)
                if len(_s_init) == 0 or len(_s_end) == 0:
                    continue
                secoes_e_anexos['secoes'].append((_s_init,_s_end))
            for _i in range(len(lines_anexo)):
                if _i == len(lines_anexo)-1:
                    _s_init = lines_anexo[_i]
                    _s_end = [len(soup_pdf.find_all('line'))]
                else:
                    _s_init = lines_anexo[_i]
                    _s_end = lines_anexo[_i+1]
                if len(_s_init) == 0 or len(_s_end) == 0:
                    continue
                secoes_e_anexos['anexos'].append((_s_init,_s_end))

            for k,val in secoes_e_anexos.items():
                for _s_init,_s_end in val:
                    content,name = find_section(soup_pdf,_s_init,_s_end)
                    if out_path_json is not None:
                        data_json[k][name] = {
                            'init':_s_init[-1],
                            'end':_s_end[0],
                            'content':content
                            }
                    if out_path_txt is not None:
                        folder = out_path_txt.parent / out_path_txt.stem
                        folder.mkdir(parents=True,exist_ok=True)
                        out_path_txt_sec = folder / pathlib.Path(f'{i}_{name}'+'.txt')
                        i += 1
                        with open(out_path_txt_sec.__str__(),'w') as f:
                            f.write(content)
            if out_path_json is not None:
                with open(out_path_json.__str__(),'w') as f:
                    json.dump(data_json,f,indent=4,ensure_ascii=False)
        segment_and_save(soup_pdf,data_json,lines_section,lines_anexo,out_path_txt,out_path_json)

    if out_path_html:
        save_html(out_path_html,soup_pdf)
    if out_path_txt and not (segment_txt_by_section or out_path_json):
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
        # 153010_1432013 PLN
        # 158155_232013 problema no sumario e seção objeto V
        # 160118_282020_1693490002550.4233 header não identificado V
        # 160160_42019 seção indentificado errada " -TCU – Plenário); " V
        # 160441_22018 numeração colocada pra fora da margem V
        # 168006_192022_1693489137533.571 dot de lista fora da margem V - possivel problema
        # 200380_62013 sumario errado PLN
        # 389088_122018 numeração fora da margem V
        # 511180_42015 sumário pego errado V
        # 910809_1142016_1693490555082.2153 quase consertado
        # 910813_22015 PLN
        # 925003_8442022 V
        # 925143_762013 V
        # 925937_131382013_1693490505459.5308 não foi pego
        # 926119_542015 junção de linhas no header
        # 926128_232014 V
        # 926132_572013 seção errada " -  GRQ.O,  requisitado  pelo  GES.O  -  Gerencia  de  Centro  Técnico  de  Ensaios  e  Suporte  a " V
        # 926560_12023 seções errada " – ICP – Brasil. "
        # 926681_342022_1693488838407.8875 sumário errado
        # 926807_12020 anexo errado
        # 988453_1822022 seção errada " -  EIRELI:  ato  constitutivo,  estatuto  ou  contrato  social  em  vigor,  acompanhado  da  últim "
        list_files = ['393031_2622014']
        if file.stem not in list_files:
            continue
        print('Processing file:',file.__str__())
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
        js = file.parent.absolute().parent /pathlib.Path('txt') / pathlib.Path(file.stem+'_json.json')
        tables = file.parent.absolute().parent /pathlib.Path('tables') / pathlib.Path(file.stem)
        # Preprocess the file
        pages = None
        start = time.time()
        ret = preprocess_pdf(
            file,
            header=False,
            footer=False,
            tables=False,
            identify_sections=True,
            delimite_margin=True,
            # sections_for_more_then_one_line=True,
            segment_txt_by_section=True,
            isBbox=True,  
            rectangles=False,
            indentify_collumns = False,
            out_file_bbox=out, 
            out_path_html=html, 
            out_path_txt=None,
            out_path_csv=tables, 
            out_path_json=js,
            pages=pages, 
            min_chain=3, 
            max_lines_header=7, 
            max_lines_footer=7, 
            cross_similarities_header=False, 
            cross_similarities_footer=False, 
            verbose=True, 
            slice_window=2,
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
    