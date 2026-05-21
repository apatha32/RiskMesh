## GitHub Actions CI/CD Setup

This document describes the automated Continuous Integration and Continuous Deployment (CI/CD) workflows for RiskMesh.

### Overview

The CI/CD pipeline automatically tests, builds, and deploys RiskMesh across multiple workflows triggered by pushes and pull requests.

---

## Workflows

### 1. **Backend CI** (`.github/workflows/backend-ci.yml`)

Runs Python backend tests and quality checks on every push and pull request.

**Triggers:**
- Push to `main` or `develop` branches (app/, tests/, requirements.txt changes)
- Pull requests to `main` or `develop` branches

**What it does:**
- Sets up PostgreSQL service for integration tests
- Installs Python dependencies from `requirements.txt`
- Runs linting with **flake8**
- Runs type checking with **mypy**
- Executes all tests with **pytest** and coverage reporting
- Uploads coverage reports to Codecov
- Generates HTML coverage report as artifact

**Matrix Testing:** Python 3.11

**Requirements:**
- PostgreSQL service running
- `pytest-asyncio` for async test support

---

### 2. **Frontend CI** (`.github/workflows/frontend-ci.yml`)

Builds and tests the React/TypeScript frontend.

**Triggers:**
- Push to `main` or `develop` branches (frontend/ changes)
- Pull requests to `main` or `develop` branches

**What it does:**
- Sets up Node.js environment
- Installs npm dependencies
- Runs **TypeScript** type checking
- Runs **ESLint** linting
- Builds production bundle with **Vite**
- Uploads build artifacts for PR review

**Matrix Testing:** Node 18.x, 20.x

**Artifacts:**
- Frontend distribution builds stored for 5 days

---

### 3. **Integration Tests** (`.github/workflows/integration-tests.yml`)

Runs end-to-end integration tests with real services.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Services:**
- PostgreSQL 15
- Redis 7

**What it does:**
- Installs Python dependencies
- Runs integration test suite (`test_integration.py`)
- Runs Phase 2 integration tests (`test_phase2_integration.py`)

**Requirements:**
- Database and cache connectivity tests
- Graph propagation with real data

---

### 4. **Docker Build & Push** (`.github/workflows/docker-build.yml`)

Builds and pushes Docker images to GitHub Container Registry (GHCR).

