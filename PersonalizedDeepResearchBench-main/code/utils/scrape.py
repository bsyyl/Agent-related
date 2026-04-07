import multiprocessing
import json
import os
import time
import argparse
import platform
from tqdm import tqdm
from .api import scrape_url
from .io_utils import load_jsonl
from concurrent.futures import ThreadPoolExecutor, as_completed


def scrape(citation_url):
    if citation_url == '':
        return {
            'url': citation_url,
            'url_content': ''
        }
    retries = 0
    while retries < 3:
        result = scrape_url(citation_url)
        retries += 1
        if 'error' in result:
            time.sleep(1)
        else:
            break

    url_content = None
    if 'error' not in result:
        title = result.get('title', '')
        content = result.get('content', '')
        description = result.get('description', '')

        url_content = f"{title}\n\n{description}\n\n{content}"
    else:
        url_content = f"scrape failed: {result.get('error', 'unknown error')}"
    return {
        'url': citation_url,
        'url_content': url_content
    } 

def process_d(d_output_path_args):
    d, output_path, args = d_output_path_args

    if not d['factual_claims_deduped']:
        return None

    factual_claims = [
        k for k, v in d['factual_claims_deduped'].items()
        if ('url_content' not in v or not v['url_content'])
    ]

    results = []
    if factual_claims:
        n_threads = min(args.n_total_process, len(factual_claims))
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(scrape, claim) for claim in factual_claims]
            for future in as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    print(f"scrape error: {e}")

    # update url_content
    for res in results:
        d['factual_claims_deduped'][res['url']]['url_content'] = res['url_content']

    return d

if __name__ == '__main__':
    if platform.system() == 'Darwin' or platform.system() == 'Windows':  
        try:
            multiprocessing.set_start_method('spawn')
        except RuntimeError:
            pass
    else: 
        try:
            multiprocessing.set_start_method('fork')
        except RuntimeError:
            pass

    parser = argparse.ArgumentParser()
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--raw_data_path", type=str, required=True)
    parser.add_argument("--n_total_process", type=int, default=1)
    args = parser.parse_args()
    
    output_path = args.output_path
    
    # initialize variables
    raw_data = []
    data_to_process = []
    processed = []
    
    try:
        raw_data = load_jsonl(args.raw_data_path)
        
        if os.path.exists(output_path):
            processed = [d['id'] for d in load_jsonl(output_path)]
            data_to_process = [d for d in raw_data if d['id'] not in processed]
        else:
            data_to_process = raw_data
    except:
        import sys
        print(f"cannot process file {args.raw_data_path}")
        sys.exit(f'{args.raw_data_path} has not been processed yet...')
    
    print(f"processing {len(data_to_process)} instances...")

    n_total_process = min(args.n_total_process, len(data_to_process))
    if n_total_process < 1:
        n_total_process = 1
    args_for_pool = [(d, output_path, args) for d in data_to_process]

    with multiprocessing.Pool(processes=n_total_process) as pool:
        for result in tqdm(pool.imap_unordered(process_d, args_for_pool), total=len(args_for_pool)):
            if result is not None:
                with open(output_path, 'a+', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
