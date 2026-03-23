from utils import get_start_and_end_dates, file_exists_in_hf_repo
import json
import argparse
from huggingface_hub import HfApi
import os
from datetime import datetime

if __name__ == '__main__':
    # parser = argparse.ArgumentParser("Pass year and month")
    # parser.add_argument('-y', '--year', help='year',type=int)
    # parser.add_argument('-m', '--month', help='month',type=int)
    # args = parser.parse_args()
    # if args:
    #     year = args.year
    #     month = args.month
    if int(os.getenv("YEAR", "0")) != 0 and int(os.getenv("MONTH", "0")) != 0:
        year = int(os.getenv("YEAR", "0"))
        month = int(os.getenv("MONTH", "0"))
    elif datetime.now().month == 1:
        year = datetime.now().year - 1
        month = 12
    else:
        year = datetime.now().year
        month = datetime.now().month - 1
    start_date, _ = get_start_and_end_dates(year, month)
    date_str = start_date.strftime('%Y-%m')
    combined = []
    country_dirs = ['ca', 'us', 'gbr']
    final_file_name = f'congressional_data_{date_str}.json'
    final_file_path = os.path.join('result', final_file_name)
    
    for dir in country_dirs:
        sub_file_path = f'result/{dir}/{date_str}.json'
        if os.path.exists(sub_file_path):
            with open(sub_file_path, 'r') as fr:
                data = json.load(fr)
                if len(data) > 0:
                    combined.extend(data)
    
    with open(final_file_path, 'w') as fw:
        json.dump(combined, fw, indent=2)
    

    