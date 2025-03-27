import os
import sys
import time
import requests

def str_to_bool(val):
    """Utility to convert environment string (e.g. 'true'/'false') to boolean."""
    return str(val).lower() in ["true", "1", "yes"]

# Read from environment
GITHUB_TOKEN = os.environ.get("MY_GITHUB_TOKEN")  # Required
MY_NAME = os.environ.get("MY_NAME", "")
MY_EMAIL = os.environ.get("MY_EMAIL", "")
USER_MODE = str_to_bool(os.environ.get("USER_MODE", "true"))
ORG_NAME = os.environ.get("ORG_NAME", "")

if not GITHUB_TOKEN:
    print("ERROR: Missing environment variable MY_GITHUB_TOKEN. Exiting.")
    sys.exit(1)

BASE_URL = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}"
}

# The other config can be environment-based or remain static defaults
ENABLE_STEP_SYNC_FORKS = str_to_bool(os.environ.get("ENABLE_STEP_SYNC_FORKS", "true"))
ENABLE_STEP_ENABLE_DEPENDABOT = str_to_bool(os.environ.get("ENABLE_STEP_ENABLE_DEPENDABOT", "true"))
ENABLE_STEP_MERGE_DEPENDABOT_PRS = str_to_bool(os.environ.get("ENABLE_STEP_MERGE_DEPENDABOT_PRS", "true"))

TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", "30"))
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "10"))
MERGE_METHOD = os.environ.get("MERGE_METHOD", "merge")

COUNT_MERGES_AS_PERSONAL_COMMITS = str_to_bool(os.environ.get("COUNT_MERGES_AS_PERSONAL_COMMITS", "true"))

# The rest of your script logic is unchanged (list_repos, merge_pr, etc.)
# Just remember to reference MY_NAME and MY_EMAIL inside merge_pr or wherever needed

# ----------------------------------------------------- #

def load_excluded_repos(file_path):
    """
    Reads lines from an 'excluded_repos.txt' file, returns a set of "owner/repo" to exclude.
    Ignores empty lines and lines starting with '#'.
    """
    excluded = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                excluded.add(line)
    except FileNotFoundError:
        # If the file doesn't exist, assume no exclusions
        print(f"No exclusion file found at: {file_path}. Proceeding without exclusions.")
    return excluded

# ================== STEP 0: LIST REPOS ================== #

def list_repos():
    """
    Returns a list of repositories where you have push (write) access.
    Paginates beyond 100 repos if necessary.
    """
    all_repos = []
    page = 1

    while True:
        if USER_MODE:
            url = f"{BASE_URL}/user/repos"
            params = {"per_page": 100, "page": page}
        else:
            url = f"{BASE_URL}/orgs/{ORG_NAME}/repos"
            params = {"per_page": 100, "page": page, "type": "all"}

        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            print(f"Error listing repos: {resp.status_code} {resp.text}")
            break

        repos_page = resp.json()
        if not repos_page:
            break

        all_repos.extend(repos_page)
        page += 1

    writable_repos = [
        r for r in all_repos
        if r.get("permissions", {}).get("push", False)
    ]
    return writable_repos

# ================== STEP 1: SYNC FORKS ================== #

def sync_fork(owner, repo_name, branch):
    """
    Sync a forked repository by merging upstream changes (POST /merge-upstream).
    """
    url = f"{BASE_URL}/repos/{owner}/{repo_name}/merge-upstream"
    data = {"branch": branch}
    resp = requests.post(url, headers=HEADERS, json=data)

    if resp.status_code == 200:
        json_resp = resp.json()
        print(f"✔️  Synced fork {owner}/{repo_name} (branch '{branch}'), "
              f"merged SHA: {json_resp.get('merge_commit_sha')}")
    else:
        print(f"❌  Failed to sync fork {owner}/{repo_name}. "
              f"Status: {resp.status_code} {resp.text}")

