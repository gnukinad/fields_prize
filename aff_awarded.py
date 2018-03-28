#!/usr/bin/env python

import pandas as pd
from bs4 import BeautifulSoup as bs
import urllib
import re
from pprint import pprint as pp

'''
DISCLAMER:
most of these functions were written to certain tasks only, you cannot use them in your code and
expect similar behaviour
'''

def get_table(t):

    '''extract table properly'''

    i = 0

    while(True):
        t = t.find_next('tr')

        if i > 2:
            break
        elif t.find_next('td').has_attr('colspan'):
            i = i + 1
        # elif len(t.find_all('td')) == 4:
        elif len(t.find_all('td')) > 2:
            break
        else:
            i = i + 1


    return t



def remove_par(a):
    '''remove parentehsis from a string'''

    regx = [r'\(.*\)', r'\[.*\]', r'\{.*\}']

    for x in regx:
        a = re.sub(x, '', a)

    return a


def remove_square_par(a):
    '''remove square parentehsis from a string'''

    regx = r'\[.*\]'

    return re.sub(regx, '', a)



def my_read_table(x):

    return pd.read_html(str(x), header=0)[0]


def extract_suitable_items(all_li, degree):

    '''extract items that meets the condition of degree, i.e. extract names with phd only'''

    all_items = [extract_name_degree_year_from_li(x) for x in all_li]

    a = []

    for item in degree:
        degree_re = re.compile(r'\b({})'.format(item), re.I)
        a.extend([x for x in all_items if degree_re.search(x['degree'])])

    return a


def extract_name_degree_year_from_li(x):

    """extract name, degree and year from http li tag"""

    cons = x.contents
    name = cons[0].text
    rem = cons[-1].strip()

    phd_re = re.compile(r'\b(phd)\b', re.I)
    year_re = re.compile(r'\b(\d{4})\b')

    degree_re = re.compile(r'\((.*)\)', re.I)

    try:
        degree = degree_re.search(rem).groups()[0]
    except:
        degree = ''

    try:
        year = year_re.search(rem).groups()[0]
        year = int(year)
    except:
        year = 0

    return dict(zip(['name', 'degree', 'year'], (name, degree, year)))


def extract_awarded_affiliations(df_fname):

    '''extract information about prize winner and the affiliation at a time of award'''

    aff_awarded_page = 'https://en.wikipedia.org/wiki/Fields_Medal'

    fname = 'fields_aff_awarded.html'

    try:
        with open(fname, 'rb') as f:
            soup = f.readlines()

        page = "\n".join(soup)

    except:

        response = urllib.request.urlopen(aff_awarded_page)
        page = response.read()

        f = open(fname, 'wb')
        f.write(page)
        f.close()


    # get html_table
    soup = bs(page, 'html.parser')
    table = soup.find_all('span', id='Fields_medalists')[0].find_all_next('table', class_='wikitable sortable')[0]

    # read table into pandas
    df = pd.read_html(str(table), header=0)[0]

    # remove all parenthesis from colnames
    cols = df.columns.tolist()

    df = df.rename(columns={cols[3]: 'Awarded_Affiliation',
                            cols[4]: 'Last_Affiliation'})

    cols = df.columns.tolist()

    new_cols = [remove_par(x) for x in cols]

    # rename cols
    df = df.rename(columns=dict(zip(cols, new_cols)))
    cols = df.columns.tolist()

    df2 = df.copy()

    # fix empty spaces due to imperfections in read_html
    for index, row in df.iterrows():

        if not str.isdigit(row['Year']):

            df2.at[index, 'Citation'] = df2.at[index, 'Awarded_Affiliation']
            df2.at[index, 'Last_Affiliation'] = df2.at[index, 'Medalists']
            df2.at[index, 'Awarded_Affiliation'] = df2.at[index, 'ICM location']
            df2.at[index, 'Medalists'] = df2.at[index, 'Year']

            df2.at[index, 'ICM location'] = ''
            df2.at[index, 'Year'] = ''

    for index, row in df.iterrows():

        if str.isdigit(row['Year']):
            year = row['Year']
            icm_location = row['ICM location']

        else:
            df2.at[index, 'Year'] = year
            df2.at[index, 'ICM location'] = icm_location

    # df2.to_excel('field_prize_awarded_aff.xlsx')
    df2.to_excel(df_fname)



