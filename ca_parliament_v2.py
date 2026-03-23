import requests
from datetime import datetime
from urllib.parse import urljoin
import os
from utils import get_dates_in_a_month
import json
from bs4 import BeautifulSoup


def get_speech_data(date: datetime):
    base_api_url = "https://api.openparliament.ca"
    speeches_endpoint = urljoin(base_api_url, "/speeches/")
    document_path = f"/debates/{date.year}/{date.month}/{date.day}/"
    params = {
        'document': document_path,
        'format': 'json',      # Ensure JSON response
        'limit': 100
    }
    headers = {}

    all_speeches = []
    next_url = speeches_endpoint

    while next_url:
        try:
            response = requests.get(next_url, params=params if next_url == speeches_endpoint else None, headers=headers)
            if response.status_code != 200:
                print(f"Warning: Skipping {next_url} due to HTTP {response.status_code}")
                break

            # Check response content exists before parsing
            if not response.content.strip():
                print(f"Warning: Empty response content at {next_url}, stopping.")
                break

            data = response.json()

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
                    'data': extract_text_from_html(item.get('content', {}).get('en')),
                    'chamber': 'House of Commons',
                    'country': 'CA'
                }

                all_speeches.append(formatted)

            next_relative_url = data.get('pagination', {}).get('next_url')
            next_url = urljoin(base_api_url, next_relative_url) if next_relative_url else None

            # Only use params for first request
            params = None

        except Exception as e:
            print(f"Error fetching data from {next_url}: {e}")
            # raise e
            continue

    return all_speeches
    
def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

if __name__ == '__main__':    
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
    dates = get_dates_in_a_month(year, month)
    
    data = []
    for date in dates:
        data.extend(get_speech_data(date))
    
    result_dir = './result/ca'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    file_path = os.path.join(result_dir, f'{datetime.strftime(dates[0], "%Y-%m")}.json')
    
    with open(file_path, 'w', encoding="utf-8") as fw:
        # ensure_ascii=False removes unicode like u2014
        json.dump(data, fw, ensure_ascii=False, indent=2)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as fr:
            data = json.load(fr)
            print(len(data))