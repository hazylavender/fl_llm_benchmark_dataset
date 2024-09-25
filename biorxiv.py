import requests
import json

def filter_license(lst):
    allowlist = ['cc_by_nc_nd', 'cc_by_nd', 'cc_by_nc', 'cc_by', 'cc0']
    return [i for i in lst if i.get('license', '') in allowlist]

if __name__ == '__main__':
    cursor = 0
    count = 100
    result = []
    start_date = '2023-04-01'
    end_date = '2024-08-31'
    try:
        while (count == 100):
            # Move cursor to the next 100 since every response can only return 100 results.
            cursor += 100
            url = f'https://api.biorxiv.org/details/biorxiv/{start_date}/{end_date}/{cursor}'
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
    except:
        retry_index = cursor - 100
        print(f'Failed to retrieve all result. Please retry starting with cursor = {retry_index}')

    with open (f'result/biorxiv_result_{start_date}_{end_date}.json', 'w') as fw:
        json.dump(result, fw, indent=2)