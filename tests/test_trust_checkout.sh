#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$(mktemp -d)"
trap 'rm -rf -- "${fixture}"' EXIT
mkdir -p "${fixture}/checkout/third party/existing"
export GIT_CONFIG_GLOBAL="${fixture}/gitconfig"
if [[ "${OSTYPE}" == msys* || "${OSTYPE}" == cygwin* ]]; then
    # Native Windows Git converts POSIX arguments; only trust values must stay
    # literal for this Linux fixture. File arguments still need conversion.
    export REAL_TEST_GIT="$(cygpath -u "$(git --exec-path)")/../../bin/git.exe"
    export GIT_CONFIG_GLOBAL="$(cygpath -w "${GIT_CONFIG_GLOBAL}")"
    git() {
        if [[ "$*" == 'config --global --add safe.directory '* ]]; then
            MSYS2_ARG_CONV_EXCL='*' "${REAL_TEST_GIT}" "$@"
        else
            "${REAL_TEST_GIT}" "$@"
        fi
    }
    export -f git
fi
cat > "${fixture}/checkout/.gitmodules" <<'EOF'
[submodule "absent"]
    path = 3rdparty/googletest
[submodule "existing"]
    path = third party/existing
EOF
cat > "${fixture}/checkout/third party/existing/.gitmodules" <<'EOF'
[submodule "nested"]
    path = llvm-project
EOF
runner="${repo}/trust-checkout/trust-checkout.sh"
( source "${runner}" "${fixture}/checkout" )
( source "${runner}" "${fixture}/checkout" )
[[ $(git config --global --get-all safe.directory | wc -l) -eq 4 ]]
git config --global --get-all safe.directory | grep -Fxq "${fixture}/checkout/3rdparty/googletest"
printf '[submodule "escape"]\npath = ../outside\n' > "${fixture}/checkout/.gitmodules"
if ( source "${runner}" "${fixture}/checkout" ); then echo 'Escaping path accepted'; exit 1; fi
if git config --global --get-all safe.directory | grep -Fxq "${fixture}/outside"; then exit 1; fi
echo 'Absent, nested, spaced, repeated and escaping submodule path checks passed.'
