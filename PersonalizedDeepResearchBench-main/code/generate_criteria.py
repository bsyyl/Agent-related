import json
import os
import re
import time
from tqdm import tqdm
from utils.api import AIClient
import concurrent.futures
import threading

# Import dimension weight generation prompts for Chinese and English
from prompt.criteria_prompt_zh import (
    personalization_eval_dimension_weight_prompt as personalization_weight_prompt_zh,
    personalization_eval_criteria_prompt_goal_alignment as personalization_goal_alignment_prompt_zh,
    personalization_eval_criteria_prompt_content_alignment as personalization_content_alignment_prompt_zh,
    personalization_eval_criteria_prompt_presentation_fit as personalization_presentation_fit_prompt_zh,
    personalization_eval_criteria_prompt_actionability as personalization_actionability_prompt_zh,
    quality_eval_dimension_weight_prompt as quality_weight_prompt_zh,
    quality_eval_criteria_prompt_depth_insight as quality_depth_insight_prompt_zh,
    quality_eval_criteria_prompt_logical_coherence as quality_logical_coherence_prompt_zh,
    quality_eval_criteria_prompt_clarity_readability as quality_clarity_readability_prompt_zh,
)
from prompt.criteria_prompt_en import (
    personalization_eval_dimension_weight_prompt as personalization_weight_prompt_en,
    personalization_eval_criteria_prompt_goal_alignment as personalization_goal_alignment_prompt_en,
    personalization_eval_criteria_prompt_content_alignment as personalization_content_alignment_prompt_en,
    personalization_eval_criteria_prompt_presentation_fit as personalization_presentation_fit_prompt_en,
    personalization_eval_criteria_prompt_actionability as personalization_actionability_prompt_en,
    quality_eval_dimension_weight_prompt as quality_weight_prompt_en,
    quality_eval_criteria_prompt_depth_insight as quality_depth_insight_prompt_en,
    quality_eval_criteria_prompt_logical_coherence as quality_logical_coherence_prompt_en,
    quality_eval_criteria_prompt_clarity_readability as quality_clarity_readability_prompt_en,
)


INPUT_FILE = "data/prompt_data/queries150_zh.jsonl"
PERSONA_FILE = "data/persona_data/personas_zh.jsonl"
OUTPUT_FILE = "data/criteria_data/criteria150_zh.jsonl"

# Processing parameters
RETRY_ATTEMPTS = 10
RETRY_DELAY = 5
PROCESS_LIMIT = 150
MAX_WORKERS = 50
DEFAULT_SAMPLE_COUNT = 5 

# Thread-safe locks
print_lock = threading.Lock()
counter_lock = threading.Lock()

# Initialize AI client
ai_client = AIClient()

def parse_llm_output_as_json(text: str, expected_type: type = list) -> dict or list or None:
    """Parse JSON output from text"""
    # Try to extract JSON from special markers
    match = re.search(r'<json_output>(.*?)</json_output>', text, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1).strip()
    else:
        # Handle possible code block format
        json_str = text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
    
    # Parse JSON
    parsed_data = json.loads(json_str)
    
    # Type checking
    if not isinstance(parsed_data, expected_type) or (isinstance(parsed_data, (list, dict)) and not parsed_data):
        return None
    
    return parsed_data

def validate_weights(data, expected_sum=1.0, tolerance=1e-6):
    """Validate if the sum of weights is close to the expected value"""
    if isinstance(data, dict):
        # Dictionary form of weights
        if not data:
            return False
        total_weight = sum(float(value) for value in data.values())
        return abs(total_weight - expected_sum) < tolerance
        
    elif isinstance(data, list):
        # List form of weights
        if not data or not all(isinstance(item, dict) and 'weight' in item for item in data):
            return False
        total_weight = sum(float(item['weight']) for item in data)
        return abs(total_weight - expected_sum) < tolerance
        
    return False

def round_weights_and_adjust(weights, decimal_places=2):
    """
    Round weights to specified decimal places and ensure the sum is 1
    """
    # Round to specified decimal places
    rounded_weights = {dim: round(float(weight), decimal_places) 
                     for dim, weight in weights.items()}
    
    # Calculate sum and check if it equals 1
    total = sum(rounded_weights.values())
    diff = 1.0 - total
    
    # If there's a difference, add it to the last dimension
    if abs(diff) > 1e-10:
        last_key = list(rounded_weights.keys())[-1]
        rounded_weights[last_key] = round(rounded_weights[last_key] + diff, decimal_places)
    
    return rounded_weights