def step_sync_forks(repos, excluded):
    print("\n=== STEP 1: SYNC FORKS ===")
    for repo in repos:
        full_name = f"{repo['owner']['login']}/{repo['name']}"
        if full_name in excluded:
            print(f"Skipping fork sync for {full_name} (excluded).")
            continue

        if repo["fork"]:
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            default_branch = repo["default_branch"]  # e.g. main, master, etc.
            parent_html_url = repo["parent"]["html_url"] if "parent" in repo else None

            print(f"Repo {owner}/{repo_name} is a fork of {parent_html_url}. "
                  f"Syncing default branch '{default_branch}'...")
            sync_fork(owner, repo_name, default_branch)
        else:
            print(f"Repo {full_name} is not a fork. Skipping fork sync.")

# ================== STEP 2: ENABLE DEPENDABOT SECURITY UPDATES ================== #

def enable_vulnerability_alerts(owner, repo_name):
    url = f"{BASE_URL}/repos/{owner}/{repo_name}/vulnerability-alerts"
    resp = requests.put(url, headers=HEADERS)
    if resp.status_code == 204:
        print(f"✔️  Enabled vulnerability alerts on {owner}/{repo_name}")
    else:
        print(f"❌  Failed to enable vulnerability alerts on {owner}/{repo_name}. "
              f"{resp.status_code} {resp.text}")

def enable_automated_security_fixes(owner, repo_name):
    url = f"{BASE_URL}/repos/{owner}/{repo_name}/automated-security-fixes"
    resp = requests.put(url, headers=HEADERS)
    if resp.status_code == 204:
        print(f"✔️  Enabled automated security fixes on {owner}/{repo_name}")
    else:
        print(f"❌  Failed to enable automated security fixes on {owner}/{repo_name}. "
              f"{resp.status_code} {resp.text}")

def step_enable_dependabot_security_updates(repos, excluded):
    print("\n=== STEP 2: ENABLE DEPENDABOT SECURITY UPDATES ===")
    for repo in repos:
        full_name = f"{repo['owner']['login']}/{repo['name']}"
        if full_name in excluded:
            print(f"Skipping Dependabot setup for {full_name} (excluded).")
            continue

        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        print(f"\n[Enabling Dependabot for] {owner}/{repo_name}")

        enable_vulnerability_alerts(owner, repo_name)
        enable_automated_security_fixes(owner, repo_name)

# ================== STEP 3: MERGE DEPENDABOT PRs ================== #

def get_open_prs(owner, repo):
    all_prs = []
    page = 1
    while True:
        url = f"{BASE_URL}/repos/{owner}/{repo}/pulls"
        params = {
            "state": "open",
            "sort": "created",
            "direction": "asc",
            "per_page": 100,
            "page": page
        }
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        page_data = resp.json()
        if not page_data:
            break
        all_prs.extend(page_data)
        page += 1
    return all_prs

def get_pr_details(owner, repo, pr_number):
    url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def get_check_runs(owner, repo, commit_sha):
    url = f"{BASE_URL}/repos/{owner}/{repo}/commits/{commit_sha}/check-runs"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("check_runs", [])

def wait_for_mergeability(owner, repo, pr_number, timeout=TIMEOUT_SECONDS, poll_interval=POLL_INTERVAL_SECONDS):
    """
    Poll until the PR is mergeable (mergeable_state == 'clean')
    or we detect failing checks or time out.
    Returns True if mergeable, False if failing or timed out.
    """
    start_time = time.time()
    while True:
        pr_data = get_pr_details(owner, repo, pr_number)
        mergeable_state = pr_data["mergeable_state"]
        head_sha = pr_data["head"]["sha"]

        # Check for failing checks
        failing_runs = [
            run for run in get_check_runs(owner, repo, head_sha)
            if run["conclusion"] in ["failure", "timed_out"]
        ]
        if failing_runs:
            print(f"❌  PR #{pr_number} has failing checks. Skipping.")
            return False

        if mergeable_state == "clean":
            print(f"✔️  PR #{pr_number} is mergeable (clean).")
            return True

        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"⏱️  Timed out waiting for PR #{pr_number} to become 'clean'. State was '{mergeable_state}'.")
            return False

        print(f"⏳  Waiting for PR #{pr_number}... (mergeable_state='{mergeable_state}')")
        time.sleep(poll_interval)