**Triggers:**
- Push to `main` (app/, Dockerfile, requirements.txt changes)
- Pull requests to `main` (builds only, doesn't push)
- GitHub releases (published)

**What it does:**
- Sets up Docker Buildx for multi-platform builds
- Logs into GitHub Container Registry (GHCR)
- Builds Docker image from `Dockerfile`
- Pushes image with semantic versioning tags:
  - `main` → `latest`
  - `v1.0.0` release → `1.0.0`, `1.0`, `latest`
  - Commits → `sha-<commit-hash>`
- Uses layer caching for faster builds

**Image Tags:**
```
ghcr.io/yourusername/riskmesh:latest
ghcr.io/yourusername/riskmesh:main
ghcr.io/yourusername/riskmesh:sha-abc123def
ghcr.io/yourusername/riskmesh:1.0.0
```

---

### 5. **Security Checks** (`.github/workflows/security.yml`)

Scans code for security vulnerabilities.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Daily schedule at 2 AM UTC

**What it does:**
- Runs **Bandit** (Python security linter)
- Checks for known vulnerabilities with **Safety**
- Generates security report artifact
- Continues on errors for visibility (doesn't block merge)

**Reports:**
- Bandit report: `bandit-report.json`
- Safety report: stdout

---

### 6. **Deployment** (`.github/workflows/deployment.yml`)

Placeholder workflow for deployment automation.

**Triggers:**
- Push to `main` branch
- GitHub releases (published)

**Current Status:**
⚠️ **TODO:** Configure deployment targets:
- Cloud provider integration (AWS, GCP, Azure, Heroku, etc.)
- Artifact registry pushes
- Infrastructure updates
- Post-deployment health checks

---

### 7. **Dependabot** (`.github/dependabot.yml`)

Automated dependency updates for Python, JavaScript, and GitHub Actions.

**Update Schedules:**
- **Python (pip)**: Weekly on Mondays at 3 AM UTC
- **JavaScript (npm)**: Weekly on Mondays at 3 AM UTC  
- **GitHub Actions**: Monthly

**Features:**
- Automatically creates pull requests for updates
- Labels PRs for easy filtering
- Limits to 10 open PRs per ecosystem
- Assigns to `ambarishpathak` for review

---

## Setup Instructions

### 1. **Configure Container Registry Access**

For Docker image pushes to GitHub Container Registry (GHCR):

1. Go to Settings → Developer settings → Personal access tokens
2. Create a token with `write:packages` scope
3. Store as repository secret: `CONTAINER_REGISTRY_TOKEN`

**Note:** GitHub Actions uses `GITHUB_TOKEN` by default, which works with GHCR.

### 2. **Configure Codecov (Optional)**

For coverage report uploads:

1. Visit [codecov.io](https://codecov.io)
2. Connect your GitHub repository
3. Coverage reports will automatically upload from CI

### 3. **Update Repository Settings**

In GitHub repository settings:

- **Branch Protection Rules** (for `main`):
  - Require status checks to pass: ✅ Backend CI, ✅ Frontend CI, ✅ Integration Tests
  - Require code review: 1 approval
  - Dismiss stale reviews
  - Require branches to be up to date

### 4. **Configure Deployment** (Optional)

Edit `.github/workflows/deployment.yml` to add:
- Cloud platform credentials
- Deployment targets
- Health check endpoints
- Rollback strategies

---

## Monitoring & Badges

### Add Status Badges to README

```markdown
![Backend CI](https://github.com/YOUR-ORG/RiskMesh/actions/workflows/backend-ci.yml/badge.svg)
![Frontend CI](https://github.com/YOUR-ORG/RiskMesh/actions/workflows/frontend-ci.yml/badge.svg)
![Docker Build](https://github.com/YOUR-ORG/RiskMesh/actions/workflows/docker-build.yml/badge.svg)
```

### View Workflow Status

1. Go to repository → **Actions** tab
2. Click any workflow to see:
   - Status and logs
   - Step-by-step execution
   - Artifact downloads
   - Test results

---

## Key Features

✅ **Automated Testing**
- Unit tests on every commit
- Integration tests with real services
- Coverage tracking with Codecov

✅ **Code Quality**
- Linting (flake8, ESLint)
- Type checking (mypy, TypeScript)
- Security scanning (Bandit, Safety)

✅ **Docker Automation**
- Automated image builds
- Semantic versioning
- Layer caching for speed
- Multi-platform support ready

✅ **Dependency Management**
- Automated dependency updates
- Security vulnerability scanning
- Scheduled update checks

✅ **CI/CD Best Practices**
- Fail fast on quality issues
- Clear test failure reporting
- Artifact retention policies
- Caching for speed

---

## Troubleshooting

### Tests Failing in CI but Passing Locally?

**Common issues:**
1. **Database connection**: CI uses `postgresql://riskmesh:testpass@localhost:5432/riskmesh_test`
2. **Redis connection**: CI uses `redis://localhost:6379`
3. **Python version**: CI uses Python 3.11
4. **Working directory**: Frontend tests use `./frontend` directory

**Solution:** Check environment variables in workflow files match your local setup.

### Docker Push Failing?

1. Verify `GITHUB_TOKEN` has `write:packages` scope
2. Check repository visibility (must be public for GHCR)
3. Review GitHub Actions logs for authentication errors

### Codecov Not Showing Coverage?

1. Ensure repository is connected to codecov.io
2. Check that coverage.xml is being generated
3. Wait 5-10 minutes for Codecov to process reports

---

## Next Steps

1. **Push to GitHub** and trigger first CI run
2. **Monitor Actions** tab for any failures
3. **Configure branch protection** with required checks
4. **Set up deployment** targets in deployment.yml
5. **Add status badges** to README.md
6. **Review Dependabot PRs** for security updates

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot)
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
