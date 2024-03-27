from utils import process_soup
import time,json,pathlib
from tqdm import tqdm

if __name__ == '__main__': 
    files = list(pathlib.Path('./.pdf_extras').glob('*.pdf'))
    bar = tqdm(total=len(files),desc='Processing')
    errosFiles = {'Uncopyable':[],'PDFImage':[],'Others':[]}
    # Preprocess the files
    for file in files:
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
        try:
            start = time.time()
            ret = process_soup(
                input_file=file,
                delimit_margin=True,
                generate_bbox=False,
                header=True,
                footer=True,
                tables=False,
                sections=True,
                min_sequence_header=5,
                min_sequence_footer=5,
                reach_search = 1,
                min_chain = 3,
                out_file_bbox=None,
                out_file_txt=txt,
                out_file_html=html,
                )
            end = time.time()
            print(f'File {file} took {end-start} seconds')
            # Save the errors
            if ret[0] == False:
                errosFiles[ret[1]].append(file.__str__())
        except Exception as e:
            print(f'Error in file {file}')
            errosFiles['Others'].append(file.__str__())
            continue
        with open('erros.json','w') as f:
            json.dump(errosFiles,f)
        bar.update(1)
    bar.close()
    