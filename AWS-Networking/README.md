# Multi-AZ VPC — CloudFormation Lab

Highly available VPC across two Availability Zones with Apache web servers in public subnets and application servers in private subnets. No SSH anywhere — all access through AWS Systems Manager.


## Architecture

```
                    Internet
                       │
                Internet Gateway
                       │
         ┌─────────────┴─────────────┐
         │                           │
   AZ1 (eu-north-1a)         AZ2 (eu-north-1b)
         │                           │
  Public 10.0.1.0/24        Public 10.0.2.0/24
  ├── Web Server             ├── Web Server
  └── NAT Gateway 1          └── NAT Gateway 2
         │                           │
  Private 10.0.3.0/24       Private 10.0.4.0/24
  └── App Server             └── App Server
```

Private subnets route through their own AZ's NAT Gateway — no cross-AZ egress dependency.

## Deploy

```bash
aws cloudformation create-stack \
  --stack-name vpc-lab-stack \
  --template-body file://vpc_stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=FullName,ParameterValue="Jamillah Ssozi" \
    ParameterKey=LabName,ParameterValue="Securely Deploying Resources in a VPC Using CloudFormation" \
  --region eu-north-1
```

Takes 5–10 minutes. Get outputs when complete:

```bash
aws cloudformation describe-stacks \
  --stack-name vpc-lab-stack \
  --region eu-north-1 \
  --query 'Stacks[0].Outputs[*].{Key:OutputKey,Value:OutputValue}' \
  --output table
```

## Validate

Open both public IPs in the browser — each page shows the instance name, AZ, and instance ID.

Connect to any instance via Session Manager:

```bash
aws ssm start-session --target <InstanceId> --region eu-north-1
```

From a web server, ping the private instances to confirm cross-tier connectivity. From a private instance, run `traceroute 8.8.8.8` — the NAT Gateway IP for that AZ appears in the path, confirming AZ-aligned routing.

## Design decisions

**Two NAT Gateways.** One per AZ so each private subnet routes through its own NAT Gateway. If AZ1 fails, AZ2 private instances still have outbound internet — no cross-AZ dependency.

**Session Manager over SSH.** Port 22 is closed everywhere. Access is IAM-controlled, auditable, and works without key management.

**Dynamic AMI.** Uses `{{resolve:ssm:/aws/service/ami-amazon-linux-latest/...}}` so the template always pulls the current Amazon Linux without region-specific AMI lookups.

**Launch Template.** Both web servers share one Launch Template — the Apache UserData script lives in one place.

## Cleanup

```bash
aws cloudformation delete-stack --stack-name vpc-lab-stack --region eu-north-1
```
