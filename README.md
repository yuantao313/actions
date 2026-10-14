# yuantao313/actions

Reusable AtomGit, TRAE CN and general CI stages. This repository contains shared
building blocks, not a project-specific workflow suite.

This is a new-repository organization and review pass. Existing workflows in
`ascend-catlass/actions` are retained and have not been redirected here. Consumer
migration requires the owner's confirmation.

## Catalog

| Area | Stages |
| --- | --- |
| AtomGit | `atomgit-api`, `atomgit-pr-metadata`, `atomgit-checkout-pr`, `atomgit-pr-status`, `atomgit-issue-context`, `atomgit-issue-comment`, `atomgit-release` |
| Model execution | `setup-traecn`, `traecn` |
| General CI | `install-python-requirements`, `trust-checkout` |

The [catalog](docs/CATALOG.md) describes boundaries, prerequisites and outputs.
The [review and migration plan](docs/MIGRATION.md) lists the components deliberately
left in the original project and the decisions still awaiting confirmation.

All runtime platform names, environment variables and routes use **AtomGit**,
`ATOMGIT_TOKEN`, `https://atomgit.com`, and `https://api.atomgit.com/api/v5`.
The API root is supported by [AtomGit's official OpenAPI documentation](https://docs.atomgit.com/docs/apis/).
A read-only check against the new API domain succeeded during preparation.

## Direct TRAE CN execution

`traecn/action.yml` calls the official CLI directly. It has no Python wrapper,
external execution script or third-party proxy. The inline Bash handles validation,
stdin prompts, temporary authentication, timeout, output files and cleanup.
Those responsibilities cannot be expressed as a command invocation alone.

```yaml
permissions:
  contents: read
jobs:
  analyze:
    runs-on: ubuntu-22.04
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - id: cli
        uses: yuantao313/actions/setup-traecn@main
      - id: agent
        uses: yuantao313/actions/traecn@main
        with:
          pat: ${{ secrets.TRAE_CN_PAT }}
          cli-path: ${{ steps.cli.outputs.cli-path }}
          expected-version: ${{ steps.cli.outputs.version }}
          model: DeepSeek-V4.1-Flash
          prompt-file: .github/prompts/task.md
          sandbox: read-only
      - if: ${{ always() && steps.agent.outputs.result-directory != '' }}
        uses: actions/upload-artifact@v4
        with:
          name: analysis
          path: ${{ steps.agent.outputs.result-directory }}
          retention-days: 7
```

Production consumers should pin a reviewed full commit SHA. Review is currently
pending; no stable major tag or automatic consumer migration has been created.
The CLI needs Linux, Bash, jq, GNU coreutils/timeout, Git and the sandbox dependencies
required by its installed version (including bubblewrap on the supported Linux setup).
Use disposable model workers without other host credentials. CLI sandbox settings
are not a replacement for worker isolation.

The PAT is used only during login; the execution child does not inherit caller
tokens. Authentication lives in a per-run HOME/XDG directory and is cleaned on exit.
Literal PAT occurrences are redacted in published result files; this does not cover
encoded credentials or arbitrary project data. Login logs are never exported.
Only successful results should be consumed. Hard runner termination can interrupt
cleanup, so reused workers need their own retention policy.

## Composing Issue stages

Compose context, model execution and publication as separate steps. The context
stage is repository-independent and records an exact source SHA. The publication
stage checks that the Issue and discussion did not change, only updates its own
marker-bearing comment, and verifies the final body by GET. A caller must serialize
runs for each Issue to prevent concurrent first-time comments.

Model attribution is optional. When supplied, the raw id is appended exactly as
`<sub>By model-id</sub>`. There is no fixed provider/model restriction. The shipped
prompt follows the author's language and uses polite, natural prose without generic
baseline disclaimers. Callers can provide their own trusted prompt file.

There is no live Issue-reply workflow in this repository. Examples belong to the
caller, which supplies its events, permissions, secrets, concurrency and review policy.

## Validation

The new repository CI runs transport and business-operation tests with fake service
responses, a fake CLI executing the actual inline Bash, and isolated checkout tests.
It does not use enterprise credentials, publish comments or upload releases.
Consumer rollout remains subject to owner confirmation.

This public repository contains 11 general stages. Hardware and vendor-specific
components remain in internal staging and the original repository.
