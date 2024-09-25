import requests
from datetime import datetime
import json
from urllib.parse import quote
import time
import argparse
import re
import os
from bs4 import BeautifulSoup
from utils import get_start_and_end_dates, clean_text, starts_with_any

API_RATE_LIMIT = 1000
API_KEY = 'n8PasSTHypf2IrWubb3WkpFKqUTNz4U98tJieYiW'
# '0hX0eme3Y5XMGMLRSp7orTlpzUCKnugtB0IOo5c6'

class USCongressionalRecordFetcher:
    def __init__(self):
        self.api_call_counter = 0
    
    def update_api_call_counter_and_sleep(self):
        self.api_call_counter += 1
        if self.api_call_counter >=  API_RATE_LIMIT:
            time.sleep(60*60)
            self.api_call_counter = 0

    def get_congressional_record_packages(self, start_date: datetime, end_date: datetime):
        # Can get at most 1000 items
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        url = f'https://api.govinfo.gov/published/{start_date_str}/{end_date_str}?pageSize=1000&collection=CREC&offsetMark=%2A&api_key={API_KEY}'
        response = requests.get(url)
        self.update_api_call_counter_and_sleep()
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Failed to fetch data from {start_date_str} to {end_date_str}: {response.status_code}")
            return None

    def get_package_id_from_collection_response(self, response_json):
        packages = response_json.get('packages', None)
        if packages:
            return [p['packageId'] for p in packages]
        else: 
            return None

    def get_all_doc_from_package_id(self, package_id):
        url = f'https://api.govinfo.gov/packages/{package_id}/granules?pageSize=1000&offsetMark=%2A&api_key={API_KEY}'
        response = requests.get(url)
        self.update_api_call_counter_and_sleep()
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Failed to fetch data for {package_id}: {response.status_code}")
            return None

    def get_all_partitions_from_a_package(self, package_id):
        package_response = self.get_all_doc_from_package_id(package_id)
        list_of_pages = package_response.get('granules', [])    
        result = []
        for page in list_of_pages:
            granule_link = page.get('granuleLink', None)
            granule_id = page.get('granuleId', None) # partition_id
            chamber = page.get('granuleClass', None)
            if not granule_link and granule_id:
                continue
            content = self.get_content_from_granual_link(granule_link)
            if not content:
                continue
            text = self.parse_html_content(content)
            title = self.get_title_from_text(text)
            speeches_result = self.get_speeches_from_text(text)
            if speeches_result:
                for speaker, speech in speeches_result:
                    date = self._get_date_from_granuleId(granule_id)
                    partition = {
                        'url': granule_link, 
                        'date_str': date, # 'yyyy-mm-dd'
                        'title': title, 
                        'speaker': speaker,
                        'data': speech,
                        'chamber': chamber,
                        'country': 'USA',
                        }
                    result.append(partition)
        return result    

    def parse_html_content(self, content) -> str:
        soup = BeautifulSoup(content, 'html.parser')
        title = str(soup.title.string) if soup.title else None
        pre = soup.find('pre')
        text = pre.get_text().strip() if pre else ''
        return self._remove_unnecessary_line_breaks(text)

    def _remove_unnecessary_line_breaks(self, text):
        # remove page number from text
        text = re.sub(r'\n\n[\[Page [A-Za-z0-9]+\]\](\n\n)?', '', text)
        # Remove multiple line breaks but keep paragraphs
        paragraphs = text.split('\n\n')
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            # Replace line breaks within paragraphs with spaces
            cleaned_paragraph = re.sub(r'\s*\n\s*', ' ', paragraph.strip())
            cleaned_paragraphs.append(cleaned_paragraph)

        # Join paragraphs with double newlines
        return '\n\n'.join(cleaned_paragraphs).strip().rstrip('\n').rstrip('_')

    def get_content_from_granual_link(self, url: str):
        url = url.replace('summary', f'htm?api_key={API_KEY}')
        response = requests.get(url)
        self.update_api_call_counter_and_sleep()
        if response.status_code == 200:
            return response.content
        else:
            print(
                f"Failed to fetch data for {url}: {response.status_code}")
            return None

    def _get_date_from_granuleId(self, granule_id):
        # example CREC-2024-06-13-pt1-PgS4098-2
        splitted = granule_id.split('-')
        return '-'.join(splitted[1:4])

    def get_speeches_from_text(self, text) -> list[tuple[str, str]]:
        # TODO: get multiple patterns from a text
        try:
            # Define the regex pattern for a paragraph starting with Mr./Mrs./Ms. followed by an all-caps name
            # pattern = re.compile(r'(\n\n(Mr\.|Mrs\.|Ms\.)\s[A-Z]+(?:-[A-Z\s]+)\.?)')
            valid_speaker = '(?:(?:Mr\.|Mrs\.|Ms\.)\s[A-Z]+-?[A-Z\s]+)\.?'
            invalid_speaker = 'The\sPRESIDING\sOFFICER'
            pattern = re.compile(fr'({valid_speaker}|{invalid_speaker})')
            
            split = re.split(pattern, text)[1:]
            speakers = re.findall(pattern,text)
            if not split or not speakers:
                return []
            result = []
            for i in range(0, len(split)-1, 2):
                speaker = split[i].rstrip('.')
                speech = split[i+1].strip().rstrip('\n').rstrip('_').replace('\n', ' ')
                # remove 'of <STATE>.' from the beginning of a speech. 
                # example 'Mr. THOMPSON of Mississippi. Mr. Speaker, I rise..." 
                # The speech will start with 'of Mississippi..' after regex pattern match
                speech = self._maybe_remove_speaker_state(speech)
                if self._is_valid_speech(speech) and speaker != invalid_speaker:
                    speech = clean_text(speech)
                    result.append((speaker, speech))
            return result
        except Exception:
            raise Exception

    def get_title_from_text(self, text) -> str:
        return text.split('\n')[0]

    def _maybe_remove_speaker_state(self, speech):
        us_states = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", 
        "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", 
        "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", 
        "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", 
        "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", 
        "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", 
        "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
        ]
        states_pattern = r'^of (' + '|'.join(re.escape(state) for state in us_states) + r')\.\s'
        return re.sub(states_pattern, '', speech)

    def _is_valid_speech(self, speech):
        if not speech:
            return False
        if 'pro tempore' in speech:
            return False
        if not starts_with_any(speech, ["Mr. Speaker,","Mr. President,","Madam Speaker,","Madam President,"]):
            return False
        if 'I ask unanimous consent that' in speech and len(speech) < 400:
            return False
        return True

def log(package_id, number_of_partition):
    log_dir = './logs'
    us_log_file = 'us_log.txt'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(os.path.join(log_dir, us_log_file), 'a') as fw:
        fw.write(f'{current_time} {package_id} {str(number_of_partition)}\n')

def write_to_json_file(new_data, file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as fr:
            data = json.load(fr)
    else:
        data = []
    data.extend(new_data)
    with open(file_path, 'w') as fw:
        json.dump(data, fw, indent=2)


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
    result_dir = './result/us'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    date_str = start_date.strftime('%Y-%m')
    file_path = os.path.join(result_dir, f'{date_str}.json')
    fetcher = USCongressionalRecordFetcher()
    collection_resposne = fetcher.get_congressional_record_packages(start_date, end_date)
    package_ids = fetcher.get_package_id_from_collection_response(collection_resposne)
    for package_id in package_ids:
        result = fetcher.get_all_partitions_from_a_package(package_id)
        print(len(result))
        write_to_json_file(result, file_path)
        log(len(result), package_id)
    
    print(fetcher.api_call_counter)