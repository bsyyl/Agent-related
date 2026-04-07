import json
import os
import threading
import concurrent.futures
import argparse
from tqdm import tqdm
import logging
import time
import re 
from utils.api import AIClient
from utils.io_utils import load_jsonl
import glob

# Import scoring prompts for Chinese and English
from prompt.score_prompt_zh import quality_generate_merged_score_prompt as zh_merged_score_prompt
from prompt.score_prompt_en import quality_generate_merged_score_prompt as en_merged_score_prompt
from utils.score_calculator import calculate_weighted_quality_scores
from utils.json_extractor import extract_json_from_markdown
from utils.clean_article import ArticleCleaner

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Fixed configuration parameters
MAX_RETRIES = 10


def process_single_item(item_data, target_articles_map, criteria_map,
                         llm_client, lock, pbar, max_retries, language):
    """Process a single task: get data, call LLM 3 times, parse results, calculate averaged quality scores"""
    item_id = item_data.get('id')
    task_text = item_data.get('task')

    # Data retrieval and validation
    if item_id not in target_articles_map:
        logger.error(f"Target article not found for ID {item_id}")
        with lock: pbar.update(1)
        return {"id": item_id, "task": task_text, "error": "Target article not found"}
    
    if item_id not in criteria_map:
        logger.error(f"Evaluation criteria not found for ID {item_id}")
        with lock: pbar.update(1)
        return {"id": item_id, "task": task_text, "error": "Evaluation criteria not found"}

    target_article_data = target_articles_map[item_id]
    criteria_data = criteria_map[item_id]
    target_article = target_article_data.get('article', '')

    # Choose scoring prompt based on language
    merged_score_prompt = zh_merged_score_prompt if language == "zh" else en_merged_score_prompt
    
    # Prepare LLM prompt
    user_prompt = merged_score_prompt.format(
        task_prompt=task_text,
        article=target_article,
        criteria_list=criteria_data.get('quality_criterions', [])
    )

    scores_list = []

    # === Run scoring 3 times ===
    for round_idx in range(3):
        llm_response_str = None
        llm_output_json = None
        success = False
        retry_count = 0

        while retry_count < max_retries and not success:
            try:
                llm_response_str = llm_client.generate(
                    user_prompt=user_prompt,
                    system_prompt=""
                )

                # Extract JSON
                json_str_extracted = extract_json_from_markdown(llm_response_str)
                if not json_str_extracted:
                    raise ValueError("Failed to extract JSON from LLM response")
                
                llm_output_json = json.loads(json_str_extracted)

                # Check expected dimensions
                expected_dims = ["depth_insight", "logical_coherence", "clarity_readability"]
                if not all(dim in llm_output_json for dim in expected_dims):
                    missing_dims = [dim for dim in expected_dims if dim not in llm_output_json]
                    raise ValueError(f"Missing expected dimensions: {missing_dims}")

                success = True

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"ID {item_id}, Round {round_idx+1}: Retry {retry_count}/{max_retries} - {str(e)}")
                    time.sleep(1.5 ** retry_count)
                else:
                    logger.error(f"ID {item_id}, Round {round_idx+1}: Failed after {max_retries} retries - {str(e)}")

        if not success:
            with lock: pbar.update(1)
            return {
                "id": item_id,
                "task": task_text,
                "error": f"Round {round_idx+1} failed after {max_retries} retries",
                "model_output": llm_response_str[:500] if llm_response_str else "No response"
            }

        try:
            # Calculate weighted scores for this round
            scores = calculate_weighted_quality_scores(llm_output_json, criteria_data, language)
            scores_list.append(scores["target"])
        except Exception as e:
            logger.error(f"ID {item_id}, Round {round_idx+1}: Error calculating scores - {str(e)}")
            with lock: pbar.update(1)
            return {
                "id": item_id,
                "task": task_text,
                "error": f"Error calculating scores in round {round_idx+1}: {str(e)}"
            }

    # === Average scores across 3 rounds ===
    final_dims = ["depth_insight", "logical_coherence", "clarity_readability"]
    averaged_dims = {dim: 0 for dim in final_dims}
    q_overall_score = 0

    for s in scores_list:
        q_overall_score += s.get("total", 0)
        for dim in final_dims:
            averaged_dims[dim] += s.get("dims", {}).get(f"{dim}_weighted_avg", 0)

    q_overall_score /= len(scores_list)
    for dim in final_dims:
        averaged_dims[dim] /= len(scores_list)

    # Prepare final result
    final_result = item_data.copy()
    final_result.update({
        "depth_insight": averaged_dims["depth_insight"],
        # "logic_clarity": averaged_dims["logic_clarity"],
        "logical_coherence": averaged_dims["logical_coherence"],
        "clarity_readability": averaged_dims["clarity_readability"],
        "q_overall_score": q_overall_score,
        "details": llm_output_json  # Include last round details for reference
    })

    with lock:
        pbar.update(1)

    return final_result


