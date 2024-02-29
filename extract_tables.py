# import unidecode,re
from tqdm import tqdm
import camelot

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
    bar.close()
    return [v for v in coords_pages.values()]
