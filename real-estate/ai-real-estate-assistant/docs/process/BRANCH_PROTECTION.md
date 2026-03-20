# Branch Protection & Required Checks (V4)

## Overview
Protect `main` and `dev` with required status checks to ensure quality gates before merge.

## Required Checks
- Backend CI: ruff, mypy, unit diff coverage (≥90), integration diff coverage (≥70), unit critical coverage (≥90)
- Frontend CI: eslint, jest tests + coverage (thresholds in `jest.config.ts`)
- Security CI: Bandit (fail on high severity, high confidence)

## GitHub Settings
1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Require status checks to pass before merging:
   - `backend` job
   - `frontend` job
   - `security` job
4. Enable “Require branches to be up to date”
5. Enable “Include administrators”
6. Enable “Block force pushes”
7. Enable “Restrict deletions”
8. Repeat for `dev`

## Notes
- Temporary thresholds are documented in [DEVELOPER_NOTES.md](../development/DEVELOPER_NOTES.md); raise to targets as tests improve.
- Avoid storing secrets in code; CI jobs must not echo secret values.
