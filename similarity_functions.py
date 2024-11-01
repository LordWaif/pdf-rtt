import spacy,re
from line_utils import remountLine
from typing import List, Tuple

NLP = spacy.load('pt_core_news_sm')
def spacy_cossine_similarity(
        elementLines1, 
        elementLines2,
        **kwargs) -> dict:
    isCrossSimilarity = kwargs.get('cross_similarity',False)
    slice_window = kwargs.get('slice_window',3)
    sim = dict()
    for _i, (p1, p2) in enumerate(zip(elementLines1, elementLines2)):
        numberOne = int(p1.get('number'))
        numberTwo = int(p2.get('number'))
        sim[f'{numberOne}-{numberTwo}'] = _spacy_cossine_similarity(remountLine(p1), remountLine(p2))
        if sim[f'{numberOne}-{numberTwo}'] < 0.5:
            del sim[f'{numberOne}-{numberTwo}']
            # Check if cross similarities should be calculated
            if isCrossSimilarity:
                # Calculate the cross similarity
                cross_similiraty = cross_similarity(elementLines1, elementLines2,sim)
                sim.update(cross_similiraty)
            else:
                # Else, calculate the slice similarity
                slice_sim = slice_similarity(elementLines1, elementLines2,sim, slice_window)
                sim.update(slice_sim)
            return sim
    return sim

def slice_similarity(
        list_phares1, 
        list_phrases2,
        similarity:dict,
        slice_window:int=3,)-> dict:
    sim = dict()
    for _i, line1 in enumerate(list_phares1):
        numberOne = int(line1.get('number'))
        slice_index_start = _i - slice_window if _i - slice_window >= 0 else 0
        slice_index_end = _i + slice_window if _i + slice_window <= len(list_phrases2) else len(list_phrases2)
        for _j in range(slice_index_start, slice_index_end):
            line2 = list_phrases2[_j]
            numberTwo = int(line2.get('number'))
            if f'{numberOne}-{numberTwo}' in similarity:
                continue
            slice_sim = _spacy_cossine_similarity(remountLine(line1), remountLine(line2))
            if slice_sim > 0.9:
                sim[f'{numberOne}-{numberTwo}'] = slice_sim
    return sim

def cross_similarity(
        list_phares1, 
        list_phrases2,
        similarity:dict)-> dict:
    sim = dict()
    for _i, line1 in enumerate(list_phares1):
        numberOne = int(line1.get('number'))
        for _j, line2 in enumerate(list_phrases2):
            numberTwo = int(line2.get('number'))
            if f'{numberOne}-{numberTwo}' in similarity:
                continue
            cross_sim = _spacy_cossine_similarity(remountLine(line1), remountLine(line2))
            if cross_sim > 0.9:
                sim[f'{numberOne}-{numberTwo}'] = cross_sim
    return sim

def _spacy_cossine_similarity(text1:str, text2:str) -> float:
    text1 = re.sub(r'\d', '@', text1)
    text2 = re.sub(r'\d', '@', text2)
    # Carregue o modelo
    doc1 = NLP(text1)
    doc2 = NLP(text2)
    return doc1.similarity(doc2)