import os
import requests
import openai

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("GITHUB_REF").split("/")[-1]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
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
        code_changes[file["filename"]] = file["patch"]
    return code_changes

# Step 3: Send Code Diff to OpenAI API (or Copilot API)
def review_code_with_ai(code_changes):
    review_comments = {}
    for filename, diff in code_changes.items():
        prompt = f"Review the following code changes and suggest improvements:\n{diff}"
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": prompt}],
        )
        review_comments[filename] = response["choices"][0]["message"]["content"]
    return review_comments

# Step 4: Post Review Comments on PR
def post_review_comments(review_comments):
    for filename, comment in review_comments.items():
        url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{PR_NUMBER}/comments"
        data = {
            "body": f"### AI Code Review:\n{comment}",
            "commit_id": os.getenv("GITHUB_SHA"),
            "path": filename,
            "position": 1,  # Adjust position for inline comments
        }
        requests.post(url, headers=HEADERS, json=data)

# Execute Code Review
if __name__ == "__main__":
    code_changes = get_code_diff()
    review_comments = review_code_with_ai(code_changes)
    post_review_comments(review_comments)
