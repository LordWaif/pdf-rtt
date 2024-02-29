# import unidecode,re
from tqdm import tqdm
import cv2
import camelot,copy

# TERMOS_TABELA_REGEX = [
#     r'\bQTD\b',
#     r'\bQuantidade\b',
#     r'\bITEM\b',
#     r'\bDescricao\b',
#     r'\bCODIGO\b',
#     r'\bCODIGO DO PRODUTO\b',
#     r'\bPRECO UNITARIO\b',
#     r'\bVALOR TOTAL\b',
#     r'\bCATEGORIA\b',
#     r'\bFORNECEDOR\b',
#     r'\bDATA DE COMPRA\b',
#     r'\bDATA DE REGISTRO\b',
#     r'\bLOCALIZACAO\b',
#     r'\bSTATUS\b',
#     r'\bPRECO\b',
#     r'\bUNIDADE\b',
#     r'\bVALOR\b',
#     r'\bTOTAL\b',
#     r'\bLOTE\b',
#     r'\bDATA DE VALIDADE\b',
#     r'\bDATA DE FABRICACAO\b',
#     r'\bDATA DE ENTREGA\b',
#     r'\bDATA DE PAGAMENTO\b',
#     r'\bDATA DE EMISSAO\b',
#     r'\bVALOR UNITARIO\b',
#     r'\bVALOR TOTAL\b',
#     r'\bVALOR DO ITEM\b',
#     r'\bVALOR DO PRODUTO\b',
#     r'\bVALOR DO LOTE\b',
#     r'\bVALOR DA COMPRA\b',
#     r'\bVALOR DA VENDA\b',
#     r'\bVALOR TOTAL DO CONTRATO\b',
#     r'\bVALOR TOTAL DO ITEM\b',
#     r'\bVALOR TOTAL DO LOTE\b',
#     r'\bVALOR TOTAL DA COMPRA\b',
#     r'\bVALOR TOTAL DA VENDA\b',
#     r'\bVALOR TOTAL DO CONTRATO\b',
#     r'\bVALOR TOTAL DO PRODUTO\b',
#     # r'\b\d*\b',
#     r'\b(.{2}\s)?\b\d*([.,]\d*)\b',
# ]
# TERMOS_TABELA_REGEX = [f'^{termo}$' for termo in TERMOS_TABELA_REGEX]

# DEPRECATED
# def recovery_lines(i,numbers,line_tables,coords):
#     proposed_line_tables = []
#     _range = 2
#     ant = i-_range if i-_range>=0 else 0
#     previous_lines = numbers[ant:i]
#     if all([_p in line_tables for _p in previous_lines]):
#         ymax_ant = coords[i]['ymax']
#         ymin_act = coords[i-1]['ymin']
#         if abs(ymin_act-ymax_ant) < 18:
#             proposed_line_tables.append(numbers[i])
#     return proposed_line_tables

# DEPRECATED
# def indentify_tables(_lines):
#     regex_search = '|'.join(TERMOS_TABELA_REGEX)
#     line_tables = []
#     proposed_line_tables = []
#     i = 0
#     numbers,lines,coords = _lines
#     while i < len(lines):
#         line = lines[i]
#         number = numbers[i]
#         # print(line,re.search(regex_search, unidecode.unidecode(line), re.IGNORECASE))
#         if re.search(regex_search, unidecode.unidecode(line), re.IGNORECASE):
#             line_tables.append(number)
#             j = i+1
#             while j < len(lines):
#                 if re.search(r'^.{0,15}$',lines[j]):
#                     line_tables.append(numbers[j])
#                 else:
#                     proposed_line_tables += recovery_lines(j,numbers,line_tables,coords)
#                     line_tables += proposed_line_tables
#                     break
#                 j += 1
#             i = j
#             continue
#         else:
#             proposed_line_tables += recovery_lines(i,numbers,line_tables,coords)
#             line_tables += proposed_line_tables
#             ...
#         i += 1
#     # print([lines[numbers.index(i)] for i in set(line_tables+proposed_line_tables)])
#     return set(line_tables+proposed_line_tables)

