{
  "Version": "2012-10-17",
  "Statement": [
  {
    "Effect": "Allow",
    "Action": [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "ec2:CreateTags",
      "ec2:*",
      "ecr:*",
      "*"
    ],
    "Resource": "*"
  }
  ]
}