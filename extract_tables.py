# import unidecode,re
from tqdm import tqdm
import camelot,os,time
from pathlib import Path

def find_tablesCamelot(file,file_html,pages,**kwargs):
    from utils import find_borders,extract_rectangle_from_pdf
    (x1,y1),(x2,y2) = find_borders(file_html)
    temp_pdf = extract_rectangle_from_pdf(file,((x1-5,y1-5),(x2+5,y2+5)))
    # Gerar pdf a apenas com oque estiver contido dentro do retangulo
    print('Extracting tables with camelot ...')
    start = time.time()
    if pages == None:
        tables = camelot.read_pdf(temp_pdf, pages='all',line_scale=50,flavor='lattice')
    else:
        tables = camelot.read_pdf(temp_pdf, pages=f'{pages[0]}-{pages[1]}',line_scale=15,flavor='lattice')
    os.remove(temp_pdf)
    if len(tables) == 0:
        print('No tables found')

    really_dimensions = [
        {
            'width':float(page.get('width')),
            'height':float(page.get('height'))
        } 
        for page in file_html.find_all('page')
    ]
    out_path_csv = kwargs.get('out_path_csv',None)
    coords_pages = {i:[] for i in range(len(really_dimensions))}
    bar = tqdm(total=len(tables),desc='Finding tables camelot')
    for _i,table in enumerate(tables):
        # img = table._image[0]
        # for cells in table.cells:
        #     for cell in cells:
        #         draw_bbox(img, (x1,y1),(x2,y2),300 / 72)     
        # Salvar imagem
        # if not img is None:
        #     cv2.imwrite(f'./imgs/{_i}.png', img)
        # print(table.df)
        founded_in_page = table.parsing_report['page']
        if out_path_csv != None:
            df = table.df
            if len(df) != 0:
                df.to_csv(out_path_csv / Path(f'table_pg_{founded_in_page}_n_{_i}_bbox_{table._bbox}.csv'),index=False)
        # print(table.parsing_report['page'])
        if pages != None and (int(founded_in_page) > pages[1] or int(founded_in_page) < pages[0]):
            bar.update(1)
            continue
        actual_dimensions = really_dimensions[founded_in_page-1]
        _bbox = table._bbox
        img = table._image[0]
        ratio_width = actual_dimensions['width']/img.shape[1]
        ratio_height = actual_dimensions['height']/img.shape[0]
        x1,y1,x2,y2 = _bbox
        ratio = 300/72
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
    bar.clear()
    bar.close()
    end = time.time()
    print(f'(Tables) Average time per page: {(end-start)/(len(really_dimensions) if pages == None else (int(pages[1])-int(pages[0])+1))}')
    return [v for v in coords_pages.values()]

import cv2
def draw_bbox(img, start_point, end_point, ratio=1):
    start_point = tuple(map(lambda x: round(x * ratio), start_point))
    end_point = tuple(map(lambda x: round(x * ratio), end_point))
    print(start_point,end_point)
    cv2.rectangle(img, start_point, end_point, (0, 255, 0), 2)
