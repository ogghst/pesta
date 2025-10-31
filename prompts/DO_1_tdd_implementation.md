IMPLEMENTATION PHASE: Test-Driven Development

We're now implementing step [X] from our plan.

TDD IMPLEMENTATION RULES:

BEFORE YOU WRITE ANY PRODUCTION CODE:
1. Write a failing test that describes the expected behavior
2. Run the test to confirm it fails (RED)
3. Show me the test and its output
4. Wait for my approval to proceed

IMPLEMENTATION CYCLE:
1. Write MINIMUM code to make the test pass (GREEN)
2. Run the test to confirm it passes
3. Refactor if needed while keeping tests green
4. Show me the implementation and test results

CRITICAL CONSTRAINTS:
❌ DON'T test interfaces - test concrete implementations
❌ DON'T use compilation errors as RED phase - use behavioral failures
❌ DON'T create mocks when real components are available
❌ DON'T implement multiple features in one step

✅ DO create stub implementations that compile but fail behaviorally
✅ DO use real components over mocks when possible
✅ DO make your reasoning visible at each step
✅ DO ask for clarification when assumptions are needed

BATCHING RULES:
- Related functionality can be grouped into parallel changes
- All changes in a batch must be tested together
- Each batch should focus on one logical feature or fix

PROGRESS TRACKING:
After each step, update the checklist:
- [x] Step completed
- [ ] Next step pending

Show me your test-first approach for step [X] now.