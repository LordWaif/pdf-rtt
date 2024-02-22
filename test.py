import pdftotext,re
from pathlib import Path

def compare(a, b):
    '''Fuzzy matching of strings to compare headers/footers in neighboring pages'''
    
    count = 0
    a = re.sub('\d', '@', a)
    b = re.sub('\d', '@', b)
    for x, y in zip(a, b):
        if x == y:
            count += 1
    return count / max(len(a), len(b))

def remove_header(pages, header_candidates, WIN):
    '''Remove headers from content dictionary. Helper function for remove_header_footer() function.'''
    
    header_weights = [1.0, 0.75, 0.5, 0.5, 0.5]
    
    for i, candidate in enumerate(header_candidates):
        temp = header_candidates[max(i-WIN, 1) : min(i+WIN, len(header_candidates))]
        maxlen = len(max(temp, key=len))
        for sublist in temp:
            sublist[:] =  sublist + [''] * (maxlen - len(sublist))
        detected = []
        for j, cn in enumerate(candidate):
            score = 0
            try:
                cmp = list(list(zip(*temp))[j])
                for cm in cmp:
                    score += compare(cn,cm) * header_weights[j]
                score = score/len(cmp)
            except:
                score = header_weights[j]
            if score > 0.5:
                detected.append(cn)
        del temp
        
        for d in detected:
            while d in pages[i][:5]:
                pages[i].remove(d)
                
    return pages

def remove_footer(pages, footer_candidates, WIN):
    '''Remove footers from content dictionary. Helper function for remove_header_footer() function.'''
    
    footer_weights = [0.5, 0.75, 1.0]
    
    for i, candidate in enumerate(footer_candidates):
        temp = footer_candidates[max(i-WIN, 1) : min(i+WIN, len(footer_candidates))]
        maxlen = len(max(temp, key=len))
        for sublist in temp:
            sublist[:] =  [''] * (maxlen - len(sublist)) + sublist
        detected = []
        for j, cn in enumerate(candidate):
            score = 0
            try:
                cmp = list(list(zip(*temp))[j])
                for cm in cmp:
                    score += compare(cn,cm)
                score = score/len(cmp)
            except:
                score = footer_weights[j]
            if score > 0.5:
                detected.append(cn)
        del temp
        
        for d in detected:
            while d in pages[i][-5:]:
                pages[i] = pages[i][::-1]
                pages[i].remove(d)
                pages[i] = pages[i][::-1]
                
    return pages


# Load pdf from folder
pdf_path = Path(".pdf_files")

# List all pdf files in the folder
pdf_files = [file for file in pdf_path.iterdir() if file.suffix == ".pdf"]

for file in pdf_files:
    with open(file, "rb") as f:
        pdf = pdftotext.PDF(f,physical = True)
    header_candidates = [] 
    footer_candidates = [] 
        
    for page in pdf: 
        page = page.split("\n")
        header_candidates.append(page[: 5 ]) 
        footer_candidates.append(page[- 3 :]) 
        
    WIN = 8
    pages = remove_header(list(pdf), header_candidates, WIN)
    # pages = remove_footer(pages, footer_candidates, WIN)
    print(pages[0])
    print(f"Number of pages in {file.name}: {len(pdf)}")
    break