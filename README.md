# NaturalCommitLint
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Typer](https://img.shields.io/badge/CLI-Typer-blueviolet)
![Rich](https://img.shields.io/badge/UI-Rich-forestgreen)
![Ollama](https://img.shields.io/badge/LLM-Ollama-yellowgreen)
![License](https://img.shields.io/badge/License-MIT-brightgreen)
![Status](https://img.shields.io/badge/Linting-AI--Powered-success)


A commit linter that uses natural language rules enforced by an LLM.

Unlike regex-based linters, it’s customizable without code and can plug directly into CI/CD pipelines.

## Demo

![Demo GIF](demo.gif)

## Overview

Tool that enforces consistent and high-quality Git commit messages using a locally running LLM. It reads the HEAD commit, applies a set of user-defined rules, and provides a verdict: `LINT_PASS` or `LINT_FAIL`.

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
git clone git@github.com:mujasoft/NaturalCommitLint.git
cd NaturalCommitLint
pip3 install -r requirements.txt
# You can simply add to your path afterwards or call from this location
```

## Usage

```bash
 Usage: NaturalCommitLint.py [OPTIONS]

 Uses LLM to lint HEAD commit message.


╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --repo-dir            -r      TEXT  Location of where the repo is cloned. [default: None]                                                          │
│ --rules-file          -f      TEXT  Location of where your rulesreside as a txt file [default: rules.txt]                                          │
│ --output              -o      TEXT  Location of where to savellm powered output to a text file. [default: None]                                    │
│ --model               -m      TEXT  Name of model. [default: llama3]                                                                               │
│ --install-completion                Install completion for the current shell.                                                                      │
│ --show-completion                   Show completion for the current shell, to copy it or customize the installation.                               │
│ --help                              Show this message and exit.                                                                                    │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


```

### Arguments

| Option            | Description                                       |
|-------------------|---------------------------------------------------|
| `--repo-dir`, `-r`    | Path to your local Git repository                 |
| `--rules-file`, `-f`   | Path to a text file containing linting rules      |
| `--model`, `-m`        | Name of the Ollama model to use (default: llama3) |
| `--output`, `-o`        | Optional path to save the linter output to a file |


## Example Rules File

Below is an example `rules.txt`

```text
1) Title (first line) MUST be strictly < 54 characters (i.e., max 53).
2) Body MUST include BOTH metadata lines (case-insensitive detection; normalize in fix):
   - "Code Review: <number>"
   - "PR: <number>" (accept "Pull Request: <number>" as equivalent, but normalize to "PR: <number>")
3) If a number is missing or unknown, use "<please_fill_in>" (do NOT invent).

```

You can customize this file to match the standards of any repository.

The name of the file is not hardcoded. You can keep multiple different text files containing rules.
## Sample Output

```
./NaturalCommitLint.py -r ~/Desktop/development/go -f rules_go.txt

╭────────────────────────────────── Head Commit for "go" ───────────────────────────────────╮
│ cmd/go/internal/work: copy vet tool's stdout to our stdout                                │
│                                                                                           │
│ The go command connects both the stdout and stderr files of                               │
│ its child commands (cmd/compile, cmd/vet, etc) to the go                                  │
│ command's own stderr. If the child command is supposed to                                 │
│ produce structure output on stderr, as is the case for                                    │
│ go vet -json or go fix -diff, it will be merged with the                                  │
│ error stream, making it useless.                                                          │
│                                                                                           │
│ This change to the go vet <-> unitchecker protocol specifies                              │
│ the name of a file into which the vet tool should write its                               │
│ stdout. On success, the go command will then copy the entire                              │
│ content of that file to its own stdout, under a lock.                                     │
│ This ensures that partial writes to stdout in case of failure,                            │
│ concurrent writes to stdout by parallel vet tasks, or other                               │
│ junk on stderr, cannot interfere with the integrity of the                                │
│ go command's structure output on stdout.                                                  │
│                                                                                           │
│ CL 702835 is the corresponding change on the x/tools side.                                │
│                                                                                           │
│ For #75432                                                                                │
│                                                                                           │
│ Change-Id: Ib4db25b6b0095d359152d7543bd9bf692551bbfa                                      │
│ Reviewed-on: https://go-review.googlesource.com/c/go/+/702815                             │
│ LUCI-TryBot-Result: Go LUCI <golang-scoped@luci-project-accounts.iam.gserviceaccount.com> │
│ Reviewed-by: Michael Matloob <matloob@google.com>                                         │
│ Auto-Submit: Alan Donovan <adonovan@google.com>                                           │
╰───────────────────────────────────────────────────────────────────────────────────────────╯


╭─────────────────────────────────────────────────────────────── Lint Output for "go" ───────────────────────────────────────────────────────────────╮
│ **Title Analysis**                                                                                                                                 │
│ The subject starts with "cmd/go/internal/work:" followed by a space, which is correct according to the requirement.                                │
│                                                                                                                                                    │
│ **Body Analysis**                                                                                                                                  │
│ The body explains why the change was made and what problem it fixes. It also provides relevant details about the changes and includes references   │
│ (CL 702835). The body is well-structured and easy to understand.                                                                                   │
│                                                                                                                                                    │
│ **Rule Compliance Summary**                                                                                                                        │
│                                                                                                                                                    │
│ * **Subject**: PASS                                                                                                                                │
│         + Starts with package name: cmd/go/internal/work:                                                                                          │
│         + Uses lowercase verb after colon: copy                                                                                                    │
│         + No trailing period at the end of subject line                                                                                            │
│         + Short enough (~76 characters or less)                                                                                                    │
│ * **Body**: PASS                                                                                                                                   │
│         + Separate subject from body by a blank line                                                                                               │
│         + Body lines are wrapped at ~76 characters                                                                                                 │
│         + Explains why the change was made and what problem it fixes                                                                               │
│ * **Footer/References**: PASS                                                                                                                      │
│         + Includes CL 702835 reference                                                                                                             │
│ * **General Style**: PASS                                                                                                                          │
│         + Does not use Signed-off-by lines                                                                                                         │
│         + Avoids alternate aliases (e.g., "Close")                                                                                                 │
│ * **Summary-Length Formatting**: PASS                                                                                                              │
│         + Subject is short enough (~76 characters or less)                                                                                         │
│         + Body lines are wrapped at ~76 characters                                                                                                 │
│                                                                                                                                                    │
│ **Verdict: LINT_PASS**                                                                                                                             │
╰────────────────────────────────────────────────────────────────── Powered by LLM ──────────────────────────────────────────────────────────────────╯

╭───────────────────────────────────────────────────────────────────── Verdict ──────────────────────────────────────────────────────────────────────╮
│ ✅ Commit message passed all lint checks.                                                                                                          │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
WARNING: Please double-check since LLMs can still make mistakes.
```

## Development Notes

This tool uses Typer for command-line interface, Rich for styled output, and Ollama to run local LLM inference. The linting prompt is dynamically constructed using the latest commit message and the contents of your `rules.txt`.

The verdict is extracted from the LLM output and must contain either `LINT_PASS` or `LINT_FAIL` for correct display.


## To-do
- Lint n commits
- Lint a specific commit
- Add automated testing

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Pull requests and issues are welcome.
