# Feature Specification: Most Comment Users

**Feature Branch**: `002-most-comment-users`
**Created**: 2025-10-20
**Status**: Draft
**Input**: User description: "most comment users"

## Clarifications

### Session 2025-10-20

- Q: What should be the default output format for displaying the most active comment users in the analysis results? → A: Table
- Q: How should the system handle users who have made zero comments but created issues? → A: Include them with comment count of 0
- Q: What performance limits should be set for processing repositories with high comment volumes? → A: Up to 1000 issues with average 10 comments each
- Q: What should be the maximum number of most active comment users to display by default? → A: Top 10 users
- Q: How should the system handle rate limiting when fetching comment data from GitHub? → A: 当前项目已经处理rate limit了，这里不用特别说明
- Q: How should the "most comment users" feature integrate with the existing CLI interface from the 001-github-issue feature? → A: 替换原有逻辑。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Display Most Active Comment Users (Priority: P1)

As a community member, I want to see users who are most active in commenting on issues so that I can identify key contributors to discussions and community engagement, and their roles

**Why this priority**: This directly addresses the core user need to analyze user activity beyond just issue creation, providing insights into discussion participation which is crucial for understanding community dynamics.

**Independent Test**: Can be fully tested by running the analyzer with comment data and verifying that users are ranked by comment count, delivering value as a standalone metric for community analysis.

**Acceptance Scenarios**:

1. **Given** a repository with issues that have comments, **When** I run the analysis with comment data included, **Then** the most active users are ranked by total comments made across all issues
2. **Given** issues with comments from multiple users, **When** the analysis calculates user activity, **Then** each user's comment count is accurately aggregated across all issues they commented on
3. **Given** users who both create issues and comment, **When** the analysis shows most active users, **Then** their comment activity is included alongside issue creation metrics

---


### Edge Cases

- What happens when no comments are available for any issues?
- How does system handle users who only create issues but never comment?
- What happens when multiple users comment on the same issue?
- How does system handle deleted or inaccessible comments?
- What happens when the same user comments multiple times on the same issue?
- Users who created issues but made zero comments are included in the most active comment users list with a comment count of 0

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate most active users based on comment count when comment data is available
- **FR-002**: System MUST aggregate comment counts across all issues for each user
- **FR-003**: System MUST include comment activity in the UserActivity model alongside issue creation metrics
- **FR-005**: System MUST handle cases where comment data is not available gracefully
- **FR-006**: System MUST provide accurate comment counts per user across the entire issue set
- **FR-007**: System MUST use table format as the default output for displaying most active comment users
- **FR-008**: System MUST include users who created issues but made zero comments in the most active comment users list with comment count of 0

### Key Entities *(include if feature involves data)*

- **UserActivity**: Enhanced to include comments_made field with accurate aggregation
- **Issue**: Contains comments collection for aggregation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see accurate comment counts for each user and their roles in the most active users list
- **SC-002**: Comment aggregation completes within reasonable time for repositories with up to 1000 issues
- **SC-003**: Comment-based rankings match manual verification for test repositories
- **SC-004**: System maintains accuracy when processing repositories with varying comment volumes
- **SC-005**: System processes repositories with up to 1000 issues and average 10 comments per issue within reasonable time limits
- **SC-006**: System displays top 10 most active comment users by default
