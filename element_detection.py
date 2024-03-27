from similarity_functions import spacy_cossine_similarity
import bs4
from typing import Tuple
from tqdm import tqdm

import statistics
def removeElements(elements,**kwargs):
    # -- Parameters --
    reach = kwargs.get('reach_search',1)
    min_chain = kwargs.get('min_chain',3)
    # ----------------
    similarities = dict()
    bar = tqdm(total=len(elements),desc='Removing elements')
    for _i, element in enumerate(elements):
        for _j in range(reach):
            if _i+_j+1 >= len(elements):
                break
            similarity = spacy_cossine_similarity(elements[_i], elements[_i+_j+1],**kwargs)
            for key, value in similarity.items():
                lines = key.split('-')
                if key not in similarities:
                    similarities[key] = [value]
                else:
                    similarities[key].append(value)
        bar.update(1)
    bar.clear()
    bar.close()
    similarities = merge_dicts(similarities)
    toExclude = []

    if len(elements) <= min_chain:
        min_chain = float('-inf')

    for key, value in similarities.items():
        lines = key.split('-')
        media = statistics.mean(value)
        if len(lines) <= min_chain:
            continue
        for _i,_v in enumerate(value):
            if _v > 0.98:
                toExclude.append(int(lines[_i]))
                toExclude.append(int(lines[_i+1]))
        if media > 0.85:
            toExclude.extend(list(map(int, lines)))
    return toExclude

def merge_dicts(original_dict):
    keys = list(original_dict.keys())
    i = 0
    while i < len(keys):
        j = 0
        while j < len(keys):
            if keys[i].split('-')[-1] == keys[j].split('-')[0]:
                p2 = '-'.join(keys[j].split('-')[1:])
                new_key = f'{keys[i]}-{p2}'
                new_value = original_dict[keys[i]] + original_dict[keys[j]]
                original_dict[new_key] = new_value
                del original_dict[keys[i]]
                del original_dict[keys[j]]
                keys = list(original_dict.keys())
                i = 0
                j = 0
            j += 1
        i += 1
    return original_dict