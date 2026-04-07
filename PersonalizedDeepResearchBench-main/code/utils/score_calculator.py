import logging

def calculate_weighted_personalization_scores(llm_output_json, criteria_data, language="en"):
    """
    Calculates weighted personalization scores based on LLM output and criteria weights.
    
    Args:
        llm_output_json: JSON output from LLM with scoring data
        criteria_data: Criteria configuration with dimension weights
        language: Language of the evaluation (default: "en")
        
    Returns:
        Dictionary with weighted scores for target model
    """
    results = {
        "target": {"dims": {}, "total": 0.0}
    }
    total_target_score = 0.0
    
    # Get personalization dimension weights from criteria_data
    personalization_weights = criteria_data.get("personalization_weights", {})
    item_id = criteria_data.get("id", "Unknown") 
    
    # Check if personalization_criterions exist
    if "personalization_criterions" not in criteria_data or not criteria_data["personalization_criterions"]:
        error_msg = f"ID: {item_id} - Missing required personalization_criterions data, cannot calculate weighted scores"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # Create a mapping from criterion text to weight for easier lookup
    criterion_weights = {}
    for dim, criterions in criteria_data.get("personalization_criterions", {}).items():
        criterion_weights[dim] = {crit['criterion']: crit['weight'] for crit in criterions}

    # Record all unmatched criteria for warnings
    unmatched_criteria = set()
    
    for dim, scores_list in llm_output_json.items():
        if not isinstance(scores_list, list):
            logging.warning(f"ID: {item_id} - Dimension '{dim}' in LLM output is not a list. Skipping.")
            continue

        if dim not in personalization_weights:
            logging.warning(f"ID: {item_id} - Dimension '{dim}' from LLM output not found in personalization dimension weights. Skipping dimension.")
            continue
            
        if dim not in criterion_weights:
            logging.warning(f"ID: {item_id} - Dimension '{dim}' from LLM output not found in criteria details. Skipping dimension.")
            continue

        dim_target_weighted_sum = 0.0
        dim_total_weight = 0.0

        dim_criteria_map = criterion_weights.get(dim, {})
        
        # Skip dimension if no criteria mapping exists
        if not dim_criteria_map:
            logging.warning(f"ID: {item_id} - No criteria mapping found for dimension '{dim}'. Skipping dimension.")
            continue

        for score_item in scores_list:
            if not isinstance(score_item, dict):
                logging.warning(f"ID: {item_id} - Item in scores_list for dimension '{dim}' is not a dictionary. Skipping item: {score_item}")
                continue

            criterion_text_raw = score_item.get("criterion")
            criterion_text = criterion_text_raw.strip() if isinstance(criterion_text_raw, str) else None

            # Check different score field formats
            # Note: The code now only handles 'target_score' or 'article_1_score' as target model score.
            target_score_raw = score_item.get("target_score")
            article_1_score_raw = score_item.get("article_1_score")

            # Prioritize 'target_score' if available, otherwise use 'article_1_score'
            score_to_use_raw = target_score_raw if target_score_raw is not None else article_1_score_raw

            try:
                target_score = float(score_to_use_raw) if score_to_use_raw is not None else None
            except (ValueError, TypeError):
                logging.warning(f"ID: {item_id} - Invalid score format for criterion '{criterion_text}' in dimension '{dim}'. Score: '{score_to_use_raw}'. Skipping criterion.")
                continue

            if criterion_text and target_score is not None:
                # Check for exact match
                weight = dim_criteria_map.get(criterion_text)
                
                # If exact match not found, try fuzzy matching
                if weight is None:
                    # First try case-insensitive matching
                    criterion_lower = criterion_text.lower()
                    for key, val in dim_criteria_map.items():
                        if key.lower() == criterion_lower:
                            weight = val
                            break
                    
                    # If still not found, try substring matching
                    if weight is None:
                        for key, val in dim_criteria_map.items():
                            # Check if criterion text contains criteria or criteria contains criterion text
                            if criterion_lower in key.lower() or key.lower() in criterion_lower:
                                weight = val
                                break
                
                # If still no match found, record and use average weight
                if weight is None:
                    unmatched_criteria.add(f"{dim}:{criterion_text}")
                    # Calculate average weight for this dimension's criteria
                    weight = sum(dim_criteria_map.values()) / len(dim_criteria_map)
                    
                dim_target_weighted_sum += target_score * weight
                dim_total_weight += weight
                
            else:
                if criterion_text:
                    if dim not in getattr(calculate_weighted_personalization_scores, '_warned_dims', set()):
                        logging.warning(f"ID: {item_id} - Criterion text mismatch for dimension '{dim}': '{criterion_text}'. Available criteria keys start with: {list(dim_criteria_map.keys())[:1] if dim_criteria_map else []}... Check prompt/output/criteria file consistency. Further mismatches in this dim won't be logged fully.")
                        if not hasattr(calculate_weighted_personalization_scores, '_warned_dims'): calculate_weighted_personalization_scores._warned_dims = set()
                        calculate_weighted_personalization_scores._warned_dims.add(dim)
                    else:
                        logging.debug(f"ID: {item_id} - Another criterion mismatch for dimension '{dim}': '{criterion_text}'")
                elif not criterion_text:
                    logging.warning(f"ID: {item_id} - Missing 'criterion' key in score item for dimension '{dim}': {score_item}. Skipping item.")

        if dim_total_weight > 0:
            dim_target_avg = dim_target_weighted_sum / dim_total_weight
        else:
            dim_target_avg = 0
            if len(scores_list) > 0:
                logging.warning(f"ID: {item_id} - No valid criteria scored for dimension '{dim}' despite {len(scores_list)} items in LLM output. Check for systematic mismatches. Dimension average set to 0.")

        results["target"]["dims"][f"{dim}_weighted_avg"] = dim_target_avg

        dim_weight = personalization_weights.get(dim, 0)
        total_target_score += dim_target_avg * dim_weight

    # Log warning if there are unmatched criteria
    if unmatched_criteria:
        logging.warning(f"ID: {item_id} - {len(unmatched_criteria)} criteria without exact matches: {unmatched_criteria}")
    
    results["target"]["total"] = total_target_score
    
    return results


