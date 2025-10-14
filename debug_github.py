#!/usr/bin/env python3
"""
Simplified debug script to test GitHub client functionality
"""
import os
import sys
from pathlib import Path

# Add src root to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("=== GitHub Client Debug Test ===\n")

    # Test 1: Check if environment token exists and show status
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        print(f"✓ GITHUB_TOKEN found in environment (masked: {env_token[:4]}...{env_token[-4:]})")
    else:
        print("✗ No GITHUB_TOKEN found in environment")

    # Test 2: Try importing GitHubClient
    try:
        from services.github_client import GitHubClient
        print("✓ Successfully imported GitHubClient")
    except Exception as e:
        print(f"✗ Failed to import GitHubClient: {e}")
        return

    # Test 3: Try creating client without token
    try:
        client_no_token = GitHubClient(token=None)
        print("✓ Successfully created GitHubClient without token")
    except Exception as e:
        print(f"✗ Failed to create GitHubClient without token: {e}")
        return

    # Test 4: Try a simple repository access with a known public repo
    test_repo_url = "https://github.com/octocat/Hello-World"
    try:
        print(f"\n--- Testing repository access: {test_repo_url} ---")
        repo = client_no_token.get_repository(test_repo_url)
        print(f"✓ Successfully accessed repository:")
        print(f"  Owner: {repo.owner}")
        print(f"  Name: {repo.name}")
        print(f"  URL: {repo.url}")
        print(f"  Is Public: {repo.is_public}")
        print(f"  Default Branch: {repo.default_branch}")

        # Test 5: Try fetching issues
        print(f"\n--- Testing issue fetching ---")
        issues = client_no_token.get_issues("octocat", "Hello-World")
        print(f"✓ Successfully fetched {len(issues)} issues")

        # Show first few issues
        for i, issue in enumerate(issues[:3]):
            print(f"  Issue #{issue.number}: {issue.title[:50]}... (state: {issue.state}, comments: {issue.comment_count})")

    except Exception as e:
        print(f"✗ Failed during repository/issue access: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()