def process_language_data(language, target_model, llm_client, clean_agent, 
                         raw_data_dir, cleaned_data_dir, max_workers, limit, query_file, criteria_file, output_file):
    """Process data for a single language (Chinese or English)"""
    
    # Step 1: Clean target model articles if needed
    logger.info(f"Checking if {target_model} articles need cleaning...")
    try:
        article_cleaner = ArticleCleaner(clean_agent)
        default_language = language

        article_cleaner.clean_articles(
            target_model, 
            raw_data_dir, 
            cleaned_data_dir, 
            max_workers,
            MAX_RETRIES,
            limit,
            default_language
            )
        cleaning_success = True
    except Exception as e:
        logger.error(f"Article cleaning failed for {target_model}: {e}")
        cleaning_success = False

    
    if not cleaning_success:
        logger.error(f"Article cleaning failed for {target_model}, cannot continue.")
        return None
    
    # Step 2: Load data for scoring
    logger.info(f"Loading {language} data from {query_file}...")
    
    try:
        all_items = load_jsonl(query_file)
        all_items = [item for item in all_items if item.get('language') == language]

        # Filter out already processed items if output_file exists
        if os.path.exists(output_file):
            existing_results = load_jsonl(output_file)
            existing_ids = {r.get('id') for r in existing_results if r.get('id')}
            all_items = [item for item in all_items if item.get('id') not in existing_ids]
            logger.info(f"Filtered out {len(existing_ids)} already processed items. {len(all_items)} items remain for processing.")
            
        # Apply limit if specified
        if limit is not None and limit > 0:
            all_items = all_items[:limit]
            
        # Get prompts from tasks
        item_ids = {item.get('id') for item in all_items if item.get('id')}
        
        # Load criteria data
        all_criteria = load_jsonl(criteria_file)
        criteria_list = [c for c in all_criteria if c.get('id') in item_ids]
            
        # Load target model articles
        target_file = os.path.join(cleaned_data_dir, f"{target_model}.jsonl")
        all_target_articles = load_jsonl(target_file)
        target_articles_list = [a for a in all_target_articles if a.get('id') in item_ids]
        if not target_articles_list:
            logger.error(f"No target articles found for model {target_model} in {language}")
            return None
            
        # Build mappings
        criteria_map = {c['id']: c for c in criteria_list}
        target_articles_map = {t['id']: t for t in target_articles_list}
        
        # Check for missing data
        for item in all_items:
            item_id = item.get('id')
            if item_id not in criteria_map:
                logger.warning(f"No criteria found for item: {str(item)[:100]}...")
            if item_id not in target_articles_map:
                logger.warning(f"No target article found for item: {str(item)[:100]}...")
                
        items_to_process = [item for item in all_items 
                           if item.get('id') in criteria_map
                           and item.get('id') in target_articles_map]
        
        if not items_to_process:
            logger.error(f"No complete task data found for {language}")
            return None
            
        logger.info(f"Processing {len(items_to_process)} {language} tasks...")
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return None
    
    # Step 3: Process each item and generate scores
    lock = threading.Lock()
    results_list = []
    
    with tqdm(total=len(items_to_process), desc=f"Scoring {language} {target_model}") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    process_single_item,
                    item,
                    target_articles_map,
                    criteria_map,
                    llm_client,
                    lock,
                    pbar,
                    MAX_RETRIES,
                    language
                )
                for item in items_to_process
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    results_list.append(result)
    
    successful_results = [res for res in results_list if "error" not in res]
    
    logger.info(f"{language} evaluation complete. Successfully scored {len(successful_results)} "
                 f"out of {len(items_to_process)} tasks.")
    
    return successful_results

