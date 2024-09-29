from utils import get_start_and_end_dates
import json
import argparse
from huggingface_hub import HfApi
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Pass year and month")
    parser.add_argument('-y', '--year', help='year',type=int)
    parser.add_argument('-m', '--month', help='month',type=int)
    args = parser.parse_args()
    year = args.year
    month = args.month
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
    
    # Upload the file to huggingface
    api = HfApi()
    api.upload_file(
        path_or_fileobj=final_file_path,
        path_in_repo=final_file_name,
        repo_id="<repo_id>", # replace this with a real repo id
        repo_type="dataset",
    )
    
