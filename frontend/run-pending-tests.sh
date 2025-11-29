#!/bin/bash

# Script to run pending E2E tests one by one and capture results

cd "$(dirname "$0")"
eval "$(fnm env)"
fnm use 22

RESULTS_DIR="test-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"

PENDING_TESTS=(
  "tests/reset-password.spec.ts"
  "tests/user-settings.spec.ts"
  "tests/forecast-crud.spec.ts"
  "tests/project-performance-dashboard.spec.ts"
  "tests/project-cost-element-tabs.spec.ts"
  "tests/time-machine.spec.ts"
)

for test_file in "${PENDING_TESTS[@]}"; do
  echo "=========================================="
  echo "Running: $test_file"
  echo "=========================================="

  filename=$(basename "$test_file" .spec.ts)
  output_file="$RESULTS_DIR/${filename}.log"

  timeout 300 npx playwright test "$test_file" --reporter=list --workers=1 > "$output_file" 2>&1
  exit_code=$?

  if [ $exit_code -eq 0 ]; then
    echo "✓ PASSED: $test_file"
  elif [ $exit_code -eq 124 ]; then
    echo "⚠ TIMEOUT: $test_file (check $output_file)"
  else
    echo "✗ FAILED: $test_file (exit code: $exit_code, check $output_file)"
  fi

  # Show summary from output
  echo "--- Summary ---"
  tail -30 "$output_file" | grep -E "(passed|failed|Error|✓|×|test\.)" || echo "No summary available"
  echo ""
done

echo "=========================================="
echo "Test run complete. Results in $RESULTS_DIR/"
echo "=========================================="
