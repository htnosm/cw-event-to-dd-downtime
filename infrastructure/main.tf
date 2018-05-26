terraform {
  required_version = "~> 0.11.1"

#  backend "s3" {
#    bucket = ""
#    key    = "tf/terraform.tfstate"
#    region = "ap-northeast-1"
#  }
}

// Provider specific configs
provider "aws" {
  version = "~> 1.6.0"
  #access_key = "${var.aws_access_key}"
  #secret_key = "${var.aws_secret_key}"
  region = "${var.aws_region}"
}

data "aws_caller_identity" "self" {}

variable aws_region {
  default = "ap-northeast-1"
}
