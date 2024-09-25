import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from unidecode import unidecode
from utils import get_start_and_end_dates, clean_text
import os
import argparse


def getDebateUrls(start_date: datetime, end_date: datetime):
    # get all the urls in https://www.theyworkforyou.com/pwdata/scrapedxml/debates/ after start date
    response = requests.get('https://www.theyworkforyou.com/pwdata/scrapedxml/debates/')
    soup = BeautifulSoup(response.content, 'html.parser')

    rows = soup.find_all('tr')

    filtered_links = []
    for row in rows:
        columns = row.find_all('td')
        if len(columns) == 5:
            href = columns[1].find('a')['href']
            file_name = columns[1].find('a').text #e.g. debates2024-07-23c.xml
            if file_name.startswith('debates'):
                date_str = file_name[7:17]
                if date_str:
                    link_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if link_date >= start_date and link_date <= end_date:
                        filtered_links.append('https://www.theyworkforyou.com/pwdata/scrapedxml/debates/'+href)
    return filtered_links

def getSpeeches(url:str):
    # input e.g. https://www.theyworkforyou.com/pwdata/scrapedxml/debates/debates2024-07-26b.xml
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return
        soup = BeautifulSoup(response.content,features="xml") #pip3 install lxml
        speeches = soup.find_all('speech')
        result = []
        date = url.split('/')[-1][7:17]
        # Extract the speaker names and the corresponding speech text
        for speech in speeches:
            if speech.get('nospeaker', '') == 'true':
                continue
            speaker = speech['speakername']
            speech_text = " ".join([p.get_text() for p in speech.find_all('p')])
            speech_text = clean_text(unidecode(speech_text))
            partition = {
                        'url': url, 
                        'date_str': date, # 'yyyy-mm-dd'
                        'title': '',
                        'speaker': speaker,
                        'data': speech_text,
                        'chamber': '',
                        'country': 'GBR',
                        }
            result.append(partition)
        return result
    except:
        # raise Exception
        print(f'failed to get result for url: {url}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Pass year and month")
    parser.add_argument('-y', '--year', help='year',type=int)
    parser.add_argument('-m', '--month', help='month',type=int)
    args = parser.parse_args()
    if args:
        year = args.year
        month = args.month
    else:
        year = datetime.now().year
        month = datetime.now().month
    start_date, end_date = get_start_and_end_dates(year, month)
    urls = getDebateUrls(start_date, end_date)
    result = []
    for url in urls:
        result_by_date = getSpeeches(url)
        if result_by_date:
            result.extend(result_by_date)
    result_dir = './result/gbr'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    if result:
        print(len(result))
        with open(os.path.join(result_dir,f'{datetime.strftime(start_date, "%Y-%m")}.json'), 'w') as fw:
            json.dump(result, fw, indent=2)