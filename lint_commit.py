# MIT License

# Copyright (c) 2025 Mujaheed Khan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import configparser
import json
import os
import re
import sys
from pathlib import Path

import requests
import typer
import shlex
import subprocess

import ollama

from rich import print
from rich.console import Console
from rich.panel import Panel


app = typer.Typer(
    help="AI powered tool to review and enhance READMEs for better"
         " communication."
)

console = Console()


def read_text(filepath):
    """Given a filepath, returns contents of file.

    Args:
        filepath (str): Path to file to read.

    Returns:
        str: Contents of file.
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def get_git_config(repo_dir):
    """Returns content of .git/config from repo.

    Args:
        repo_dir (str): location of repo.

    Returns:
        str: contents of repo.
    """

    return read_text(os.path.join(repo_dir, ".git", "config"))


def send_prompt_to_LLM(prompt: str, model: str = "llama3") -> str:
    """Sends prompt to specified LLM and returns output.

    Args:
        prompt (str): Block of text containg prompt.
        model (str, optional): Name of model. Defaults to "llama3".

    Returns:
        str: response from LLM.
    """

    with console.status("[bold green]Analyzing your commit message with LLM...[/]"):
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
    return response['message']['content']


def extract_json_block(text: str) -> dict:
    """Extracts last JSON code block from a string and returns it as a dict."""

    pattern = r"```json\s*({.*?})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if not match:
        raise ValueError("No valid JSON block found in the input.")

    json_str = match.group(1)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON content: {e}")


def get_real_path(filepath: str) -> str:
    """Return real path from a given path

    Args:
        filepath (str): Path to file.

    Returns:
        str: Real filepath.
    """
    return str(Path(filepath).resolve())


def extract_markdown_block(text: str) -> str:
    """
    Extracts the first markdown code block from a string.

    Returns the markdown code as a string.
    """
    pattern = r"```markdown\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def get_head_commit(repo_dir: str) -> str:
    cmd = f'cd "{repo_dir}" && git show HEAD --name-only'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                            check=True)
    return result.stdout.strip()

def extract_text_block(text: str) -> str:
    """
    Extracts the first markdown code block from a string.

    Returns the markdown code as a string.
    """
    pattern = r"```text\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_changes_made_block(text: str) -> list:
    """Extracts changes made by the LLM as a list.

    Args:
        text (str): output from LLM.

    Returns:
        bool: True if match found otherwise false.
        list: Changes made by LLM.
    """

    pattern = r"```json\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    if len(matches) == 0:
        return False, []
    block = matches[-1].strip() if matches else ""

    data = json.loads(block)

    return True, data['changes_made']


def validate_setup(repo_dir):
    """Fail if repo_dir doesn't exist or README.md is not there".

    Args:
        repo_dir (str): location of repo.
    """

    if repo_dir is None:
        sys.exit("ERROR: You must specify a repo directory.")

    if not os.path.exists(repo_dir):
        sys.exit(f"ERROR: \"{repo_dir}\" does not exist.")

    if not os.path.exists(os.path.join(repo_dir, "README.md")):
        sys.exit("ERROR: Please ensure there is a README.md in your repo.")


def get_owner_and_repo_from_git_config(repo_dir):
    """Returns 'owner' and 'repo_name' from git repo directory

    Args:
        repo_dir (str): location of repo.

    Returns:
        owner(str): name of owner. 'None' if not found.
        repo(str): name of repo. 'None' if not found.
    """

    config_path = os.path.join(repo_dir, ".git", "config")
    if not os.path.exists(config_path):
        print(f"*** ERROR: File not found: {config_path}")
        return None, None

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        url = config['remote "origin"']['url']
    except KeyError:
        print("Could not find 'origin' remote in git config.")
        return None, None

    # Match both HTTPS and SSH GitHub URLs
    match = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/([^.]+)(\.git)?", url)
    if match:
        owner, repo = match.group(1), match.group(2)
        return owner, repo
    else:
        print("Could not parse GitHub owner/repo from URL.")
        return None, None
    
@app.command()
def lint_head_commit_mesasge(
    repo_dir: str = typer.Option(None, "--repo-dir", "-r",
                                 help="Location of where the repo is cloned."),
    output: str = typer.Option("output_readme.md", "--output", "-o",
                               help="Location of where to save"
                                    " formula file."),
    model: str = typer.Option("llama3", "--model", "-m", help="Name of model.")
                             ):
    """Uses LLM to generate an improved README file."""

    git_config_info = get_git_config(repo_dir)
    owner, repo = get_owner_and_repo_from_git_config(repo_dir)
    head_commit = get_head_commit(repo_dir)

    print("We are working on:")
    print(head_commit)
    print("")

    prompt = f"""
You are an expert in Git commit message standards. Act as a strict linter and helpful coach.

The commit_message is:
{head_commit}
"""

    prompt += """
REQUIREMENTS
1) Title (first line) MUST be strictly < 54 characters (i.e., max 53).
2) Body MUST include BOTH metadata lines (case-insensitive detection; normalize in fix):
   - "Code Review: <number>"
   - "PR: <number>" (accept "Pull Request: <number>" as equivalent, but normalize to "PR: <number>")
3) If a number is missing or unknown, use "<please_fill_in>" (do NOT invent).
4) Ensure exactly one blank line between title and body in the fixed message.
5) Preserve meaning; you MAY tighten wording, fix grammar, and prefer imperative mood for the title.
6) Detect PR via lines starting with "PR:" or "Pull Request:"; detect Code Review via lines starting with "Code Review:" (all case-insensitive; ignore surrounding whitespace).
7) Do not output anything except a single JSON object (no code fences, no extra prose).


OUTPUT FORMAT (single s object only)
\{
  "verdict": "pass" | "fail",
  "title_length": <integer>,
  "title_status": "ok" | "too_long",
  "has_pr": <true|false>,
  "has_code_review": <true|false>,

  "suggestions": [
    "Actionable bullet #1",
    "Actionable bullet #2"
  ],

  "fixed_message": \{
    "title": "<rewritten concise, imperative title (≤53 chars)>",
    "body": "<rewritten body (no metadata lines), preserving meaning>",
    "code_review": "<number or <please_fill_in>>",
    "pr": "<number or <please_fill_in>>",
    "full_text": "Title\n\nBody\nCode Review: <...>\nPR: <...>"
  \}
}

EVALUATION STEPS (for you to follow before emitting JSON)
- Parse title as the first non-empty line. Count characters exactly (no trimming for count).
- Check for a blank line after the title in the original; enforce exactly one in the fixed message.
- Search the body for PR and Code Review lines as specified (case-insensitive).
- When normalizing, always output:
  Code Review: <value>
  PR: <value>
- If no body exists, synthesize a minimal one-sentence rationale (why), then append the two metadata lines.


"""

    # AI an hallucinate and act unpredictably so try multiple times.
    no_of_attempts = 3
    for x in range(no_of_attempts):
        results = send_prompt_to_LLM(prompt, model)
        print(results)
        break

    print()
    console.print("[bold yellow]WARNING: Please double-check since"
                  " LLMs can make still make mistakes.[/]")
if __name__ == "__main__":
    app()
