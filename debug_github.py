#!/usr/bin/env python3
"""
Debug script to test GitHub client directly
"""
import os
import itertools
from src.issue_finder.services.github_client import GitHubClient
from src.issue_finder.utils.auth import get_auth_token

def debug_github_client():

    # Test with token if available
    token = get_auth_token()
    if token:
        print(f"\nTesting with token (masked: {token[:4]}...{token[-4:]})...")
        try:
            client = GitHubClient(auth_token=token)
            repo = client.get_repository("github", "spec-kit")
            print(f"Repository info: {repo}")

            print("Fetching issues...")

            # Get up to 5 issues
            print("Getting up to 5 issues...")
            all_issues = list(itertools.islice(client.get_issues("github", "spec-kit"), 5))
            print(f"Successfully fetched {len(all_issues)} issues")

            # Show issues
            print("Issues:")
            for i, issue in enumerate(all_issues):
                print(f"  Issue {i+1}: #{issue.number} - {issue.title[:50]}...")

            # Check if any are pull requests
            pr_count = sum(1 for issue in all_issues if issue.is_pull_request)
            print(f"Pull requests in sample: {pr_count}")
            print(f"Pure issues in sample: {len(all_issues) - pr_count}")

        except Exception as e:
            print(f"Error with token: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No GITHUB_TOKEN found in environment")
        print("Please set GITHUB_TOKEN environment variable first")

if __name__ == "__main__":
    debug_github_client()
