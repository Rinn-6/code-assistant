import os
import requests
import openai

# Load environment variables
GITHUB_TOKEN = os.getenv("TOKEN_GITHUB")  
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_REF = os.getenv("GITHUB_REF", "")

if "pull" in GITHUB_REF:
    PR_NUMBER = GITHUB_REF.split("/")[2]  # Extract PR number
else:
    raise ValueError("This script should only run on pull requests.")

# Headers for GitHub API
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",  # Use 'Bearer' for better authentication
    "Accept": "application/vnd.github.v3+json",
}

# Step 1: Fetch PR Files
def get_pr_files():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []

# Step 2: Extract Code Changes (Diff)
def get_code_diff():
    files = get_pr_files()
    code_changes = {}
    for file in files:
        code_changes[file["filename"]] = file.get("patch", "")  # Use `.get()` to prevent KeyErrors
    return code_changes

# Step 3: Send Code Diff to OpenAI API
def review_code_with_ai(code_changes):
    review_comments = {}
    for filename, diff in code_changes.items():
        if not diff.strip():
            continue  # Skip empty diffs
        
        prompt = f"Review the following code changes and suggest improvements:\n{diff[:4096]}"  # Limit token usage

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": prompt}],
        )

        review_comments[filename] = response["choices"][0]["message"]["content"]
    return review_comments

# Step 4: Post AI Review Comments on PR
def post_review_comments(review_comments):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{PR_NUMBER}/comments"  # General PR comment
    comment_body = "### 🤖 AI Code Review:\n"

    for filename, comment in review_comments.items():
        comment_body += f"\n#### `{filename}`\n{comment}\n"

    data = {"body": comment_body}
    response = requests.post(url, headers=HEADERS, json=data)

    if response.status_code == 201:
        print("✅ AI review comment posted!")
    else:
        print(f"❌ Failed to post comment: {response.json()}")

# Execute AI Code Review
if __name__ == "__main__":
    code_changes = get_code_diff()
    review_comments = review_code_with_ai(code_changes)
    post_review_comments(review_comments)
