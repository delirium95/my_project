# GitHub Actions and Lambda deployment

The workflow at `.github/workflows/ci.yml` runs on every pull request and push to `main`.
It uses clean PostgreSQL and Redis service containers, so migrations and integration tests do not
depend on a developer's local Docker data.

## What the workflow verifies

| Job | Checks |
| --- | --- |
| Backend | Ruff lint/format, repository pre-commit hooks, Alembic upgrade, `alembic check`, unit tests, integration tests, and a `coverage.xml` artifact |
| Frontend | `tsc --noEmit` and the Vite production build |
| Deploy Lambda | Only after both jobs pass on a push to `main`; builds the Lambda container and deploys the SAM stack |

The deployment job is associated with the GitHub environment `lambda-production`. Configure
required reviewers in that environment if a human approval should precede every AWS release.

## One-time GitHub configuration

In **Settings → Environments → lambda-production**, add the following variables:

| Variable | Example |
| --- | --- |
| `AWS_REGION` | `eu-central-1` |
| `AWS_SAM_STACK_NAME` | `boutique-analytics-demo` |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::123456789012:role/boutique-github-deploy` |
| `FRONTEND_ORIGIN` | `https://main.example.amplifyapp.com` |
| `LAMBDA_SUBNET_IDS` | `subnet-aaa,subnet-bbb` |
| `LAMBDA_SECURITY_GROUP_ID` | `sg-0123456789abcdef0` |

Add these environment **secrets** (never variables):

| Secret | Purpose |
| --- | --- |
| `DATABASE_URL` | TLS RDS PostgreSQL URL |
| `REDIS_URL` | Private TLS ElastiCache URL |
| `JWT_SECRET` | Unique application signing secret, 32+ characters |

The workflow intentionally does not supply Kaggle credentials. The low-cost private-VPC deployment
profile has no NAT Gateway; seed data locally as described in [cloud-deployment.md](cloud-deployment.md).

## AWS OIDC role

Create an AWS IAM OpenID Connect provider for `https://token.actions.githubusercontent.com` with
audience `sts.amazonaws.com`, then make the deploy role trust only this repository environment:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:delirium95/my_project:environment:lambda-production"
      }
    }
  }]
}
```

Attach a deployment policy that permits the SAM/CloudFormation stack, its ECR image repository,
Lambda function, IAM execution role, and CloudFormation change sets. Scope resource ARNs to this
project once the first successful stack has been created. GitHub's OIDC flow grants short-lived
credentials; it does not require storing long-lived AWS access keys in GitHub.

## Migration safety

`alembic upgrade head` runs against the disposable CI database before any tests. `alembic check`
then compares SQLAlchemy metadata to the migration history and fails if a model change has no
matching migration. Production RDS migration remains an explicit administrative step before the
first Lambda deployment because the low-cost private-VPC setup does not expose database access to
the GitHub-hosted runner.
