import bs4
import subprocess
from layout_functions import merge_split_words,merge_split_lines,restore_blocks,reOrder,numerateLines,isPDFImage,isUncopyable
from mark_functions import mapping_mark_line,_mark_bbox,mapping_mark_coord,coords_to_line
from PyPDF2 import PdfWriter, PdfReader
import tempfile,statistics,time
import shutil,json
from extract_tables import find_tablesCamelot

MARGIN_COLORS = (0.98, 0.93, 0)
HEADER_COLOR = (1,0,0)
FOOTER_COLOR = (1,0,0)
TABLE = (0.447, 0.055, 0.58)
TABLE_CONTENT = (0.447, 0.055, 0.58)
SECTION_COLOR = (0, 0, 1)
ANEXO_COLOR = (0, 1, 0)
SUMMARY_COLOR = (0.5, 0.5, 1)

def extract_soup_from_pdf(path, pages=None):
    if pages is not None:
        cmd = ['pdftotext', '-layout', path, '-bbox-layout', '/dev/stdout', '-f', str(pages[0]), '-l', str(pages[1])]
    else:
        cmd = ['pdftotext', '-layout', path, '-bbox-layout', '/dev/stdout']
    pdf_html = subprocess.check_output(cmd).decode('utf-8')
    soup = bs4.BeautifulSoup(pdf_html, 'html.parser')
    return soup

def find_margin(soup):
    coords = {}
    for _p,_page in enumerate(soup.find_all('page')):
        coords[_p] = []
        page_height = float(_page.get('height'))
        margin = [float(_l.get('xmin')) for _l in _page.find_all('line')]
        if len(margin) == 0:
            continue
        margin = min([statistics.mode(margin),statistics.mean(margin)])
        coords[_p].append((((margin,0),1,page_height),page_height))
        for _l in _page.find_all('line'):
            if float(_l.get('xmax')) < margin:
                xMin = round(float(_l.get('xmin')),2)
                yMin = round(float(_l.get('ymin')),2)
                xMax = round(float(_l.get('xmax')),2)
                yMax = round(float(_l.get('ymax')),2)
                width = xMax - xMin
                height = yMax - yMin
                coords[_p].append((((xMin,yMin),width,height),page_height))
                _l.decompose()
    return soup,coords

def remountLine(line):
    content = ' '.join([_.text for _ in line.find_all('word')])
    return content

def save_html(file, soup):
    with open(file, 'w') as f:
        f.write(str(soup.prettify()))

def save_txt(file, soup):
    with open(file, 'w') as f:
        f.write('\n'.join(list(map(remountLine,soup.find_all('line')))))

def save_blocks(file, soup):
    content = []
    for block in soup.find_all('block'):
        lines = block.find_all('line')
        conteudo_bloco = ' '.join([_w.text for line in lines for _w in line.find_all('word')])
        if conteudo_bloco.strip().replace(' ','') == '':
            continue
        content.append(conteudo_bloco)
    with open(file, 'w') as f:
        f.write('\n'.join(content))

def find_content(soup,section_start,section_end):
    content = []
    title_section = section_start[2]
    if section_end is not None:
        next_section = section_end[2]
        numberEnd = int(next_section.get('number'))
    else:
        numberEnd = int(soup.find_all('line')[-1].get('number'))
    numberStart = int(title_section.get('number'))
    for _n in range(numberStart+1,numberEnd):
        content.append(remountLine(soup.find('line',number=str(_n))))
    return {'title':remountLine(title_section),'content':'\n'.join(content)}

def generate_json(soup,sections):
    data_json = {'secoes':[],'anexos':[]}
    for i in range(len(sections)):
        first = sections[i]
        second = sections[i+1] if i+1 < len(sections) else None
        if first[3] == 'secao':
            data_json['secoes'].append(find_content(soup,first,second))
        elif first[3] == 'anexo':
            data_json['anexos'].append(find_content(soup,first,second))
    return data_json

