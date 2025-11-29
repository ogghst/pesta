LARGE-SCALE REFACTORING PLAN

This change touches many files. Let's proceed carefully:

1. IMPACT ANALYSIS
   - List all files that will be modified
   - Map dependencies between these files
   - Identify integration points with unchanged code
   - Note any database or configuration changes

2. PHASED APPROACH
   Break refactoring into safe, testable phases:
   Phase 1: [description]
   - Files touched: [list]
   - Tests to verify: [list]
   - Rollback point

   Phase 2: [description]
   ...

3. TEST STRATEGY
   - Which existing tests must still pass?
   - What new tests are needed?
   - How do we verify no regressions?

4. COMMUNICATION ARTIFACTS
   - What do we need to document for the team?
   - What migration steps are needed?
   - What's the rollback procedure?

Proceed step-by-step with test verification after each phase.
