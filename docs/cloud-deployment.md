# Deploy Boutique Analytics on AWS

This is the AWS-only deployment profile for the project. It is intentionally sized for a
demonstration: one Lambda container, one single-AZ RDS PostgreSQL database, and one
ElastiCache Serverless cache.

```mermaid
flowchart LR
  Browser --> Amplify[AWS Amplify Hosting\nVite static site]
  Amplify -->|HTTPS /api calls| Lambda[Lambda Function URL\nFastAPI + Mangum]
  Lambda -->|private VPC| RDS[(RDS PostgreSQL)]
  Lambda -->|private VPC| Redis[(ElastiCache Serverless\nRedis OSS)]
```

The repository includes two deployment artefacts:

- `backend/Dockerfile.lambda` — a Lambda-compatible Python 3.14 container image.
- `infra/template.yaml` — an AWS SAM template that builds the image, creates the Lambda
  function URL, and attaches the function to your existing VPC.

## Why a Lambda Function URL, not API Gateway?

The Kaggle import may download, unpack, and process a moderately large archive. API Gateway
has a much shorter integration timeout; Lambda Function URLs can wait for the Lambda invocation
up to the function timeout. The template therefore gives Lambda 15 minutes and 1 GB of
ephemeral storage. For a production import flow, replace the synchronous request with a queue
and worker, but this is a better fit for the demonstration.

## Cost and scope first

RDS, ElastiCache, and especially a NAT Gateway can incur charges even when a demo is idle.
The baseline below keeps the database and cache private and does **not** give the Lambda outgoing
internet access. That means cloud Kaggle import is intentionally off; seed the data once from a
trusted machine before making RDS private. This avoids paying for a NAT Gateway just to make a
one-off demo import work.

If cloud-side Kaggle import is a requirement, add a NAT Gateway to the Lambda private-subnet
route table and pass `KAGGLE_USERNAME` / `KAGGLE_KEY` during deployment. Remove the NAT Gateway
again after the import if it is no longer needed.

## Prerequisites

- AWS CLI configured for the test account and a region selected.
- Docker 20.10.10+ and the AWS SAM CLI installed locally.
- A source repository connected to AWS Amplify for the frontend.
- A newly generated `JWT_SECRET` of at least 32 characters:

  ```bash
  openssl rand -hex 32
  ```

Never commit `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, or Kaggle credentials. Do not put any
of them in `VITE_*`: Vite embeds these values into the public JavaScript bundle.

## 1. Create the VPC security groups

Use one VPC for Lambda, RDS, and ElastiCache. The default VPC is enough for a short-lived demo
if it exists in the chosen region; use at least two subnets in separate Availability Zones.

Create three security groups:

| Group | Inbound | Outbound |
| --- | --- | --- |
| `boutique-lambda` | None | TCP 5432 to `boutique-rds`; TCP 6379 to `boutique-cache` |
| `boutique-rds` | TCP 5432 from `boutique-lambda` only | Default |
| `boutique-cache` | TCP 6379 from `boutique-lambda` only | Default |

Record the two subnet IDs and the `boutique-lambda` security-group ID. They are SAM template
parameters. Lambda Function URLs still receive public HTTPS traffic; the VPC setting controls
only the function's outgoing network access.

## 2. Create RDS PostgreSQL

In the RDS console, create a PostgreSQL database with:

| Setting | Demo value |
| --- | --- |
| Engine | PostgreSQL (current supported minor version) |
| Deployment | Single-AZ, development/test template |
| Initial database name | `boutique` |
| Public access | `No` after initial seed |
| VPC | The VPC from step 1 |
| Security group | `boutique-rds` |
| Backup retention | The smallest acceptable value for the demo |

Use a generated database password. When the instance is available, form the API setting from
its endpoint:

```dotenv
DATABASE_URL=postgresql://DATABASE_USER:DATABASE_PASSWORD@YOUR_RDS_ENDPOINT:5432/boutique?sslmode=require
```

The backend turns this standard RDS URL into the `asyncpg` dialect and configures TLS, so do not
manually rewrite it to `postgresql+asyncpg`. RDS Proxy is optional for this small demo: Lambda is
configured with `SERVERLESS=true` and `NullPool`. Add RDS Proxy before raising concurrency.

## 3. Create ElastiCache Serverless

Create a Redis OSS Serverless cache in the same VPC and select:

- the same subnets as Lambda;
- `boutique-cache` as its security group;
- TLS enabled (the normal serverless configuration);
- no access-control user group for this isolated test cache.

The last choice is only acceptable because the cache has no public route and its security group
accepts traffic solely from the Lambda security group. If you enable ElastiCache RBAC/IAM
authentication later, add the matching Redis credential/token provider to the application rather
than exposing a cache without network isolation.

When the cache is available, use its endpoint in this format:

```dotenv
REDIS_URL=rediss://YOUR_ELASTICACHE_ENDPOINT:6379/0
```

Redis holds cache entries and one-time refresh-token records. It does not hold the source data;
resetting it may require users to sign in again but does not remove PostgreSQL data.

## 4. Seed schema and Olist data once

Because the private Lambda has no NAT Gateway in this low-cost profile, use a controlled,
temporary local connection to seed RDS:

1. In RDS, temporarily make the DB publicly accessible and add an inbound `5432` rule only for
   your current public IP address with `/32` CIDR. Do not use `0.0.0.0/0`.
2. From the local backend environment, point `DATABASE_URL` to the RDS URL and run:

   ```bash
   cd backend
   uv run alembic upgrade head
   uv run python -m boutique.commands.seed_olist /path/to/olist-csvs --replace
   ```

   You can obtain the CSVs through the existing local, authenticated **Import Olist data** flow.
   The server-side Kaggle key stays local during this step.
3. Verify rows in RDS, then disable public access and remove the temporary IP rule.

This is intentionally a one-time administrative operation. The deployed Lambda does not need a
Kaggle key or public internet to serve the dashboard once the Olist data is present.

## 5. Build and deploy the Lambda container with SAM

From the repository root, build the container image:

```bash
sam build --template-file infra/template.yaml --use-buildkit
```

For the first deployment, run:

```bash
sam deploy --guided --stack-name boutique-analytics-demo
```

SAM will prompt for the database URL, Redis URL, JWT secret, frontend origin, the two subnet IDs,
and the Lambda security group. It builds the image from `backend/Dockerfile.lambda`, pushes it to
an ECR repository, then creates the CloudFormation stack. Let SAM create the ECR repository when
it offers to do so. Do not save secret parameter values into a committed `samconfig.toml`.

For the first API-only smoke test, leave `FrontendOrigin` as `http://localhost:5173`. After
Amplify assigns the real dashboard URL, run `sam deploy --guided` again and replace it with the
exact `https://...amplifyapp.com` origin.

