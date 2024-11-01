import re
import statistics
from line_utils import remountLine

PREFIXO =r'(^)\s?(((SE[CÇ][ÃA]O)|(CAP[IÍ]TULO)|(CL[ÁA]USULA))([ ]){1,5})?(([LXVI]{1,8})|(\d{1,3})|((D[ÉE]CIM[AO]|(VIG[ÉE]SIM[AO]))?((PRIMEIR[AO])|(SEGUND[AO])|(TERCEIR[AO])|(QUART[AO])|(QUINT[AO])|(SEXT[AO])|(S[ÉE]TIM[AO])|(OITAV[AO])|(NON[AO])|)))([ )—––.-]+)([0])?([ )—––.-]*)(\n){0,2}'
EXP_GERAL = re.compile(r'('+PREFIXO+'((([A-ZÀÁÃÂÄÈÉÊËÍÎÔÕÓÒÖÛÚÙÜÇ-])+([0-9() \'“”""ªº\/:.,;–$%#@!\?&\*\|·])*){4,}))')
EXP_AVISO = re.compile(r'^(AVISO).{0,20}(LICITA[ÇC][ÃA]O)',flags=re.M)
EXP_ANEXO = re.compile(rf'((({PREFIXO})|^)(ANEXO[S]?).*)',flags=re.M)
EXP_SUMARIO = re.compile(r'^(SUM[ÁA]RIO|INDÍCE|SÚMULA|SEÇÕES|EPÍTOME).*$',flags=re.M)


def identify_sections(pdf_html):
    """
    Identifies sections and summary lines in a PDF HTML.

    Args:
        pdf_html (BeautifulSoup): The parsed HTML of the PDF.

    Returns:
        tuple: A tuple containing two lists. The first list contains the identified sections,
               where each section is represented as a tuple containing the page index, page height,
               and the line element. The second list contains the summary lines, which are line numbers
               that are likely to be part of the summary.

    """
    sections = []
    summary_page = None
    summary_punctuation = []
    for _i,_page in enumerate(pdf_html.find_all('page')):
        for _line in _page.find_all('line'):
            line = remountLine(_line)
            if EXP_SUMARIO.search(line):
                summary_page = _i
            if EXP_ANEXO.search(line):
                sections.append((_i,_page.get('height'),_line,'anexo'))
                # print(' '.join([_w.get_text() for _w in sections[-1][2].find_all('word')]))
            elif EXP_GERAL.search(line):
                sections.append((_i,_page.get('height'),_line,'secao'))
                # print(_line.get('number'),' '.join([_w.get_text() for _w in sections[-1][2].find_all('word')]))
            if _i <= 5:
                # if _i <= 1:
                #     print(_line.get('number'),' '.join([_w.get_text() for _w in _line.find_all('word')]))
                if len(sections) > 1:
                    isCalculated = False
                    if len(summary_punctuation) > 0:
                        if summary_punctuation[-1][0] == (sections[-1][2].get('number'),sections[-2][2].get('number'),_i):
                            isCalculated = True
                    if not isCalculated:
                        summary_punctuation.append(
                            (
                                (
                                    sections[-1][2].get('number'),
                                    sections[-2][2].get('number'),
                                    _i
                                ),
                                indentify_summary
                                    (
                                        sections[-2],
                                        sections[-1],
                                        summary_page
                                    )
                            )
                        )
    summary_punctuation_per_page = {}
    summary_lines = []
    for _ in summary_punctuation:
        if _[0][2] not in summary_punctuation_per_page:
            summary_punctuation_per_page[_[0][2]] = [_]
        else:
            summary_punctuation_per_page[_[0][2]].append(_)
    
    for _ in summary_punctuation_per_page:
        punctuations = list(
        map(
            lambda x: (x[0],round(x[1],2)),
            filter(lambda x: x[1]>0,
                summary_punctuation_per_page[_]
                )
            )
        )
        if len(punctuations) < 3:
            continue
        _moda = statistics.mode([_[1] for _ in punctuations])
        if len([_p for _p in punctuations if _p[1] == _moda])/len(punctuations) > 0.5:
            _numbera = [_[0][0] for _ in punctuations]
            _numberl = [_[0][1] for _ in punctuations]
            _lines_summary = _numbera + _numberl
            _lines_summary = list(set(_lines_summary))
            _lines_summary.sort()
            _i,_f = _lines_summary[0],_lines_summary[-1]
            summary_lines.extend([_ for _ in range(_i,_f+1)])
    return sections,summary_lines

def indentify_summary(last_section, actual_section,summary_page=None):
    """
    Calculates the punctuation for identifying if a section is a summary.

    Args:
        last_section (tuple): A tuple containing the page number, height, and section of the last section.
        actual_section (tuple): A tuple containing the page number, height, and section of the actual section.

    Returns:
        float: The punctuation value indicating the likelihood of the actual section being a summary.
    """
    _pglast, _heightlast, last_section, _type = last_section
    _pgactual, _heightactual, actual_section, _type = actual_section
    punctuation = 0
    coordernates_actual = {'ymin': float(actual_section.get('ymin')), 'ymax': float(actual_section.get('ymax'))}
    coordernates_last = {'ymin': float(last_section.get('ymin')), 'ymax': float(last_section.get('ymax'))}
    if _pglast == summary_page:
        # print(' '.join([_w.get_text() for _w in actual_section.find_all('word')]))
        # print(' '.join([_w.get_text() for _w in last_section.find_all('word')]))
        punctuation += 1
    if _pglast < _pgactual:
        distance = (coordernates_actual['ymin'] + float(_heightlast)) - coordernates_last['ymax']
    elif _pglast == _pgactual:
        distance = coordernates_actual['ymin'] - coordernates_last['ymax']
    else:
        raise ValueError('Page order is wrong')
    sum_dist =(coordernates_actual['ymax'] - coordernates_actual['ymin']) + (coordernates_last['ymax'] - coordernates_last['ymin'])
    lenght_line = sum_dist / 2
    if int(last_section.get('number')) == int(actual_section.get('number'))-1:
        punctuation += 1
    if distance < lenght_line * 1.2:
        if distance < 0:
            distance = abs(distance)
        punctuation += 2 / (distance)
        actual_last_word = actual_section.find_all('word')[-1]
        last_last_word = last_section.find_all('word')[-1]

        actual_last_word_text = re.sub(f'\d+', '@', re.sub(f'[^\d]', '', actual_last_word.get_text()))
        last_last_word_text = re.sub(f'\d+', '@', re.sub(f'[^\d]', '', last_last_word.get_text()))

        if actual_last_word_text != '' and last_last_word_text != '':
            punctuation += actual_last_word_text == last_last_word_text

    return punctuation


