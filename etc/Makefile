#
# Admin Makefile. Used by CSCI E-11 course administrators.
#
# This file is provided for students to see, but not to use.
#

CANONICAL_OWNER_ID=099720109477
SSH_KEY_NAME=seasons
REGION?=us-east-2

# Canonical Ubuntu 26.04 LTS AMD64 images published 2026-08-19.
AMI_us-east-1=ami-03ceeebf93c41fdae
AMI_us-east-2=ami-066bae1901917f0ae
AMI_ARN_us-east-1=arn:aws:ec2:us-east-1::image/$(AMI_us-east-1)
AMI_ARN_us-east-2=arn:aws:ec2:us-east-2::image/$(AMI_us-east-2)
AMI=$(AMI_$(REGION))
AMI_ARN=$(AMI_ARN_$(REGION))

list-running-instances:
	aws ec2 describe-instances \
	  --filters "Name=instance-state-name,Values=running" \
	  --region $(REGION) \
	  --query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,PublicIP:PublicIpAddress,LaunchTime:LaunchTime,AZ:Placement.AvailabilityZone}' \
	  --output table

list-security-groups:
	aws ec2 describe-security-groups --region $(REGION) --query 'SecurityGroups[].{Description:Description,GroupId:GroupId,GroupName:GroupName}' --output table

list-lts-images:
	aws ec2 describe-images \
	  --region $(REGION) \
	  --owners $(CANONICAL_OWNER_ID) \
	  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-resolute-26.04-amd64-server-*" \
	            "Name=state,Values=available" \
	  --query 'reverse(sort_by(Images, &CreationDate))[:5].{ID:ImageId, Name:Name, CreationDate:CreationDate, Region:`$(REGION)`}' \
	  --output table

show-lts-image:
	@echo Region: $(REGION)
	@echo AMI: $(AMI)
	@echo ARN: $(AMI_ARN)

list-roles:
	aws iam list-roles --query 'Roles[*].RoleName' --output table

list-custom-policies:
	aws iam list-policies --scope Local --query 'Policies[*].{Name:PolicyName,Arn:Arn}' --output table

.PHONY: list-running-instances list-security-groups list-lts-images show-lts-image list-roles list-custom-policies