def merge_pr(owner, repo, pr_number, pr_title):
    """
    If COUNT_MERGES_AS_PERSONAL_COMMITS = True:
      - Do a squash merge,
      - Add a 'Co-authored-by' line with MY_NAME and MY_EMAIL.
    Otherwise:
      - Use MERGE_METHOD (e.g., 'merge', 'rebase', or 'squash') with no special co-author line.
    """
    if COUNT_MERGES_AS_PERSONAL_COMMITS:
        # We'll do a SQUASH MERGE with a co-author line
        final_method = "squash"
        co_author_line = f"Co-authored-by: {MY_NAME} <{MY_EMAIL}>"
        commit_title = f"Squash Merge: {pr_title}"
        commit_message = f"This merges Dependabot changes.\n\n{co_author_line}"
    else:
        final_method = MERGE_METHOD
        commit_title = pr_title
        commit_message = "Merging Dependabot changes."

    merge_url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
    data = {
        "merge_method": final_method,
        "commit_title": commit_title,
        "commit_message": commit_message
    }
    resp = requests.put(merge_url, headers=HEADERS, json=data)
    if resp.status_code == 200:
        merge_info = resp.json()
        if merge_info.get("merged"):
            print(f"✔️  Successfully merged PR #{pr_number} via {final_method} merge.")
        else:
            print(f"❌  API responded but did not merge PR #{pr_number}: {merge_info}")
    else:
        print(f"❌  Merge API call failed for PR #{pr_number}: {resp.status_code} {resp.text}")

def step_merge_dependabot_prs(repos, excluded):
    print("\n=== STEP 3: MERGE DEPENDABOT PRs ===")
    for repo in repos:
        full_name = f"{repo['owner']['login']}/{repo['name']}"
        if full_name in excluded:
            print(f"Skipping Dependabot merges for {full_name} (excluded).")
            continue

        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        print(f"\n[Checking Dependabot PRs in] {full_name}")

        open_prs = get_open_prs(owner, repo_name)
        dependabot_prs = [pr for pr in open_prs if pr["user"]["login"] == "dependabot[bot]"]

        if not dependabot_prs:
            print("No open Dependabot PRs.")
            continue

        for pr in dependabot_prs:
            pr_number = pr["number"]
            pr_title = pr["title"]
            print(f"\n=> Found Dependabot PR #{pr_number}: {pr_title}")

            can_merge = wait_for_mergeability(owner, repo_name, pr_number)
            if can_merge:
                merge_pr(owner, repo_name, pr_number, pr_title)
            else:
                print(f"Skipping PR #{pr_number} due to failing checks or timeout.")

# ================== MAIN ================== #

def main():
    print("=== STARTING SCRIPT ===")
    
    # 1) Load the exclusion list
    excluded_repos = load_excluded_repos(EXCLUDED_REPOS_FILE)
    if excluded_repos:
        print("Excluding these repos:")
        for er in excluded_repos:
            print(f"  - {er}")

    # 2) List Repos
    repos = list_repos()
    print(f"\nFound {len(repos)} repos with push access (USER_MODE={USER_MODE}).")

    # 3) Step 1: Sync Forks
    if ENABLE_STEP_SYNC_FORKS:
        step_sync_forks(repos, excluded_repos)

    # 4) Step 2: Enable Dependabot Security Updates
    if ENABLE_STEP_ENABLE_DEPENDABOT:
        step_enable_dependabot_security_updates(repos, excluded_repos)

    # 5) Step 3: Merge Dependabot PRs
    if ENABLE_STEP_MERGE_DEPENDABOT_PRS:
        step_merge_dependabot_prs(repos, excluded_repos)

    print("=== ALL STEPS COMPLETED ===")

if __name__ == "__main__":
    main()
