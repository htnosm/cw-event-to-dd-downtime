resource "aws_iam_role" "cw-event-to-dd-downtime_role" {
  name               = "cw-event-to-dd-downtime"
  path               = "/"
  assume_role_policy = "${data.aws_iam_policy_document.cw-event-to-dd-downtime_lambda_function_assume_role_policy.json}"
}

data "aws_iam_policy_document" "cw-event-to-dd-downtime_lambda_function_assume_role_policy" {
  statement {
    effect = "Allow"
    principals {
      identifiers = [
        "lambda.amazonaws.com"
      ]
      type = "Service"
    }
    actions = [
      "sts:AssumeRole"
    ]
  }
}

resource "aws_iam_role_policy" "cw-event-to-dd-downtime_role_policy" {
  name = "cw-event-to-dd-downtime_lambda_policy"
  role = "${aws_iam_role.cw-event-to-dd-downtime_role.id}"
  policy = "${data.aws_iam_policy_document.cw-event-to-dd-downtime_role_policy.json}"
}
data "aws_iam_policy_document" "cw-event-to-dd-downtime_role_policy" {
  statement {
    effect = "Allow"
    actions = [
      "logs:*",
      "kms:Decrypt",
      "iam:GetPolicy",
      "iam:GetPolicyVersion",
      "lambda:InvokeAsync",
      "lambda:InvokeFunction",
      "lambda:ListFunctions",
    ]
    resources = [ "*" ]
  }
}

output "iam_role_arn" {
  value = "${aws_iam_role.cw-event-to-dd-downtime_role.arn}"
}
