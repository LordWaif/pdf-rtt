from preprocesser import preprocess_pdf
from pathlib import Path

# Define the file paths
file = Path('Diário Oficial de Teresina_04-01-2024_3672.pdf')
out = Path('example_bbox.pdf')
html = Path('example.html')
txt = Path('example.txt')
# Define the pages to process
pages = (1, 5)

'''
file (str): The path to the PDF file.
isBbox (bool, optional): Indicates whether to mark bounding boxes. Defaults to True.
out_file_bbox (str, optional): The path to save the PDF file with marked bounding boxes. Defaults to None,
    which overwrites the original file.
out_path_html (str, optional): The path to save the preprocessed PDF as HTML. Defaults to None, which
    does not save as HTML.
out_path_txt (str, optional): The path to save the preprocessed PDF as TXT. Defaults to None, which
    does not save as TXT.
pages (list, optional): A list of page numbers to process. Defaults to None, which processes all pages.
min_chain (int, optional): The minimum number of similarity lines each and other that must be considered as part of the header or footer. Default is 5.
max_lines_header (int, optional): The maximum number of lines allowed in the header. Default is 10.
max_lines_footer (int, optional): The maximum number of lines allowed in the footer. Default is 10.
cross_similarities_header (bool, optional): Whether to consider cross similarities in the header. Default is False.
cross_similarities_footer (bool, optional): Whether to consider cross similarities in the footer. Default is False.
verbose (bool, optional): Whether to display warnings. Default is True.
slice_window (int, optional): The size of the window to slice the sentences. Default is 3.
'''

# Preprocess the PDF
preprocess_pdf(
            file,
            isBbox=True,  
            out_file_bbox=out, 
            out_path_html=html, 
            out_path_txt=txt, 
            pages=pages, 
            min_chain=5, 
            max_lines_header=10, 
            max_lines_footer=10, 
            cross_similarities_header=False, 
            cross_similarities_footer=True, 
            verbose=True, 
            slice_window=3
        )
