# 🛑 AWS EC2 Multi-Region Instance Stopper (Lambda Script)

This AWS Lambda Python script stops EC2 instances across multiple AWS regions. Instances are defined in a hardcoded list inside the script. It’s useful for automating shutdowns of development or non-production environments to save costs.

---

## 📜 Python Code

```python
import boto3

def lambda_handler(event, context):
    region_map = {}

    for line in INSTANCE_LIST.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split()
        if len(parts) < 4:
            print(f"Skipping invalid line: {line}")
            continue

        instance_id, name, ip, region = parts[:4]
        print(f"Preparing to stop {name} ({instance_id}) in {region}, IP: {ip}")
        region_map.setdefault(region, []).append(instance_id)

    for region, instance_ids in region_map.items():
        print(f"Stopping instances in region {region}: {instance_ids}")
        ec2 = boto3.client('ec2', region_name=region)
        ec2.stop_instances(InstanceIds=instance_ids)


INSTANCE_LIST = """
# InstanceID           Name         IP_Address      Region
i-0123456789abcde      WebServer1   192.168.1.10    ap-south-1
i-0abcdef12345678      DBServer     192.168.1.11    us-east-1
i-0fedcba987654321     AppServer    192.168.1.12    eu-west-1
# i-00000000000000000  TestServer   192.168.1.99    us-west-2
"""

## 🧠 How It Works

### Step-by-Step Breakdown:

1. **Initialize a `region_map` dictionary**:
   - This dictionary will store regions as keys and lists of EC2 Instance IDs to stop as values.

2. **Parse the `INSTANCE_LIST`**:
   - The script reads each non-empty and uncommented line (ignores lines starting with `#`).
   - It splits the line into four parts: `instance_id`, `name`, `ip`, and `region`.

3. **Group Instances by Region**:
   - It populates `region_map` where each region maps to a list of instances in that region.

4. **Stop Instances Using Boto3**:
   - For each region in `region_map`, a regional EC2 client is created using `boto3`.
   - The script then sends a `stop_instances` request to AWS for the list of Instance IDs in that region.

## 📝 Example `INSTANCE_LIST`

```text
# InstanceID           Name         IP_Address      Region
i-0123456789abcde      WebServer1   192.168.1.10    ap-south-1
i-0abcdef12345678      DBServer     192.168.1.11    us-east-1
i-0fedcba987654321     AppServer    192.168.1.12    eu-west-1
# i-00000000000000000  TestServer   192.168.1.99    us-west-2
