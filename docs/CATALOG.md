# Shared stage catalog

All actions use `runs.using: composite` and work when loaded remotely: helper paths
resolve from `GITHUB_ACTION_PATH`, not from the caller's repository. Generic AtomGit
helpers live in `_lib`; TRAE CN runs directly from its YAML.

| Stage | Inputs and behavior | Main outputs |
| --- | --- | --- |
| `atomgit-api` | token, HTTP method, fixed-root path, optional body file and form/JSON encoding; supports empty mutation responses | response-file |
| `atomgit-pr-metadata` | repository and open PR number; validates branch refs and exact head SHA | base-ref, head-ref, head-sha |
| `atomgit-checkout-pr` | repository, PR number, validated base ref/head SHA, fresh workspace path; merges into the target actually fetched; conflicts fail | worktree, base-sha, head-sha |
| `atomgit-pr-status` | repository, PR number, start/finish, result, run URL; optional labels, comment body file and existing comment id; publishes comments as JSON | comment-id |
| `atomgit-issue-context` | Issue URL and source directory; optionally supplied trusted prompt; clones public source if absent, paginates discussion | worktree, prompt-file, context-file, source-sha |
| `atomgit-issue-comment` | context snapshot, UTF-8 body and optional raw model id; rejects stale context, owns one reply and GET-verifies it | comment-id, comment-url, result-file |
| `atomgit-release` | repository, tag, optional title/body file and JSON array of asset paths; no wheel or package assumptions | release-url, tag |
| `setup-traecn` | pinned version and compressed artifact SHA-256 values; default 0.209.1 supports x86_64/aarch64; another version needs explicit hashes | cli-path, version |
| `traecn` | PAT, literal/file prompt, worktree, optional raw model/schema, sandbox and budget; no standalone execution script | result-directory, response-file, events-file, stderr-file, result-file, status, exit-code |
| `install-python-requirements` | requirements file, optional package exclusions; excludes direct requests only; pip still resolves dependencies | none |
| `trust-checkout` | contained checkout/submodule paths, using caller's Git configuration scope | none |

## Worker boundaries

The AtomGit, direct CLI and generic CI stages require a prepared Linux environment.
For private source repositories, supply a pre-checked-out source directory and keep
Git credentials under the caller's checkout policy. The public-source convenience
clones use AtomGit HTTPS URLs without adding platform tokens to clone commands.

## Changed generic interfaces

- Repository inputs are required; there is no fixed upstream project.
- The direct CLI input is `pat`, and its action directory is `traecn`.
- AtomGit Issue context and publication are separate actions; neither chooses a fixed model.
- Python requirements exclude nothing by default; project-specific exclusions are caller inputs.
- Release assets are arbitrary files; project wheel validation belongs in the caller.
