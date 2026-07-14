# GitHub Actions and Lambda deployment

The workflow at `.github/workflows/ci.yml` runs on every pull request and push to `main`.
It uses clean PostgreSQL and Redis service containers, so migrations and integration tests do not
depend on a developer's local Docker data.

## What the workflow verifies

| Job | Checks |
| --- | --- |
| Backend | Ruff lint/format, repository pre-commit hooks, Alembic upgrade, `alembic check`, unit tests, integration tests, and a `coverage.xml` artifact |
| Frontend | Vitest + React Testing Library, `tsc --noEmit`, and the Vite production build |
| Deploy Lambda | Only after both jobs pass on a push to `main`; builds the Lambda container, deploys the SAM stack, and invokes the private migration Lambda |
| Deploy frontend | Builds React with the deployed API URL, syncs it to private S3, and invalidates CloudFront |

The deployment job is associated with the GitHub environment `lambda-production`. Configure
required reviewers in that environment if a human approval should precede every AWS release.

## One-time GitHub configuration

In **Settings → Environments → lambda-production**, add the following variables:

| Variable | Example |
| --- | --- |
| `AWS_REGION` | `us-east-1` |
| `AWS_SAM_STACK_NAME` | `boutique-analytics-demo` |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::123456789012:role/boutique-github-deploy` |
| `FRONTEND_ORIGIN` | `https://d123example.cloudfront.net` |
| `LAMBDA_SUBNET_IDS` | `subnet-aaa,subnet-bbb` |
| `LAMBDA_SECURITY_GROUP_ID` | `sg-0123456789abcdef0` |
| `STATIC_SITE_BUCKET` | `boutique-analytics-demo-123456789012-us-east-1` |
| `CLOUDFRONT_DISTRIBUTION_ID` | `E1234567890ABC` |

Add these environment **secrets** (never variables):

| Secret | Purpose |
| --- | --- |
| `DATABASE_URL` | TLS RDS PostgreSQL URL |
| `REDIS_URL` | Private TLS ElastiCache URL |
| `JWT_SECRET` | Unique application signing secret, 32+ characters |
| `KAGGLE_USERNAME` | Kaggle account username for the optional in-app importer |
| `KAGGLE_KEY` | Kaggle API token for the optional in-app importer |

The deploy job passes the optional Kaggle credentials only to the API Lambda. The VPC still needs
the optional one-AZ NAT Gateway while the importer downloads the archive; disable it after the
one-time import as described in [cloud-deployment.md](cloud-deployment.md).

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
matching migration. The API deployment invokes the dedicated migration Lambda after every
successful SAM update. It shares the API Lambda's VPC configuration, so `alembic upgrade head`
reaches private RDS without exposing the database to the GitHub-hosted runner.
