#!/bin/bash
# Target model name
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

TARGET_MODEL="test"    #set to your target model here, e.g., "gemini_2.5_pro", "O3", ...

# Common parameters for PQR evaluations
RAW_DATA_DIR="data/test_data/raw_data"
OUTPUT_DIR="results"
N_TOTAL_PROCESS=10
QUERY_DATA_PATH="data/prompt_data/queries150_zh.jsonl"
PERSONA_DATA_PATH="data/persona_data/personas_zh.jsonl"
CRITERIA_FILE_PATH="data/criteria_data/criteria150_zh.jsonl"

# Specify log output file
mkdir -p "$OUTPUT_DIR/output_logs"
OUTPUT_LOG_FILE="$OUTPUT_DIR/output_logs/${TARGET_MODEL}.log"

# Clear log file
echo "Starting benchmark tests, log output to: $OUTPUT_LOG_FILE" > "$OUTPUT_LOG_FILE"

echo "Running benchmark for target model: $TARGET_MODEL"
echo -e "\n\n========== Starting evaluation for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"

# --- Phase 1: Personalization Evaluation ---
echo "==== Phase 1: Running Personalization Evaluation for $TARGET_MODEL ====" | tee -a "$OUTPUT_LOG_FILE"
P_OUTPUT="$OUTPUT_DIR/personalization/$TARGET_MODEL"
mkdir -p $P_OUTPUT

# Base command for current target model
PYTHON_CMD="python -u code/eval_personalization.py \"$TARGET_MODEL\" --raw_data_dir $RAW_DATA_DIR --max_workers $N_TOTAL_PROCESS --query_file $QUERY_DATA_PATH --output_dir $P_OUTPUT --persona_file $PERSONA_DATA_PATH --criteria_file $CRITERIA_FILE_PATH"

# Add optional parameters
if [[ -n "$LIMIT" ]]; then
  PYTHON_CMD="$PYTHON_CMD $LIMIT"
fi

if [[ -n "$SKIP_CLEANING" ]]; then
  PYTHON_CMD="$PYTHON_CMD $SKIP_CLEANING"
fi

if [[ -n "$ONLY_ZH" ]]; then
  PYTHON_CMD="$PYTHON_CMD $ONLY_ZH"
fi

if [[ -n "$ONLY_EN" ]]; then
  PYTHON_CMD="$PYTHON_CMD $ONLY_EN"
fi

if [[ -n "$FORCE" ]]; then
  PYTHON_CMD="$PYTHON_CMD $FORCE"
fi

# Execute command and append stdout and stderr to single log file
echo "Executing command: $PYTHON_CMD" | tee -a "$OUTPUT_LOG_FILE"
eval $PYTHON_CMD >> "$OUTPUT_LOG_FILE" 2>&1

echo "Completed Personalization benchmark test for target model: $TARGET_MODEL"
echo -e "\n========== Personalization test completed for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"

# --- Phase 2: Quality Evaluation ---
echo "==== Phase 2: Running Quality Evaluation for $TARGET_MODEL ====" | tee -a "$OUTPUT_LOG_FILE"
Q_OUTPUT="$OUTPUT_DIR/quality/$TARGET_MODEL"
mkdir -p $Q_OUTPUT

# Base command for current target model
PYTHON_CMD="python -u code/eval_quality.py \"$TARGET_MODEL\" --raw_data_dir $RAW_DATA_DIR --max_workers $N_TOTAL_PROCESS --query_file $QUERY_DATA_PATH --output_dir $Q_OUTPUT --criteria_file $CRITERIA_FILE_PATH"

# Add optional parameters
if [[ -n "$LIMIT" ]]; then
  PYTHON_CMD="$PYTHON_CMD $LIMIT"
fi

if [[ -n "$SKIP_CLEANING" ]]; then
  PYTHON_CMD="$PYTHON_CMD $SKIP_CLEANING"
fi

if [[ -n "$ONLY_ZH" ]]; then
  PYTHON_CMD="$PYTHON_CMD $ONLY_ZH"
fi

if [[ -n "$ONLY_EN" ]]; then
  PYTHON_CMD="$PYTHON_CMD $ONLY_EN"
fi

if [[ -n "$FORCE" ]]; then
  PYTHON_CMD="$PYTHON_CMD $FORCE"
fi

# Execute command and append stdout and stderr to single log file
echo "Executing command: $PYTHON_CMD" | tee -a "$OUTPUT_LOG_FILE"
eval $PYTHON_CMD >> "$OUTPUT_LOG_FILE" 2>&1

echo "Completed Quality benchmark test for target model: $TARGET_MODEL"
echo -e "\n========== Quality test completed for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"


# --- Phase 3: Reliability Evaluation ---
echo "==== Phase 3: Running Reliability Evaluation for $TARGET_MODEL ====" | tee -a "$OUTPUT_LOG_FILE"

# Create citation output directory if it doesn't exist
R_OUTPUT="$OUTPUT_DIR/reliability/$TARGET_MODEL"
RAW_DATA_PATH="$RAW_DATA_DIR/$TARGET_MODEL.jsonl"
mkdir -p $R_OUTPUT

# Run citation extraction, deduplication, scraping, and validation
echo "Extracting citations for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
python -u -m code.utils.extract --raw_data_path $RAW_DATA_PATH --output_path $R_OUTPUT/extracted.jsonl --query_data_path $QUERY_DATA_PATH --n_total_process $N_TOTAL_PROCESS

echo "Deduplicate citations for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
python -u -m code.utils.deduplicate --raw_data_path $R_OUTPUT/extracted.jsonl --output_path $R_OUTPUT/deduplicated.jsonl --query_data_path $QUERY_DATA_PATH --n_total_process $N_TOTAL_PROCESS

echo "Scrape webpages for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
python -u -m code.utils.scrape --raw_data_path $R_OUTPUT/deduplicated.jsonl --output_path $R_OUTPUT/scraped.jsonl --n_total_process $N_TOTAL_PROCESS

echo "Validate citations for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
python -u -m code.utils.validate --raw_data_path $R_OUTPUT/scraped.jsonl --output_path $R_OUTPUT/validated.jsonl --query_data_path $QUERY_DATA_PATH --n_total_process $N_TOTAL_PROCESS

echo "Collecting statistics for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
python -u -m code.utils.stat --input_path $R_OUTPUT/validated.jsonl --output_path $R_OUTPUT/reliability_result.txt

echo "Completed Reliability Evaluation for target model: $TARGET_MODEL"
echo -e "\n========== Reliability Evaluation completed for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"


# --- Phase 4: Aggregate Overall Scores ---
echo "==== Phase 4: Aggregating Overall Scores for $TARGET_MODEL ====" | tee -a "$OUTPUT_LOG_FILE"
OVERALL_OUTPUT="$OUTPUT_DIR/overall/$TARGET_MODEL"
mkdir -p $OVERALL_OUTPUT

python -u -m code.utils.aggregate_overall \
    --base_dir $OUTPUT_DIR \
    --target_model $TARGET_MODEL \
    --output_dir $OVERALL_OUTPUT >> "$OUTPUT_LOG_FILE" 2>&1

echo "Completed Overall Aggregation for $TARGET_MODEL"
echo -e "\n========== Overall Aggregation completed for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"

echo "--------------------------------------------------"


echo "All benchmark tests completed. Logs saved in $OUTPUT_LOG_FILE"