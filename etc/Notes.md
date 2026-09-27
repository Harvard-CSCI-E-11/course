Import a key paid:
```
KEYFILE=$HOME/.ssh/id_ed25519.pub
aws ec2 import-key-pair \
  --key-name mykey \
  --public-key-material fileb://$KEYFILE \
  --region us-east-2
```

List key pairs:
```
aws ec2 describe-key-pairs --region us-east-2 --output table
```

Describe LTS images:
```
aws ec2 describe-images \
  --region us-east-2 \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-resolute-26.04-amd64-server-*" \
            "Name=state,Values=available" \
  --query 'reverse(sort_by(Images, &CreationDate))[:5].{ID:ImageId, Name:Name, CreationDate:CreationDate, Region:`us-east-2`}' \
  --output table
```

Canonical Ubuntu 26.04 LTS AMD64 images published 2026-08-19:

| Region | AMI ID | EC2 image ARN |
|---|---|---|
| `us-east-1` | `ami-03ceeebf93c41fdae` | `arn:aws:ec2:us-east-1::image/ami-03ceeebf93c41fdae` |
| `us-east-2` | `ami-066bae1901917f0ae` | `arn:aws:ec2:us-east-2::image/ami-066bae1901917f0ae` |

For automation that should always use Canonical's current Ubuntu 26.04 AMD64
image, resolve this public SSM parameter in the target region:

```
/aws/service/canonical/ubuntu/server/26.04/stable/current/amd64/hvm/ebs-gp3/ami-id
```


Launch an instance:
```
aws ec2 run-instances \
	  --instance-type t3a.nano \
	  --image-id $AMI \
	  --key-name $SSH_KEY_NAME \
	  --region $REGION \
	  --tag-specifications  'ResourceType=instance,Tags=[{Key=Name,Value=makefile-launch}]'
 ```


Delete unused security groups:
```
for sg in $(aws ec2 describe-security-groups --region us-east-2 --query 'SecurityGroups[].{GroupId:GroupId}' --output text)
  do
	echo $sg
    aws ec2 delete-security-group --region us-east-2 --group-id $sg
  done
```
