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

import typer
import subprocess

import ollama

from rich import print
from rich.console import Console
from rich.panel import Panel


app = typer.Typer(
    help="AI powered tool to lint commit messages."
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
    """Extracts the first markdown code block from a string.

    Returns the markdown code as a string.
    """
    pattern = r"```markdown\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def get_head_commit(repo_dir: str) -> str:
    """Obtain head commit message from a git repo.

    Args:
        repo_dir (str): Location to git repo.

    Returns:
        str: head commit message
    """
    cmd = f'cd "{repo_dir}" && git show HEAD --name-only'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                            check=True)
    return result.stdout.strip()


def extract_text_block(text: str) -> str:
    """Extracts the first markdown code block from a string.

    Args:
        text (str): gets a text block

    Returns:
        str: Returns the markdown code as a string.
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
    """Fail if repo_dir doesn't exist or .git is not there".

    Args:
        repo_dir (str): location of repo.
    """

    if repo_dir is None:
        sys.exit("ERROR: You must specify a repo directory.")

    if not os.path.exists(repo_dir):
        sys.exit(f"ERROR: \"{repo_dir}\" does not exist.")

    if not os.path.exists(os.path.join(repo_dir, ".git")):
        sys.exit("ERROR: This is not a git repo!")


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


def print_linter_output(results: str, repo: str):
    """Format and render the LLM output with structured styling."""

    results = results.strip()

    # Smart verdict detection (customize if needed)
    if "LINT_FAIL" in results:
        verdict_style = "bold red"
        verdict_text = "❌ Commit message needs revision."
    else:
        verdict_style = "bold green"
        verdict_text = "✅ Commit message passed all lint checks."

    # Main output panel
    console.print(Panel.fit(
        results,
        title=f"Lint Output for \"{repo}\"",
        subtitle="Powered by LLM",
        style="green"
    ))

    # Verdict summary
    console.print()
    console.print(Panel(verdict_text, title="Verdict", style=verdict_style))


@app.command()
def lint_head_commit_message(
    repo_dir: str = typer.Option(None, "--repo-dir", "-r",
                                 help="Location of where the repo is cloned."),
    rules_filepath: str = typer.Option("rules.txt", "--rules-file", "-f",
                                       help="Location of where your rules"
                                            "reside as a txt file"),
    output: str = typer.Option(None, "--output", "-o",
                               help="Location of where to save"
                                    "llm powered output to a text file."),
    model: str = typer.Option("llama3", "--model", "-m", help="Name of model.")
                             ):
    """Uses LLM to lint HEAD commit message."""

    owner, repo = get_owner_and_repo_from_git_config(repo_dir)
    head_commit = get_head_commit(repo_dir)

    print("")
    console.print(
                  Panel.fit(f"{head_commit}",
                            title=f"Head Commit for \"{repo}\"",
                            subtitle="This commit will be reviewed",
                            style="cyan")
                 )
    print("")
    prompt = f"""
You are an expert in Git commit message standards. Act as a strict linter.

The commit_message is:
{head_commit}
"""
    rules = read_text(rules_filepath)

    prompt += f"""
REQUIREMENTS
{rules}

Give a verdict in the form "LINT_FAIL | LINT_PASS" . The verdict should be the
final line. E.g. 'Verdict: LINT_FAIL'. Talk in the third person.
Be professional.
"""

    # AI an hallucinate and act unpredictably so try multiple times.
    no_of_attempts = 3
    for x in range(no_of_attempts):
        results = send_prompt_to_LLM(prompt, model)

        if results.strip():

            break

    print()
    print_linter_output(results, repo)

    if output is not None:
        with open(output, 'a+',  encoding='utf-8') as f:
            f.write(results.strip() + "\n\n")

    console.print("[bold yellow]WARNING: Please double-check since"
                  " LLMs can still make mistakes.[/]")


if __name__ == "__main__":
    app()
