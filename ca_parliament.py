import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from unidecode import unidecode
import os
from utils import get_start_and_end_dates, clean_text
import argparse
from urllib.parse import urljoin

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
        

def get_speech_data(date: datetime):
    base_api_url = "https://api.openparliament.ca"
    speeches_endpoint = f"{base_api_url}/speeches/"
    document_path = f"/debates/{date.year}/{date.month}/{date.day}/"

    params = {'document': document_path, 'limit': 100}
    all_speeches = []

    next_url = speeches_endpoint
    while next_url:
        try:
            response = requests.get(next_url, params=params if next_url == speeches_endpoint else None)

            # If request fails, print warning and skip this page
            if response.status_code != 200:
                print(f"Warning: Skipping {next_url} due to HTTP {response.status_code}")
                break  # or use `continue` if you want to try the next page anyway

            data = response.json()
        except Exception as e:
            print(f"Error fetching data from {next_url}: {e}")
            break

        for item in data.get('objects', []):
            full_url = urljoin(base_api_url, item.get('url')) if item.get('url') else None

            subject_title = (
                item.get('h3', {}).get('en') or
                item.get('h2', {}).get('en') or
                item.get('h1', {}).get('en')
            )

            formatted = {
                'url': full_url,
                'date_str': item.get('time', '')[:10],
                'title': subject_title,
                'speaker': item.get('attribution', {}).get('en'),
                'data': item.get('content', {}).get('en'),
                'chamber': 'House of Commons',
                'country': 'CA'
            }

            all_speeches.append(formatted)

        # Go to the next page if available
        next_relative_url = data.get('pagination', {}).get('next_url')
        next_url = urljoin(base_api_url, next_relative_url) if next_relative_url else None
        params = None  # Only needed for the first request

    return all_speeches

# Example usage
if __name__ == "__main__":
    date_input = datetime(2025, 6, 19)
    speeches = get_speech_data(date_input)
    print(f"Total speeches found: {len(speeches)}\n")
    for speech in speeches:
        print(speech)


# Example usage
if __name__ == "__main__":
    date_input = datetime(2025, 6, 19)
    speeches = get_speech_data(date_input)
    print(f"Total speeches found: {len(speeches)}\n")
    for speech in speeches:
        print(speech)

    
     
if __name__ == '__main__':
    # parser = argparse.ArgumentParser("Pass year and month")
    # parser.add_argument('-y', '--year', help='year',type=int)
    # parser.add_argument('-m', '--month', help='month',type=int)
    # args = parser.parse_args()
    # if args:
    #     year = args.year
    #     month = args.month
    print(f'Extracting Canadian parliamentary dataset.')
    if int(os.getenv("YEAR", "0")) != 0 and int(os.getenv("MONTH", "0")) != 0:
        year = int(os.getenv("YEAR", "0"))
        month = int(os.getenv("MONTH", "0"))
    elif datetime.now().month == 1:
        year = datetime.now().year - 1
        month = 12
    else:
        year = datetime.now().year
        month = datetime.now().month - 1
    start_date, end_date = get_start_and_end_dates(year, month)
    
    
    

    hansard_ids = get_hansard_ids(start_date, end_date)
    result_dir = './result/ca'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    file_path = os.path.join(result_dir, f'{datetime.strftime(start_date, "%Y-%m")}.json')
    data = []
    for i in hansard_ids:
        result = get_speeches_from_page_content(i)
        if(result and len(result) > 0):
            data.extend(result)
    
    with open(file_path, 'w') as fw:
        json.dump(data, fw, indent=2)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as fr:
            data = json.load(fr)
            print(len(data))