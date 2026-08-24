# Release notes

## 2026-08-23: uv and Python 3.14 migration

### Project and dependency management

- Migrated all 15 retained repository `pyproject.toml` files from Poetry-specific or
  mixed metadata to standard `[project]` metadata suitable for uv. The existing
  Flit metadata in `lab4/server/` was already standard and only needed the
  Python requirement update.
- Set every project to Python `>=3.14,<3.15` and removed dependency upper bounds
  so uv can select the current compatible release of each dependency.
- Replaced 14 subproject Poetry lockfiles with independently generated
  `uv.lock` files.
  `lab4/server/` is application package metadata used inside the parent lab 4
  environment, so it continues to use `lab4/uv.lock` rather than owning a
  second environment lock.
- Removed the obsolete `lab3/poetry.toml` virtual-environment configuration.
- Marked the lab and Lambda application projects as non-packages where
  appropriate and separated development dependencies into uv dependency
  groups.
- Removed the top-level `pyproject.toml`, its former `poetry.lock`, and the
  replacement top-level `uv.lock`. The root Poetry project was added after the
  course and was not required by any lab, Lambda, test, or root orchestration
  target.
- Added root `lock-all`, `sync-all`, and `update-all` orchestration for the 14
  independent project environments. The root Makefile is now purely an
  orchestrator and does not create a root virtual environment. Repository-wide
  linting enumerates the maintained projects explicitly.
- Preserved the flat `etc/e11-cli/e11/` package layout. The uv build backend is
  configured with `module-name = "e11"` and `module-root = ""`; no source-tree
  relocation is required.
- Kept the `e11` and `e11admin` console entry points and changed workstation
  installation to `uv tool install --python 3.14`.

### Makefiles, Lambda, and CI

- Converted every maintained Makefile command from `poetry install` and
  `poetry run` to locked `uv sync` and `uv run` workflows.
- Replaced the Poetry export plugin with uv's built-in `uv export`. Both Lambda
  projects export production-only, hash-free `src/requirements.txt` files for
  AWS SAM from their committed lockfiles.
- Replaced the Lambda wheel-vendoring command with `uv build --wheel`. The
  generated wheel remains named `e11.whl` inside each Lambda source tree for
  compatibility with the existing SAM package layout.
- Added `**/e11.whl` to the repository ignore rules. No vendored e11 wheel is
  tracked; build and SAM cache copies remain reproducible local artifacts.
- Changed both SAM templates to the `python3.14` runtime and build method.
- Updated GitHub Actions to provision Python 3.14 and uv 0.12.5, with uv caching
  enabled.
- Updated the Ubuntu installer for Ubuntu 26.04, Python 3.14, and the official
  uv installer.

### Documentation and repository layout

- Replaced Poetry instructions and examples with uv throughout tracked internal
  documentation and runtime guidance.
- Added a repository-layout section to the root `README.md` explaining the
  independent labs, shared symlinked application files, Linux and MEMENTO
  variants, e11/Lambda services, staff files, and root orchestration.
- Updated course, architecture, testing, security, and installation documents
  for Python 3.14 and the uv workflow.
- Reviewed both TODO files. Removed obsolete or completed scratch items from the
  root backlog, retained current course-operation and lab-installation work,
  and marked the completed tooling normalization and non-mutating Lambda lint
  work in `etc/e11-cli/doc/TODO.md`. The remaining e11 items still correspond
  to code or test behavior present in the repository.
- Removed `lab5/server/todo.js`: it was an unreferenced Python fragment stored
  with a JavaScript extension, superseded by the shared Lab 5 image-board
  implementation.

### Compatibility cleanup from current tools

- Applied current Ruff formatting and safe fixes to `lambda-home`, including
  modern Python 3.14 annotations and import ordering.
- Made Lambda linting non-mutating; `make lint` now reports drift, while the
  explicit `make format` target applies Ruff fixes and formatting.
