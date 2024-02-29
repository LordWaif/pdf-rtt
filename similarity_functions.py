import spacy,re
from typing import List, Tuple

NLP = spacy.load('pt_core_news_sm')
def spacy_cossine_similarity(
        list_phares1:Tuple[List[int],List[str]], 
        list_phrases2:Tuple[List[int],List[str]], 
        header=False, 
        footer=False, 
        cross_similarities_header=False, 
        cross_similarities_footer=False,
        slice_window=3) -> dict:
    '''
    Calculates the cosine similarity between two lists of phrases using spacy.

    Args:
        list_phares1 (list): The first list of phrases.
        list_phrases2 (list): The second list of phrases.
        header (bool, optional): Specifies if the list is a header. Defaults to False.
        footer (bool, optional): Specifies if the list is a footer. Defaults to False.
        cross_similarities_header (bool, optional): Specifies if cross similarities should be calculated for header. Defaults to False.
        cross_similarities_footer (bool, optional): Specifies if cross similarities should be calculated for footer. Defaults to False.
        slice_window (int, optional): The size of the window to slice the sentences. Defaults to 3.

    Returns:
        dict: A dictionary containing the cosine similarity between each pair of phrases.

    Raises:
        ValueError: If neither header nor footer is specified.
    '''
    # Check if the list is a header or a footer
    if not(footer or header):
        raise ValueError('You must specify if the list is a header or a footer.')

    sim = dict()
    for _i, (p1, p2) in enumerate(zip(list_phares1[1], list_phrases2[1])):
        # Calculate the similarity between the phrases
        sim[f'{list_phares1[0][_i]}-{list_phrases2[0][_i]}'] = _spacy_cossine_similarity(p1, p2)
        # Check if the similarity is too low
        if sim[f'{list_phares1[0][_i]}-{list_phrases2[0][_i]}'] < 0.5:
            del sim[f'{list_phares1[0][_i]}-{list_phrases2[0][_i]}']
            # Check if cross similarities should be calculated
            if cross_similarities_header and header:
                # Calculate the cross similarity
                cross_similiraty = cross_similarity(list_phares1, list_phrases2)
                sim.update(cross_similiraty)
            elif header:
                # Else, calculate the slice similarity
                slice_sim = slice_similarity(list_phares1, list_phrases2, slice_window)
                sim.update(slice_sim)
            # Check if cross similarities should be calculated
            if cross_similarities_footer and footer:
                # Calculate the cross similarity
                cross_similiraty = cross_similarity(list_phares1, list_phrases2)
                sim.update(cross_similiraty)
            elif footer:
                # Else, calculate the slice similarity
                slice_sim = slice_similarity(list_phares1, list_phrases2, slice_window)
                sim.update(slice_sim)
            return sim
    return sim

def slice_similarity(
        list_phares1:Tuple[List[int],List[str]], 
        list_phrases2:Tuple[List[int],List[str]],
        slice_window:int=3)-> dict:
    """
    Calculate the similarity between slices of sentences from two lists of phrases.

    Args:
        list_phares1 (Tuple[List[int],List[str]]): A tuple containing the page numbers and sentences of the first list.
        list_phrases2 (Tuple[List[int],List[str]]): A tuple containing the page numbers and sentences of the second list.
        slice_window (int, optional): The size of the window to slice the sentences. Defaults to 3.

    Returns:
        dict: A dictionary containing the page numbers of the sentences and their similarity scores.
    """
    numPages1,sentences1 = list_phares1
    numPages2,sentences2 = list_phrases2
    sim = dict()
    for _i, sentence in enumerate(sentences1):
        slice_index_start = _i - slice_window if _i - slice_window >= 0 else 0
        slice_index_end = _i + slice_window if _i + slice_window <= len(sentences2) else len(sentences2)
        for _j in range(slice_index_start, slice_index_end):
            sentence2 = sentences2[_j]
            slice_sim = _spacy_cossine_similarity(sentence, sentence2)
            if slice_sim > 0.9:
                sim[f'{numPages1[_i]}-{numPages2[_j]}'] = slice_sim
    return sim

def cross_similarity(
        list_phares1:Tuple[List[int],List[str]], 
        list_phrases2:Tuple[List[int],List[str]])-> dict:
    """
    Calculate the cross similarity between two lists of phrases.

    Args:
        list_phares1 (list): The first list of phrases.
        list_phrases2 (list): The second list of phrases.

    Returns:
        dict: A dictionary containing the cross similarity scores between phrases.
              The keys are in the format 'numPages1-numPages2' and the values are the cross similarity scores.
    """
    numPages1,sentences1 = list_phares1
    numPages2,sentences2 = list_phrases2
    sim = dict()
    for _i, sentence in enumerate(sentences1):
        for _j, sentence2 in enumerate(sentences2):
            cross_sim = _spacy_cossine_similarity(sentence, sentence2)
            if cross_sim > 0.9:
                sim[f'{numPages1[_i]}-{numPages2[_j]}'] = cross_sim
    return sim

def _spacy_cossine_similarity(text1:str, text2:str) -> float:
    '''Calculates the cossine similarity between two phrases using spacy.

    Args:
        text1 (str): The first phrase.
        text2 (str): The second phrase.

    Returns:
        float: The cosine similarity between the two phrases.
    '''
    text1 = re.sub(r'\d', '@', text1)
    text2 = re.sub(r'\d', '@', text2)
    # Carregue o modelo
    doc1 = NLP(text1)
    doc2 = NLP(text2)
    return doc1.similarity(doc2)