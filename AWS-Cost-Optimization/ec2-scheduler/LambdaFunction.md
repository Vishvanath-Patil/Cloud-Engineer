# 🚀 Steps to Create AWS Lambda Function to Manage EC2 Instances

This guide provides a step-by-step process to create an AWS Lambda function for starting, stopping, or rebooting EC2 instances, based on the visual walkthrough.

---

## 📍 Step 1: Go to AWS Lambda Console

Navigate to the AWS Management Console, then:
- Open **Services** → **Lambda**
- Click on **Create function**

![Step 1](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/1bff33d4-a538-4f4e-89ff-7453ea552104)

---

## 🧾 Step 2: Author from Scratch

- Choose **Author from scratch**
- Function name: `StopStartEC2Function`
- Runtime: `Python 3.12` (or latest available)
- Permissions:
  - Choose **Create a new role with basic Lambda permissions**

![Step 2](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/5546d925-1c99-47cc-80cd-78e9b7840ae0)

---

## ✏️ Step 3: Edit Function Code

After creation, scroll to the **Code source** section.

- Replace the default code with your EC2 control logic.

![Step 3](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/8b69784f-2218-45ae-8530-a40c0d39c31b)

---

## 🔐 Step 4: Add IAM Permissions

Go to the **Configuration** tab → **Permissions** → Click on **Role name**.

- In IAM, click **Add permissions** → **Attach policies**.
- Attach a custom policy with `ec2:StartInstances`, `ec2:StopInstances`, `ec2:RebootInstances`, and `ec2:DescribeInstances`.

![Step 4](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/185c3d42-83b1-4abe-a3ca-89f3f666585d)

---

## ✅ Example Policy to Attach

See `IAM-Policy.md` in this repo for a full example IAM policy to use.

---

## 🧪 Step 5: Deploy the Function

Click **Deploy** after editing the code.

![Deploy](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/ea97e0a1-8c68-41c2-a9c8-e1f5680a8965)

---

## 🧭 Step 6: Test the Function

- Click **Test**
- Create a new test event with a name (e.g., `testEvent`)
- Leave default JSON `{}` and click **Test**

![Test 1](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/89c4d7f2-7613-43d8-8aab-cfd3fd4bd534)

![Test 2](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/3cb88e80-e7bd-43aa-846d-e35dd039c71c)

---

## ⏰ Step 7: Add Scheduled Trigger (Optional)

To automate instance start/stop:

- Go to **Triggers**
- Click **Add Trigger**
- Choose **EventBridge (CloudWatch Events)**
- Create a new rule with a schedule expression (e.g., `cron(0 8 * * ? *)`)

![Trigger 1](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/b2ae32df-23f2-48f3-9bd1-69ae64c5f022)

![Trigger 2](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/a32c55d0-77ca-4958-9e86-c48ca4991b0e)

![Trigger 3](https://github.com/Vishvanath-Patil/AWS-Cost-Optimization-Tasks/assets/130968991/21a69bcd-404d-4935-9bec-c433f5a744a0)

---

## 📌 Notes

- Lambda functions are **region-specific**. Make sure you deploy and test in the same region as your target EC2 instances.
- Use environment variables for more flexibility (e.g., instance IDs, region).
