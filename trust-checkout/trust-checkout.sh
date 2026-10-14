#!/usr/bin/env bash
set -euo pipefail

checkout="$(cd "${1:?Checkout path required}" && pwd -P)"
declare -A visited=()

trust_tree() {
    local tree=$1 entries status=0 entry path submodule
    [[ -z "${visited[${tree}]:-}" ]] || return 0
    visited[${tree}]=1
    if ! git config --global --get-all safe.directory | grep -Fx -- "${tree}" > /dev/null; then
        git config --global --add safe.directory "${tree}"
    fi
    echo "Trusted Git directory: ${tree}"
    [[ -f "${tree}/.gitmodules" ]] || return 0
    entries=$(mktemp)
    git config --null --file "${tree}/.gitmodules" \
        --get-regexp '^submodule\..*\.path$' > "${entries}" || status=$?
    if [[ ${status} -gt 1 ]]; then
        rm -f -- "${entries}"
        echo "Cannot read submodule paths in ${tree}" >&2
        return "${status}"
    fi
    while IFS= read -r -d '' entry; do
        path=${entry#*$'\n'}
        submodule=$(realpath -m -- "${tree}/${path}")
        # Do not grant trust outside this task's mounted checkout.
        if [[ -z "${path}" || "${path}" == /* || "${submodule}" != "${checkout}/"* ]]; then
            rm -f -- "${entries}"
            echo "Submodule path escapes the checkout: ${path}" >&2
            return 1
        fi
        # Register even absent submodules, before git submodule update runs.
        trust_tree "${submodule}" || { rm -f -- "${entries}"; return 1; }
    done < "${entries}"
    rm -f -- "${entries}"
}

trust_tree "${checkout}"
