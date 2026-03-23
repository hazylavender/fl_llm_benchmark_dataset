import requests
import argparse
import json
from utils import get_start_and_end_dates, file_exists_in_hf_repo
from huggingface_hub import HfApi
from datetime import datetime
import os

def filter_license(lst):
    allowlist = ['cc_by_nc_nd', 'cc_by_nd', 'cc_by_nc', 'cc_by', 'cc0']
    return [i for i in lst if i.get('license', '') in allowlist]

if __name__ == '__main__':
    # parser = argparse.ArgumentParser("Pass year and month")
    # parser.add_argument('-y', '--year', help='year',type=int)
    # parser.add_argument('-m', '--month', help='month',type=int)
    # args = parser.parse_args()
    # if args:
    #     year = args.year
    #     month = args.month
    print(f'Extracting biorxiv dataset.')
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
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    cursor = 0
    count = 100
    result = []
    while (count == 100):
        # Move cursor to the next 100 since every response can only return 100 results.
        cursor += 100
        url = f'https://api.biorxiv.org/details/biorxiv/{start_date_str}/{end_date_str}/{cursor}'
        content = requests.get(url).json()
        messages = content.get('messages',[])
        if messages and messages[0].get('status', '') == 'ok':
            count = messages[0]['count']
        else:
            count = 0
        collection = content.get('collection', [])
        collection = filter_license(collection)
        if collection:
            result.extend(collection)
        
    date_str = start_date.strftime('%Y-%m')
    result_dir = './result/bio'
    file_name = f'biorxiv_result_{date_str}.json'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    with open (os.path.join(result_dir,file_name), 'w') as fw:
        json.dump(result, fw, indent=2)
    
