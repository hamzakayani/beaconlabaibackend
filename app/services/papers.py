import requests
import time
from bs4 import BeautifulSoup
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


PUBMED_URL = {
    'base': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
    'esearch': 'esearch.fcgi?db={db}&term={term}&retmode=json&retmax={retmax}',
    'esummary': 'esummary.fcgi?db={db}&id={ids}&retmode=json',
    'efetch': "efetch.fcgi?db={db}&id={uid}&retmode={retmode}",
}

def parse_doi_ws_json(data):
    '''
    Parse the JSON returns from DOI webservice
    https://api.crossref.org/works/
    '''
    paper_info = {
        'title': '',
        'abstract': '',
        'pub_date': '',
        'authors': '',
        'journal': '',
    }
        
    # Retrieve title
    if data is None or 'message' not in data:
        # what???
        return None

    if 'title' not in data['message']:
        # no need to parse if title is not there
        return None
    
    title = data['message']['title'][0]
    paper_info['title'] = title
    
    # Retrieve abstract
    if 'abstract' in data['message']:
        abstract_html = data['message']['abstract']
        abstract_text = BeautifulSoup(abstract_html, 'html.parser').get_text()
        paper_info['abstract'] = abstract_text
    else:
        paper_info['abstract'] = ""
    
    # Retrieve publication date
    if 'published-print' in data['message']:
        publication_date_parts = data['message']['published-print']['date-parts'][0]
        publication_date = '-'.join(str(part) for part in publication_date_parts)
        paper_info['pub_date'] = publication_date
    else:
        paper_info['pub_date'] = ""
    
    # Retrieve authors
    authors = []
    if 'author' in data['message']:
        for author in data['message']['author']:
            an = ''
            if 'given' in author:
                an = author['given']
            if 'family' in author:
                if an == '':
                    an = author['family']
                else:
                    an = an + ' ' + author['family']
            
            if an != '':
                authors.append(an)
        
        paper_info['authors'] = '; '.join(authors)
    
    # Retrieve journal information
    if 'container-title' in data['message']:
        journal_info = data['message']['container-title'][0]
        paper_info['journal'] = journal_info
    
    return paper_info

def doi_fetch(doi):
    '''
    Get paper metadata by DOI

    Returns

    1. Parsed result
    2. Raw JSON result
    '''
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        paper_info = parse_doi_ws_json(data)

        if paper_info is None:
            return None, None, 'None Information'

        return paper_info, data, 'OK'

    else:
        return None, None, 'DOI Service Error %s' % response.status_code

def _get_e_fetch_url(uid, db='pubmed', retmode='xml'):
    url = PUBMED_URL['base'] + PUBMED_URL['efetch'].format(db=db, uid=uid, retmode=retmode)
    return url

def _e_fetch(ids, db='pubmed'):
    '''
    Get the raw xml data from pubmed
    '''
    try_times = 0

    while True:
        url = _get_e_fetch_url(','.join(ids))
        print('* e_fetch %s' % url)
        r = requests.get(url)

        if r.status_code == 200:
            return r.text

        # something wrong?
        try_times += 1
        print('* Something wrong, HTTP Status Code: {0}'.format(r.status_code))
        if r.status_code == 429:
            print('* Reached MAX request limit of PubMed')

        if try_times < 3:
            dur = 7 * try_times
            print('* Wait for %s seconds and try again ...' % dur)
            time.sleep(dur)
        else:
            break
    
    print('* Tried e_fetch %s times but still failed ...' % try_times)
    return None


def e_fetch(ids, db='pubmed'):
    '''
    get JSONfied data
    '''
    text = _e_fetch(ids, db)

    if text is None:
        return None

    # parse the xml tree
    root = ET.fromstring(text)

    ret = {
        'result': {
            'uids': []
        }
    }
    for item in root.findall('PubmedArticle'):
        # check each item
        paper = {
            'uid': '',
            'sortpubdate': [],
            'date_pub': [],
            'date_epub': [],
            'date_revised': [],
            'date_completed': [],
            'source': '',
            'title': '',
            'authors': [],
            'abstract': [],
            'raw_type': 'pubmed_xml',
            'xml': ET.tostring(item, encoding='utf8', method='xml')
        }

        # check each xml node
        for node in item.iter():
            if node.tag == 'PMID': 
                if paper['uid'] == '':
                    paper['uid'] = node.text
                else:
                    # other PMIDs will also appear in result
                    pass

            elif node.tag == 'ArticleTitle':
                paper['title'] = node.text

            elif node.tag == 'Abstract':
                for c in node:
                    if c is None or c.text is None:
                        pass
                    else:
                        paper['abstract'].append(c.text)

            elif node.tag == 'ISOAbbreviation':
                paper['source'] = node.text

            # 2021-03-24: there are four types of date
            # take this for example: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=27717298&retmode=xml
            # I guess
            # - ArticleDate is the ePub date
            # - PubDate is the journal physical publication date
            # - DateCompleted is ... I don't know
            # - DateRevised is the online revision date
            # in the last, if ArticleDate is available, just use ArticleDate
            # if not, follow the order above

            elif node.tag == 'ArticleDate':
                for c in node:
                    paper['date_epub'].append(c.text)

            elif node.tag == 'PubDate':
                for c in node:
                    paper['date_pub'].append(c.text)

            elif node.tag == 'DateCompleted':
                for c in node:
                    paper['date_completed'].append(c.text)

            elif node.tag == 'DateRevised':
                for c in node:
                    paper['date_revised'].append(c.text)
                
            elif node.tag == 'AuthorList':
                for c in node:
                    fore_name = c.find('ForeName')
                    last_name = c.find('LastName')
                    name = ('' if fore_name is None else fore_name.text) + ' ' + \
                           ('' if last_name is None else last_name.text)

                    paper['authors'].append({
                        'name': name,
                        'authtype': 'Author'
                    })
        # merge abstract
        paper['abstract'] = ' '.join(paper['abstract'])

        # try to find the good date
        paper['date_epub'] = '-'.join(paper['date_epub'])
        paper['date_pub'] = '-'.join(paper['date_pub'])
        paper['date_completed'] = '-'.join(paper['date_completed'])
        paper['date_revised'] = '-'.join(paper['date_revised'])

        if paper['date_epub'] != '':
            paper['sortpubdate'] = paper['date_epub']
        elif paper['date_pub'] != '':
            paper['sortpubdate'] = paper['date_pub']
        elif paper['date_pub'] != '':
            paper['sortpubdate'] = paper['date_completed']
        elif paper['date_pub'] != '':
            paper['sortpubdate'] = paper['date_revised']
        else:
            paper['sortpubdate'] = ''

        # append to return
        if paper['uid'] != '':
            ret['result']['uids'].append(paper['uid'])
            ret['result'][paper['uid']] = paper

    return ret