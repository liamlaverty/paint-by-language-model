#!/usr/bin/env bash
# run_queue.sh
# Reads src/datafiles/queue.json and executes main.py for each incomplete run.
# Usage: ./run_queue.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUEUE_FILE="$SCRIPT_DIR/src/datafiles/queue.json"
MAIN_PY="$SCRIPT_DIR/src/paint_by_language_model/main.py"
DRY_RUN=false

# Parse flags
for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
    esac
done

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Install with: brew install jq" >&2
    exit 1
fi

if ! conda run -n paint-by-language-model python --version &> /dev/null; then
    echo "Error: conda environment 'paint-by-language-model' not found." >&2
    exit 1
fi

echo "Loading queue from: $QUEUE_FILE"
echo ""

total=$(jq 'length' "$QUEUE_FILE")
incomplete=$(jq '[.[] | select(.isComplete == false)] | length' "$QUEUE_FILE")
echo "Queue: $total total, $incomplete incomplete"
echo ""

# Iterate over each entry in the queue
jq -c '.[]' "$QUEUE_FILE" | while IFS= read -r entry; do
    is_complete=$(echo "$entry" | jq -r '.isComplete')
    output_id=$(echo "$entry" | jq -r '."output-id"')

    if [ "$is_complete" = "true" ]; then
        echo "Skipping '$output_id' (already complete)"
        continue
    fi

    # Build CLI arguments from JSON fields
    artist=$(echo "$entry" | jq -r '.artist')
    subject=$(echo "$entry" | jq -r '.subject')

    cmd=(conda run -n paint-by-language-model python "$MAIN_PY"
        --artist "$artist"
        --subject "$subject"
        --output-id "$output_id"
    )

    # Optional arguments - only add if present and non-null
    expanded_subject=$(echo "$entry" | jq -r '."expanded-subject" // empty')
    [ -n "$expanded_subject" ] && cmd+=(--expanded-subject "$expanded_subject")

    provider=$(echo "$entry" | jq -r '.provider // empty')
    [ -n "$provider" ] && cmd+=(--provider "$provider")

    planner_model=$(echo "$entry" | jq -r '."planner-model" // empty')
    [ -n "$planner_model" ] && cmd+=(--planner-model "$planner_model")

    max_iterations=$(echo "$entry" | jq -r '."max-iterations" // empty')
    [ -n "$max_iterations" ] && cmd+=(--max-iterations "$max_iterations")

    target_score=$(echo "$entry" | jq -r '."target-score" // empty')
    [ -n "$target_score" ] && cmd+=(--target-score "$target_score")

    strokes_per_query=$(echo "$entry" | jq -r '."strokes-per-query" // empty')
    [ -n "$strokes_per_query" ] && cmd+=(--strokes-per-query "$strokes_per_query")

    stroke_types=$(echo "$entry" | jq -r '."stroke-types" // empty')
    [ -n "$stroke_types" ] && cmd+=(--stroke-types "$stroke_types")

    api_key=$(echo "$entry" | jq -r '."api-key" // empty')
    [ -n "$api_key" ] && cmd+=(--api-key "$api_key")

    log_level=$(echo "$entry" | jq -r '."log-level" // empty')
    [ -n "$log_level" ] && cmd+=(--log-level "$log_level")

    gif_frame_duration=$(echo "$entry" | jq -r '."gif-frame-duration" // empty')
    [ -n "$gif_frame_duration" ] && cmd+=(--gif-frame-duration "$gif_frame_duration")

    echo "Running: $output_id"
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] ${cmd[*]}"
        echo ""
        continue
    fi

    echo "  Command: ${cmd[*]}"
    echo ""

    if "${cmd[@]}"; then
        echo "Completed: $output_id"
        # Mark as complete in the queue JSON file
        tmp=$(mktemp)
        jq --arg id "$output_id" \
            'map(if ."output-id" == $id then .isComplete = true else . end)' \
            "$QUEUE_FILE" > "$tmp" && mv "$tmp" "$QUEUE_FILE"
        echo "Marked '$output_id' as complete in queue."
    else
        echo "Failed: $output_id (exit code $?)" >&2
        echo "Halting queue execution." >&2
        exit 1
    fi
    echo ""
done

echo "Queue processing finished."
