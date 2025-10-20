# Data Model: Most Comment Users Feature

**Date**: 2025-10-20
**Feature**: 002-most-comment-users

## Overview

This feature extends the existing data model to include comment activity tracking alongside issue creation metrics. The enhancement maintains backward compatibility while adding comment aggregation capabilities.

## Enhanced Entities

### UserActivity (Extended)

**Purpose**: Represents a user's activity in the repository, now including both issue creation and comment contributions.

**Fields**:
- `username: str` - GitHub username (required, unique identifier)
- `issues_created: int` - Number of issues created by this user (existing field)
- `comments_made: int` - Total number of comments made across all issues (new field)
- `last_activity: datetime` - Most recent activity timestamp (existing field, may need update logic)

**Validation Rules**:
- `username` must be non-empty string
- `issues_created` must be >= 0
- `comments_made` must be >= 0
- `last_activity` must be valid datetime

**State Transitions**:
- Initial state: `issues_created=0, comments_made=0`
- Issue creation: increment `issues_created`, update `last_activity`
- Comment creation: increment `comments_made`, update `last_activity`

**Relationships**:
- Aggregates data from multiple `Issue` entities
- Referenced by `MetricsAnalyzer` for ranking calculations

### Issue (Existing, Referenced)

**Purpose**: GitHub issue with associated comments.

**Relevant Fields for This Feature**:
- `number: int` - Issue number
- `comments: List[Comment]` - Collection of comments on this issue (referenced for aggregation)
- `user: User` - Issue creator (used for issue creation counting)

**Note**: The `Issue` model already exists and is used for comment source data.

### Comment (New Reference Entity)

**Purpose**: Represents a single comment on an issue.

**Fields**:
- `id: int` - GitHub comment ID
- `user: User` - Comment author (nullable for deleted users)
- `body: str` - Comment text content
- `created_at: datetime` - Comment creation timestamp

**Note**: This is a reference entity used during aggregation but not stored in the final data model.

## Aggregation Logic

### Comment Counting Process

1. **Collection Phase**: For each issue, fetch all comments using GitHub API
2. **Filtering Phase**: Filter out comments where `user` is None (deleted users)
3. **Aggregation Phase**: Count comments per username using dictionary accumulator
4. **Merging Phase**: Combine comment counts with existing issue creation counts
5. **Ranking Phase**: Sort users by `comments_made` descending, then `issues_created` as tiebreaker

### Data Flow

```
GitHub API Issues → IssueAnalyzer → Comment Aggregation → UserActivity List → Ranking → Output
```

### Edge Cases Handled

- **No Comments Available**: Users with 0 comments still included in results
- **Deleted Comment Authors**: Comments with null users are skipped (not counted)
- **Multiple Comments by Same User**: Properly aggregated per user
- **Comments on Own Issues**: Counted separately from issue creation
- **Mixed Activity**: Users who both create issues and comment are handled correctly

## Storage and Performance

### In-Memory Processing
- All aggregation performed in memory during analysis
- No persistent storage required
- Memory usage scales with: `number_of_issues * average_comments_per_issue`

### Performance Characteristics
- **Time Complexity**: O(I * C) where I = issues, C = average comments per issue
- **Space Complexity**: O(U + I * C) where U = unique users
- **API Calls**: I + 1 additional API calls (one per issue for comments)

## Validation and Error Handling

### Input Validation
- Comment data validated during API response parsing
- Null user handling prevents crashes on deleted accounts
- Unicode content in comments handled via existing JSON serialization

### Error Scenarios
- **Missing Comment Permissions**: Gracefully skip comment fetching, include users with comment_count = 0
- **Rate Limiting**: Leverage existing rate limit handling, continue with available data
- **Network Failures**: Partial results acceptable, users without comment data get count = 0

## Backward Compatibility

- Existing `UserActivity` structure maintained with optional `comments_made` field
- Existing analysis workflows continue to function
- New comment metrics are additive, not replacing existing functionality
- CLI interface extensions are backward compatible