def extract_host_phd(df_fname):

    '''extract information about the winner and his host phd university'''

    link = 'https://en.wikipedia.org/wiki/List_of_Fields_Medal_winners_by_university_affiliation'

    fname = 'fields_host_phd.html'

    try:

        print('in try')
        with open(fname, 'r') as f:
            soup = f.readlines()

        print('soup detected')
        page = "\n".join(soup)
        print('page detected')

        print('reading page from local storage')

    except:

        response = urllib.request.urlopen(link)
        page = response.read()

        print('reading page from web storage')

        f = open(fname, 'wb')
        f.write(page)
        f.close()


    # get all tables from web page
    soup = bs(page, 'html.parser')
    all_tables = soup.find_all('table', class_='wikitable')

    # identify which tables are needed
    # this cols are in the tables that are needed for us
    cols_in_table = ['Affiliations', 'Graduate and Attendees', 'Long-term Academic Staff', 'Temporary Academic Staff']
    gut_tables = [x for x in all_tables if my_read_table(x).columns.tolist() == cols_in_table]

    tables = []
    tables2 = []
    tables3 = []

    # for a in gut_tables[:5]:
    for i, a in enumerate(gut_tables):
        # a = gut_tables[0]

        aff_name = a.find_next('tr').find_next('tr').text.strip()

        # print('i is', i)
        # print('aff_name ', aff_name)

        b = a.find_next('tr').find_next('tr')

        t = get_table(b)
        ext = extract_suitable_items(t.find_next('td').find_next('td').find_all('li'), 'phd')

        ext2 = ext.copy()

        # add aff_name to every item in the list
        [x.update({'host_phd_aff': aff_name, 'prize': 'field'}) for x in ext2]

        ext = {'aff_name': aff_name, 'table': ext}

        if 'Michigan' in aff_name:
            print('qwewqeq')
            # print(b)
            # print(t)

        tables.append(ext)
        tables2.append(ext2)
        tables3.extend(ext2)

    print('len(gut_tables)')
    print(len(gut_tables))

    df = pd.DataFrame(tables3)
    df.to_excel(df_fname)




