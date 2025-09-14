# llmlinter

AI-powered commit message linter with customizable rules.

Built using Python, Typer, Rich, and Ollama (local LLMs).

## Demo

![Demo GIF](demo.gif)

## Overview

`llmlinter` enforces consistent and high-quality Git commit messages using a locally running LLM. It reads the HEAD commit, applies a set of user-defined rules, and provides a verdict: `LINT_PASS` or `LINT_FAIL`.

The LLM is instructed to include one of these tokens in its final response, which is then parsed by the tool.

At the moment, this tool only analyzes the HEAD.

This tool is designed for use in both local development and CI pipelines.

## Why was this made?
A lot of tools exist to lint commits but I wondered what would happen if we allowed a LLM to lint the commit for us? One big advantage is that the LLM takes care of analyzing how to detect linting violations which makes it very extensible across different codebases.

## Features

- Lints the latest Git commit (HEAD)
- Uses local LLMs via [Ollama](https://ollama.com)
- Supports customizable rules defined in a plain text file
- Provides human-readable CLI output using Rich
- Writes results to a file if needed

## Installation

Requirements:

- Python 3.8 or higher
- [Ollama](https://ollama.com) installed and running locally

Clone the repository and install dependencies:

```bash
git clone https://github.com/mujasoft/llmlinter.git
cd llmlinter
pip install -r requirements.txt
```

## Usage

```bash
llmlinter lint-head-commit-message   --repo-dir /path/to/git/repo   --rules-file rules.txt   --model llama3   --output lint_results.txt
```

### Arguments

| Option            | Description                                       |
|-------------------|---------------------------------------------------|
| `--repo-dir`      | Path to your local Git repository                 |
| `--rules-file`    | Path to a text file containing linting rules      |
| `--model`         | Name of the Ollama model to use (default: llama3) |
| `--output`        | Optional path to save the linter output to a file |


## Example Rules File

Below is an example `rules.txt` based on the Go project's commit message guidelines:

```text
1) Title (first line) MUST be strictly < 54 characters (i.e., max 53).
2) Body MUST include BOTH metadata lines (case-insensitive detection; normalize in fix):
   - "Code Review: <number>"
   - "PR: <number>" (accept "Pull Request: <number>" as equivalent, but normalize to "PR: <number>")
3) If a number is missing or unknown, use "<please_fill_in>" (do NOT invent).

```

You can customize this file to match the standards of any repository.


## Sample Output

```
Head Commit for "mujasoft/llmlinter"
-------------------------------------

net/http: handle timeout propagation in roundtripper

- Title starts with a package prefix
- Title is under 54 characters
- Missing "PR: <number>" metadata line

Verdict: LINT_FAIL
```

## Development Notes

This tool uses Typer for command-line interface, Rich for styled output, and Ollama to run local LLM inference. The linting prompt is dynamically constructed using the latest commit message and the contents of your `rules.txt`.

The verdict is extracted from the LLM output and must contain either `LINT_PASS` or `LINT_FAIL` for correct display.


## FUTURE WORK
- Lint n commits
- Lint a specific commit


## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Pull requests and issues are welcome.