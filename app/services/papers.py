import requests

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