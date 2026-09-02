#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

script_path="$(readlink -f "${BASH_SOURCE[0]}")"
script_dir="$(cd "$(dirname "${script_path}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
script_name="$(basename "${BASH_SOURCE[0]}")"

usage() {
    cat <<EOF
Show commits and paths that belong to this downstream fork.

Usage: ${script_name} [<upstream-ref> [<downstream-ref>]]

Defaults:
  upstream-ref    upstream/main
  downstream-ref  HEAD
EOF
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi
if (( $# > 2 )); then
    usage >&2
    die "Expected at most two git refs."
fi

upstream_ref="${1:-upstream/main}"
downstream_ref="${2:-HEAD}"

resolve_commit() {
    local ref="$1"

    git -C "${repo_root}" rev-parse --verify --quiet "${ref}^{commit}" ||
        die "Git ref does not resolve to a commit: ${ref}"
}

upstream_sha="$(resolve_commit "${upstream_ref}")"
downstream_sha="$(resolve_commit "${downstream_ref}")"
if ! merge_base="$(
    git -C "${repo_root}" merge-base "${upstream_sha}" "${downstream_sha}"
)"; then
    die "The selected refs have no common ancestor."
fi

commit_count="$(
    git -C "${repo_root}" rev-list --count "${upstream_sha}..${downstream_sha}"
)"
path_count="$(
    git -C "${repo_root}" diff --name-only "${merge_base}..${downstream_sha}" -- |
        awk 'END { print NR + 0 }'
)"

printf 'Upstream ref: %s (%s)\n' \
    "${upstream_ref}" "$(git -C "${repo_root}" rev-parse --short=12 "${upstream_sha}")"
printf 'Downstream ref: %s (%s)\n' \
    "${downstream_ref}" "$(git -C "${repo_root}" rev-parse --short=12 "${downstream_sha}")"
printf 'Shared base: %s\n' \
    "$(git -C "${repo_root}" rev-parse --short=12 "${merge_base}")"
printf 'Downstream-only commits: %s\n' "${commit_count}"
printf 'Changed paths since shared base: %s\n' "${path_count}"

printf '\nDownstream-only commit list:\n'
if (( commit_count == 0 )); then
    printf '(none)\n'
else
    git -C "${repo_root}" log --format='%h %s' \
        "${upstream_sha}..${downstream_sha}"
fi

printf '\nChanged path list:\n'
if (( path_count == 0 )); then
    printf '(none)\n'
else
    git -C "${repo_root}" diff --name-status \
        "${merge_base}..${downstream_sha}" --
fi