def main():
    parser = argparse.ArgumentParser(description='Score model articles using detailed evaluation criteria and LLM.')
    parser.add_argument('target_model', type=str, help='Name of target model to evaluate')
    parser.add_argument('--limit', type=int, default=None, help='Limit on number of prompts to process (for testing).')
    parser.add_argument('--skip_cleaning', action='store_true', help='Skip article cleaning step.')
    parser.add_argument('--only_zh', action='store_true', help='Only process Chinese data.')
    parser.add_argument('--only_en', action='store_true', help='Only process English data.')
    parser.add_argument('--force', action='store_true', help='Force re-evaluation even if results exist.')
    
    # Add only the parameters that need to be configurable via command line
    parser.add_argument('--raw_data_dir', type=str, default="data/test_data/raw_data", help='Directory containing raw data.')
    parser.add_argument('--cleaned_data_dir', type=str, default="data/test_data/cleaned_data", help='Directory for cleaned data.')
    parser.add_argument('--max_workers', type=int, default=5, help='Maximum number of worker threads.')
    parser.add_argument('--query_file', type=str, default="data/prompt_data/queries.jsonl", help='Path to query file with language information.')
    parser.add_argument('--output_dir', type=str, default="results", help='Directory for output results.')
    parser.add_argument('--criteria_file', type=str, default="data/criteria_data/criteria.jsonl", help='Path to criteria file.')
    
    args = parser.parse_args()

    # Extract parameters from args
    target_model = args.target_model
    limit = args.limit
    skip_cleaning = args.skip_cleaning
    only_zh = args.only_zh
    only_en = args.only_en
    force = args.force
    raw_data_dir = args.raw_data_dir
    cleaned_data_dir = args.cleaned_data_dir
    max_workers = args.max_workers
    query_file = args.query_file
    output_dir = args.output_dir
    criteria_file = args.criteria_file
    
    os.makedirs(output_dir, exist_ok=True)
    
    # check if the results file exists
    output_file = os.path.join(output_dir, "quality_results.jsonl")
    result_file = os.path.join(output_dir, "quality_result.txt")
    existing_results = []
    existing_ids = set()
    
    if os.path.exists(output_file) and not force:
        try:
            existing_results = load_jsonl(output_file)
            existing_ids = {r.get('id') for r in existing_results if r.get('id')}
            logger.info(f"Found existing results file with {len(existing_results)} entries")
            
            # if limit is specified and the number of existing results is greater than or equal to limit, return
            if limit is not None and len(existing_results) >= limit:
                logger.info(f"Existing results ({len(existing_results)}) meet or exceed limit ({limit}). Skipping evaluation.")
                
                # calculate and print the average scores of the existing results
                successful_results = [r for r in existing_results if "error" not in r]
                if successful_results:
                    depth_insight_avg = sum(r.get("depth_insight", 0) for r in successful_results) / len(successful_results)
                    # logic_clarity_avg = sum(r.get("logic_clarity", 0) for r in successful_results) / len(successful_results)
                    logical_coherence_avg = sum(r.get("logical_coherence", 0) for r in successful_results) / len(successful_results)
                    clarity_readability_avg = sum(r.get("clarity_readability", 0) for r in successful_results) / len(successful_results)
                    q_overall_avg = sum(r.get("q_overall_score", 0) for r in successful_results) / len(successful_results)

                    logger.info("\n=== Existing Quality Evaluation Results Summary ===")
                    logger.info(f"Depth & Insight:              {depth_insight_avg:.4f}")
                    # logger.info(f"Logic & Clarity:              {logic_clarity_avg:.4f}")
                    logger.info(f"Logical Coherence:            {logical_coherence_avg:.4f}")
                    logger.info(f"Clarity & Readability:        {clarity_readability_avg:.4f}")
                    logger.info(f"Q-Overall Score:              {q_overall_avg:.4f}")
                    logger.info("================================")
                
                return
        except Exception as e:
            logger.warning(f"Error reading existing results file: {e}. Will create new results.")
            existing_results = []
            existing_ids = set()
    
    llm_client = AIClient()
    clean_agent = llm_client
    
    all_results = list(existing_results)  # initialize with existing results
    
    # load all items, filter out the processed item IDs
    all_items = load_jsonl(query_file)
    if existing_ids:
        logger.info(f"Will skip {len(existing_ids)} already processed item IDs")

    # chinese data processing
    if not only_en:
        logger.info("Starting Chinese data processing...")
        if not skip_cleaning:
            # filter out the processed chinese items
            zh_items = [item for item in all_items if item.get('language') == 'zh' and item.get('id') not in existing_ids]
            if not zh_items:
                logger.info("All Chinese items have been processed already. Skipping.")
            elif limit is not None:
                existing_zh_count = len([
                    item for item in all_items 
                    if item.get('language') == 'zh' and item.get('id') in existing_ids
                ])
                remaining_limit = max(0, limit - existing_zh_count)
                if remaining_limit > 0:
                    logger.info(f"Processing up to {remaining_limit} more Chinese items (limit: {limit}, already processed: {existing_zh_count})")
                    zh_results = process_language_data(
                        "zh", target_model, llm_client, clean_agent,
                        raw_data_dir, cleaned_data_dir, max_workers, remaining_limit, query_file, criteria_file, output_file
                    )
                    if zh_results:
                        all_results.extend(zh_results)
                else:
                    logger.info(f"Already reached limit for Chinese items ({existing_zh_count}/{limit}). Skipping.")
            else:
                # if limit is not specified, process all unprocessed items
                zh_results = process_language_data(
                    "zh", target_model, llm_client, clean_agent,
                    raw_data_dir, cleaned_data_dir, max_workers, limit, query_file, criteria_file, output_file
                )
                if zh_results:
                    all_results.extend(zh_results)
        else:
            logger.info("Skipping article cleaning step for Chinese data.")

    # english data processing
    if not only_zh:
        logger.info("Starting English data processing...")
        if not skip_cleaning:
            # filter out the processed english items
            en_items = [item for item in all_items if item.get('language') == 'en' and item.get('id') not in existing_ids]
            if not en_items:
                logger.info("All English items have been processed already. Skipping.")
            elif limit is not None:
                existing_en_count = len([
                    item for item in all_items 
                    if item.get('language') == 'en' and item.get('id') in existing_ids
                ])
                remaining_limit = max(0, limit - existing_en_count)
                if remaining_limit > 0:
                    logger.info(f"Processing up to {remaining_limit} more English items (limit: {limit}, already processed: {existing_en_count})")
                    en_results = process_language_data(
                        "en", target_model, llm_client, clean_agent,
                        raw_data_dir, cleaned_data_dir, max_workers, remaining_limit, query_file, criteria_file, output_file
                    )
                    if en_results:
                        all_results.extend(en_results)
                else:
                    logger.info(f"Already reached limit for English items ({existing_en_count}/{limit}). Skipping.")
            else:
                # if limit is not specified, process all unprocessed items
                en_results = process_language_data(
                    "en", target_model, llm_client, clean_agent,
                    raw_data_dir, cleaned_data_dir, max_workers, limit, query_file, criteria_file, output_file
                )
                if en_results:
                    all_results.extend(en_results)
        else:
            logger.info("Skipping article cleaning step for English data.")

    # output results to file
    if all_results:
        # sort by ID
        all_results.sort(key=lambda x: x.get('id', float('inf')))

        logger.info(f"Saving {len(all_results)} results to {output_file}...")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in all_results:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
            logger.info("Results saved successfully.")

            # calculate and print the average scores
            successful_results = [r for r in all_results if "error" not in r]
            if successful_results:
                depth_insight_avg = sum(r.get("depth_insight", 0) for r in successful_results) / len(successful_results)
                logical_coherence_avg = sum(r.get("logical_coherence", 0) for r in successful_results) / len(successful_results)
                clarity_readability_avg = sum(r.get("clarity_readability", 0) for r in successful_results) / len(successful_results)
                q_overall_avg = sum(r.get("q_overall_score", 0) for r in successful_results) / len(successful_results)

                logger.info("\n=== Quality Evaluation Results Summary ===")
                logger.info(f"Depth & Insight:              {depth_insight_avg:.4f}")
                logger.info(f"Logical Coherence:            {logical_coherence_avg:.4f}")
                logger.info(f"Clarity & Readability:        {clarity_readability_avg:.4f}")
                logger.info(f"Q Overall Score:              {q_overall_avg:.4f}")
                logger.info("================================")

                # write the results to the result file
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(f"Depth & Insight: {depth_insight_avg:.4f}\n")
                    f.write(f"Logical Coherence: {logical_coherence_avg:.4f}\n")
                    f.write(f"Clarity & Readability: {clarity_readability_avg:.4f}\n")
                    f.write(f"Q Overall Score: {q_overall_avg:.4f}\n")

        except IOError as e:
            logger.error(f"Failed to write results to {output_file}: {e}")
    else:
        logger.warning("No results to save.")

    logger.info("--- Quality Evaluation Run Summary ---")
    logger.info(f"Target model: {target_model}")
    logger.info(f"Total items processed: {len(all_results)}")
    logger.info(f"Results file: {output_file}")
    logger.info("-------------------")

if __name__ == "__main__":
    main()