# DEPRECATED
# def weslley_indentify_tables_incomplete(pdf_html):
#     pages = pdf_html.find_all('page')
#     coords = []
#     for _page in pages:
#         coords_page = []
#         lines = _page.find_all('line')
#         for _i,_line in enumerate(lines):
#             ymin = float(_line['ymin'])
#             ymax = float(_line['ymax'])
#             xmin = float(_line['xmin'])
#             xmax = float(_line['xmax'])
#             slice = 4
#             if _i+1 < len(lines):
#                 _iWhile = _i
#                 while _iWhile < slice+_i:
#                     _iWhile += 1
#                     if _iWhile < len(lines):
#                         next_ymin = float(lines[_iWhile]['ymin'])
#                         next_xmin = float(lines[_iWhile]['xmin'])
#                         next_ymax = float(lines[_iWhile]['ymax'])
#                         next_xmax = float(lines[_iWhile]['xmax'])
#                         space_between_x = next_xmin - xmax
#                         space_between_y = next_ymin - ymin
#                         if next_ymin == ymin and next_ymax == ymax:
#                             width = xmax - xmin
#                             height = ymax - ymin
#                             coords_page.append((((xmin,ymin),width,height),float(_page['height'])))
#                             coords_page.append((((next_xmin,next_ymin),next_xmax - next_xmin,next_ymax - next_ymin),float(_page['height'])))
#         coords.append(coords_page)
#     return coords

def find_tablesCamelot(file,file_html,pages):
    tables = camelot.read_pdf(file.__str__(), pages='all')
    really_dimensions = [
        {
            'width':float(page.get('width')),
            'height':float(page.get('height'))
        } 
        for page in file_html.find_all('page')
    ]
    coords_pages = {i:[] for i in range(len(really_dimensions))}
    bar = tqdm(total=len(tables),desc='Finding tables camelot')
    for _i,table in enumerate(tables):
        founded_in_page = table.parsing_report['page']
        if int(founded_in_page) > pages[1] or int(founded_in_page) < pages[0]:
            bar.update(1)
            continue
        actual_dimensions = really_dimensions[founded_in_page-1]
        _bbox = table._bbox
        img = table._image[0]
        ratio_width = actual_dimensions['width']/img.shape[1]
        ratio_height = actual_dimensions['height']/img.shape[0]
        x1,y1,x2,y2 = _bbox
        ratio = 300/72
        # new_img = copy.deepcopy(img)
        # pdf_height = img.shape[0] / ratio
        x1 = (x1*ratio)*ratio_width
        x2 = (x2*ratio)*ratio_width
        y1 = (y1*ratio)*ratio_height
        y2 = (y2*ratio)*ratio_height
        y1 = actual_dimensions['height'] - y1
        y2 = actual_dimensions['height'] - y2
        really_width = x2-x1
        really_height = y2-y1
        coord = (((x1,y1),really_width,really_height),actual_dimensions['height'])
        coords_pages[founded_in_page-1].append(coord)
        bar.update(1)
    bar.close()
    return [v for v in coords_pages.values()]

# DEPRECATED
# def draw_bbox(img, start_point, end_point, ratio=1):
#     start_point = tuple(map(lambda x: round(x * ratio), start_point))
#     end_point = tuple(map(lambda x: round(x * ratio), end_point))
#     cv2.rectangle(img, start_point, end_point, (0, 255, 0), 2)

# DEPRECATED
# def find_tabulate(file):
#     import tabula
#     tables = tabula.read_pdf(file, pages='all')
#     print(tables[0])
        

# if __name__ == '__main__':
#     import pickle
#     with open('lines.pkl','rb') as f:
#         lines = pickle.load(f)
#         print(indentify_tables(lines)) # [0, 1, 2]