# Repo Sentinel operating rules

Repo Sentinel hooks guard this repository. Treat hook feedback as mandatory unless the user explicitly authorizes a policy change.

Before ending a task that changed code or infrastructure files, run a targeted verification command and cite the command/result in your final response.

Useful commands:

```bash
python .repo-sentinel/repo_sentinel.py status
python .repo-sentinel/repo_sentinel.py check --record
```
