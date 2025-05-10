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