- Corrected the repository pre-commit hook so staged filenames containing
  spaces are checked and re-staged as complete paths.
- Simplified nested conditions and context managers, removed redundant
  exception interpolation, narrowed DynamoDB cleanup exceptions, and removed an
  unused duplicated hostname-suffix constant. These changes preserve behavior
  while satisfying the current Ruff and Pylint releases.
- Reformatted the shared lab 4--6 Jinja templates with the current djLint
  release and removed a stale Lab 6 virtual-environment interpreter typo.

### Validation

- `make lock-all` completed for all 14 independent environments.
- `make sync-all` completed under CPython 3.14.6.
- Both Lambda `requirements.txt` exporters and e11 wheel-vendoring targets
  completed successfully.
- `make lint-all` passed across every listed project.
- `make check-all` passed with DynamoDB Local: 115 e11 tests, 93 lambda-home
  tests, and 6 lambda-leaderboard tests, with no failures or errors. Pyright,
  Pylint, Ruff, djLint, and both SAM template validations also passed.

### Course-content import

- Added the Lab 0--8 Markdown sources, `doc/Differences from 2025.md`, and their
  shared `doc/images/` assets to Git so the current course material is versioned
  with the implementation it documents.
- Applied narrowly scoped Ubuntu 26.04 and Python 3.14 corrections to
  `Differences from 2025.md` and Labs 1, 2, 3, and 7. The imported images were
  not modified.
- Removed the obsolete `doc/CodeHighlighter/` JavaScript highlighter and its
  configuration; the current Markdown course sources do not use it.

### Ubuntu 26.04 image follow-up

- Updated all distribution-version references, including the imported lab
  document sources, to Ubuntu 26.04 LTS. References to the `ubuntu` login user,
  `/home/ubuntu`, Ubuntu package mirrors, and GitHub's `ubuntu-latest` runner
  label remain unchanged because they are identifiers rather than OS versions.
- Updated the e11 test container base from Ubuntu 22.04 to Ubuntu 26.04.
- Replaced the remaining Python 3.12 and 3.13 references in the imported lab
  document sources with Python 3.14.
- Updated the EC2 image discovery filter to Canonical's Resolute 26.04 AMD64 GP3
  naming convention.
- Recorded the Canonical Ubuntu 26.04 AMD64 images published 2026-08-19:
  `ami-03ceeebf93c41fdae` for `us-east-1` and `ami-066bae1901917f0ae`
  for `us-east-2`, together with their EC2 image ARNs and the stable Canonical
  public SSM parameter path.
- Updated Lab 1 to require the AMD64 image and an AMD64-v3-compatible EC2
  instance type.
- Confirmed that both deployed Lambda applications use `python3.14` for their
  SAM runtime and build method. The users-table SAM application contains only a
  DynamoDB resource and therefore has no Lambda runtime to update.
- Added a non-deploying leaderboard `make validate` target and made leaderboard
  linting validate its Python 3.14 SAM template.
- Removed the leaderboard template's invalid empty ACM ARN default. Deployment
  configuration continues to pass an empty parameter explicitly when the stack
  should create its certificate.

### Stable student checkout documentation

- Updated student-facing documentation for Spring 2027 and instructed students
  to clone the annual `spring27` repository into the stable `$HOME/course`
  checkout directory.
- Updated Lab commands, shell prompts, and supporting documentation to use
  `$HOME/course`, `~/course`, or `/home/ubuntu/course` as appropriate.
- Updated annual repository URLs to `spring27`, repaired the root CI badge and
  clone URL, and corrected stale leaderboard, Lab 3, and MEMENTO source links.
- Replaced stale Amazon Linux `/home/ec2-user` examples with Ubuntu's
  `/home/ubuntu` path and corrected the imported Lab 1 Poetry description to
  describe uv.
- This documentation change anticipates the installer, runtime, service, and
  test migrations tracked by issues #56--#62; those implementations must land
  before the new checkout instructions are operationally complete.
