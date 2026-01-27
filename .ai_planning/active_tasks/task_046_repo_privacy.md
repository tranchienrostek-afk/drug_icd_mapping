# Task 046: Switch Repository to Private & Update Authentication

**Status**: ⏸️ PENDING
**Priority**: Medium
**Created**: 2026-01-27

## Context
User plans to switch the GitHub repository `drug_icd_mapping` from **Public** to **Private**.
Current CI/CD pipeline runs on **Self-hosted runners** (Production Server). The deployment workflow uses manual `git pull` commands which may fail without proper credentials for a private repository.

## Objective
Ensure Dev, Staging, and Production environments continue to function (pull/push code) seamlessly after the repository becomes private.

## Pre-Flight Checks
1. [ ] Check current git remote configuration on servers:
   ```bash
   cd /root/workspace/drug_icd_mapping
   git remote -v
   ```

## Implementation Plan

### 1. Fix Server Authentication (Staging & Prod)
The `git pull origin main` command in `deploy.yml` runs on the server. For a private repo, it needs credentials.

**Option A: SSH Keys (Recommended)**
- [ ] Generate SSH Key on server: `ssh-keygen -t ed25519`
- [ ] Add public key to GitHub Repo **Deploy Keys**.
- [ ] Switch remote to SSH:
  ```bash
  git remote set-url origin git@github.com:tranchienrostek-afk/drug_icd_mapping.git
  ```

**Option B: Personal Access Token (PAT)**
- [ ] Generate PAT with `repo` scope.
- [ ] Configure credential helper on server:
  ```bash
  git config --global credential.helper store
  git pull # Enter PAT as password once
  ```

### 2. Verify CI/CD
- [ ] Self-hosted runner uses `GITHUB_TOKEN` for `actions/checkout`.
- [ ] Verify if manual `git pull` steps in `run` scripts utilize the token or rely on system git config.
  - *Note*: If using SSH, `git pull` will work fine.
  - *Note*: `actions/checkout` ensures the workspace is clean, but our script does a `pull` inside the persistent folder `/root/workspace/...`. This specific folder's git config is what matters.

## Validation
- [ ] Switch repo to Private.
- [ ] Run manual `git pull` on server to verify access.
- [ ] Trigger CI/CD pipeline and ensure it passes.
