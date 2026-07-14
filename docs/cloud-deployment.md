# Deploy Boutique Analytics on AWS

The demo deployment is deliberately cost-conscious and uses the existing default VPC in
`us-east-1`. A one-AZ NAT Gateway is optional, and is used only when the in-app Kaggle importer
needs outbound internet access.

```mermaid
flowchart LR
  Browser --> CF[CloudFront]
  CF --> S3[Private S3 frontend bucket]
  Browser -->|HTTPS API| URL[Lambda Function URL]
  URL --> API[FastAPI Lambda]
  API --> RDS[(Private RDS PostgreSQL)]
  API --> Redis[(Private ElastiCache Redis)]
  CI[GitHub Actions OIDC] --> CF
  CI --> API
```

## What the two stacks do

| Stack | Source | Creates |
| --- | --- | --- |
| Foundation | `infra/foundation.yaml` | security groups, private RDS/Redis, a private S3 bucket, CloudFront, and the GitHub OIDC deploy role |
| Application | `infra/template.yaml` | API Lambda Function URL and an in-VPC migration Lambda |

The GitHub workflow deploys the application stack, invokes `alembic upgrade head` through the
private migration Lambda, builds the Vite app with the deployed API URL, uploads it to S3, and
invalidates CloudFront. No database or Redis credential enters the frontend bundle.

## Cost profile and limitations

- RDS `db.t3.micro` (20 GiB), one `cache.t3.micro` Redis node, CloudFront Price Class 100, and
  S3 are appropriate only for a short-lived demo. They continue to bill while running.
- The Kaggle importer needs a NAT Gateway while it downloads the archive. Enable the supplied
  one-AZ option, import once, then disable it to stop the NAT hourly charge.
- The default VPC subnets are sufficient for this demo. The database and cache remain private:
  only the Lambda security group can reach ports 5432 and 6379.

## 1. Create the foundation stack

Confirm that the chosen VPC has two subnets in different Availability Zones, then use a generated
password that is never committed or printed:

```bash
export AWS_REGION=us-east-1
export VPC_ID=vpc-...                 # existing default VPC
export SUBNET_IDS=subnet-aaa,subnet-bbb
read -rsp 'PostgreSQL password: ' DATABASE_PASSWORD; echo

aws cloudformation deploy \
  --region "$AWS_REGION" \
  --stack-name boutique-analytics-foundation \
  --template-file infra/foundation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    VpcId="$VPC_ID" \
    SubnetIds="$SUBNET_IDS" \
    DatabasePassword="$DATABASE_PASSWORD"
unset DATABASE_PASSWORD
```

Record the stack outputs. The database URL is constructed from the `DatabaseEndpoint` and the
password entered above:

```dotenv
DATABASE_URL=postgresql://boutique:YOUR_PASSWORD@DATABASE_ENDPOINT:5432/boutique?sslmode=require
REDIS_URL=rediss://REDIS_ENDPOINT:6379/0
```

The S3 bucket is private. CloudFront uses an Origin Access Control to read it, which preserves
HTTPS delivery without public-bucket access. [AWS recommends OAC for this pattern](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html).

## 2. Configure the GitHub Environment

Create **Settings → Environments → `lambda-production`** in `delirium95/my_project`. Add these
environment variables from the foundation stack outputs:

| Variable | Source |
| --- | --- |
| `AWS_REGION` | `us-east-1` |
| `AWS_SAM_STACK_NAME` | `boutique-analytics-demo` |
| `AWS_DEPLOY_ROLE_ARN` | `GitHubDeploymentRoleArn` |
| `FRONTEND_ORIGIN` | `https://CloudFrontDomainName` |
| `LAMBDA_SUBNET_IDS` | the two subnets passed to foundation |
| `LAMBDA_SECURITY_GROUP_ID` | `LambdaSecurityGroupId` |
| `STATIC_SITE_BUCKET` | `StaticSiteBucketName` |
| `CLOUDFRONT_DISTRIBUTION_ID` | `CloudFrontDistributionId` |

Add these environment **secrets**:

| Secret | Value |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URL constructed above |
| `REDIS_URL` | `RedisUrl` output |
| `JWT_SECRET` | a new random value of 32+ characters |
| `KAGGLE_USERNAME` | Kaggle account username, when enabling the importer |
| `KAGGLE_KEY` | Kaggle API token, when enabling the importer |

The foundation role trusts only GitHub tokens whose subject is
`repo:delirium95/my_project:environment:lambda-production`; it uses short-lived OIDC credentials,
not stored AWS keys.

## 3. Deploy from GitHub

Merge the PR to `main`. The workflow runs quality checks first, then:

1. builds and deploys the Lambda container with SAM;
2. invokes the migration Lambda, which performs `alembic upgrade head` against private RDS;
3. builds React with `VITE_API_BASE_URL=<Lambda Function URL>/api/v1`;
4. synchronizes `frontend/dist` to the private bucket and invalidates CloudFront.

Open `https://CloudFrontDomainName` after the workflow finishes. The Lambda Function URL remains
public only for API traffic; FastAPI CORS permits the exact CloudFront origin and uses secure,
cross-site refresh cookies.

## Cleanup

After the demo, delete the application stack first and then the foundation stack:

```bash
aws cloudformation delete-stack --stack-name boutique-analytics-demo --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name boutique-analytics-demo --region us-east-1
aws cloudformation delete-stack --stack-name boutique-analytics-foundation --region us-east-1
```

Empty any retained S3 bucket objects and delete any ECR image repositories left by SAM. The
foundation template sets the demo RDS and Redis resources to delete with the stack, so do not use
it for data that must be retained.
