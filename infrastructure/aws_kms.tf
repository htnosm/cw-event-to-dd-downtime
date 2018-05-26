resource "aws_kms_key" "cw-event-to-dd-downtime_kms_key" {
  description = "cw-event-to-dd-downtime"
  policy = <<_EOF
{
  "Id": "key-cw-event-to-dd-downtime-policy",
  "Statement": [
    {
      "Action": "kms:*",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${data.aws_caller_identity.self.account_id}:root"
      },
      "Resource": "*",
      "Sid": "Enable IAM User Permissions"
    },
    {
      "Action": [
        "kms:Create*",
        "kms:Describe*",
        "kms:Enable*",
        "kms:List*",
        "kms:Put*",
        "kms:Update*",
        "kms:Revoke*",
        "kms:Disable*",
        "kms:Get*",
        "kms:Delete*",
        "kms:TagResource",
        "kms:UntagResource",
        "kms:ScheduleKeyDeletion",
        "kms:CancelKeyDeletion"
      ],
      "Effect": "Allow",
      "Principal": {
        "AWS": "${aws_iam_role.cw-event-to-dd-downtime_role.arn}"
      },
      "Resource": "*",
      "Sid": "Allow access for Key Administrators"
    }
  ],
  "Version": "2012-10-17"
}
_EOF
}

resource "aws_kms_alias" "cw-event-to-dd-downtime_kms_alias" {
  name          = "alias/cw-event-to-dd-downtime"
  target_key_id = "${aws_kms_key.cw-event-to-dd-downtime_kms_key.key_id}"
}

output "kms_key_id" {
  value = "${aws_kms_key.cw-event-to-dd-downtime_kms_key.key_id}"
}

output "kms_key_arn" {
  value = "${aws_kms_key.cw-event-to-dd-downtime_kms_key.arn}"
}
