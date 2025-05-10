# AWS VPC FAQ

## 1. What is a Public Subnet?
A public subnet is a subnet within a VPC that has a route to the Internet through an Internet Gateway (IGW). Instances in a public subnet have public IP addresses or Elastic IPs, allowing direct access from the Internet.

## 2. What is a Private Subnet?
A private subnet is a subnet that does not have direct access to the Internet. Instances in a private subnet communicate with the Internet via a NAT Gateway or a VPC Endpoint.

## 3. How do you access an instance from a Private Subnet?
To access an instance in a private subnet, you can:
- Use a **Bastion Host** in a public subnet.
- Set up a **VPN or Direct Connect**.
- Use **AWS Systems Manager Session Manager**.

## 4. Application Load Balancer: Public Subnet or Private Subnet?
- **Public Subnet**: If the ALB is serving traffic from the Internet, it should be placed in a public subnet.
- **Private Subnet**: If the ALB is serving internal traffic (e.g., for microservices), it should be placed in a private subnet.

## 5. What is a NAT Gateway?
A NAT Gateway allows instances in a private subnet to initiate outbound Internet connections while preventing inbound connections from the Internet.

## 6. What is an Internet Gateway?
An Internet Gateway (IGW) allows resources in a VPC to communicate with the Internet. It enables outbound and inbound traffic for public subnets.

## 7. How do you access an S3 bucket that is outside a VPC?
- Use an **S3 VPC Endpoint (Gateway Type)** to privately access S3 without traversing the public Internet.
- Use a **NAT Gateway** if instances are in a private subnet.
- Use **AWS PrivateLink** if a SaaS provider exposes S3 services.

## 8. What is a VPC Endpoint (Gateway) and why is it used?
A **VPC Gateway Endpoint** allows instances in a VPC to privately access AWS services like S3 and DynamoDB without needing an Internet Gateway or NAT Gateway.

## 9. What is a VPC Endpoint (Interface Type) and why is it used?
A **VPC Interface Endpoint** enables private connectivity to AWS services over AWS PrivateLink, using ENIs within the VPC. This is used for services like AWS Secrets Manager, API Gateway, and CloudWatch.

## 10. How do we access a Third-Party SaaS Application from our VPC?
- **VPC Peering** (if the SaaS provider allows it).
- **AWS PrivateLink** (if the provider supports it).
- **Public Internet** with appropriate security configurations.

## 11. What is PrivateLink and why do we use it?
AWS PrivateLink allows secure, private connectivity between VPCs and AWS services or third-party applications without exposing traffic to the public Internet.

## 12. How do we communicate between VPCs?
- **VPC Peering** (for direct communication between two VPCs).
- **Transit Gateway** (for scalable connectivity across multiple VPCs).
- **AWS PrivateLink** (for accessing specific services securely).

## 13. How do we communicate between multiple VPCs?
- **VPC Peering** (for small-scale setups).
- **Transit Gateway** (for scalable, centralized connectivity).
- **AWS PrivateLink** (for service-specific connections).

## 14. What is VPC Peering?
VPC Peering enables direct communication between two VPCs using private IPs. It is suitable for connecting a limited number of VPCs within or across AWS accounts.

## 15. What is a Transit Gateway?
AWS Transit Gateway acts as a central hub that connects multiple VPCs, on-premises networks, and Direct Connect gateways for scalable and secure networking.

## 16. Ways to enable connectivity between On-Premises Data Centers and AWS:
- **AWS Direct Connect** (dedicated fiber connection).
- **Site-to-Site VPN** (encrypted tunnel over the Internet).
- **Transit Gateway** (for managing multiple VPN connections).
- **VPC Peering** (for limited use cases).

## 17. What is Client VPN and why do we use it?
AWS Client VPN provides a secure, encrypted connection for remote users to access AWS and on-prem resources securely. It is used to enable remote access without requiring a bastion host or public exposure.
