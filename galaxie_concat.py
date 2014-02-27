#!/usr/bin/python
# -*- coding: utf-8 -*-
# Pierre Haessig — Février 2014
""" Concaténation et filtrage des postes GALAXIE

"""

from __future__ import division, print_function, unicode_literals
import os.path
import datetime
import urllib
import io
from bs4 import BeautifulSoup

today = datetime.date.today()

urls = {
'published':
'https://www.galaxie.enseignementsup-recherche.gouv.fr/ensup/ListesPostesPublies/Emplois_publies_TrieParCorps.html',
'prepub':
'https://www.galaxie.enseignementsup-recherche.gouv.fr/ensup/ListesPostesPublies/Emplois_prepublies_TrieParCorps.html',
#'tous xls':
#'https://www.galaxie.enseignementsup-recherche.gouv.fr/ensup/ListesPostesPublies/ListePostePubliesAnnuelle.xls'
}

def decode(req):
    'decode the lines of the request'
    enc = 'iso-8859-1'
    for line in req:
        yield line.decode(enc)

def fix_th(req):
    'fix wrong closing tags'
    for line in req:
        if '<th' in line:
            line = line.replace('</td>', '</th>')
        yield line

def read_table(url, save=True):
    '''reads `url` and return the text content (html)'''
    basename = os.path.basename(url)
    print('downloading {:s}...'.format(basename))
    req =  urllib.urlopen(url)
    stamp = today.isoformat()
    html = ''.join(fix_th(decode(req)))
    req.close()
    if save:
        output = stamp+' '+basename
        print('saving {}'.format(output))
        with io.open(output, 'w', encoding='iso-8859-1') as out:
            out.write(html)
    return html

def extract_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    tabs = soup.find_all('table')
    assert len(tabs) == 2
    # Extraction des lignes :
    rows = tabs[1].find_all('tr', recursive=False)
    header = rows[0]
    rows = rows[1:]
    return (header, rows)


def section_filter(section, rows):
    '''filtre par section de poste'''
    try:
        section = set(section)
    except TypeError: # 'int' object is not iterable
        section = set([section])
    #print('sections choisies : {}'.format(section))
    
    for tr in rows:
        cols = tr.find_all('td')
        assert len(cols) == 16
        row_sections = [td.text for td in cols[7:10]]
        row_sections = [int(n) for n in row_sections if n != '']
        if section & set(row_sections):
            yield tr

def corps_filter(corps, rows):
    '''filtre par type de poste MCF vs. PR'''
    for tr in rows:
        cols = tr.find_all('td')
        assert len(cols) == 16
        row_corps = cols[5].text
        assert row_corps in ['MCF', 'PR']
        if corps ==  row_corps:
            yield tr


def extract_data(urls, sections, corps):
    'calls all the above functions to do the job'
    data={}
    print('Sélection des postes')
    print(' * sections {}'.format(sections))
    print(' * corps {}'.format(corps))
    for key in urls:
        html = read_table(urls[key], save=False)
        header, rows = extract_table(html)
        head_list = [th.b.text for th in header.find_all('th')]
        selected_rows = list(corps_filter(corps,
                              section_filter(sections, rows)
                             ))
        print('  nb poste correspondants : {}'.format(len(selected_rows)))
        data[key] = {'header':header,
                     'head list': head_list,
                     'rows':selected_rows}
    # end for
    return data

html_template = '''<!DOCTYPE HTML>
<html>
  <head>
    <title>Postes GALAXIE</title>
    <meta http-equiv=Content-Type content="text/html; charset=utf-8">
    <style>
      {css}
    </style>
  </head>
  <body>
    <h1>Liste concaténée des postes GALAXIE</h1>
    
    <p>Extraction du {date}</p>
    <p>{infos}</p>
    <p>nombre de postes correspondants : {nb_res}</p>

    <table>
      <thead>
      {header}
      </thead>
      <tbody>
      {table}
      </tbody>
    </table>
  </body>
</html>
'''

css='''
body {font-family: sans;}

table {
border-spacing: 0px; border-collapse: collapse;}

td, th {
border:1px solid black;}

th {
font-weight:bold; background-color:#DDD}

td.comment {
text-align: center;
font-style: italic;
background-color:#EEE
}

/*Etablissement et lieu*/
td:nth-child(2), td:nth-child(15) {
  background-color: #AACCFF;
}

/*Sections*/
td:nth-child(8), td:nth-child(9), td:nth-child(10) {
  background-color: #FFFFDD;
}

/*Profil*/
td:nth-child(14) {
  background-color: #DDFFDD;
}
'''

### DO the job

if __name__ == '__main__':
    sections = [63]
    corps = 'MCF'
    extracted_data = extract_data(urls, sections, corps)

    header = extracted_data['published']['header']

    table = '<tr><td colspan="16" class="comment">postes publiés</td></tr>'
    table += ''.join(unicode(r) for r in extracted_data['published']['rows'])
    table += '<tr><td colspan="16" class="comment">prépublications</td></tr>'
    table += ''.join(unicode(r) for r in extracted_data['prepub']['rows'])

    infos = 'sections choisies : {}, corps : {}'.format(sections, corps)

    nb_res = '{:d} + {:d} prépubliés'.format(
              len(extracted_data['published']['rows']),
              len(extracted_data['prepub']['rows']))

    html_out = html_template.format(header = unicode(header),
                                    table=table,
                                    infos=infos,
                                    nb_res=nb_res,
                                    date=today.isoformat(),
                                    css=css)


    # Écrire le fichier
    output = '{} concat.html'.format(today.isoformat())
    print('Enregistrement de "{}"...'.format(output))
    with io.open(output, 'wt', encoding='utf-8') as out:
        out.write(html_out)
