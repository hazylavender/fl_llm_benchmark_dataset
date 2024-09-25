import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from unidecode import unidecode
import os
from utils import get_start_and_end_dates, clean_text
import argparse

def get_content_from_url(url) -> str:
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(
            f"Failed to fetch data for url {url}: {response.status_code}")
        return None

def get_speeches_from_page_content(hansard_id):
    try:
        url = f'https://www.ourcommons.ca/Content/House/441/Debates/{hansard_id}/HAN{hansard_id}-E.XML'
        content = get_content_from_url(url)
        
        root = ET.fromstring(content)
        order_of_business_list = root.findall('.//OrderOfBusiness')
    
        date = root.find('.//ExtractedItem[@Name="HeaderDate"]').text
        date = datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d")
        chamber = root.find('.//ExtractedItem[@Name="Institution"]').text
        
        result = []
        for business in order_of_business_list:
            interventions = business.findall('.//Intervention')
            subject_title = business.find('.//SubjectOfBusinessTitle').text if business.find('.//SubjectOfBusinessTitle') is not None else ''
            for intervention in interventions:
                person_speaking = intervention.find('.//PersonSpeaking')
                if person_speaking is not None:
                    affiliation = person_speaking.find('.//Affiliation')
                    if affiliation is not None:
                        speaker = affiliation.text
                
                content = intervention.find('.//Content')
                if content is not None:
                    if content.findall('.//B'): 
                        continue
                    para_texts = content.findall('.//ParaText')
                    speech = []
                    for para in para_texts:
                        if para is not None:
                            speech.append(_clean_text(_get_full_text(para)))
                    speech = clean_text(unidecode(' '.join(speech)))
                partition = {
                            'url': url, 
                            'date_str': date, #yyyy-mm-dd
                            'title': subject_title, 
                            'speaker': unidecode(_get_speaker_name(speaker)),
                            'data': speech,
                            'chamber': chamber,
                            'country': 'CA'
                            }
                result.append(partition)
        return result
    except:
        print(f'Failed to get speech for handsard id {hansard_id}')

def _clean_text(text):
    text = text.replace(r'\"', '"')
    text = text.replace('\n', '').strip()
    return text

def _get_speaker_name(name) -> str:
    # remove the trailing paranthesis
    return re.sub(r'\s*\(.*?\)', '', name)

def _get_full_text(element):
    texts = [element.text.strip()] if element.text else []
    for subelement in element:
        texts.append(_get_full_text(subelement))
        if subelement.tail:
            texts.append(subelement.tail.strip())
    return ' '.join(filter(None, texts))

def get_hansard_ids(start_date: datetime, end_date: datetime) -> list[int]:
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    try:
        url = f'https://api.openparliament.ca/debates/?date__range={start_date_str}%2C{end_date_str}&format=json'
        content = requests.get(url).json()["objects"]
        hansard_ids = []
        for info in content:
            if info.get('number', None):
                hansard_ids.append(int(info['number']))
        return hansard_ids
    except:
        print(f'failed to get a list of hansard ids for dates between {start_date_str} and {end_date_str}')
     
if __name__ == '__main__':
    parser = argparse.ArgumentParser("Pass year and month")
    parser.add_argument('-y', '--year', help='year',type=int)
    parser.add_argument('-m', '--month', help='month',type=int)
    args = parser.parse_args()
    year = args.year
    month = args.month
    start_date, end_date = get_start_and_end_dates(year, month)

    hansard_ids = get_hansard_ids(start_date, end_date)
    result_dir = './result/ca'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    file_path = os.path.join(result_dir, f'{datetime.strftime(start_date, "%Y-%m")}.json')
    data = []
    for i in hansard_ids:
        result = get_speeches_from_page_content(i)
        data.extend(result)
    
    with open(file_path, 'w') as fw:
        json.dump(data, fw, indent=2)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as fr:
            data = json.load(fr)
            print(len(data))