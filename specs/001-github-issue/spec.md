# Feature Specification: GitHub Project Activity Analyzer

**Feature Branch**: `001-github-issue`
**Created**: 2025-10-14
**Status**: Draft
**Input**: User description: "用户提供GitHub项目地址，根据用户提供的issue过滤条件（其中包括评论数量），输出内容。补充，用户查issue的目的是了解这个项目的活跃情况和社区关注热点"

## Clarifications

### Session 2025-10-14

- Q: How should users enable/disable comment content retrieval? → A: Command-line flag (e.g., `--include-comments` or `-c`) to enable comment content retrieval
- Q: How should GitHub API authentication be handled for rate limiting? → A: Optional GitHub personal access token via environment variable (e.g., `GITHUB_TOKEN`) or command-line flag
- Q: How should comment content be structured in output formats? → A: Include comment content as nested array within each issue object (e.g., `issue.comments = [comment1, comment2, ...]`)
- Q: How should the system handle comment retrieval failures? → A: Continue processing issues but include an error indicator/marker for issues where comment retrieval failed
- Q: How should users specify a limit for the number of returned issues? → A: Command-line flag (e.g., `--limit N`) with default value of 100

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project Activity Assessment (Priority: P1)

As a potential contributor, investor, or community member, I want to analyze a GitHub repository's issues filtered by comment count and other activity indicators, so I can understand the project's current activity level, identify community hotspots, and assess the health and engagement of the project.

**Why this priority**: This addresses the core user need of evaluating project vitality and community focus. Comment count serves as a direct proxy for community interest and discussion activity, helping users quickly identify the most relevant and actively discussed issues in the project.

**Independent Test**: Can be fully tested by providing a valid GitHub repository URL and comment count filter, then verifying that only issues matching the criteria are returned in a structured format.

**Acceptance Scenarios**:

1. **Given** a valid GitHub repository URL and a minimum comment count of 5, **When** the tool processes the request, **Then** it returns only issues that have 5 or more comments
2. **Given** a valid GitHub repository URL and a maximum comment count of 10, **When** the tool processes the request, **Then** it returns only issues that have 10 or fewer comments
3. **Given** an invalid GitHub repository URL, **When** the tool processes the request, **Then** it displays a clear error message indicating the repository was not found

---

### User Story 2 - Community Hotspot Identification (Priority: P2)

As a community researcher or project evaluator, I want to combine comment count filtering with issue labels, creation dates, and activity patterns, so I can identify trending topics, recurring problems, and areas of sustained community interest within the project.

**Why this priority**: This enables deeper analysis of community dynamics by allowing users to correlate high-comment issues with specific labels (like "bug", "feature", "question") and timeframes, revealing patterns in what the community cares about most and how those interests evolve over time.

**Independent Test**: Can be tested by providing a GitHub repository URL with multiple filter criteria (e.g., comment count >= 3, label="bug", state="open") and verifying that only issues matching all criteria are returned.

**Acceptance Scenarios**:

1. **Given** a GitHub repository URL with filters for comment count >= 2, label="enhancement", and state="open", **When** the tool processes the request, **Then** it returns only open enhancement issues with 2 or more comments
2. **Given** a GitHub repository URL with filters for comment count between 1-5 and assignee="john-doe", **When** the tool processes the request, **Then** it returns only issues assigned to john-doe with 1-5 comments

---

### User Story 3 - Activity Metrics and Trends (Priority: P2)

As a project analyst or community manager, I want to see aggregated metrics about issue activity such as average comment count, most active time periods, and trending labels, so I can get a high-level overview of project health and community engagement patterns without examining individual issues.

**Why this priority**: This provides immediate insights into project vitality through summary statistics, complementing the detailed issue filtering with macro-level activity indicators that help users quickly assess overall project health.

**Independent Test**: Can be tested by providing a GitHub repository URL and requesting activity metrics, then verifying that summary statistics including average comment count, activity distribution by time period, and top labels are returned.

**Acceptance Scenarios**:

1. **Given** a GitHub repository URL with recent activity, **When** the user requests activity metrics, **Then** the system returns average comment count per issue, total issues analyzed, and top 5 most used labels
2. **Given** a GitHub repository URL with issues spanning multiple months, **When** the user requests activity metrics, **Then** the system returns a breakdown of issue activity by month showing which periods had the highest engagement

---

### User Story 4 - Comment Content Analysis (Priority: P2)

As a community researcher or project evaluator, I want to access the actual comment content from filtered issues, so I can understand the specific topics being discussed, identify recurring themes, and analyze community sentiment around key issues.

**Why this priority**: This provides deep qualitative insights beyond just quantitative metrics. Understanding what people are actually saying in comments reveals the true nature of community hotspots and helps identify specific concerns, suggestions, or debates that drive engagement.

**Independent Test**: Can be tested by providing a GitHub repository URL with `--include-comments` flag, then verifying that the actual comment text from matching issues is included in the output alongside issue metadata.

**Acceptance Scenarios**:

1. **Given** a GitHub repository URL with `--include-comments` flag and a minimum comment count of 3, **When** the tool processes the request, **Then** it returns issues with 3+ comments including the full text of all comments for each issue
2. **Given** a GitHub repository URL with `--include-comments` flag and specific issue filters, **When** the tool processes the request, **Then** it returns only the comment content from issues that match all specified criteria
3. **Given** a GitHub repository URL with `--include-comments` flag for issues with many comments, **When** the tool processes the request, **Then** it includes all comment content without truncation (respecting API pagination limits)

---
### User Story 5 - Formatted Output Options (Priority: P3)

As a user who needs to share or further process the filtered results, I want to choose from different output formats (JSON, CSV, or human-readable text), so I can easily integrate the results into my workflow or share them with team members.

**Why this priority**: This provides flexibility for different user needs and integration scenarios, making the tool more versatile and useful in various contexts.

**Independent Test**: Can be tested by running the same filter query with different output format options and verifying that the results are correctly formatted according to the selected format.

**Acceptance Scenarios**:

1. **Given** a GitHub repository URL and comment count filter with output format set to JSON, **When** the tool processes the request, **Then** it returns results in valid JSON format with issue details
2. **Given** a GitHub repository URL and comment count filter with output format set to CSV, **When** the tool processes the request, **Then** it returns results in valid CSV format with headers and properly escaped values

---

### Edge Cases

- What happens when the GitHub API rate limit is exceeded during processing? (System should detect rate limit headers and provide clear guidance about using authentication token for higher limits)
- How does system handle repositories with thousands of issues that require pagination?
- What happens when no issues match the specified filtering criteria?
- How does the system handle private repositories that require authentication?
- What happens when the user provides invalid filter values (e.g., negative comment count)?
- How does the system handle issues with extremely large numbers of comments (e.g., 1000+ comments)?
- What happens when comment content includes very long text or special characters?
- How does the system handle API failures during comment retrieval after successful issue filtering? (System should continue processing and include error indicators for issues with failed comment retrieval)
- What happens when the user specifies a limit that is less than 1 or greater than the total number of matching issues?

### Error Message Standards

**Repository URL Errors**:
- Invalid format: "Invalid repository URL format. Expected: https://github.com/owner/repo. Example: https://github.com/facebook/react"
- Not found: "Repository not found or inaccessible. Verify URL and ensure repository is public. Check spelling and try again."

**Filter Value Errors**:
- Negative comments: "Invalid comment count: -5. Comment count must be non-negative integer. Use --min-comments 0 or higher."
- Invalid date: "Invalid date format: '2024-13-45'. Use YYYY-MM-DD format. Example: 2024-01-15"
- Invalid limit: "Invalid limit: -10. Limit must be a positive integer. Use --limit 100 or higher."

**Rate Limit Errors**:
- API limit exceeded: "GitHub API rate limit exceeded. Wait 60 seconds or use authentication token for higher limits. Set GITHUB_TOKEN environment variable or use --token flag."

### Metrics Calculation Rules

