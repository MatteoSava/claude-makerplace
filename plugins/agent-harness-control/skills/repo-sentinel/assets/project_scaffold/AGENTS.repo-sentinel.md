# Repo Sentinel operating rules

Repo Sentinel is active in this repository. Follow these rules before finishing work:

- Do not modify `.repo-sentinel/`, `.codex/`, `.claude/`, `.agents/`, secret-like files, generated folders, or existing migration files unless the user explicitly authorizes that change.
- Do not run destructive commands such as `git reset --hard`, `git clean -fdx`, `terraform apply/destroy`, `kubectl delete`, `docker system prune`, or `curl | sh`.
- After changing code, run at least one targeted verification command such as `python -m pytest`, `npm test`, `go test ./...`, `cargo test`, or `python .repo-sentinel/repo_sentinel.py check --record`.
- Summarize exactly which checks ran and their result.

Local command:

```bash
python .repo-sentinel/repo_sentinel.py status
```
