module "lambda_function_frontend" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "${var.environment}_frontend_function"
  description   = "${var.environment} function to get data from DynamoDB and pass to frontend"
  handler       = "frontend.lambda_handler"
  publish       = true
  runtime       = "python3.11"

  memory_size = 512
  timeout     = 5

  environment_variables = {
    DYNAMO_TABLE = module.dynamo.dynamodb_table_id
  }

  source_path = [
    {
      path             = "${path.module}/lambda_frontend"
      pip_requirements = false
    }
  ]

  attach_policies = true
  policies        = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  attach_policy_statements = true
  policy_statements = {
    dynamo = {
      effect    = "Allow",
      actions   = ["dynamodb:*"],
      resources = [module.dynamo.dynamodb_table_arn]
    }
  }

  allowed_triggers = {
    AllowExecutionFromAPIGateway = {
      service    = "apigateway"
      source_arn = "${module.api_gateway.apigatewayv2_api_execution_arn}/*/*"
    }
  }

  cloudwatch_logs_retention_in_days = 3

  tags = var.tags
}

module "lambda_function_ingest" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "${var.environment}_ingest_function"
  description   = "${var.environment} function to gain insights and put data in DynamoDB"
  handler       = "ingest.lambda_handler"
  publish       = true
  runtime       = "python3.11"

  memory_size = 256
  timeout     = 60

  environment_variables = {
    DYNAMO_TABLE         = module.dynamo.dynamodb_table_id
    TRANSCRIBE_S3_BUCKET = module.call_transcription_s3_bucket.s3_bucket_id
  }

  source_path = [
    {
      path             = "${path.module}/lambda_ingest"
      pip_requirements = true
    }
  ]

  attach_policies = true
  policies        = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]

  attach_policy_statements = true
  policy_statements = {
    bedrock = {
      effect    = "Allow",
      actions   = ["bedrock:InvokeModel"],
      resources = ["*"]
    }
    comprehend = {
      effect    = "Allow",
      actions   = ["comprehend:*"],
      resources = ["*"]
    }
    dynamo = {
      effect    = "Allow",
      actions   = ["dynamodb:*"],
      resources = [module.dynamo.dynamodb_table_arn]
    }
    s3 = {
      effect  = "Allow",
      actions = ["s3:*"],
      resources = [
        module.call_recording_s3_bucket.s3_bucket_arn,
        "${module.call_recording_s3_bucket.s3_bucket_arn}/*",
        module.call_transcription_s3_bucket.s3_bucket_arn,
        "${module.call_transcription_s3_bucket.s3_bucket_arn}/*"
      ]
    }
    transcribe = {
      effect    = "Allow",
      actions   = ["transcribe:*"],
      resources = ["*"]
    }
  }

  cloudwatch_logs_retention_in_days = 3

  tags = var.tags
}
