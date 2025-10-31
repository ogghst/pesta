PATTERN COMPLIANCE CHECK

Before implementing this feature, verify compliance with established patterns:

1. ARCHITECTURE ALIGNMENT
   - Which layer does this belong to? (presentation, business logic, data access)
   - Are we following the separation of concerns?
   - Are we respecting existing boundaries and interfaces?

2. EXISTING PATTERN REUSE
   - Search for similar implementations in the codebase
   - List the patterns they follow (factory, repository, service, etc.)
   - Confirm we're using the same approach for consistency

3. DEPENDENCY MANAGEMENT
   - How are dependencies injected in similar classes?
   - What's the lifecycle management pattern?
   - Are we following the same approach?

4. ERROR HANDLING
   - How do similar features handle errors?
   - What exception types are used?
   - What's the logging pattern?

5. TESTING PATTERNS
   - How are similar features tested?
   - What test utilities or fixtures exist?
   - What's the typical test structure?

Document your findings before proceeding with implementation.