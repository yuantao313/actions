# Review before consumer migration

## Completed scope

A new `yuantao313/actions` repository contains 11 shared stages covering platform API
operations, model execution and general CI operations. Names, code paths,
environment variables and default endpoints in this repository use AtomGit.

Existing `ascend-catlass/actions` files, workflows, schedules, references and secrets
were not renamed, removed or redirected during this pass. The new CI is independent
and uses fixtures rather than service credentials. No existing Issue or PR was
commented on during organization of the new repository.

## Intentionally left in the original project

- CATLASS DSL dev/IR/Lit/wheel/device-battery test stages and build commands.
- Header-dependency selection, example/test-group mapping and DSL/non-DSL classification.
- CATLASS requirement exclusions and runner/image/version choices.
- CATLASS wheel naming/version derivation, bundle validation and PyPI publishing policy.
- Exact project release/tag checks, organization mirror destinations and deploy keys.
- Project schedules, NPU runner labels and version-baseline orchestration.
- The live project Issue-reply workflow, its configured model and trigger/publication policy.

The general mechanics underneath these operations were extracted where they have
independent inputs; their project-specific composition remains in the original repo.

## Internal staging

Four hardware stages and their related tests are retained outside this public
repository. They have not been published or migrated.

## Awaiting owner confirmation

1. Review this catalog and determine the first full commit SHA to pin.
2. Confirm which existing workflows should switch to which shared stage interfaces.
3. Confirm old-repository AtomGit name/domain and secret-name conversions as a separate change.
4. Confirm service credentials and worker provisioning for consumer integration tests.
5. Decide whether to publish a stable major tag after successful integration.

No consumer PR, deletion, redirect or automatic production integration is part of
this pass. The owner explicitly requested review before those actions.

## Provenance

The starting inventory came from `ascend-catlass/actions` at commit
`42ee26c`, with platform APIs generalized to required repository inputs and toolchain
operations kept separate from project test/build policies. Hardware-specific
components are excluded from this public repository.

AtomGit v5 endpoint selection follows the owner's upstream migration confirmation
and the [official Chinese OpenAPI documentation](https://docs.atomgit.com/docs/apis/).
The new API domain was additionally verified by a read-only request. Old consumer
routes stay untouched until the owner confirms their conversion.
