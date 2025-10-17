<Additional_info>
**Optionally**, you can retrieve information about the current feature we are working on. Do so **only if it's really necessary**.
For getting more context on feature we are working on:
1. Run `.specify/scripts/bash/check-prerequisites.sh --json` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.
2. Load and analyze available design documents:
   - IF EXISTS: Read tasks.md for the complete task list and execution plan
   - IF EXISTS: Read plan.md for tech stack, architecture, and file structure
   - IF EXISTS: Read data-model.md for entities
   - IF EXISTS: Read contracts/ for API endpoints
   - IF EXISTS: Read research.md for technical decisions
   - IF EXISTS: Read quickstart.md for test scenarios
   - IF EXISTS: Read spec.md for user stories and non-technical requirements
</Additional_info>