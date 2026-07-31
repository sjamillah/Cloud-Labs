# Auto Scaling Web Tier on AWS

This is a small web tier that scales itself. Traffic comes in through a load balancer, gets spread across a couple of EC2 instances sitting in private subnets, and an Auto Scaling Group adds or removes instances depending on how busy things are — no manual intervention, no SSH keys floating around, and no clicking through the AWS console to build any of it.

I built this as a CloudFormation lab, deployed through Git sync so every change to the infrastructure goes through an actual pull request before it touches anything real, instead of just running `aws cloudformation deploy` from a terminal and hoping for the best.

## How it's laid out

```
                         Internet
                            |
                    [Internet Gateway]
                            |
        +-------------------+-------------------+
        |                                        |
  Public Subnet AZ-a                      Public Subnet AZ-b
   [ALB eni]  [NAT GW 1]                  [ALB eni]  [NAT GW 2]
        \         |                              /       |
         \        |                             /        |
          \       v                            /         v
           +---- Application Load Balancer ----+
                        |  round-robin
        +---------------+---------------+
        |                               |
 Private Subnet AZ-a             Private Subnet AZ-b
  [EC2 - ASG]  <---------------->  [EC2 - ASG]
   min:1 desired:1 max:4
   scales out above 30% CPU, back in below 20%
```

Two Availability Zones, so losing one doesn't take the whole thing down. The load balancer and NAT Gateways sit in the public subnets; the actual servers live in private subnets and have no public IP at all — the only way in is through the load balancer, and the only way to log into a box is through SSM Session Manager, not SSH.

## A few things worth knowing before you dig in

**The scaling isn't symmetric on purpose.** It scales out fast (30% CPU, sustained for 2 minutes) and scales back in slowly (below 20%, sustained for 6 minutes). If both thresholds were the same number, you'd get flapping — add an instance, average CPU drops, immediately remove it, CPU creeps back up, add it again, forever. The gap between the two numbers is what stops that.

**There are two NAT Gateways, not one.** A single shared one is cheaper, and that was actually the first version of this — but it meant one AZ having a bad day would also kill internet access for the *other* AZ's private subnet, which didn't feel right. So it costs a bit more now, on purpose.

**IAM is split into three separate roles** rather than one role doing everything: one just handles the Git sync mechanics, one actually provisions the AWS resources, and one is what the running EC2 instances themselves are allowed to do (which is basically nothing beyond SSM access). Splitting them means a problem in one doesn't automatically become a problem in the others.

## Repo layout

```
AWS-Compute-Services/lab1-autoscaling/
├── autoscaling-lab.yaml
└── README.md
```

Just the one template — everything is in there, VPC through CloudWatch alarms.

## Getting it running

Push the template, then create the stack in the console using "Sync from Git" rather than uploading the template directly. CloudFormation will open a pull request with the generated deployment file — merging that PR is what actually kicks off the deploy, not the push itself.

```bash
git add AWS-Compute-Services/lab1-autoscaling/
git commit -m "Auto scaling lab: VPC, ALB, ASG, step scaling on CPU"
git push origin main
```

Once it's up:

```bash
aws cloudformation describe-stacks --stack-name autoscaling-lab-stack \
  --query "Stacks[0].Outputs" --output table --region eu-north-1
```

That gives you the ALB's DNS name — `curl` it and you should get back a page showing which specific instance answered.

## The rest of the docs

This README is deliberately just the overview. Everything else lives next to it:

- `aws-fundamentals-primer.docx` — if any of the AWS terms above are unfamiliar, start here
- `autoscaling-lab-explained.docx` — the reasoning behind every design choice, plus a log of the actual errors hit while building this
- `build-log.docx` — the chronological version of how this got built, warts and all
- `master-execution-checklist.docx` — the exact commands and IAM policies, in order, for actually running the whole thing end to end

## Tearing it down

The two NAT Gateways are what actually cost money here, so don't leave this running:

```bash
aws ec2 describe-nat-gateways --region eu-north-1 \
  --query "NatGateways[?State!='deleted'].[NatGatewayId,State]" --output table
```

Delete the stack, then run that again and make sure both show `deleted`.