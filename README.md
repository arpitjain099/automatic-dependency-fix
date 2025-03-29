# Secure-Cred Dependabot Manager

🔒 Secure your repos. 💪 Build your GitHub street cred.

A **Python script** and **GitHub Actions workflow** that helps automate:

- 🔄 Syncing forks of repositories (so your fork is always up-to-date with upstream).
- 🛡️ Enabling Dependabot security updates (vulnerability alerts + automated security fixes).
- ✅ Merging open Dependabot PRs (with optional co-authoring so your contribution graph gets the love it deserves).

No secrets or personal data are hardcoded — all configuration is driven by environment variables, so you can keep the repo public and your GitHub tokens safe in Secrets.

Start patching smarter. Get the credit you deserve.

> **Pro Tip:**
> By actively merging Dependabot PRs (especially with the co-author option), you not only keep your projects secure and up-to-date but also build your GitHub contribution graph. This can boost your "street cred" as an active, proactive developer!

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Contribution Benefits](#contribution-benefits)
- [Usage - Locally](#usage---locally)
- [Usage - GitHub Actions](#usage---github-actions)
  - [1) Provide Your Token](#1-provide-your-token)
  - [2) Configure the Workflow](#2-configure-the-workflow)
  - [3) Trigger the Workflow](#3-trigger-the-workflow)
- [Environment Variables](#environment-variables)
- [Excluded and Included Repositories](#excluded-and-included-repositories)
- [Running in an Organization Context](#running-in-an-organization-context)
- [Caution and Best Practices](#caution-and-best-practices)
- [License](#license)

---

## Features

- **Fork Sync**  
  Keeps your forked repositories in sync with their upstream by calling GitHub’s `POST /repos/{owner}/{repo}/merge-upstream` API.

- **Dependabot Security**  
  Automates enabling both vulnerability alerts and automated security fixes on your repositories.

- **Auto-Merging Dependabot PRs**  
  Checks if they’re mergeable and merges them. If you enable `COUNT_MERGES_AS_PERSONAL_COMMITS`, it does a squash merge with a co-author line so you can see them in your GitHub contributions graph.

- **Environment-Driven**  
  No hardcoded secrets; toggles and settings (like `USER_MODE`, `MY_NAME`, `MY_EMAIL`) come from environment variables so your credentials remain safe in GitHub Actions Secrets.

---

## Prerequisites

1. A **Personal Access Token** (PAT) or **Fine-grained PAT** with sufficient scopes:
   - **`repo`** scope (or `public_repo` if only targeting public repositories).  
   - **`security_events`** scope if you want to enable vulnerability alerts and automated security fixes.  
   - Possibly **`workflow`** scope if your forks have workflow files.  
2. **Python 3** installed.  
3. The **`requests`** Python library (`pip install requests`).

---

## Contribution Benefits

By actively merging Dependabot PRs using this tool, you not only keep your dependencies secure and your repositories up-to-date but also:

Increase your GitHub contribution count: When you use the COUNT_MERGES_AS_PERSONAL_COMMITS feature, your co-authored squash merge appears in your contribution graph.

Showcase your proactive maintenance skills: Regularly updating dependencies is a sign of an active and responsible developer.

Earn "street cred": Being seen as someone who actively maintains and secures projects can boost your reputation within the developer community.

---

## Usage - Locally

1. **Clone** or **download** this repository.  
2. **Install** Python dependencies:
   ```bash
   pip install --upgrade pip
   pip install requests
  ```
3. Export environment variables in your terminal:
  ```
  export MY_GITHUB_TOKEN="ghp_your_personal_access_token"
  export MY_NAME="Your Name"
  export MY_EMAIL="your_verified_email@users.noreply.github.com"
  export USER_MODE="true"             # "true" for personal user repos, "false" for org
  export ORG_NAME="someOrganization"  # only used if USER_MODE="false"
  export ENABLE_STEP_SYNC_FORKS="true"
  export ENABLE_STEP_ENABLE_DEPENDABOT="true"
  export ENABLE_STEP_MERGE_DEPENDABOT_PRS="true"
  export TIMEOUT_SECONDS="30"
  export POLL_INTERVAL_SECONDS="10"
  export MERGE_METHOD="merge"
  export COUNT_MERGES_AS_PERSONAL_COMMITS="true"
  ```
(Optional) Create an inclusion file (included_repos.txt) in the repository root with one "owner/repo" per line to whitelist repositories. If this file exists and is non-empty, only the listed repositories will be processed.

(Optional) Create an exclusion file (excluded_repos.txt) in the repository root with one "owner/repo" per line to skip certain repositories.

4. Run the script:
  ```bash
  python dependency-fix.py
  ```
5. The script will:

- **List repositories** you can push to
- **Sync forks** if enabled
- **Enable Dependabot vulnerability alerts** & automated fixes
- **Merge Dependabot PRs** (if checks pass and the step is enabled)

## Usage - GitHub Actions

### 1) Provide Your Token

1. In your repository, go to **Settings > Security > Secrets and variables > Actions**.  
2. Create a **New repository secret** named `MY_GITHUB_TOKEN` containing your PAT.  
   - Ensure it has `repo` (and `security_events` if you want vulnerability alerts) scopes.  
   - If you’re enabling workflow file changes in a fork, you might need `workflow` scope too.

### 2) Configure the Workflow

We provide a sample workflow in [`.github/workflows/dependency-manager.yml`](.github/workflows/dependency-manager.yml). It:

- Supports **manual** runs (`workflow_dispatch`) with user-provided inputs.  
- Runs on a **weekly schedule** using `cron`.  
- Checks out your code, sets up Python, installs `requests`, then runs `python dependency-fix.py`.  
- Passes environment variables (like your name/email, `USER_MODE`, etc.) from either default values or from workflow inputs.

### 3) Trigger the Workflow

- **Manual**: Go to the **Actions** tab, select **Dependabot Manager**, and click **Run workflow**.  
  - Fill in optional inputs (`USER_MODE`, `ORG_NAME`, `MY_NAME`, etc.).  
- **Scheduled**: The workflow runs automatically at the time specified in `on.schedule:`.

---

## Environment Variables

| **Variable**                       | **Description**                                                                                 | **Default**                   |
|-----------------------------------|-----------------------------------------------------------------------------------------------|--------------------------------|
| `MY_GITHUB_TOKEN`                 | **Required**. PAT with `repo` (and optionally `security_events`, `workflow`).                 | _(none)_                       |
| `MY_NAME`                         | Your name for co-author lines in merges.                                                      | `""` (empty)                   |
| `MY_EMAIL`                        | Your verified GitHub email for co-author lines.                                               | `""` (empty)                   |
| `USER_MODE`                       | `"true"` to manage personal user repos, `"false"` for org repos.                              | `"true"`                       |
| `ORG_NAME`                        | Organization name if `USER_MODE=false`.                                                       | `""`                           |
| `EXCLUDED_REPOS_FILE`            | Path to a file listing repos to exclude.                                                      | `"excluded_repos.txt"`         |
| `ENABLE_STEP_SYNC_FORKS`         | `"true"` or `"false"`: run the fork-sync step or not.                                         | `"true"`                       |
| `ENABLE_STEP_ENABLE_DEPENDABOT`   | `"true"` or `"false"`: enable Dependabot security or not.                                     | `"true"`                       |
| `ENABLE_STEP_MERGE_DEPENDABOT_PRS`| `"true"` or `"false"`: merge Dependabot PRs or not.                                           | `"true"`                       |
| `TIMEOUT_SECONDS`                 | Seconds to wait for PR checks to pass.                                                        | `"30"`                         |
| `POLL_INTERVAL_SECONDS`           | How often (in seconds) to poll for PR checks.                                                 | `"10"`                         |
| `MERGE_METHOD`                    | `"merge"`, `"rebase"`, or `"squash"` if not using co-author logic.                            | `"merge"`                      |
| `COUNT_MERGES_AS_PERSONAL_COMMITS`| `"true"` → do a squash merge with a co-author line. `"false"` → use `MERGE_METHOD`.           | `"true"`                       |

---

## Excluded Repositories

## Excluded and Included Repositories

- **Excluded Repositories:**  
  If you create a file named `excluded_repos.txt` in the same directory as `dependency-fix.py`, the script will skip any repositories listed inside it. Each line should contain `owner/repo`. Lines that are empty or start with `#` are ignored.

  **Example `excluded_repos.txt`:**
  ```text
  myuser/old-fork
  someorg/secret-internal-repo
  ```
- **Included Repositories:**
  Optionally, you can also create a file named included_repos.txt. If this file exists and is non-empty, the script will only process repositories whose owner/repo names appear in this file. This provides a whitelist, ensuring that only explicitly trusted repositories are updated.

  **Example `included_repos.txt`:**
  ```text
  myuser/trusted-repo
  someorg/critical-project
  ```

---

## Running in an Organization Context

If you set `USER_MODE="false"`, the script targets an organization’s repositories via the endpoint `/orgs/{ORG_NAME}/repos`. Additional points:

1. **Fine-grained Access Tokens**: If using a fine-grained PAT, ensure you give the token access to all relevant repos and the `contents`, `pull requests`, `security events` permissions.  
2. **SAML/SSO**: If your org enforces SAML single sign-on, your token must be authorized under SAML for the script to successfully manage repos.  
3. **Org-Level Settings**: Some orgs restrict certain actions (e.g., merging PRs, enabling vulnerability alerts) to owners or specific roles. Confirm your user can do these actions.  
4. **`ORG_NAME`**: Provide the exact organization slug (e.g., `"github"`, `"microsoft"`, etc.).

---

## Caution and Best Practices

**WARNING:**  
Automatically merging dependency updates can sometimes lead to unexpected issues or break your project functionality. Not all dependency updates are safe to merge automatically—some updates might require manual testing, further review, or specific integration adjustments.

**Best Practices:**
- **Review Changes:** Always review the changes that Dependabot proposes before merging.
- **Use an Exclusion List:** It is highly recommended to maintain an `excluded_repos.txt` file with a list of repositories where automatic updates should be disabled (e.g., legacy projects, production-critical systems, or repos with complex dependency management).
- **Test Thoroughly:** Consider running dependency updates in a staging environment before applying them to your main branches.

---

## License

**Licensed under the Apache License, Version 2.0** (the "License");  
you may not use this file except in compliance with the License.

You may obtain a copy of the License at  
[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software  
distributed under the License is distributed on an “AS IS” BASIS,  
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  

See the [LICENSE](LICENSE) file for the full text of the license.
