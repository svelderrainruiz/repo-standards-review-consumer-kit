"""Refuse unsafe or incomplete answers before the consumer kit is generated."""

import json
import re
import sys

# Rendered as a JSON string literal so no answer can change this hook's code.
ANSWERS = json.loads({{ cookiecutter | tojson | tojson }})

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
DIRECTORY = re.compile(r"[A-Za-z0-9._][A-Za-z0-9._/-]{0,199}")
PATTERN = re.compile(r"[A-Za-z0-9._*][A-Za-z0-9._*/-]{0,199}")
RELEASE_OWNED = {
    "rsr_tag": re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+"),
    "rsr_commit": re.compile(r"[0-9a-f]{40}"),
    "workbench_image": re.compile(r"[a-z0-9.-]+(?::[0-9]+)?/[a-z0-9._/-]+@sha256:[0-9a-f]{64}"),
}


def entries(name):
    value = ANSWERS.get(name)
    if not isinstance(value, str):
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def path_errors(name, pattern):
    items = entries(name)
    if items is None:
        return [f"{name} must be a comma-separated string"]
    errors = []
    for item in items:
        segments = item.split("/")
        if (
            pattern.fullmatch(item) is None
            or item.endswith("/")
            or "" in segments
            or any(segment in (".", "..", ".git") for segment in segments)
        ):
            errors.append(f"{name}: unsafe path {item!r}")
    return errors


def main():
    errors = []
    # Private template settings name output paths, so they must keep the template's own values.
    if ANSWERS.get("_gitattributes") != ".gitattributes" \
            or ANSWERS.get("_copy_without_render") != [".repo-standards-review/check_consumer.py",
                                                ".repo-standards-review/observations.py",
                                                ".repo-standards-review/wiki_generate.py"] \
            or not isinstance(ANSWERS.get("__kit_dir"), str) \
            or re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", ANSWERS["__kit_dir"]) is None:
        errors.append("the template's private settings were overridden")
    if not isinstance(ANSWERS.get("repo_name"), str) or NAME.fullmatch(ANSWERS["repo_name"]) is None \
            or ANSWERS["repo_name"] in (".", ".."):
        errors.append(f"repo_name is not a safe directory name: {ANSWERS.get('repo_name')!r}")
    if ANSWERS.get("forge") not in ("github", "gitlab"):
        errors.append(f"forge must be github or gitlab: {ANSWERS.get('forge')!r}")
    for name, pattern in (("github_runs_on", LABEL), ("default_branches", BRANCH)):
        items = entries(name)
        if not items or any(pattern.fullmatch(item) is None or ".." in item for item in items):
            errors.append(f"{name} needs one or more safe comma-separated values: {ANSWERS.get(name)!r}")
    if not isinstance(ANSWERS.get("gitlab_stage"), str) or LABEL.fullmatch(ANSWERS["gitlab_stage"]) is None:
        errors.append(f"gitlab_stage is not a safe stage name: {ANSWERS.get('gitlab_stage')!r}")
    errors += path_errors("script_dirs", DIRECTORY)
    errors += path_errors("lf_paths", PATTERN)
    errors += path_errors("exempt_paths", PATTERN)
    for name, pattern in RELEASE_OWNED.items():
        value = ANSWERS.get(name)
        if value == "":
            errors.append(
                f"{name} is empty: release-owned values come from the RSR release manifest "
                "(cruft update --variables-to-update), never from stored answers"
            )
        elif not isinstance(value, str) or pattern.fullmatch(value) is None:
            errors.append(f"{name} is not a valid release value: {value!r}")
    if errors:
        for error in errors:
            sys.stderr.write(f"consumer kit: {error}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
