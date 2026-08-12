# Elastic Beanstalk Python App with GitHub Actions CI/CD

Flask app on Elastic Beanstalk that reads/writes a visit counter in DynamoDB. Pushing to `main` triggers an automatic redeploy through GitHub Actions. No SSH, no stored AWS keys in the repo.

Note: the rubric for this lab asked for Node.js or Java. This uses Python instead, a known and accepted deviation.

## Stack

- Python 3.12, Flask, gunicorn
- AWS Elastic Beanstalk (single instance)
- DynamoDB (visit counter)
- S3 (deployment bundles)
- GitHub Actions + OIDC (no long-lived AWS credentials)

## Repo layout

```
AWS-Compute-Services/lab2-elastic-beanstalk/
├── application.py
├── requirements.txt
├── Procfile
└── .gitignore

.github/workflows/
└── deploy.yaml
```

`deploy.yaml` has to live at the repo root, under `.github/workflows/`. GitHub Actions won't pick it up from anywhere else.

## Endpoints

| Route | Returns |
|---|---|
| `GET /` | JSON with the current visit count, incremented on each call |
| `GET /version` | The short git SHA of the currently deployed commit |
| `GET /health` | `{"status": "ok"}`, used by Beanstalk's health checks |

## Environment variables

Set as Elastic Beanstalk environment properties, not in code:

| Variable | Value |
|---|---|
| `AWS_REGION` | `eu-north-1` |
| `DYNAMODB_TABLE_NAME` | `eb-app-visits` |

## One-time setup (manual, console)

1. Create the S3 bucket: `eb-deploy-python-lab`
2. Create the DynamoDB table: `eb-app-visits`, partition key `counter_id` (String), on-demand capacity
3. Create the EC2 instance role: `eb-deploy-python-lab-role`, with `AWSElasticBeanstalkWebTier` plus an inline policy for DynamoDB read/write on that one table
4. Register GitHub as an OIDC identity provider in IAM, if not already done
5. Create the deploy role: `eb-github-deploy-role`, trusted by that OIDC provider, scoped to this repo and branch
6. Create the Elastic Beanstalk application and environment, uploading an initial zip from the S3 bucket above, with the instance role and environment variables from the tables above

Full click-by-click steps are in the separate execution guide docs, not repeated here.

## Deploying after setup

Just push to `main`. The workflow packages the app, uploads it to S3, registers a new application version, updates the environment, and fails the build if the environment doesn't come back healthy.

## Checking it's live

```bash
curl http://<environment-url>/
curl http://<environment-url>/version
```

## IAM notes

Elastic Beanstalk doesn't use a service-linked role for its own internal work. It runs its internal operations (its own S3 bucket, its own CloudFormation stack, EC2, Auto Scaling) under the identity of whoever calls its API. That means `eb-github-deploy-role` needs real permissions across S3, CloudFormation (scoped to Beanstalk's own `awseb-e-*` stacks only), EC2, Auto Scaling, and SNS. Every grant is scoped to the narrowest resource AWS actually supports. Where no per-resource ARN exists (EC2, Auto Scaling, load balancing), the permission is scoped to the action list instead of a blanket `*` action.

## Cleanup

1. Terminate the Beanstalk environment (this is the ongoing cost, EC2 running continuously)
2. Delete the DynamoDB table
3. Empty and delete the S3 bucket
4. Leave the OIDC provider in place. It's account-level, not specific to this lab.

## Known leftover

`eb-lab-stack.yaml` in this folder is from an earlier CloudFormation-based approach that was abandoned in favor of manual console setup. It's not part of the current working setup and can be deleted.