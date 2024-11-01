from utils import process_soup
import time,json,pathlib
from tqdm import tqdm
import pandas as pd
import traceback

if __name__ == '__main__': 
    files = list(pathlib.Path('./pdf-examples').glob('*.pdf'))
    process_files = [_.stem.replace('_txt','') for _ in list(pathlib.Path('/var/projetos/rtt_conversor_result').glob('*.txt'))]
    bar = tqdm(total=len(files),desc='Processing')
    errosFiles = {'Uncopyable':[],'PDFImage':[],'Others':[]}
    # Preprocess the files
    pandas_data = []
    for file in files:
        print('Processing file:',file.__str__())
        if file.name != "EDITAL PREGÃO ELETRONICO Nº 023-2024 FORNECIMENTO DE PNEUS E BATERIAS.pdf":
            continue
        # Define the output paths
        html = pathlib.Path('./html') / pathlib.Path(file.stem+'_html.html')
        txt = pathlib.Path('./result') / pathlib.Path(file.stem+'_txt.txt')
        csv = pathlib.Path('./csv') / pathlib.Path(file.stem+'_csv.csv')
        bbox = pathlib.Path('./bbox') / pathlib.Path(file.stem+'_bbox.pdf')
        # Preprocess the file
        pages = None
        try:
            start = time.time()
            ret = process_soup(
                input_file=file,
                generate_bbox=False,
                header=True,
                footer=True,
                tables=False,
                sections=False,
                min_sequence_header=5,
                min_sequence_footer=5,
                preprocess_soup=True,
                delimit_margin=False,
                reach_search = 1,
                min_chain = 3,
                out_file_bbox=bbox,
                out_file_txt=None,
                out_file_blocks=txt,
                out_file_html=html,
                out_path_csv=csv,
                )
            end = time.time()
            pandas_data.append({'file':file.__str__(),'time':end-start,'isProcessed':ret[0],'Output':ret[1]})
            print(f'File {file} took {end-start} seconds')
            # Save the errors
            df = pd.DataFrame(pandas_data)
            df.to_csv('process.csv')
            if ret[0] == False:
                errosFiles[ret[1]].append(file.__str__())
        except Exception as e:
            print(f'Error in file {file}\n{traceback.format_exc()}')
            errosFiles['Others'].append(file.__str__())
            continue
        with open('erros.json','w') as f:
            json.dump(errosFiles,f,indent=4,ensure_ascii=False)
        bar.update(1)
    bar.close()
    