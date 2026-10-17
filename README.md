# Diving Timer Web

A browser-based timer for controlled breathing and breath-hold exercises.
Configure a four-step cycle, follow visual timers and English voice prompts,
and save your training history when signed in.

Django serves the pages and stores sessions in PostgreSQL. Vanilla JavaScript
runs the timer. Celery and Redis handle verification emails in the background.

## Safety warning

**Breath-hold training can cause loss of consciousness, injury, or death.**
Do not train alone. Use qualified supervision and appropriate safety procedures.
Never use this application for breath-hold exercises in water without qualified
in-person supervision. Do not hyperventilate before a breath hold.

This application is a timing tool, not a medical device or safety system. It does
not replace professional instruction. Consult a qualified medical professional
before you start a breath-hold training program.

## Contents

- [Features](#features)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Local setup with Docker](#local-setup-with-docker)
- [Configuration reference](#configuration-reference)
- [Usage](#usage)
- [Development and checks](#development-and-checks)
- [REST API](#rest-api)
- [Production deployment and releases](#production-deployment-and-releases)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)
- [Contributing](#contributing)

## Features

### Breathing timer

- Four phases: inhale, hold after inhale, exhale, and optional hold after exhale.
- Configurable phase durations and number of rounds.
- Current phase, phase countdown, session countdown, and round indicator.
- English voice prompts through the browser's Web Speech API.
- Start, pause, resume, and reset controls.
- Anonymous use without an account. Anonymous sessions are not saved.

### Accounts and training history

- Email-based registration and login, with POST-based logout.
- Account activation through a signed email verification link.
- Explicit confirmation: opening the link shows a page; submitting its form
  activates the account. The user must then sign in.
- Verification email resend for the pending account in the same browser session.
- Background email delivery through Celery, Redis, and Gmail SMTP.
- Saved exercise settings and training sessions for signed-in users.
- Personal statistics overview, history by exercise type, and session details.
- Cancellation of unfinished sessions and deletion of final sessions.
- Authenticated versioned REST endpoints for training data and lifecycle actions.

Only **four-step breathing** has a working timer and exercise configuration.
CO₂ and O₂ table identifiers exist in the model, but those exercise types are
not implemented as training screens.

## Technology stack

| Component | Current configuration |
| --- | --- |
| Python | 3.12 (`>=3.12,<3.13`) |
| Web framework | Django 6.1.2 |
| REST framework | Django REST Framework 3.18.3 |
| Database | PostgreSQL; image tag selected by `POSTGRES_VERSION` |
| Database driver | Psycopg 3 |
| Background tasks | Celery with Redis broker and result backend |
| Application server | Gunicorn in Linux containers |
| Static files and reverse proxy | Nginx |
| Frontend | Django templates, HTML, CSS, vanilla JavaScript |
| Voice prompts | Browser Web Speech API |
| Dependency management | uv, `pyproject.toml`, and `uv.lock` |
| Quality checks | pytest, pytest-django, Ruff, and mypy |
| Automation | GitHub Actions, Docker Buildx, Docker Hub, and SSH deployment |

Dependency constraints are in `pyproject.toml`; resolved versions are in
`uv.lock`. The package version is separate from Docker release tags.

## Architecture

```text
Browser
  |
  v
Nginx :8080 --------------------> collected static files
  |
  v
Gunicorn / Django -------------> PostgreSQL
  |
  v
Redis -------------------------> Celery worker ----> Gmail SMTP
```

The browser runs the countdown and voice prompts. Django validates saved
settings, checks session ownership, and stores lifecycle changes. The current
timer uses Django POST endpoints, not the separate REST API.

Main data models:

- `accounts.User`: the custom email-based user model.
- `training.Exercise`: the base exercise type.
- `training.FourStepBreathingExercise`: phase settings and round count, stored
  through Django multi-table inheritance.
- `training.Training`: one user's session, linked to an exercise configuration.
  It stores status and creation, first-pause, completion, and cancellation times.

A signed-in start creates exercise settings and an `in_progress` training in
one transaction. Subsequent actions update that training. Final states are
`completed` and `cancelled`.

Compose runs migrations and static collection as separate one-shot services.
Nginx reads collected files from a shared volume. The application runs as a
non-root user; static collection overrides that user to write to its volume.

## Local setup with Docker

### Requirements

- Git.
- Docker Engine or Docker Desktop with Linux containers.
- Docker Compose V2 (`docker compose`).
- A modern browser with JavaScript enabled.
- Gmail SMTP credentials for registration and email verification.

Host Python and uv are not required for the full container setup. They are
required for host-side development checks.

Commands use Bash syntax. On Windows, use Git Bash with Docker Desktop running.
Run commands from the repository root unless stated otherwise.

### 1. Clone the repository

```bash
git clone https://github.com/DmitryIsarenko/diving_timer_web.git
cd diving_timer_web
```

### 2. Create `.env.local`

Copy `.env.example` to `.env.local` in the repository root:

```bash
cp .env.example .env.local
```

Replace the example database credentials, Django secret, and SMTP credentials.
For local Docker use, keep `DB_HOST=postgres`, `DB_PORT=5432`,
`REDIS_HOST=redis`, and `REDIS_PORT=6379`. Set the browser-facing values to:

```dotenv
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
SITE_BASE_URL=http://127.0.0.1:8080
```

`SITE_BASE_URL` must include `http://` or `https://`. For deployment, use the
full public URL and set the corresponding hosts in `DJANGO_ALLOWED_HOSTS`.

Use a dedicated Gmail account and an app password where required by Google.
Without valid SMTP credentials, the anonymous timer remains available, but real
email verification cannot complete.

Keep real credentials out of Git, images, screenshots, and issue reports.
`.env.local`, `.env.prod`, and `.env` are excluded from Git and Docker builds.

### 3. Validate and start the stack

```bash
docker compose --env-file .env.local -f docker-compose.local.yaml config --quiet
docker compose --env-file .env.local -f docker-compose.local.yaml up -d --build
docker compose --env-file .env.local -f docker-compose.local.yaml ps -a
```

Open **http://127.0.0.1:8080/**, the Nginx entry point with static file support.
Startup can take time while images build and health checks finish. Successful
`migrate` and `collectstatic` containers exit with code `0`; they do not remain
running.

Both `--env-file` and service-level `env_file` are needed. The first supplies
Compose substitutions such as database credentials and image versions. The
second passes application settings into containers.

### Local ports

| Host address | Container destination | Purpose |
| --- | --- | --- |
| `127.0.0.1:8080` | Nginx `80` | Main browser entry point |
| `127.0.0.1:8000` | Web `8000` | Direct application diagnostics |
| `127.0.0.1:5430` | PostgreSQL `5432` | Host database access |
| `127.0.0.1:6380` | Redis `6379` | Host Redis access |

Inside Compose, use `postgres:5432` and `redis:6379`, not host ports or
`localhost`. Local Compose does not mount source code or enable automatic reload.
Rebuild affected images after code changes.

### Useful commands

```bash
# Application and worker logs
docker compose --env-file .env.local -f docker-compose.local.yaml logs -f web celery_worker

# One-shot service logs
docker compose --env-file .env.local -f docker-compose.local.yaml logs migrate collectstatic

# Create an administrator interactively
docker compose --env-file .env.local -f docker-compose.local.yaml exec web python manage.py createsuperuser

# Stop without deleting named volumes
docker compose --env-file .env.local -f docker-compose.local.yaml down
```

Named volumes hold PostgreSQL data, Redis AOF data, and collected static files.
**Do not add `--volumes` / `-v` to `down` unless you intend to delete that data.**
Volumes are not backups.

## Configuration reference

| Variable | Purpose and default |
| --- | --- |
| `SECRET_KEY` | Required, non-empty Django secret; no default |
| `DEBUG` | Boolean; defaults to `False`; invalid values raise an error |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts; default: `localhost, 127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL credentials; no application defaults |
| `DB_HOST`, `DB_PORT` | PostgreSQL address; no application defaults |
| `POSTGRES_VERSION` | PostgreSQL image tag used by Compose |
| `REDIS_HOST` | Redis hostname; application default: `127.0.0.1` |
| `REDIS_PORT` | Redis port; application default: `6379` |
| `REDIS_VERSION` | Required Redis image tag in production; local Compose uses `latest` |
| `EMAIL_HOST_USER` | Gmail SMTP account |
| `EMAIL_HOST_PASSWORD` | Gmail SMTP credential / app password |
| `DEFAULT_FROM_EMAIL` | Sender; defaults to `EMAIL_HOST_USER` when unset |
| `SITE_BASE_URL` | Base URL for verification links; default: `http://127.0.0.1:8000` |
| `EMAIL_VERIFICATION_MAX_AGE` | Link lifetime in seconds; default: `86400` |
| `APP_IMAGE` | Required application image reference in production Compose |
| `NGINX_IMAGE` | Required Nginx image reference in production Compose |

SMTP uses `smtp.gmail.com:587`, STARTTLS, and a 10-second timeout. These values
are set in Django settings, not read from environment variables. Celery uses
Redis database `0` for both its broker and result backend.

`SITE_BASE_URL` must match the browser entry point. It controls links in new
emails, not the server bind address. Changes do not update old emails. Use
hostnames without a scheme or port in `DJANGO_ALLOWED_HOSTS`.

Django calls `load_dotenv()` for ordinary `.env` discovery. It does not explicitly
select `.env.local` or `.env.prod`; Compose injects those files into containers.
Existing process environment variables take precedence over dotenv values.

## Usage

1. Open `/trainings/` and select four-step breathing.
2. Set phase durations in seconds and the number of rounds.
3. Select **Start**. Sign in first if you want to save the session.
4. Follow the phase label, countdowns, and voice prompts.
5. Use **Pause**, **Resume**, or **Reset** as needed.
6. Open `/exercise-statistics/` to review saved sessions.

| Parameter | Default | Minimum |
| --- | --- | --- |
| Inhale | 5 seconds | 1 second |
| Hold after inhale | 20 seconds | 1 second |
| Exhale | 4 seconds | 1 second |
| Hold after exhale | 2 seconds | 0 seconds; zero skips the phase |
| Rounds | 5 | 1 |

These are application defaults, **not recommended medical or training targets**.
Planned duration is the sum of enabled phases multiplied by the round count.
It is not a measured physiological performance result.

**Resume restarts the current round from inhale.** It does not continue from
the middle of the paused phase. Reset cancels an unfinished saved session.
Cancellation keeps history; deletion removes a final session permanently.

To register, open `/accounts/register/`, submit an email and password, open the
verification email, and select **Confirm email**. Then sign in at
`/accounts/login/`. Links expire after 24 hours by default. Resend currently has
a server-side **10-second** minimum interval and depends on the pending account
stored in the same browser session.

## Development and checks

Use Python 3.12 and uv. Prepare the development environment with:

```bash
uv sync --locked --group dev
```

For host-side checks, provide a local `.env` or exported environment variables.
Use local database credentials, with `DB_HOST=127.0.0.1` and `DB_PORT=5430` for
the Compose database. For host Redis access, use `REDIS_HOST=127.0.0.1` and
`REDIS_PORT=6380`. Do not replace container addresses in `.env.local` with these
host addresses.

Run lint and formatting checks from the repository root:

```bash
uv run --no-sync ruff check --no-fix .
uv run --no-sync ruff format --check .
```

Run Django-aware checks from the directory that contains `manage.py`:

```bash
cd diving_timer
uv run --no-sync mypy .
uv run --no-sync python manage.py check
uv run --no-sync pytest -v
```

Ruff has automatic fixing enabled in project configuration. Use `--no-fix` for
a read-only check. Python formatting uses a 79-character line limit and single
quotes.

Tests use pytest, pytest-django, and PostgreSQL. The database role must be able
to create a separate test database. **Never run tests with production
credentials.** Account view tests use in-memory email and Celery eager execution
where configured. They do not validate real SMTP, Redis, or a separate worker.

The suite covers accounts, forms, models, training views, ownership, lifecycle
actions, and REST endpoints. There is no automated browser timer test harness.
Check countdowns and voice prompts manually in a browser.

For host-side development, run `uv run --no-sync python manage.py runserver`
from the same directory. Set a matching `SITE_BASE_URL` and allowed hosts.
Gunicorn runs in Linux containers, not as a native Windows development server.

## REST API

Base path: `/api/v1/`. All endpoints require authentication and restrict data
to the current user's sessions. The project uses DRF's default session/basic
authentication; it does not provide token or JWT issuance. Use HTTPS for
credentials. Session-authenticated write requests require CSRF.

Paths below are relative to the base path:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `trainings/` | List the current user's sessions |
| `GET` | `trainings/{training_id}/` | Read one session |
| `PATCH` | `trainings/{training_id}/` | Apply a lifecycle action |
| `DELETE` | `trainings/{training_id}/` | Delete a completed or cancelled session |
| `GET` | `trainings/four-step-breathing/` | List sessions with four-step settings |
| `GET` | `trainings/four-step-breathing/{training_id}/` | Read a session with its settings |
| `POST` | `trainings/four-step-breathing/create/` | Create settings and an in-progress session |

Example creation body:

```json
{
  "inhale_duration_seconds": 5,
  "inhale_hold_duration_seconds": 20,
  "exhale_duration_seconds": 4,
  "exhale_hold_duration_seconds": 2,
  "round_count": 5
}
```

Example lifecycle body:

```json
{"action": "pause"}
```

Actions are `pause`, `resume`, `complete`, and `cancel`. Pause requires
`in_progress`; resume requires `paused`; complete requires `in_progress`;
cancel permits unfinished states. Invalid transitions return `409 Conflict`.
Invalid input returns `400 Bad Request`. Missing or other users' sessions
return `404 Not Found`.

Creation returns `201 Created`; successful deletion returns `204 No Content`.
Deleting an unfinished session through the API returns `400 Bad Request`.
Lists are not paginated. No OpenAPI documentation is configured.

## Production deployment and releases

Production Compose uses prebuilt images, not server-side builds. The release
workflow currently builds **Linux ARM64** application and Nginx images; it does
not publish a multi-architecture image set.

The production entry point is `127.0.0.1:8080`. A host reverse proxy must provide
public access. PostgreSQL, Redis, and Gunicorn have no published production
host ports. Included container Nginx settings serve HTTP only; they do not
configure a public domain or TLS certificate.

Before public account use, configure and verify HTTPS, proxy trust, Django
security settings, backups, and real email delivery. Do not submit real passwords
through a public HTTP connection.

### Configuration files

- `.env.prod`: secret server-side application and service settings. Provision it
  before deployment. Use `DEBUG=False`, internal database/Redis addresses, a
  public `SITE_BASE_URL`, and appropriate allowed hosts.
- `.release.env`: `APP_IMAGE` and `NGINX_IMAGE` references. The workflow generates
  and transfers this file. It must not contain credentials.
- `docker-compose.prod.yaml`: services and persistent volumes.

The server requires Compose V2 with multiple `--env-file` support. The workflow
updates `/opt/diving_timer_web` in this order:

```bash
docker compose --env-file .env.prod --env-file .release.env -f docker-compose.prod.yaml config --quiet
docker compose --env-file .env.prod --env-file .release.env -f docker-compose.prod.yaml pull
docker compose --env-file .env.prod --env-file .release.env -f docker-compose.prod.yaml up -d
```

This describes the existing update procedure, not complete server provisioning.
There is no preliminary `down`. Migration and static collection services prepare
the release through Compose dependencies. Updates are not atomic or guaranteed
to have zero downtime.

### GitHub Actions

```text
Feature branch -> PR to dev -> CI -> merge
dev -> PR to main -> CI -> merge
Release tag push -> CI -> ARM64 builds -> Docker Hub -> SSH deployment
```

| Workflow | Responsibility |
| --- | --- |
| `ci-on-pr.yml` | Call CI for pull requests targeting `dev` or `main` |
| `reusable-ci.yml` | Ruff lint, format check, mypy, Django check, pytest, and a test PostgreSQL service |
| `deploy-on-tag-push.yml` | Handle tags matching `v*.*.*`; require CI before deployment |
| `reusable-deploy.yml` | Publish both images, transfer release files, and update the server |

A normal push or merge to `main` does not trigger release deployment. Image
versions come from the Git tag through `github.ref_name`. Release runs share
a concurrency group with `cancel-in-progress: false`.

Required repository configuration:

| Type | Name | Purpose |
| --- | --- | --- |
| Variable | `DOCKERHUB_USERNAME` | Docker Hub namespace |
| Secret | `DOCKERHUB_TOKEN` | Image publication credentials |
| Secret | `HOST` | Deployment server address |
| Secret | `VPS_USERNAME` | SSH deployment user |
| Secret | `SSH_KEY` | Full private SSH key |
| Secret | `SSH_PASSPHRASE` | Private key passphrase, if applicable |

Create release tags on the intended, checked commit. Do not move or overwrite
published Git or Docker tags. The tag pattern is not strict SemVer validation
and does not prove that a commit belongs to `main`. Configure branch protection
separately from workflow files.

The workflow has no HTTP smoke check or automatic rollback. Success alone does
not prove that registration, static files, email, and all user scenarios work.
Rolling back an image does not roll back migrations. Verify backup and recovery
procedures separately.

## Project structure

```text
diving_timer_web/
├── .github/workflows/           # PR checks and tag-based releases
├── diving_timer/
│   ├── manage.py
│   ├── diving_timer/            # Settings, URLs, WSGI/ASGI, Celery, logging
│   ├── accounts/                # Custom user, registration, email, tasks, tests
│   └── training/
│       ├── api/v1/              # DRF views, serializers, and routes
│       ├── migrations/
│       ├── static/              # CSS and browser JavaScript
│       ├── templates/           # Pages and exercise-specific partials
│       ├── templatetags/
│       ├── tests/
│       ├── constants.py
│       ├── forms.py
│       ├── models.py
│       ├── urls.py
│       └── views.py
├── nginx/
│   ├── Dockerfile
│   └── default.conf
├── .env.example                # Environment configuration template
├── conftest.py                 # Shared pytest fixtures
├── docker-compose.local.yaml   # Local builds and diagnostic ports
├── docker-compose.prod.yaml    # Prebuilt production images
├── Dockerfile                  # Application image
├── pyproject.toml              # Dependencies and tool settings
├── uv.lock
└── README.md
```

## Troubleshooting

| Symptom | Checks |
| --- | --- |
| Compose reports missing variables | Supply `--env-file`; service `env_file` does not supply YAML substitutions |
| Database connection fails | Use `postgres:5432` in Compose or `127.0.0.1:5430` on the host; check database health and migration logs |
| Changed database password fails | Initialization variables do not reset credentials in an existing volume; update the PostgreSQL role deliberately |
| CSS or JavaScript is missing | Use port `8080`; check `collectstatic` exit status and Nginx logs; rebuild after code changes |
| Verification email does not arrive | Check worker health, Redis, worker logs, Gmail credentials, and spam; a registration page is not proof of delivery |
| Verification link has the wrong address | Correct `SITE_BASE_URL` and request a new email |
| Django rejects the host | Add the browser hostname to `DJANGO_ALLOWED_HOSTS`, without scheme or port |
| Voice prompts are silent | Check browser support, English voices, and system audio |
| A session remains unfinished after exit | Cancel it from statistics; page-exit delivery is not guaranteed |

Project logging writes to stdout and rotates warning/error files under
`diving_timer/logs/`. Production Docker logs use the `json-file` driver with a
`10m` size limit and three files per configured long-running service. Application
log files are not stored in a mounted persistent volume.

## Known limitations

- The interface and voice prompts are English only.
- Background-tab restrictions, browser scheduling, and device sleep can affect
  countdowns and speech. This is not a precision or safety-critical timer.
- Leaving, reloading, or closing the timer attempts cancellation through
  `pagehide`. Delivery is not guaranteed. Switching tabs does not cancel.
- The training ID is held in page memory. Recovery after reload and cross-tab
  synchronization are not implemented.
- Email tasks have no application-level automatic retry or guaranteed
  publication mechanism. Redis persistence does not guarantee delivery.
- Pending verification resend depends on the original browser session. There is
  no separate pending-account recovery flow by email in another browser.
- REST lists have no pagination. API deletion does not use the same row-lock
  pattern as lifecycle updates; full concurrent-write behavior needs more work.
- Standard rotating file logging does not coordinate rotation across processes.
  Prefer centralized stdout/stderr collection as deployment grows.
- Production hardening requires independent verification of TLS/proxy settings,
  backups, restore, SSH host verification, and release recovery. Some deployment
  actions track `master` instead of an immutable revision.

## Contributing

1. Create a focused branch.
2. Add or update tests for changed server behavior.
3. Run lint, formatting, typing, Django checks, and pytest.
4. Check affected browser flows manually when needed.
5. Open a pull request to `dev`. Integration into `main` and release tagging
   are separate steps.

Do not commit credentials, runtime logs, generated static files, or local data.
Document configuration changes. Distinguish implemented features from plans.

## Contact

- Maintainer: Dmitry Isarenko
- Email: isarenko.dmitry.it@gmail.com
- Repository: https://github.com/DmitryIsarenko/diving_timer_web