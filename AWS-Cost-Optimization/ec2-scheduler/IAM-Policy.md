# 🔐 IAM Policy for AWS Lambda to Control EC2 Instances

This policy grants an AWS Lambda function the minimum necessary permissions to **start**, **stop**, and **reboot** EC2 instances, as well as to **describe** their current state.

---

## 📜 IAM Policy JSON

```json
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
			"Resource": "arn:aws:ec2:*:<AccountID>:instance/*"
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

> 🔁 Replace `<AccountID>` with your actual AWS account ID (e.g., `123456789012`).

---

## 🔍 Explanation

### 🎯 Statement 1: Instance Control

```json
{
	"Sid": "VisualEditor0",
	"Effect": "Allow",
	"Action": [
		"ec2:RebootInstances",
		"ec2:StartInstances",
		"ec2:StopInstances"
	],
	"Resource": "arn:aws:ec2:*:<AccountID>:instance/*"
}
```

- **Purpose**: Grants Lambda permission to control EC2 instance power state.
- **Actions**:
  - `StartInstances`: Start a stopped instance.
  - `StopInstances`: Stop a running instance.
  - `RebootInstances`: Restart an instance.
- **Resource Scope**: Limited to all EC2 instances (`instance/*`) within your AWS account, across any region (`*`).

---

### 🔍 Statement 2: Describe Access

```json
{
	"Sid": "VisualEditor1",
	"Effect": "Allow",
	"Action": "ec2:DescribeInstances",
	"Resource": "*"
}
```

- **Purpose**: Required for the Lambda function to **query instance states**.
- **Action**:
  - `DescribeInstances`: Lists instances and their metadata.
- **Resource**: `*` (this action does not support resource-level restriction).

---

## 🧠 Why Attach This Policy to Lambda?

AWS Lambda runs with an **IAM execution role**. To allow the function to manage EC2 instances, this role must have the necessary permissions.

Without this policy:

- The Lambda function would **fail** with an `AccessDenied` error when trying to start/stop instances.
- EC2 operations would not be authorized.

---

## ✅ Usage Example

Attach this policy to the Lambda **execution role** either by:

1. Creating a custom IAM policy with this JSON and attaching it to the role.
2. Embedding it inline while creating the role.

---

## 🔐 Principle of Least Privilege

- The policy follows **least privilege** by limiting EC2 actions to only the needed ones.
- You can further **restrict `Resource`** by specifying individual instance ARNs for tighter security.

---

## 📌 Related AWS Services

- **AWS Lambda**: Serverless compute that uses this policy to automate EC2 tasks.
- **Amazon EC2**: Virtual machines that are being controlled.
- **IAM**: Used to define and enforce permissions for Lambda.