def get_prompts_by_language(language):
    """Select prompt templates based on language"""
    if language == "zh":
        return {
            "personalization_weight_prompt": personalization_weight_prompt_zh,
            "personalization_criteria_prompts": {
                "goal_alignment": personalization_goal_alignment_prompt_zh,
                "content_alignment": personalization_content_alignment_prompt_zh,
                "presentation_fit": personalization_presentation_fit_prompt_zh,
                "actionability_practicality": personalization_actionability_prompt_zh,
            },
            "quality_weight_prompt": quality_weight_prompt_zh,
            "quality_criteria_prompts": {
                "depth_insight": quality_depth_insight_prompt_zh,
                "logical_coherence": quality_logical_coherence_prompt_zh,
                "clarity_readability": quality_clarity_readability_prompt_zh,
            }
        }
    else:  # Default to English
        return {
            "personalization_weight_prompt": personalization_weight_prompt_en,
            "personalization_criteria_prompts": {
                "goal_alignment": personalization_goal_alignment_prompt_en,
                "content_alignment": personalization_content_alignment_prompt_en,
                "presentation_fit": personalization_presentation_fit_prompt_en,
                "actionability_practicality": personalization_actionability_prompt_en,
            },
            "quality_weight_prompt": quality_weight_prompt_en,
            "quality_criteria_prompts": {
                "depth_insight": quality_depth_insight_prompt_en,
                "logical_coherence": quality_logical_coherence_prompt_en,
                "clarity_readability": quality_clarity_readability_prompt_en,
            }
        }

def generate_weights_multiple_times(item_id, task, persona, language, sample_count=DEFAULT_SAMPLE_COUNT):
    """
    Generate dimension weights multiple times for both personalization and quality,
    and return the averaged, normalized, rounded weights for each.
    """
    personalization_samples = []
    quality_samples = []

    # Get weight prompt template for the corresponding language
    prompts = get_prompts_by_language(language)
    personalization_weight_prompt_template = prompts["personalization_weight_prompt"]
    quality_weight_prompt_template = prompts["quality_weight_prompt"]

    # Format user prompts
    personalization_user_prompt = personalization_weight_prompt_template.format(
        task_prompt=task, persona_prompt=persona
    )
    quality_user_prompt = quality_weight_prompt_template.format(task_prompt=task)

    # === Multiple sampling for personalization and quality ===
    for _ in range(sample_count):
        for attempt in range(RETRY_ATTEMPTS):
            # Generate weights
            personalization_output = ai_client.generate(user_prompt=personalization_user_prompt, system_prompt="")
            quality_output = ai_client.generate(user_prompt=quality_user_prompt, system_prompt="")

            try:
                parsed_personalization = parse_llm_output_as_json(personalization_output, expected_type=dict)
                parsed_quality = parse_llm_output_as_json(quality_output, expected_type=dict)

                if parsed_personalization and validate_weights(parsed_personalization):
                    personalization_samples.append(parsed_personalization)

                if parsed_quality and validate_weights(parsed_quality):
                    quality_samples.append(parsed_quality)

                # If both succeed, break retry loop
                if parsed_personalization and parsed_quality:
                    break

            except Exception:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise  # Raise exception on last attempt

            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)

    # If no successful samples, return None
    if not personalization_samples or not quality_samples:
        return None, None

    # === Calculate average weights function ===
    def average_and_normalize(samples):
        dimensions = set()
        for sample in samples:
            dimensions.update(sample.keys())
        avg_weights = {}
        for dim in dimensions:
            values = [sample.get(dim, 0) for sample in samples if dim in sample]
            if len(values) == len(samples):
                avg_weights[dim] = sum(values) / len(values)
        # Normalize
        total = sum(avg_weights.values())
        for dim in avg_weights:
            avg_weights[dim] = avg_weights[dim] / total
        # Round and adjust
        return round_weights_and_adjust(avg_weights, decimal_places=2)

    personalization_weights = average_and_normalize(personalization_samples)
    quality_weights = average_and_normalize(quality_samples)

    return personalization_weights, quality_weights


