terraform {
  backend "s3" {
    bucket = "bsc.sandbox.terraform.state"
    key    = "aws_callcenter_ai"
    region = "us-east-2"
  }
}