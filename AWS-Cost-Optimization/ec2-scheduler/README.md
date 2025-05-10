# 🕒 AWS EC2 Scheduler with Lambda & EventBridge

This project automates the starting and stopping of EC2 instances to optimize AWS costs.
By leveraging AWS Lambda and EventBridge, you can schedule EC2 instances to run only during desired timeframes, such as business hours.

# Problem Statement

### You work for xyz Company. Your company wanted to reduce the bill on unused EC2-Instances during office off hours.

## You are asked to perform the following tasks:

### 1. Stop the EC2-Instances ( Test, Dev & QA ) after 10PM

### 2. Start the EC2-Instances ( Test, Dev & QA ) after 7AM 

---

## 🚀 Prerequisites

- An active AWS account
- Permissions to create Lambda functions, IAM roles, and EventBridge rules
- Python 3.12 or later

---

## 🛠️ Setup Instructions

### 1. **Create IAM Policy**

Define an IAM policy that grants the necessary permissions for the Lambda function to manage EC2 instances.
Refer to `IAM-Policy.md` for the policy JSON and detailed explanation.

### 2. **Create IAM Role**

- Navigate to the IAM console.
- Create a new role with the following settings:
  - **Trusted entity**: AWS Lambda
  - **Permissions**: Attach the IAM policy created in step 1
- Note the Role ARN for later use.

### 3. **Develop Lambda Function**

- Navigate to the AWS Lambda console.
- Click on **Create function**.
- Choose **Author from scratch**.
- Configure the function:
  - **Function name**: `EC2SchedulerFunction`
  - **Runtime**: Python 3.12
  - **Permissions**: Use the IAM role created in step 2

### 4. **Add Lambda Function Code**

- In the Lambda function's code editor, replace the default code with the contents of `lambda_function.py`.
- Modify the `INSTANCE_LIST` variable to include your EC2 instance details:

<pre><code>
INSTANCE_LIST = """
# InstanceID           Name         IP_Address      Region
i-0123456789abcde      WebServer1   192.168.1.10    ap-south-1
i-0abcdef12345678      DBServer     192.168.1.11    us-east-1
i-0fedcba987654321     AppServer    192.168.1.12    eu-west-1
"""
</code></pre>

- Click **Deploy** to save the changes.

### 5. **Test Lambda Function**

- In the Lambda console, click on **Test**.
- Configure a new test event with default settings.
- Click **Test** to execute the function and verify it starts/stops the specified EC2 instances.

### 6. **Schedule with EventBridge**

- Navigate to the Amazon EventBridge console.
- Click on **Create rule**.
- Configure the rule:
  - **Name**: `StartEC2Instances` or `StopEC2Instances`
  - **Event Source**: EventBridge (Schedule)
  - **Schedule pattern**: Define using cron expressions (e.g., `cron(0 9 * * ? *)` for 9 AM daily)
  - **Target**: Select the Lambda function created earlier
- Click **Create** to activate the rule.

---

## 📄 Additional Resources

- [IAM-Policy.md](IAM-Policy.md): Detailed IAM policy for Lambda permissions.
- [LambdaFunction.md](LambdaFunction.md): Step-by-step guide to create and configure the Lambda function.
- [AWS Instance Scheduler Documentation](https://docs.aws.amazon.com/solutions/latest/instance-scheduler-on-aws/solution-overview.html): Official AWS documentation for advanced scheduling solutions.

---

## ✅ Best Practices

- **Tagging**: Use consistent tags on EC2 instances to manage schedules effectively.
- **Monitoring**: Enable CloudWatch logs for the Lambda function to monitor execution and troubleshoot issues.
- **Security**: Follow the principle of least privilege when assigning IAM permissions.

---

## 📬 Support

For issues or feature requests, please open an [issue](https://github.com/Vishvanath-Patil/Cloud-Engineer/issues) in this repository.

---

By following this guide, you can efficiently manage your EC2 instances' uptime, leading to significant cost savings and streamlined operations.