def process_soup(**kwargs):
    from element_detection import removeElements
    # ---- Variables ----
    delimit_margin = kwargs.get('delimit_margin',False)
    isBbox = kwargs.get('generate_bbox',False)
    input_file = kwargs.get('input_file',None)

    header = kwargs.get('header',False)
    footer = kwargs.get('footer',False)
    tables = kwargs.get('tables',False)
    split_sections = kwargs.get('sections',False)

    preprocess_soup = kwargs.get('preprocess_soup',True)

    out_file_bbox = kwargs.get('out_file_bbox',None)
    out_file_txt = kwargs.get('out_file_txt',None)
    out_file_json = kwargs.get('out_file_json',None)
    out_file_html = kwargs.get('out_file_html',None)
    out_file_blocks = kwargs.get('out_file_blocks',None)

    pages = kwargs.get('pages',None)
    # -------------------
    soup = extract_soup_from_pdf(input_file)
    toExclude = []
    mark_points = {}
    if isPDFImage(soup):
        print(f'File {input_file} is a PDF image')
        return False,'PDFImage'
    if isUncopyable(soup):
        print(f'File {input_file} is uncopyable')
        return False,'Uncopyable'
    if isBbox:
        if not out_file_bbox:
            raise Exception('out_file_bbox must be defined')
        else:
            shutil.copy(input_file,out_file_bbox)
    if preprocess_soup:
        soup = reOrder(soup)
        soup = merge_split_words(soup)
        soup = merge_split_lines(soup)
    if delimit_margin:
        soup,line_exclude_margin = find_margin(soup)
        toExclude.extend(line_exclude_margin)
        if isBbox:
            mark_points = mapping_mark_coord(soup,line_exclude_margin,mark_points,MARGIN_COLORS)
    soup = numerateLines(soup)
    if header:
        print('Processing header')
        min_sequence = kwargs.get('min_sequence_header',10)
        elements = [page.find_all('line')[:min_sequence] for page in soup.find_all('page')]
        start = time.time()
        toExcludeHeader = removeElements(elements,**kwargs)
        print(f'Time to remove header: {time.time()-start}')
        toExclude.extend(toExcludeHeader)
        if isBbox:
            mark_points = mapping_mark_line(soup,toExcludeHeader,mark_points,HEADER_COLOR)

    if footer:
        print('Processing footer')
        min_sequence = kwargs.get('min_sequence_footer',10)
        elements = [page.find_all('line')[-min_sequence:] for page in soup.find_all('page')]
        start = time.time()
        toExcludeFooter = removeElements(elements,**kwargs)
        print(f'Time to remove header: {time.time()-start}')
        toExclude.extend(toExcludeFooter)
        if isBbox:
            mark_points = mapping_mark_line(soup,toExcludeFooter,mark_points,FOOTER_COLOR)

    if tables:
        print('Processing tables')
        coord_tables_camelot = find_tablesCamelot(input_file, soup, pages,**kwargs)
        elements_inside_table = coords_to_line(soup,coord_tables_camelot)
        toExclude.extend(elements_inside_table)
        if isBbox:
            mark_points = mapping_mark_coord(soup,coord_tables_camelot,mark_points,TABLE)
            mark_points = mapping_mark_line(soup,elements_inside_table,mark_points,TABLE_CONTENT)

    if split_sections:
        print('Processing sections')
        from extract_sections import identify_sections
        sections,summary_lines = identify_sections(soup)
        number_sections_withOut_summary = [_ for _ in sections if int(_[2].get('number')) not in summary_lines]
        number_sections = [_ for _ in number_sections_withOut_summary if int(_[2].get('number')) if _[3] == 'secao']
        number_anexos = [_ for _ in number_sections_withOut_summary if int(_[2].get('number')) if _[3] == 'anexo']
        print(f'Found {len(number_sections)} sections, {len(number_anexos)} anexos and {len(summary_lines)} summary lines')
        toExclude.extend(summary_lines)
        toExclude.extend(number_anexos)
        if isBbox:
            mark_points = mapping_mark_line(soup,number_sections,mark_points,SECTION_COLOR)
            mark_points = mapping_mark_line(soup,number_anexos,mark_points,ANEXO_COLOR)
            mark_points = mapping_mark_line(soup,summary_lines,mark_points,SUMMARY_COLOR)

    soup = restore_blocks(soup)
    soup = exclude_lines(soup,toExclude)
    if split_sections and out_file_json:
        data_json = generate_json(soup,number_sections_withOut_summary)
        with open(out_file_json,'w') as f:
            json.dump(data_json,f,indent=4,ensure_ascii=False)

    if out_file_txt:
        save_txt(out_file_txt,soup)

    if out_file_html:
        save_html(out_file_html,soup)
    
    if out_file_blocks:
        save_blocks(out_file_blocks,soup)

    if isBbox:
        print('Marking bbox')
        start = time.time()
        _mark_bbox(out_file_bbox,mark_points,out_file_bbox,pages)
        print(f'Time to mark bbox: {time.time()-start}')
    return True,'Sucess'

def _remountLinesWithCoord(lines):
    '''Remounts a line to be used in the cosine similarity function.
    
    Args:
        lines (list): A list of lines containing dictionaries with 'number' and 'bbox' keys.
        
    Returns:
        tuple: A tuple containing two lists. The first list contains the 'number' values from the input lines,
               and the second list contains the 'bbox' values from the input lines.
    '''
    _pgN,_lines,_coord = [],[],[]
    for i, line in enumerate(lines):
        _pgN.append(int(line.get('number')))
        content = ' '.join([_.text for _ in line.find_all('word')])
        _lines.append(content)
        _coord.append({'xmin':float(line.get('xmin')),
                       'ymin':float(line.get('ymin')),
                       'xmax':float(line.get('xmax')),
                       'ymax':float(line.get('ymax'))})
    return _pgN, _lines, _coord

def exclude_lines(soup_pdf, toExclude):
    for page in soup_pdf.find_all('page'):
        for line in page.find_all('line'):
            if int(line.get('number')) in toExclude:
                line.decompose()
    return soup_pdf