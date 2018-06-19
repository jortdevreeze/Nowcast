# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 09:58:25 2018

@author: jdevreeze
"""

from datetime import datetime
from dateutil.parser import parse

import re
import csv
import time
import requests

def get_relatedwiki(title, lang='en', level=1, related=None, method='restrict'):
    """
    Get the number of related Wikipedia pages. 
    
    This functions extracts all page names that link to the specified page. By adding restrictions
    you can filter out a lot of pages that have only litte relevance for the topic. Please note that 
    these keywords words will be added to the number of related pages (if they exist).
    
    If you would like to find related pages for 'Influenza' you would get topics such as 'Bioterrorism',
    or 'Alexander Fleming' as well. Of course these topics are related, but when someone is feeling ill, 
    that person would more likely be interested in related topics such as 'Soar throat', or 'runny nose'.
    By adding more keywords, you can extend or restrict the number of related topics that have back-links 
    and to-links to the specified Wikipedia page. In addition, it also allows you to put more weight on
    links that shared by the specified page and the pages in the related keywords list.

    Args:
        title: The title of the article
        lang: The article language (default 'en')
        level: The number of links we should go back (only 1 is supported at the moment)
        related: Add other pages that should share the same backlinks
        method: Use 'restrict' (default), 'extent', or 'weight' (not yet implemented)
        
    Returns:
        A list with related pages and their weights.
    
    Raises:
        ValueError: A valid title should be specified.
        ValueError: A valid language should be specified.
        ValueError: A valid number of backlinks should be specified. Currently only one is supported.
        ValueError: A valid restriction list should be specified.
        ValueError: A valid method should be specified.
        ValueError: An unexpected error occured while connecting to Wikipedia.
    """
    
    if title is None or type(title) is not str:
        raise ValueError("A valid title should be specified.")
    
    if lang is None or type(lang) is not str:
        raise ValueError("A valid language should be specified.")
        
    if level > 1 or type(level) is not int:
        raise ValueError("A valid number of backlinks should be specified. Currently only one is supported.") 
    
    if related is not None and type(related) is not list:
        raise ValueError("A valid list with related keywords should be specified.") 
    
    if method not in ['restrict', 'extend', 'weight']:
        raise ValueError("A valid method should be specified.")
    
    # Create internal method to send the request to the MediaWiki API
    
    def __extract(params, lang):
        
        prefix = 'https://'
        suffix = '.wikipedia.org/w/api.php'
        
        url = prefix + lang + suffix       
        
        resp = requests.get(url, params)
        
        if resp.status_code != requests.codes.ok:
             raise ValueError("An unexpected error occured while connecting to Wikipedia (Status code: ", resp.status_code, ").")
        
        return resp.json()    
    
    # Compile a list of all articles to check.
    
    if related is None:
        articles = [title]
    else:    
        articles = [title] + related
    
    backlinks = {}
    tolinks = {}
    control = []
    
    first = True

    for article in articles:
        
        print('Processing article: ' + article)

        # Specify the paramters needed to extract all back-links
        
        links = []        
        params = {
            'action' : 'query',
            'list'   : 'backlinks',
            'bltitle' : article.replace(' ', '_'),
            'format' : 'json'
        }
            
        # Iterate through the entire list of back-links
        
        print('Extracting back-links...')        
        
        while True:        
            
            data = __extract(params, lang)          
            
            if 'query' in data:
                valid = True
                if 'backlinks' in data['query']:
                    for backlink in data['query']['backlinks']:  
                        if ':' not in backlink['title']:
                            links.append(backlink['title'])           
                
                if 'continue' not in data:
                    break
            
                params['blcontinue'] = data['continue']['blcontinue']
                time.sleep(1)
            
        if first is True:
            backlinks = {'title' : links}
            links = []
        else:
            backlinks['related'] = links
        
        # Specify the paramters needed to extract all to-links
        
        links = []        
        params = {
            'action' : 'query',
            'prop'   : 'links',
            'titles' : article.replace(' ', '_'),
            'format' : 'json'
        }
        
        # Iterate through the entire list of to-links

        print('Extracting to-links...')

        while True:        
            
            data = __extract(params, lang)          
            
            if 'query' in data:
                
                valid = True
                pageid = list(data['query']['pages'].keys())[0] 
                
                if 'links' in data['query']['pages'][pageid]:
                    for tolink in data['query']['pages'][pageid]['links']:  
                        if ':' not in tolink['title']:
                            links.append(tolink['title'])           
                
                if 'continue' not in data:
                    break
            
                params['plcontinue'] = data['continue']['plcontinue']
                time.sleep(1)
        
        if first is True:
            tolinks = {'title' : links}
            links = []
            first = False
        else:
            tolinks['related'] = links 
            
        if valid is True:
            control.append(article)
            valid = False
        
        time.sleep(1)
    
    if 'related' not in backlinks:
        related = backlinks['title'] + tolinks['title']
        control = []
        weights = [1] * (len(control) + len(related))
        
    else:
        
        if method is 'restrict' or method is 'extend':
                    
            if method is 'restrict':
                back = [i for i in backlinks['title'] if i in backlinks['related']]
                to = [i for i in tolinks['title'] if i in tolinks['related']]            
            else:
                back = backlinks['title'] + backlinks['related']
                to = tolinks['title'] + tolinks['related']            
        
            related = back + to
            weights = [1] * (len(control) + len(related))
        
        if method is 'weight':
            
            denum = len(related)
            list1 = backlinks['title'] + tolinks['title']
            list2 = backlinks['related'] + tolinks['related']
            
            results1 = {}
            results2 = {}
            
            for i in list1:
                
                # Reward weight if keyword is in the both main page and in the others
                
                results1[i] = (1 + ((list2.count(i) + 1) / (denum + 1)))
                
            list3 = [i for i in list2 if i not in list1] 
            
            for j in list3:
                
                # Penalize weight if keyword is not in main page, but in others
                
                results2[j] = (list3.count(j) / (denum + 1)) 
                
            # Merge both dictionaries
                
            results3 = {**results1, **results2}            
            related = [*results3]
            
            # Give the related keywords maximum weight
            
            weights = list([max(results3.values())] * len(control)) + list(results3.values())            
      
    return control + related, weights

def get_wikiviews(title, lang='en', access='all-access', agents='all-agents', interval='daily', first=None, last=None):
    """
    Get the number of page views for the Wikipedia page. 
    
    This method relies on the REST v1 API from MediaWiki. The number of pageviews are
    only available from August 2015 until today.
    
    For documentation about this API, see: 
    
        https://wikimedia.org/api/rest_v1/ 
    
    Args:
        title: The title of the article
        lang: The article language (default 'en').
        access: If you want to filter by access method, use one of desktop, mobile-app or 
            mobile-web. If you are interested in pageviews regardless of access method, 
            use all-access (Default).
        agents: If you want to filter by agent type, use one of user, bot or spider. 
            If you are interested in pageviews regardless of agent type, use 
            all-agents (Default)
        interval: The time unit for the response data. The only supported granularity 
            for this endpoint is daily (Default) and monthly.
        first: The first date to look for (default None).
        last: The last date to look for (default None). If no date is specified it 
            will only look for revisions done on the first date.
    
    Returns:
        A dict with the dates and the amount of page views for each date.
    
    Raises:
        ValueError: A valid title should be specified.
        ValueError: A valid language should be specified.
        ValueError: A valid access filter should be specified.
        ValueError: A valid agent filter should be specified.
        ValueError: A valid interval should be specified.
        ValueError: A valid start date must be specified.
        ValueError: A valid end date must be specified.
        ValueError: The specified dates could not be converted to a YYYYMMDD format.
        ValueError: The start date is more recent than the last date.
        ValueError: A valid start date must be specified.
        ValueError: An unexpected error occured while connecting to Wikipedia.
        ValueError: The request did not return any information.
    """
    
    if title is None or type(title) is not str:
        raise ValueError("A valid title should be specified.")
    
    if lang is None or type(lang) is not str:
        raise ValueError("A valid language should be specified.")

    if access not in ['all-access', 'desktop', 'mobile-app', 'mobile-web']:
        raise ValueError("A valid access filter should be specified.")
    
    if agents not in ['all-agents', 'user', 'bot', 'spider']:
        raise ValueError("A valid agent filter should be specified.") 
    
    if interval not in ['daily', 'monthly']:
        raise ValueError("A valid interval should be specified.")
           

    first, last = __validate_dates(first, last, '%Y%m%d')    
    title = title.replace(' ', '_')
    
    # Define variables for the REST v1 API
    
    base = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article'
    wiki = lang + '.wikipedia'  
    
    # Merge the paramters into a valid REST v1 API request
    
    rest = '/'.join((base, wiki, access, agents, title, interval, first, last))
    
    # Request the number of page views
    
    resp = requests.get(rest)
    data = resp.json()

    if resp.status_code != requests.codes.ok:    
            
            if 'detail' in data:
                
                # Page doesn't exist or there is no data available
            
                raise ValueError(data['detail']) 
                
            else:
                raise ValueError("An unexpected error occured while connecting to Wikipedia (Status code: ", resp.status_code, ").")
    
    if 'items' not in data:
        raise ValueError("The request did not return any information.")
        
    dates = []
    views = []
    
    for item in data['items']:
        
        timestamp = datetime.strptime(item['timestamp'][:-2], '%Y%m%d')
        timestamp = timestamp.strftime('%Y%m%d')
        
        dates.append(timestamp)
        views.append(item['views'])
    
    return {'dates' : dates, 'views' : views}          

def get_sharkviews(title, lang='en', interval='daily', first=None, last=None):
    """
    Get the number of page views for the Wikipedia page before August 2015
    and from January 2008. 
    
    This method relies on the Wikishark website. For documentation about 
    this website, see: 
    
        http://www.wikishark.com
    
    Unfortunately, wikishark doesn't use an API, so this method extracts the
    pageid from the source. This can be unreliable when the website changes in
    the future.
    
    Args:
        title: The title of the article
        lang: The article language (default 'en').        
        interval: The time unit for the response data. The only supported granularity 
            for this endpoint is hourly, daily (Default) and monthly.
        first: The first date to look for (default None).
        last: The last date to look for (default None). If no date is specified it 
            will only look for revisions done on the first date.
    
    Returns:
        A dict with the dates and the amount of page views for each date.
    
    Raises:
        ValueError: A valid title should be specified.
        ValueError: A valid language should be specified.
        ValueError: A valid interval should be specified.
        ValueError: An unexpected error occured while connecting to Wikishark.
        ValueError: The request did not return any information.
    """
    
    if title is None or type(title) is not str:
        raise ValueError("A valid title should be specified.")
    
    if lang is None or type(lang) is not str:
        raise ValueError("A valid language should be specified.")
    
    if interval not in ['hourly', 'daily', 'monthly']:
        raise ValueError("A valid interval should be specified.")
           
    first, last = __validate_dates(first, last, '%m/%d/%Y')    
    title = title.replace(' ', '_')   
    
    # Define variables for the Wikishark website
    
    base = 'http://www.wikishark.com/title'    
    rest = '/'.join((base, lang, title))
    
    # Request the number of page views
    
    resp = requests.get(rest)
    data = resp.text

    if resp.status_code != requests.codes.ok: 
        raise ValueError("An unexpected error occured while connecting to Wikishark (Status code: ", resp.status_code, ").")
    
    # Regular expression to extract the pageid
    
    match = re.search('\/translate\/id\/\d+', data)
    pageid = re.findall('\d+', match.group(0))[0]
    
    if interval is 'weekly':
        view = 1
    elif interval is 'daily':
        view = 2
    else:
        view = 3
    
    base = 'http://www.wikishark.com/json_print.php'
    params = {
        'values' : pageid,
        'datefrom' : first,
        'dateto' : last,
        'view' : view,
        'normalized' : 0,
        'scale' : 0,
        'peak' : 0,
        'log' : 0, 
        'zerofix' : 0, 
        'sumall' : 0,
        'format' : 'csv'
    }
    
    resp = requests.get(base, params)
    
    if resp.status_code != requests.codes.ok:
         raise ValueError("An unexpected error occured while connecting to Wikipedia (Status code: ", resp.status_code, ").")
    
    data = resp.content.decode('utf-8')
    df = csv.reader(data.splitlines(), delimiter=',')
    
    dates = []
    views = []    
    
    for row in list(df):

        timestamp = datetime.strptime(row[0], '%m/%d/%Y')
        timestamp = timestamp.strftime('%Y%m%d')
        
        dates.append(timestamp)
        views.append(row[1])

    return {'dates' : dates, 'views' : views}  
    
def __validate_dates(first, last, dformat):
    """
    This method validates the date range required for the other methods. 
    
    Args:
        first: The first date to look for (default None).
        last: The last date to look for (default None). If no date is specified it 
            will only look for revisions done on the first date.
        dformat: This specifies how the format should be formated (e.g., YYYYMMDD)
        
    Returns:
        Two strings with the first and last date.
        
    Raises:
        ValueError: A valid start date must be specified.
        ValueError: A valid end date must be specified.
        ValueError: The specified dates could not be converted to a specified format.
        ValueError: The start date is more recent than the last date.
        ValueError: A valid start date must be specified.
    """
    
    if first is not None and type(first) is not str:
        raise ValueError("A valid start date must be specified.")
    
    if last is not None and type(last) is not str:
        raise ValueError("A valid end date must be specified.")    
    
    if first is not None:
        
        if last is None:
            last = first
        
        try:
            
            first = parse(first)
            first = first.strftime(dformat)
            
            last = parse(last)
            last = last.strftime(dformat)
            
        except:                    
            raise ValueError("The specified dates could not be converted to a specified format.") 
        
        if first > last:
            raise ValueError("The start date is more recent than the last date.")    
                  
    else:
        
        if last is not None:
            raise ValueError("A valid start date must be specified.")
            
        first = datetime.strftime(datetime.now(), dformat)
        last = first
        
    return first, last
    
    
#related = get_related(title='Influenza', lang='de', level=1, related=['Halsschmerzen', 'Erkältung'])
#related, weights = get_related(title='Influenza', lang='de', level=1, related=['Halsschmerzen'])
#related, weights = get_related(title='Influenza', lang='de', level=1, related=['Halsschmerzen', 'Erkältung'], method='weight')

data1 = get_sharkviews(title='Influenza', lang='de', interval='daily', first='01-01-2008', last='01-08-2015')
data2 = get_wikiviews(title='Influenza', lang='de', interval='daily', first='01-08-2015', last='01-08-2017')


import tensorflow as tf