The stack output `BoutiqueApiFunctionUrl` is the API root. The frontend value is that URL followed
by `api/v1`, for example:

```dotenv
VITE_API_BASE_URL=https://abcde.lambda-url.eu-central-1.on.aws/api/v1
```

## 6. Deploy the React frontend with Amplify Hosting

In AWS Amplify, create a hosting app from the repository and configure the monorepo frontend:

| Setting | Value |
| --- | --- |
| App root / build root | `frontend` |
| Build command | `npm ci && npm run build` |
| Artifact directory | `dist` |
| Environment variable | `VITE_API_BASE_URL=<BoutiqueApiFunctionUrl>api/v1` |

Amplify provides an HTTPS domain after the first build. Set that exact URL as `FrontendOrigin` in
the SAM deployment and redeploy Lambda so FastAPI CORS accepts browser requests with cookies.

Amplify and a Lambda Function URL use separate sites. The supplied template therefore sets
`COOKIE_SAMESITE=none` together with `COOKIE_SECURE=true`; this allows the HttpOnly refresh cookie
to accompany cross-site HTTPS API requests. Some privacy-restricted browsers block all third-party
cookies. For a durable public deployment, put frontend and `/api/*` behind one custom CloudFront
domain and restore `COOKIE_SAMESITE=lax`.

## 7. Verify the demo

```bash
curl -fsS https://YOUR_FUNCTION_URL/api/v1/health/live
curl -fsS https://YOUR_FUNCTION_URL/api/v1/health/ready
```

Then open the Amplify URL and verify:

1. registration and login;
2. a page reload (refresh-token cookie);
3. summary cards, revenue chart, histogram, heatmap, and orders table;
4. From/To date controls update the three analytical views.

The Kaggle import button is not intended to work in the no-NAT cloud profile. Keep importing
locally for the demo, or deliberately add a NAT Gateway and server-side Kaggle credentials if
you need that control in the deployed app.

## Monitoring and cleanup

- Watch Lambda logs and errors in CloudWatch.
- Use `/api/v1/health/live` for process liveness and `/api/v1/health/ready` for database/cache
  readiness.
- Delete the CloudFormation stack, the RDS instance/snapshots, ElastiCache cache, Amplify app,
  and unused ECR image repository when the demonstration ends. These services can continue to
  bill after the Lambda function has been deleted.

## Optional next step: production hardening

- Add RDS Proxy before increasing Lambda concurrency.
- Store database, Redis, JWT, and Kaggle secrets in AWS Secrets Manager instead of passing stack
  parameters.
- Move Kaggle import to SQS + a worker and restrict it to administrator accounts.
- Put Amplify/CloudFront and the API under one custom domain to make refresh cookies first-party.
