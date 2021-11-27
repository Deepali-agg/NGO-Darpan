# -*- coding: utf-8 -*-
"""
Created on Sat Nov 27 12:39:10 2021

@author: Deepali
@description: Scraping data of NGOs
"""
# Standard
import re 

# External
from bs4 import BeautifulSoup 
import pandas as pd 
import requests
import tqdm

# Local

NGO_DATA_URL = 'https://ngodarpan.gov.in/index.php/ajaxcontroller/show_ngo_info'
STATEWISE_URL = 'https://ngodarpan.gov.in/index.php/home/statewise'
REQUIRED_COLS = ['Name','State', 'City','Type of NGO', 'Work Area/Purpose', 
                 'Mail','Phone','Address', 'Website','Year of Registration', 'Name of Achievement']

def get_token(sess):
    '''Generating CSRF token'''
    req_csrf = sess.get('https://ngodarpan.gov.in/index.php/ajaxcontroller/get_csrf')
    return req_csrf.json()['csrf_token']

def get_ids(url):
    '''Gather IDs of NGOs from statewise webpage. Return list of IDs of all 10 NGOs in page'''
    site = requests.get(url)
    soup = BeautifulSoup(site.content, 'html.parser')
    ids = []
    for i in soup.find_all('table')[0].find_all('a'):
        ids.append(i.attrs['onclick'].split('"')[1])
    return ids

def get_json_data(id_):
    '''Retrieve json data of an NGO'''
    ses = requests.Session()
    site = ses.post(url = NGO_DATA_URL,
                    headers={'X-Requested-With' : 'XMLHttpRequest'},
                    data = {"id":id_, 'csrf_test_name' : get_token(ses)})
    data = site.json()
    ses.close()
    return data

def if_empty(cell):
    if (cell == None) or (cell == ''):
        return 'Not Available'
    else:
        return cell

def generate_dictionary(data, df):
    '''Creates dictionary of all required columns'''
    df['Name'].append(if_empty(data['infor']['0']['ngo_name'].title()))
    df['State'].append(if_empty(data['registeration_info'][0]['StateName'].title()))
    df['City'].append(if_empty(data['registeration_info'][0]['nr_city'].title()))
    df['Type of NGO'].append(if_empty(data['registeration_info'][0]['TypeDescription']))  
    df['Work Area/Purpose'].append(if_empty(data['infor']['issues_working_db'].title()))
    df['Mail'].append(if_empty(data['infor']['0']['Email'].lower()))
    df['Phone'].append(if_empty(data['infor']['0']['Mobile']))
    df['Address'].append(if_empty(data['registeration_info'][0]['nr_add']).title())
    df['Website'].append(if_empty(data['infor']['0']['ngo_url']))
    df['Year of Registration'].append(if_empty(data['registeration_info'][0]['ngo_reg_date'][-4:]))
    df['Name of Achievement'].append(if_empty(data['infor']['0']['Major_Activities1']).capitalize())

def ngo_type(x):
    for i in x:
        list_= re.sub("[^A-Za-z ]","", i).lower().split()
    if 'nongovernment' or 'private' in l:
        return 'Non-Government'
    else:
        return 'Government'

site = requests.get(STATEWISE_URL)
soup = BeautifulSoup(site.content, 'html.parser')
state_links = {}
for ele in soup.find_all('a', class_= 'bluelink11px'):
    state_links[ele.text.split('(')[0].strip()] = ele.attrs['href']

while True:
    state = (input('Enter state as given on the site (or type "q" to quit):')).strip().upper()
    if state == 'Q':
        break
    elif state_links.get(state, 0) == 0:
        print('Please enter a valid state as given in the site.\n')
        continue 
    try:
        start_page = int(input('Start page: '))
        end_page = int(input('End page: '))
    except ValueError:
        print('Please enter numbers.\n')
        continue
    if start_page > end_page:
        print('Enter appropriate start and end page numbers.\n')
        continue
    else:
        urls_list = []
        for page_no in range(start_page, end_page+1):
            urls_list.append(state_links[state][:-1] + f'{str(page_no)}?per_page=10')
        df = {col:[] for col in REQUIRED_COLS}
        print('Extracting data...')
        for url in tqdm.tqdm(urls_list, desc = 'Pages scraped'):
            ids = get_ids(url)
            for id_ in ids:
                data = get_json_data(id_)
                generate_dictionary(data, df)
        df = pd.DataFrame(df)
        df['Type of NGO'] = df['Type of NGO'].map(ngo_type)
        print('Saving file...')
        df.to_excel(f'{state} NGOs pg{start_page}-{end_page}.xlsx', index = False)
        print('Done!')
        break


