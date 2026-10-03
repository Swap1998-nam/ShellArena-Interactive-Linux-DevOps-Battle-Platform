# Bring this version into your GitHub checkout

The runnable ZIP contains the complete version 2 source without secrets, dependencies, database files, or Git history. Use a new branch when applying it to an existing checkout.

A companion Git patch is provided for the original base commit `dfbbd4f`. Save or commit any work you already have first. From your existing repository checkout:

```bash
git switch -c feat/shellarena-production-foundation
git am /path/to/ShellArena-v2.patch
```

The patch includes the new files and deletion of the obsolete `backend/Dockerfile` and `frontend/Dockerfile`. If your repository has changed since the base commit, inspect any conflict before continuing; do not overwrite newer changes blindly.

After reviewing the diff and running the checks:

```bash
git push -u origin feat/shellarena-production-foundation
```

Open a pull request and require CI before merging. No GitHub branch or pull request was published by the build workspace because authenticated GitHub access was not available.
