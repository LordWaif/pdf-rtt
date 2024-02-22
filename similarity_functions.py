import spacy,re

NLP = spacy.load('pt_core_news_sm')
def spacy_cossine_similarity(list_phares1, list_phrases2,header=False,footer=False):
    '''Calculates the cossine similarity between two lists of phrases using spacy.'''
    if not(footer or header):
        raise ValueError('You must specify if the list is a header or a footer.')
    # if len(list_phares1[1]) == 0 or len(list_phrases2[1]) == 0:
    #     raise ValueError('The lists must have at least one element.')
    # if len(list_phares1[1]) != len(list_phrases2[1]):
    #     raise ValueError('The lists must have the same length.')
    sim = dict()
    for _i,(p1, p2) in enumerate(zip(list_phares1[1], list_phrases2[1])):
        sim[f'{list_phares1[0][_i]}-{list_phrases2[0][_i]}'] = _spacy_cossine_similarity(p1, p2)
        if sim[f'{list_phares1[0][_i]}-{list_phrases2[0][_i]}'] < 0.5:
            del sim[f'{list_phares1[0][_i]}-{list_phrases2[0][_i]}']
            if footer:
                cross_similiraty = cross_similarity(list_phares1, list_phrases2)
                sim.update(cross_similiraty)
            return sim
    return sim

def cross_similarity(list_phares1, list_phrases2):
    numPages1 = list_phares1[0]
    numPages2 = list_phrases2[0]
    sentences1 = list_phares1[1]
    sentences2 = list_phrases2[1]
    sim = dict()
    for _i, sentence in enumerate(sentences1):
        for _j, sentence2 in enumerate(sentences2):
            cross_sim = _spacy_cossine_similarity(sentence, sentence2)
            if cross_sim > 0.9:
                sim[f'{numPages1[_i]}-{numPages2[_j]}'] = cross_sim
    return sim

def _spacy_cossine_similarity(text1, text2):
    '''Calculates the cossine similarity between two phrases using spacy.'''
    text1 = re.sub(r'\d', '@', text1)
    text2 = re.sub(r'\d', '@', text2)
    # Carregue o modelo
    doc1 = NLP(text1)
    doc2 = NLP(text2)
    return doc1.similarity(doc2)