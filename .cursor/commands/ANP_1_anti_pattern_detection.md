ANTI-PATTERN DETECTION

Watch for these warning signs during implementation:

1. SCOPE CREEP INDICATORS
   - "While we're here, let's also..."
   - Touching files not in the original plan
   - Solving problems not in the requirements
   
   RESPONSE: Stop and ask "Is this essential to the current objective?"

2. CONTEXT DRIFT SIGNALS
   - Duplicating code that exists elsewhere
   - Ignoring established patterns
   - Creating new abstractions unnecessarily
   
   RESPONSE: "Search for existing solutions first."

3. TDD VIOLATION FLAGS
   - "Let me just implement this first, then test"
   - Writing many tests at once
   - Tests that always pass
   
   RESPONSE: "Show me the failing test first."

4. OVER-ENGINEERING SYMPTOMS
   - Complex abstractions for simple problems
   - Solving hypothetical future problems
   - Too many configuration options
   
   RESPONSE: "What's the simplest thing that works?"

5. BATCH SIZE BLOAT
   - Commits exceeding 100 lines
   - Touching more than 5 files
   - Multiple unrelated changes
   
   RESPONSE: "Let's break this into smaller pieces."

Alert me if you see any of these patterns emerging.