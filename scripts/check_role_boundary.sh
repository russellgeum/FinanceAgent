#!/usr/bin/env bash

set -euo pipefail


usage() {
    cat <<'EOF'
Usage:
  scripts/check_role_boundary.sh <gemini|claude> [--scope all|staged|unstaged]

Description:
  Validate changed files against role boundaries defined in AGENTS.md.

Scopes:
  all       Check staged + unstaged + untracked files (default)
  staged    Check staged changes only
  unstaged  Check unstaged changes + untracked files

Examples:
  scripts/check_role_boundary.sh gemini
  scripts/check_role_boundary.sh claude --scope staged
EOF
}


print_allowed_rules() {
    local role="$1"
    if [[ "$role" == "gemini" ]]; then
        cat <<'EOF'
Allowed paths for gemini:
  - docs/**
  - README.md
  - AGENTS.md
EOF
        return
    fi

    cat <<'EOF'
Allowed paths for claude:
  - src/**
  - main.py
  - requirements.txt
  - tests/**
EOF
}


is_allowed_for_role() {
    local role="$1"
    local file_path="$2"

    if [[ "$role" == "gemini" ]]; then
        case "$file_path" in
            docs/*|README.md|AGENTS.md)
                return 0
                ;;
        esac
        return 1
    fi

    case "$file_path" in
        src/*|main.py|requirements.txt|tests/*)
            return 0
            ;;
    esac
    return 1
}


collect_changed_files() {
    local scope="$1"
    local temp_file="$2"

    if [[ "$scope" == "all" || "$scope" == "staged" ]]; then
        git diff --cached --name-only -z >> "$temp_file"
    fi

    if [[ "$scope" == "all" || "$scope" == "unstaged" ]]; then
        git diff --name-only -z >> "$temp_file"
        git ls-files --others --exclude-standard -z >> "$temp_file"
    fi
}


main() {
    local role="${1:-}"
    local scope="all"

    if [[ "$role" == "-h" || "$role" == "--help" ]]; then
        usage
        exit 0
    fi

    if [[ -z "$role" ]]; then
        usage
        exit 2
    fi

    if [[ "$role" != "gemini" && "$role" != "claude" ]]; then
        echo "Invalid role: $role"
        usage
        exit 2
    fi

    shift || true

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --scope)
                if [[ $# -lt 2 ]]; then
                    echo "Missing value for --scope"
                    usage
                    exit 2
                fi
                scope="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 2
                ;;
        esac
    done

    if [[ "$scope" != "all" && "$scope" != "staged" && "$scope" != "unstaged" ]]; then
        echo "Invalid scope: $scope"
        usage
        exit 2
    fi

    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "This command must run inside a git repository."
        exit 2
    fi

    local temp_file
    temp_file="$(mktemp)"
    trap 'rm -f "$temp_file"' EXIT

    collect_changed_files "$scope" "$temp_file"

    declare -a changed_files=()

    while IFS= read -r -d '' file_path; do
        local already_seen="0"
        local existing_path

        if [[ -z "$file_path" ]]; then
            continue
        fi

        if [[ "${#changed_files[@]}" -gt 0 ]]; then
            for existing_path in "${changed_files[@]}"; do
                if [[ "$existing_path" == "$file_path" ]]; then
                    already_seen="1"
                    break
                fi
            done
        fi

        if [[ "$already_seen" == "1" ]]; then
            continue
        fi

        changed_files+=("$file_path")
    done < "$temp_file"

    if [[ "${#changed_files[@]}" -eq 0 ]]; then
        echo "No changed files found (scope: $scope)."
        exit 0
    fi

    declare -a violations=()
    local path
    for path in "${changed_files[@]}"; do
        if ! is_allowed_for_role "$role" "$path"; then
            violations+=("$path")
        fi
    done

    if [[ "${#violations[@]}" -eq 0 ]]; then
        echo "Boundary check passed for role='$role' (scope: $scope)."
        echo "Checked files:"
        for path in "${changed_files[@]}"; do
            echo "  - $path"
        done
        exit 0
    fi

    echo "Boundary check failed for role='$role' (scope: $scope)."
    print_allowed_rules "$role"
    echo "Violation files:"
    for path in "${violations[@]}"; do
        echo "  - $path"
    done
    exit 1
}


main "$@"