**Trending Labels Algorithm**:
- Calculate label usage frequency for last 30 days (current period)
- Calculate label usage frequency for previous 30-day period (baseline)
- Compute percentage change: ((current - baseline) / baseline) × 100
- Include labels with ≥25% increase AND ≥5 total occurrences
- Sort by percentage change descending
- Return top 10 labels or all qualifying labels (whichever is less)

**Time-Based Activity Breakdown**:
- Group issues by creation date (weekly intervals for repositories with >100 issues, monthly for ≤100 issues)
- Calculate metrics per interval: total issues, average comments, unique commenters
- Include trend indicators (↑/↓/→) showing change from previous interval

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a GitHub repository URL as input from the user
- **FR-002**: System MUST support filtering issues by comment count with options for minimum, maximum, or range values
- **FR-003**: System MUST retrieve issue data from the GitHub API for the specified repository, supporting optional authentication via GitHub personal access token (environment variable `GITHUB_TOKEN` or command-line flag) to increase rate limits
- **FR-004**: System MUST support additional filtering criteria including issue state (open/closed), labels, assignees, and creation/update dates
- **FR-005**: System MUST provide aggregated activity metrics including average comment count, total issues analyzed, and trending labels calculated as: labels with highest comment activity in last 30 days compared to previous 30-day period, sorted by percentage increase (minimum 25% increase threshold)
- **FR-006**: System MUST provide time-based activity breakdowns showing issue engagement patterns over different time periods: monthly breakdown for repositories with >100 issues, weekly breakdown for 50-100 issues, and daily breakdown for <50 issues
- **FR-007**: System MUST support optional retrieval and output of actual comment content from filtered issues, enabled via command-line flag (e.g., `--include-comments` or `-c`)
- **FR-008**: System MUST provide output in multiple formats (JSON, CSV, human-readable text) that can include comment content when requested
- **FR-009**: System MUST handle GitHub API pagination for repositories with large numbers of issues, including pagination for comment retrieval
- **FR-010**: System MUST display clear error messages for invalid repository URLs or API errors
- **FR-011**: System MUST handle cases where no issues match the filtering criteria gracefully
- **FR-012**: System MUST respect GitHub API rate limits and provide appropriate feedback when limits are reached
- **FR-013**: System MUST be limited to public repositories only (private repositories are out of scope)
- **FR-014**: System MUST support limiting the number of returned issues with a command-line flag (e.g., `--limit N`), defaulting to 100 issues

### Key Entities *(include if feature involves data)*

- **GitHub Repository**: Represents a GitHub project with owner and repository name, serves as the source for issue data
- **Issue**: Represents a single GitHub issue with attributes including title, body, state, labels, assignees, comment count, creation date, and update date
- **Comment**: Represents individual comments on issues with attributes including comment text, author, creation date, and reply relationships. Comments are structured as a nested array within each Issue object.
- **Filter Criteria**: Represents user-defined conditions for filtering issues, including comment count ranges, labels, assignees, issue state, and limit for number of returned issues
- **Output Format**: Represents the desired format for presenting filtered results (JSON, CSV, or human-readable text) that may include comment content structured as nested arrays within issue objects

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully analyze GitHub project activity and receive results in under 10 seconds for repositories with up to 1000 issues (without comment content) or under 30 seconds (with comment content), measured under standard conditions: 100Mbps network, 4GB RAM, GitHub API rate limits not exceeded, and average issue length of 200 characters
- **SC-002**: The tool correctly handles repositories with up to 5000 issues without performance degradation or data loss, including proper pagination for comment retrieval
- **SC-003**: 95% of users can successfully identify community hotspots and project activity patterns without requiring documentation
- **SC-004**: The tool provides accurate activity metrics, filtered results, and comment content that match manual verification of the same criteria applied directly on GitHub
- **SC-005**: Error messages are clear and actionable, enabling 90% of users to resolve input errors on their first attempt. Messages must include: (1) specific error description, (2) expected format/example, (3) suggested resolution steps, and (4) reference to help documentation when available
- **SC-006**: Users can identify the top 5 most discussed topics in a project within 2 minutes of using the tool
- **SC-007**: Users can access complete comment content for issues with up to 100 comments without data loss or truncation