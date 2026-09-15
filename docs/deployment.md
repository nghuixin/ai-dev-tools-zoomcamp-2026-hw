# Deployment

The production artifact is one Docker image: FastAPI serving the Vite build, talking to Postgres.

## Health

`GET /health` returns `{"status":"ok"}` when the API can talk to the store/DB. Compose, the ALB, and GitHub deploy all check this path.

## Local / VM with Compose

```bash
docker compose -f docker-compose.yml up --build
```

Open http://localhost:8091. Data lives in the `postgres_data` volume.

| Variable | Default | Purpose |
|---|---|---|
| `APP_PORT` | `8091` | Host port for the app |
| `POSTGRES_PORT` | `5432` | Host port for Postgres |
| `APP_IMAGE` | `mini-kanban` (built locally) | Image to run for `app` |
| `SDIP_DATABASE_URL` | set in compose to the `postgres` service | App DB URL (also accepts `DATABASE_URL`) |

## CI/CD (GitHub Actions + AWS OIDC)

`.github/workflows/ci.yml`:

1. Frontend and backend unit tests **in parallel**
2. One Compose stack; integration + Playwright against it
3. On push to `main`/`master`, if `AWS_ROLE_ARN` is set, calls `deploy.yml`

`.github/workflows/deploy.yml` (also on tags `v*` and **Actions → Deploy**):

1. Assume the IAM role via **GitHub OIDC** (no access keys in GitHub)
2. Deploy `infra/ecr.yml`, build/push `linux/amd64`, deploy `infra/app.yml`
3. Poll `http://<alb>/health` until `{"status":"ok"}`

### One-time AWS setup

From an admin principal (temporary user is fine):

```bash
aws cloudformation deploy \
  --stack-name mini-kanban-github-oidc \
  --template-file infra/github-oidc.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides GitHubSub=repo:<your-org>/<your-repo>:*
```

Copy the `RoleArn` output. In the GitHub repo: **Settings → Secrets and variables → Actions → Variables**:

| Variable | Value |
|---|---|
| `AWS_ROLE_ARN` | that role ARN |
| `AWS_REGION` | `us-east-1` (optional) |

If the account already has `token.actions.githubusercontent.com`, pass `ExistingOidcProviderArn`.

Do not store AWS access keys in GitHub. Delete the temporary admin user after the OIDC stack exists.

## Manual AWS deploy

```powershell
aws configure
.\infra\deploy.ps1
```

Tear down: `.\infra\destroy.ps1`. Cost is `db.t3.micro` + Fargate + ALB (no NAT).