if __name__ == "__main__":

    '''concatenate two tables (with affiliation at time of a award and phd host affiliation)'''

    # df_host_phd_fname = 'field_prize_host_phd.xlsx'
    # df_awarded_aff_fname = 'field_prize_awarded_aff.xlsx'

    df_host_phd_fname = 'field_prize_host_phd_extended.xlsx'
    df_awarded_aff_fname = 'field_prize_awarded_aff_extended.xlsx'

    cname_awarded_aff = 'Medalists'
    cname_host_phd = 'name'

    # runs this code to extract data
    # beware you need to fix the names manually in both files due to inconsistency in namings
    # perelman, margulis, thom, jones, cohen, kontsevich roth milnor, schwartz
    # extract_awarded_affiliations(df_awarded_aff_fname)
    # extract_host_phd(df_host_phd_fname)

    # run this code to merge two dataframes

    awarded_aff = pd.read_excel(df_awarded_aff_fname)
    host_phd = pd.read_excel(df_host_phd_fname)



    common_winner_names = list(set(awarded_aff[cname_awarded_aff].tolist()) & set(host_phd[cname_host_phd].tolist()))

    in_awarded_not_phd  = list(set(awarded_aff[cname_awarded_aff].tolist()) - set(host_phd[cname_host_phd].tolist()))

    in_phd_not_awarded  = list(set(host_phd[cname_host_phd].tolist()) - set(awarded_aff[cname_awarded_aff].tolist()))

    df = pd.DataFrame(columns=[cname_host_phd, 'awarded_affiliation', 'host_phd_affiliation', 'last_affiliation', 'award_year', 'degree', 'citation']).set_index(cname_host_phd)

    # awarded_aff = awarded_aff.set_index('Medalists')
    # host_phd = host_phd.set_index("name")

    aaa = []

    for i, name in enumerate(common_winner_names):

        dict_awarded_aff = awarded_aff.groupby(cname_awarded_aff).get_group(name).to_dict('records')
        dict_host_phd = host_phd.groupby(cname_host_phd).get_group(name).to_dict('records')

        dict_awarded_aff = dict_awarded_aff[0]

        if len(dict_host_phd) > 1:

            for d in dict_host_phd:
                # dict_host_phd = dict_host_phd[0]


                aaa.append({
                    'name'                 : name,
                    'awarded_affiliation'  : remove_square_par(dict_awarded_aff['Awarded_Affiliation']),
                    'last_affiliation'     : remove_square_par(dict_awarded_aff['Last_Affiliation']),
                    'host_phd_affiliation' : remove_square_par(d['host_phd_aff']),
                    'award_year'           : dict_awarded_aff['Year'],
                    'degree'               : d['degree'],
                    'citation'             : remove_square_par(dict_awarded_aff['Citation']),
                    'award'                : 'field'
                })

        else:

            dict_host_phd = dict_host_phd[0]


            aaa.append({
                'name'                 : name,
                'awarded_affiliation'  : remove_square_par(dict_awarded_aff['Awarded_Affiliation']),
                'last_affiliation'     : remove_square_par(dict_awarded_aff['Last_Affiliation']),
                'host_phd_affiliation' : remove_square_par(dict_host_phd['host_phd_aff']),
                'award_year'           : dict_awarded_aff['Year'],
                'degree'               : remove_square_par(dict_host_phd['degree']),
                'citation'             : remove_square_par(dict_awarded_aff['Citation']),
                'award'                : 'field'
            })


    # create df with names in awarded but not in phd
    bbb = []
    for i, name in enumerate(in_awarded_not_phd):

        dict_awarded_aff = awarded_aff.groupby(cname_awarded_aff).get_group(name).to_dict('records')

        dict_awarded_aff = dict_awarded_aff[0]

        bbb.append({
            'name'                 : name,
            'awarded_affiliation'  : remove_square_par(dict_awarded_aff['Awarded_Affiliation']),
            'last_affiliation'     : remove_square_par(dict_awarded_aff['Last_Affiliation']),
            'host_phd_affiliation' : '',
            'award_year'           : dict_awarded_aff['Year'],
            'degree'               : '',
            'citation'             : remove_square_par(dict_awarded_aff['Citation']),
            'award'                : 'field'
        })


    # create df with names in phd but not in awarded
    ccc = []
    for i, name in enumerate(in_phd_not_awarded):

        dict_host_phd = host_phd.groupby(cname_host_phd).get_group(name).to_dict('records')

        if len(dict_host_phd) > 1:

            for d in dict_host_phd:
                # dict_host_phd = dict_host_phd[0]

                ccc.append({
                    'name'                 : name,
                    'awarded_affiliation'  : '',
                    'last_affiliation'     : '',
                    'host_phd_affiliation' : remove_square_par(dict_host_phd['host_phd_aff']),
                    'award_year'           : dict_host_phd['year'],
                    'degree'               : dict_host_phd['degree'],
                    'citation'             : '',
                    'award'                : 'field'
                })

        else:

            dict_host_phd = dict_host_phd[0]


            ccc.append({
                'name'                 : name,
                'awarded_affiliation'  : '',
                'last_affiliation'     : '',
                'host_phd_affiliation' : remove_square_par(dict_host_phd['host_phd_aff']),
                'award_year'           : dict_host_phd['year'],
                'degree'               : dict_host_phd['degree'],
                'citation'             : '',
                'award'                : 'field'
            })

    df = pd.DataFrame(aaa)
    df.to_excel('field_prize_concatenated.xlsx', index=False)

    '''
    df_awarded_aff = pd.DataFrame(bbb)
    df_awarded_aff.to_excel('field_in_awarded_aff.xlsx', index=False)

    df_host_phd = pd.DataFrame(ccc)
    df_host_phd.to_excel('field_in_host_phd.xlsx', index=False)
    '''
