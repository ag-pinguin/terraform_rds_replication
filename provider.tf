# We need access to two AWS accounts - source and destination

provider "aws" {
  alias = "src"
}

provider "aws" {
  alias = "dst"
}

data "aws_caller_identity" "source" {
  provider = aws.src
}

data "aws_caller_identity" "dest" {
  provider = aws.dst
}

