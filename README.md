# repo-standards-review consumer kit

A [cookiecutter](https://cookiecutter.readthedocs.io/) template that repositories
in the RSR ecosystem adopt, and later update, with [cruft](https://cruft.github.io/cruft/).
Each RSR release publishes it, with that release's manifest, to the public
template-only repository
[`svelderrainruiz/repo-standards-review-consumer-kit`](https://github.com/svelderrainruiz/repo-standards-review-consumer-kit),
tagged with the release (`vX.Y.Z`). Use that repository as the cruft template
(no `--directory`). Each consumer then:

- pins one RSR release in `.repo-standards-review.json`: the tag, the full
  commit, and the digest-pinned assurance-workbench image;
- checks out its executable scripts with LF line endings on every platform,
  through a generated `.gitattributes`. This includes Windows with
  `core.autocrlf=true`, as in cookiecutter-django #7063;
- runs `.repo-standards-review/check_consumer.py` in CI. The check needs only
  Python 3.9+ and Git, so it also runs on fork pull requests, which can't pull
  the private workbench image. It fails on a script that isn't LF-pinned and on
  an `exempt_paths` file (listed in `.repo-standards-review/kit.json`) that a
  later rule turns back into text. It also fails when the pin differs from the
  release manifest published for its tag, or from the kit release recorded in
  `.cruft.json`. It resolves attributes only from tracked
  `.gitattributes` files, so `.git/info/attributes` and system or global
  attribute files make no difference, as in the RSR evidence scanner.

The template contains no standards text.

## Answers

| Answer | Meaning |
| --- | --- |
| `repo_name` | The consumer's name. The baked output directory is its slug, for example `sandboxsbomreporting`. |
| `forge` | `github` writes `.github/workflows/repo-standards-review.yml`; `gitlab` writes `.gitlab/repo-standards-review.gitlab-ci.yml` for an `include: [{local: ...}]`. The GitLab job ignores the consumer's `default:` block (`inherit: default: false`), so a default `before_script` for another toolchain doesn't run in its Python image. |
| `github_runs_on` | Comma-separated runner labels for the GitHub job, for example `self-hosted, linux`. |
| `default_branches` | Comma-separated branches whose pushes run the check. Merge and pull requests always run it. |
| `gitlab_stage` | Stage for the GitLab job. It must be one of the consumer's `stages:`, or GitLab refuses to create the pipeline. mprr, for example, uses `verify`. |
| `script_dirs` | Comma-separated directories whose files check out with `text=auto eol=lf`. Binary files in them are left alone. |
| `lf_paths` | Extra `.gitattributes` patterns that check out with LF, such as a single extensionless script. |
| `exempt_paths` | Byte-provenance patterns that keep their exact bytes (`-text`). They come last among the kit's rules, and the consumer check fails if a rule added after them overrides one. |
| `rsr_tag`, `rsr_commit`, `workbench_image` | **Owned by the release.** The defaults are empty, and baking fails until they are supplied from the RSR release manifest. |

The kit always pins `*.sh`, the top-level hook directories (`.githooks`,
`githooks`, `git-hooks`, `.husky`), and its own files:
`.repo-standards-review.json`, `.cruft.json`, and the `.repo-standards-review/`
directory. They are repository metadata, so keep them out of product packages
such as a VSIX, a wheel, or an image. labview-benchmark-actor, for example,
lists them in `.vscodeignore`. The pre-generation hook refuses unsafe answers before writing
anything: parent, absolute, `.git`, space- or newline-containing paths, injected
runner labels or stages, and unknown forges.

Answers and release manifests are trusted inputs: cookiecutter renders them with Jinja before the hook checks them.

## Release-owned values

Never store release values as ordinary answers. cruft freezes answers in
`.cruft.json`, so an update would keep the old pin while `cruft check` still
reports "up to date". Take them from the release manifest,
`manifests/vX.Y.Z.json` in the public repository, on every bake or update:

```bash
tag=v0.4.0
cruft update --skip-apply-ask --checkout "$tag" --variables-to-update "$(
  curl -fsSL "https://raw.githubusercontent.com/svelderrainruiz/repo-standards-review-consumer-kit/refs/tags/$tag/manifests/$tag.json" |
  python3 -c 'import json, sys; m = json.load(sys.stdin); print(json.dumps({k: m[k] for k in ("rsr_tag", "rsr_commit", "workbench_image")}))'
)"
```

Don't save the manifest inside the project first: cruft refuses to update a
working tree that has untracked files.

Use `--variables-to-update` with a flat JSON object. `--variables-to-update-file`
expects the nested `.cruft.json` shape, and with a flat file it silently changes
nothing.

The template refuses missing or malformed release values, but it can't tell a
stale value from a current one: cruft never tells a template which release it is
being updated to. The consumer check catches both ways a pin can go stale:

- **Linkage, offline:** `.cruft.json` records the kit release the consumer is on
  (`checkout`), and it must equal the pin's `rsr_tag`. An update without the new
  values moves the kit but not the pin, so this check fails.
- **Manifest, online by default:** the pin must equal the manifest published for
  its tag. A tag that was never released, or a commit or image digest changed by
  hand, fails. If the manifest can't be fetched, the check reports UNKNOWN
  (exit 2). `--offline` skips only this comparison.

## Updating a repository adopted at v0.4.0

The v0.4.0 kit block had no closing line, so in a repository whose own rules
follow the block, the update that introduces the closing line cannot apply
cleanly, although cruft still reports success. Check `git status` after that
update. Depending on the repository's history, you will see one of two outcomes:

- **A `.gitattributes.rej` file.** Add its lines by hand, then delete the `.rej` file.
- **Conflict markers in `.gitattributes`, shown as `UU` in `git status`.** Remove
  the markers and keep both sides. Don't run `git add -A` while markers are present.

Either way, the kit's new last line(s), ending with
`# End of the repo-standards-review consumer-kit rules.`, go directly after the
kit's previous last rule and above the repository's own rules. Then run the
consumer check. Later updates apply cleanly.

## Adopting the kit in an existing repository

`cruft link` records the linkage but brings in no files, and `cruft diff` skips
files that a project doesn't have. So adopt the kit by baking it once and copying
the result, `.cruft.json` included:

```bash
cruft create https://github.com/svelderrainruiz/repo-standards-review-consumer-kit --checkout <tag> \
  --no-input --output-dir /tmp/kit \
  --extra-context '{"repo_name": "<name>", "forge": "github", "script_dirs": "scripts", "rsr_tag": "...", "rsr_commit": "...", "workbench_image": "..."}'
cp -r /tmp/kit/*/. <repository>/
```

Then, in this order:

1. Move any rules from the repository's previous `.gitattributes` below the kit's
   closing line (`# End of the repo-standards-review consumer-kit rules.`). cruft
   keeps them through later updates. A broad rule such as
   `* text=auto eol=lf` placed there overrides the kit's `-text` exemptions:
   scope it, or repeat the exemptions after it.
2. Run `git add -A` so the new kit files are tracked; the check reads only
   tracked files.
3. Run `python3 .repo-standards-review/check_consumer.py` and fix everything it
   reports **before** renormalizing. If it names a script, add that script's
   directory or path to the answers. If it names an exempt file, fix the rule
   that overrides the exemption. Otherwise renormalizing would rewrite that
   file's bytes.
4. Run `git add --renormalize .`, then commit. `--renormalize` re-adds only
   files that are already tracked, which is why step 2 comes first.

## Validation

These paths are in the RSR source repository, where the kit is maintained under
`templates/consumer/`.

`scripts/eval_consumer_template.py` (TEST-159) publishes the kit to a local
repository the way the release pipeline does, checks pins against a local
manifest server, and bakes the kit for
labview-benchmark-actor, projectbuddy, vi-history-suite, mprr, and
SandboxSBOMReporting, and exercises cruft creation, drift detection, update, and
adoption. It runs in the `validate-consumer-template` CI job, and in
`validate-skill-windows` with the Windows runner's `core.autocrlf=true`. To run it
locally:

```bash
python3 -m pip install --require-hashes --no-deps -r templates/consumer/bake-requirements.txt
python3 scripts/eval_consumer_template.py
```

To change the tool versions, edit `bake-requirements.in` and regenerate the lock
with
`uv pip compile --universal --generate-hashes --python-version 3.11 --no-header templates/consumer/bake-requirements.in -o templates/consumer/bake-requirements.txt`.
