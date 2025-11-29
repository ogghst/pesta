#!/bin/bash

# Script to run Playwright tests individually and update test log

cd "$(dirname "$0")"
eval "$(fnm env)"
fnm use 22

LOG_FILE="../docs/frontend-e2e-test-log.md"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M CET")

run_test_file() {
  local test_file=$1
  local filename=$(basename "$test_file" .spec.ts)
  echo "Running: $test_file"

  # Run test and capture output
  local output=$(timeout 180 npx playwright test "$test_file" --reporter=list --workers=1 2>&1)
  local exit_code=$?

  # Extract test counts
  local passed=$(echo "$output" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")
  local failed=$(echo "$output" | grep -oP '\d+(?= failed)' | tail -1 || echo "0")
  local total=$(echo "$output" | grep -oP '\d+(?= passed)' | tail -1 || echo "0")

  # Determine status
  local status="❌ Failed"
  if [ $exit_code -eq 0 ]; then
    status="✅ Passing"
  elif [ $exit_code -eq 124 ]; then
    status="⚠️  Timeout"
  fi

  echo "  Status: $status"
  echo "  Passed: $passed, Failed: $failed"

  # Save detailed output
  echo "$output" > "/tmp/${filename}-detailed.log"

  return $exit_code
}

echo "Starting test execution at $TIMESTAMP"
echo "=========================================="
echo ""

# List of test files
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

# Run each test
for test_file in "${TEST_FILES[@]}"; do
  run_test_file "$test_file"
  echo ""
done

echo "=========================================="
echo "Test execution complete. Check detailed logs in /tmp/"
echo "Update $LOG_FILE manually with results."
