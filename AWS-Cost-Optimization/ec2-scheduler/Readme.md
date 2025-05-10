
# Problem Statement

### You work for xyz Company. Your company wanted to reduce the bill on unused EC2-Instances during office off hours.

## You are asked to perform the following tasks:

### 1. Stop the EC2-Instances ( Test, Dev & QA ) after 7PM

### 2. Start the EC2-Instances ( Test, Dev & QA ) after 8AM before 9AM

## Create Policy

Create Policy with following permissions for EC2 Instances

```bash
 {
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": [
				"ec2:RebootInstances",
				"ec2:StartInstances",
				"ec2:StopInstances"
			],
			"Resource": "arn:aws:ec2:*:106298549500:instance/*"
		},
		{
			"Sid": "VisualEditor1",
			"Effect": "Allow",
			"Action": "ec2:DescribeInstances",
			"Resource": "*"
		}
	]
}
```
```bash
 import boto3

region = "us-west-2"
instances = ['i-009ada209b43ae9f9','i-09c079adedcda7d67','i-0818c7818f67330c6']

ec2 = boto3.client('ec2', region_name=region)
def lambda_handler(event, context):
  ec2.stop_instances(InstanceIds=instances) #For Start change to start_instances
  print("Started Your instances: '+ str")
```
![lambda3](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/2151130d-3b2f-45eb-a94c-92b75d22cf80)

![lambda2](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/402de95a-38bd-4ea7-9256-ca476fe5af1d)


![lambda1](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/853cbbc6-5eac-4d91-bb1a-3e489c79a1ec)

![l4](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/1bff33d4-a538-4f4e-89ff-7453ea552104)

![l5](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/5546d925-1c99-47cc-80cd-78e9b7840ae0)

![l7](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/8b69784f-2218-45ae-8530-a40c0d39c31b)

![l8](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/185c3d42-83b1-4abe-a3ca-89f3f666585d)

![image](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/ea97e0a1-8c68-41c2-a9c8-e1f5680a8965)

![l10](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/89c4d7f2-7613-43d8-8aab-cfd3fd4bd534)

![l11](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/3cb88e80-e7bd-43aa-846d-e35dd039c71c)

![l12](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/b2ae32df-23f2-48f3-9bd1-69ae64c5f022)

![strtrigger1](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/a32c55d0-77ca-4958-9e86-c48ca4991b0e)

![strtr2](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/21a69bcd-404d-4935-9bec-c433f5a744a0)




