#!/bin/bash

# Script to run Playwright tests individually and capture results

cd "$(dirname "$0")"
eval "$(fnm env)"
fnm use 22

TEST_FILES=(
  "tests/login.spec.ts"
  "tests/sign-up.spec.ts"
  "tests/reset-password.spec.ts"
  "tests/user-settings.spec.ts"
  "tests/cost-performance-report.spec.ts"
  "tests/forecast-crud.spec.ts"
  "tests/project-performance-dashboard.spec.ts"
  "tests/project-cost-element-tabs.spec.ts"
  "tests/time-machine.spec.ts"
)

RESULTS_DIR="test-results-individual"
mkdir -p "$RESULTS_DIR"

for test_file in "${TEST_FILES[@]}"; do
  echo "=========================================="
  echo "Running: $test_file"
  echo "=========================================="

  filename=$(basename "$test_file" .spec.ts)
  output_file="$RESULTS_DIR/${filename}.log"

  timeout 180 npx playwright test "$test_file" --reporter=list --workers=1 > "$output_file" 2>&1

  exit_code=$?

  if [ $exit_code -eq 0 ]; then
    echo "✓ PASSED: $test_file"
  elif [ $exit_code -eq 124 ]; then
    echo "⚠ TIMEOUT: $test_file (check $output_file)"
  else
    echo "✗ FAILED: $test_file (check $output_file)"
  fi

  # Show summary
  tail -20 "$output_file" | grep -E "(passed|failed|Error|✓|×)" || echo "No summary available"
  echo ""
done

echo "=========================================="
echo "Test run complete. Results in $RESULTS_DIR/"
echo "=========================================="