def process_single_item_sequential(item):
    """Process a single data item, executing two phases: generating weights and generating criteria"""
    item_id = item.get('id')
    task = item.get('task')
    language = item.get('language', 'en')
    persona = item.get('persona', None)
    
    # === Phase 1: Multiple sampling to generate dimension weights and take average ===
    personalization_weights, quality_weights = generate_weights_multiple_times(
        item_id, task, persona, language, DEFAULT_SAMPLE_COUNT
    )
    
    # === Phase 2: Generate detailed criteria ===
    prompts = get_prompts_by_language(language)
    # criteria_prompts = prompts["criteria_prompts"]
    # current_criterions = {}
    personalization_criteria_prompts = prompts["personalization_criteria_prompts"]
    quality_criteria_prompts = prompts["quality_criteria_prompts"]
    personalization_criterions = {}
    quality_criterions = {}

    # === Generate personalization criteria ===
    for dim_name, criteria_prompt_template in personalization_criteria_prompts.items():
        user_prompt_criteria = criteria_prompt_template.format(task_prompt=task, persona_prompt=persona)
        
        for attempt in range(RETRY_ATTEMPTS):
            criteria_output = ai_client.generate(user_prompt=user_prompt_criteria, system_prompt="")
            
            try:
                parsed_criteria = parse_llm_output_as_json(criteria_output, expected_type=list)
                if parsed_criteria and validate_weights(parsed_criteria):
                    personalization_criterions[dim_name] = parsed_criteria
                    break
            except Exception:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
    # === Generate quality criteria ===
    for dim_name, criteria_prompt_template in quality_criteria_prompts.items():
        user_prompt_criteria = criteria_prompt_template.format(task_prompt=task)
        
        for attempt in range(RETRY_ATTEMPTS):
            criteria_output = ai_client.generate(user_prompt=user_prompt_criteria, system_prompt="")
            
            try:
                parsed_criteria = parse_llm_output_as_json(criteria_output, expected_type=list)
                if parsed_criteria and validate_weights(parsed_criteria):
                    quality_criterions[dim_name] = parsed_criteria
                    break
            except Exception:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)

    # === Successfully completed all phases ===
    final_data = item.copy()
    final_data.update({
        "personalization_weights": personalization_weights,
        "quality_weights": quality_weights,
        "personalization_criterions": personalization_criterions,
        "quality_criterions": quality_criterions
    })
    final_data.pop('persona', None)
    return final_data, item_id

def generate_criteria_pipeline(input_file, persona_file, output_file, process_limit, max_workers, sample_count=DEFAULT_SAMPLE_COUNT):
    """Main process: read data, process, write to final file"""
    start_time = time.time()
    success_count_this_run = 0
    error_count_this_run = 0
    results_this_run = []

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # read persona data(json file)
    if os.path.exists(persona_file):
        with open(persona_file, 'r', encoding='utf-8') as f:
            persona_data = [json.loads(line) for line in f if line.strip()]
    else:
        print(f"Persona file {persona_file} not found.")
        return
    persona_map = {p.get('userid'): p for p in persona_data}

    # Read input data
    input_data_to_process = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if process_limit is not None and len(input_data_to_process) >= process_limit:
                break
            data = json.loads(line)
            if data.get('id') and data.get('task'):
                # if data.get('id') != 228:
                #     continue
                # Also include language field in processing items
                language = data.get('language', 'en')  # Default to English
                userid = data.get('userid', '')
                data['persona'] = persona_map.get(userid, {}) if userid else None
                input_data_to_process.append(data)

    if not input_data_to_process:
        print("No items to process.")
        return

    print(f"Starting to process {len(input_data_to_process)} items using up to {max_workers} threads...")
    print(f"Each weight will be sampled {sample_count} times and averaged...")
    
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for item in input_data_to_process:
            futures.append(executor.submit(process_single_item_sequential, item))

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Generating criteria"):
            try:
                result_data, item_id = future.result()
                success_count_this_run += 1
                results_this_run.append(result_data)
            except Exception as exc:
                print(f'Failed to process item: {exc}')
                error_count_this_run += 1

    # Write results
    with open(output_file, 'w', encoding='utf-8') as f:
        results_this_run.sort(key=lambda x: x.get('id', ''))
        for result in results_this_run:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    end_time = time.time()
    duration = end_time - start_time
    items_attempted = len(input_data_to_process)
    items_per_sec = items_attempted / duration if duration > 0 else 0

    print("\n--- Run Summary ---")
    print(f"Total items attempted:      {items_attempted}")
    print(f"Items successfully processed:  {success_count_this_run}")
    print(f"Items failed:        {error_count_this_run}")
    print(f"Total runtime:        {duration:.2f} seconds ({items_per_sec:.2f} items/sec)")
    print(f"Maximum threads used:      {max_workers}")
    print(f"Samples per weight:    {sample_count}")
    print(f"Final result file:          {output_file}")

if __name__ == "__main__":
    # Call the main function directly with the config parameters defined above
    generate_criteria_pipeline(
        INPUT_FILE, 
        PERSONA_FILE,
        OUTPUT_FILE, 
        PROCESS_LIMIT, 
        MAX_WORKERS,
        DEFAULT_SAMPLE_COUNT
    )
