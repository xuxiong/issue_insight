# Tasks: Most Comment Users

**Input**: Design documents from `./specs/002-most-comment-users/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md
**Tests**: The examples below include test tasks. Tests are REQUIRED - Feature will be developed test-first with failing tests before implementation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project CLI structure maintained as existing codebase

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create Python 3.11+ virtual environment with PyGithub>=2.1.0, click>=8.1.0, rich>=13.0.0, pydantic>=2.0.0, orjson>=3.9.0, requests>=2.31.0, tabulate>=0.9.0 dependencies
- [ ] T002 [P] Configure linting and formatting tools (black, mypy, ruff) for Python 3.11+ code quality standards

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Comment fetching infrastructure already exists** - GitHub client has `get_comments_for_issue()` method using PyGithub's `issue.get_comments()`.

- [ ] T003 Extend UserActivity model in src/models/__init__.py to include comments_made field (int, default 0)
- [ ] T004 Implement comment aggregation logic in src/services/issue_analyzer.py using dictionary-based counting per user
- [ ] T005 [REVIEW] Enhance comment fetching integration - verify get_comments_for_issue method works with existing issue fetching pipeline (conditional comment retrieval when filter_criteria.include_comments=True)
- [ ] T006 Extend filter engine in src/services/filter_engine.py to handle comment data availability checks (comments loaded vs comment_count only)
- [ ] T007 Configure Rich table output in src/lib/formatters/ for comment-based user rankings

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Display Most Active Comment Users (Priority: P1) 🎯 MVP

**Goal**: Enable repository maintainers to see users who are most active in commenting on issues, ranking them by total comments made across all issues

**Independent Test**: Can be fully tested by running the analyzer with comment data and verifying that users are accurately ranked by comment count, delivering value as a standalone metric for community analysis

### Tests for User Story 1 (REQUIRED - write failing tests BEFORE implementation) ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Contract test for comment aggregation API in tests/contract/test_comment_aggregation.py
- [ ] T009 [P] [US1] Integration test for comment-based user rankings in tests/integration/test_us1_most_comment_users.py
- [ ] T010 [P] [US1] Unit test for comment counting logic in tests/unit/test_comment_aggregation.py

### Implementation for User Story 1

- [ ] T011 [P] [US1] Extend UserActivity model in src/models/__init__.py with comments_made field validation (>=0)
- [ ] T012 [P] [US1] Verify/enhance comment fetching integration in src/services/github_client.py (ensure get_comments_for_issue method integrates properly with issue analysis pipeline)
- [ ] T013 [US1] Implement comment aggregation in IssueAnalyzer service src/services/issue_analyzer.py (depends on T011, T012)
- [ ] T014 [US1] Extend MetricsAnalyzer in src/services/metrics_analyzer.py for comment-based ranking with issues_created as tiebreaker
- [ ] T015 [US1] Add Rich table formatter in src/lib/formatters/ for displaying top 10 most active comment users
- [ ] T017 [US1] Add error handling for missing comment data in src/services/github_client.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T018 [P] Documentation updates in README.md for most comment users feature
- [ ] T019 Code cleanup and refactoring for comment aggregation logic

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Tests (REQUIRED) MUST be written and FAIL before implementation (TDD)
- Models before services (T011 before T013)
- Services before CLI integration (T013, T014 before T016)
- Core implementation before integration (T013-T015 before T016)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for comment aggregation API in tests/contract/test_comment_aggregation.py"
Task: "Integration test for comment-based user rankings in tests/integration/test_us1_most_comment_users.py"
Task: "Unit test for comment counting logic in tests/unit/test_comment_aggregation.py"

# Launch all models for User Story 1 together:
Task: "Extend UserActivity model in src/models/__init__.py with comments_made field validation (>=0)"
Task: "Add comment fetching method to GitHubClient in src/services/github_client.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with comment data
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done: Implement User Story 1
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD requirement)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