def calculate_weighted_quality_scores(llm_output_json, criteria_data, language="en"):
    """
    Calculates weighted quality scores based on LLM output and criteria weights.
    
    Args:
        llm_output_json: JSON output from LLM with scoring data
        criteria_data: Criteria configuration with quality dimension weights
        language: Language of the evaluation (default: "en")
        
    Returns:
        Dictionary with weighted scores for target model
    """
    results = {
        "target": {"dims": {}, "total": 0.0}
    }
    total_target_score = 0.0
    
    # Get quality dimension weights from criteria_data
    quality_weights = criteria_data.get("quality_weights", {})
    item_id = criteria_data.get("id", "Unknown") 
    
    # Check if quality_criterions exist
    if "quality_criterions" not in criteria_data or not criteria_data["quality_criterions"]:
        error_msg = f"ID: {item_id} - Missing required quality_criterions data, cannot calculate weighted scores"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # Create a mapping from criterion text to weight for easier lookup
    criterion_weights = {}
    for dim, criterions in criteria_data.get("quality_criterions", {}).items():
        criterion_weights[dim] = {crit['criterion']: crit['weight'] for crit in criterions}

    # Record all unmatched criteria for warnings
    unmatched_criteria = set()
    
    for dim, scores_list in llm_output_json.items():
        if not isinstance(scores_list, list):
            logging.warning(f"ID: {item_id} - Dimension '{dim}' in LLM output is not a list. Skipping.")
            continue

        if dim not in quality_weights:
            logging.warning(f"ID: {item_id} - Dimension '{dim}' from LLM output not found in quality dimension weights. Skipping dimension.")
            continue
            
        if dim not in criterion_weights:
            logging.warning(f"ID: {item_id} - Dimension '{dim}' from LLM output not found in criteria details. Skipping dimension.")
            continue

        dim_target_weighted_sum = 0.0
        dim_total_weight = 0.0

        dim_criteria_map = criterion_weights.get(dim, {})
        
        # Skip dimension if no criteria mapping exists
        if not dim_criteria_map:
            logging.warning(f"ID: {item_id} - No criteria mapping found for dimension '{dim}'. Skipping dimension.")
            continue

        for score_item in scores_list:
            if not isinstance(score_item, dict):
                logging.warning(f"ID: {item_id} - Item in scores_list for dimension '{dim}' is not a dictionary. Skipping item: {score_item}")
                continue

            criterion_text_raw = score_item.get("criterion")
            criterion_text = criterion_text_raw.strip() if isinstance(criterion_text_raw, str) else None

            # Check different score field formats
            target_score_raw = score_item.get("target_score")
            article_1_score_raw = score_item.get("article_1_score")

            # Prioritize 'target_score' if available, otherwise use 'article_1_score'
            score_to_use_raw = target_score_raw if target_score_raw is not None else article_1_score_raw

            try:
                target_score = float(score_to_use_raw) if score_to_use_raw is not None else None
            except (ValueError, TypeError):
                logging.warning(f"ID: {item_id} - Invalid score format for criterion '{criterion_text}' in dimension '{dim}'. Score: '{score_to_use_raw}'. Skipping criterion.")
                continue

            if criterion_text and target_score is not None:
                # Check for exact match
                weight = dim_criteria_map.get(criterion_text)
                
                # If exact match not found, try fuzzy matching
                if weight is None:
                    criterion_lower = criterion_text.lower()
                    for key, val in dim_criteria_map.items():
                        if key.lower() == criterion_lower:
                            weight = val
                            break
                    
                    if weight is None:
                        for key, val in dim_criteria_map.items():
                            if criterion_lower in key.lower() or key.lower() in criterion_lower:
                                weight = val
                                break
                
                # If still no match found, record and use average weight
                if weight is None:
                    unmatched_criteria.add(f"{dim}:{criterion_text}")
                    weight = sum(dim_criteria_map.values()) / len(dim_criteria_map)
                    
                dim_target_weighted_sum += target_score * weight
                dim_total_weight += weight
                
            else:
                if criterion_text:
                    if dim not in getattr(calculate_weighted_quality_scores, '_warned_dims', set()):
                        logging.warning(f"ID: {item_id} - Criterion text mismatch for dimension '{dim}': '{criterion_text}'. Available criteria keys start with: {list(dim_criteria_map.keys())[:1] if dim_criteria_map else []}... Check prompt/output/criteria file consistency. Further mismatches in this dim won't be logged fully.")
                        if not hasattr(calculate_weighted_quality_scores, '_warned_dims'): 
                            calculate_weighted_quality_scores._warned_dims = set()
                        calculate_weighted_quality_scores._warned_dims.add(dim)
                    else:
                        logging.debug(f"ID: {item_id} - Another criterion mismatch for dimension '{dim}': '{criterion_text}'")
                elif not criterion_text:
                    logging.warning(f"ID: {item_id} - Missing 'criterion' key in score item for dimension '{dim}': {score_item}. Skipping item.")

        if dim_total_weight > 0:
            dim_target_avg = dim_target_weighted_sum / dim_total_weight
        else:
            dim_target_avg = 0
            if len(scores_list) > 0:
                logging.warning(f"ID: {item_id} - No valid criteria scored for dimension '{dim}' despite {len(scores_list)} items in LLM output. Check for systematic mismatches. Dimension average set to 0.")

        results["target"]["dims"][f"{dim}_weighted_avg"] = dim_target_avg

        dim_weight = quality_weights.get(dim, 0)
        total_target_score += dim_target_avg * dim_weight

    # Log warning if there are unmatched criteria
    if unmatched_criteria:
        logging.warning(f"ID: {item_id} - {len(unmatched_criteria)} criteria without exact matches: {unmatched_criteria}")
    
    results["target"]["total"] = total_target_score
    
    return results
