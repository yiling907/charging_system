provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "user_avatar_bucket" {
  bucket = "user-avatar-bucket-dev"
  tags = {
    Name        = "Avatar Upload Bucket"
    Environment = "Dev"
  }
}

resource "aws_sqs_queue" "order_status_queue" {
  name                      = "order-status-change-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400
  receive_wait_time_seconds = 20
}

data "archive_file" "requests_layer_zip" {
  type        = "zip"
  source_dir  = ".lambda_layers/requests/"
  output_path = ".lambda_layers/requests_layer.zip"
}

resource "aws_lambda_layer_version" "requests_layer" {
  layer_name          = "requests-layer"
  description         = "Layer containing requests library for Python"
  filename            = data.archive_file.requests_layer_zip.output_path
  source_code_hash    = data.archive_file.requests_layer_zip.output_base64sha256
  compatible_runtimes = ["python3.11", "python3.10", "python3.9"]
}


resource "aws_lambda_function" "create_order_function" {
  function_name    = "create-order-function"
  filename         = "create_order.zip"
  source_code_hash = filebase64sha256("create_order.zip")
  handler          = "create_order.handler"
  runtime          = "python3.9"
  role             = "arn:aws:iam::362643364860:role/LabRole"

  environment {
    variables = {
      CHARGER_STATUS_CHANGE_QUEUE_URL = aws_sqs_queue.order_status_queue.url
      UPDATE_PAYMENT_STATUS_API       = "http://chargingdev.eba-bmzp7bju.us-east-1.elasticbeanstalk.com/api/charging/records/",
      UPDATE_CHARGER_STATUS_API       = "http://chargingdev.eba-bmzp7bju.us-east-1.elasticbeanstalk.com/api/charging/chargers/",
      SCHEDULED_UPDATE_LAMBDA_ARN     = aws_lambda_function.scheduled_status_update_function.arn,
      AWS_ACCOUNT_ID                  = "362643364860"
    }
  }
  layers = [
    aws_lambda_layer_version.requests_layer.arn
  ]

}


resource "aws_lambda_function" "scheduled_status_update_function" {
  function_name    = "scheduled-status-update-function"
  filename         = "scheduled_update.zip"
  source_code_hash = filebase64sha256("scheduled_update.zip")
  handler          = "scheduled_update.handler"
  runtime          = "python3.9"
  role             = "arn:aws:iam::362643364860:role/LabRole"

  environment {
    variables = {
      UPDATE_CHARGER_STATUS_API = "http://chargingdev.eba-bmzp7bju.us-east-1.elasticbeanstalk.com/api/charging/chargers/",
      AWS_ACCOUNT_ID            = "362643364860",
    }
  }
  layers = [
    aws_lambda_layer_version.requests_layer.arn
  ]
}

resource "aws_lambda_function" "upload_avatar_function" {
  function_name    = "upload-avatar-function"
  filename         = "upload_avatar.zip"
  source_code_hash = filebase64sha256("upload_avatar.zip")
  handler          = "upload_avatar.handler"
  runtime          = "python3.9"
  role             = "arn:aws:iam::362643364860:role/LabRole"

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.user_avatar_bucket.bucket,
    }
  }
  layers = [
    aws_lambda_layer_version.requests_layer.arn
  ]
}


resource "aws_api_gateway_rest_api" "gateway" {
  name                         = "IntegrationAPI"
  api_key_source               = "HEADER"
  disable_execute_api_endpoint = false

  endpoint_configuration {
    types = ["EDGE"]
  }

  binary_media_types = [
    "*/*"
  ]
}

resource "aws_api_gateway_resource" "root" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = ""
  path_part   = ""
}

resource "aws_api_gateway_resource" "backend" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.root.id
  path_part   = "backend"
}

resource "aws_api_gateway_resource" "service_management" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.root.id
  path_part   = "service_management"
}

resource "aws_api_gateway_resource" "html" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.root.id
  path_part   = "html"
}

resource "aws_api_gateway_resource" "s3" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.root.id
  path_part   = "s3"
}


resource "aws_api_gateway_resource" "user_id" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.s3.id
  path_part   = "{user_id}"
}


resource "aws_api_gateway_resource" "image_name" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.user_id.id
  path_part   = "{image_name}"
  depends_on  = [aws_api_gateway_resource.user_id]
}


resource "aws_api_gateway_method" "get_image" {
  rest_api_id   = aws_api_gateway_rest_api.gateway.id
  resource_id   = aws_api_gateway_resource.image_name.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.user_id"    = true
    "method.request.path.image_name" = true
    "method.request.header.Accept"   = true

  }
}


resource "aws_api_gateway_method_response" "response_200" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  resource_id = aws_api_gateway_resource.image_name.id
  http_method = aws_api_gateway_method.get_image.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration" "s3_integration" {
  rest_api_id             = aws_api_gateway_rest_api.gateway.id
  resource_id             = aws_api_gateway_resource.image_name.id
  http_method             = aws_api_gateway_method.get_image.http_method
  integration_http_method = "GET"
  type                    = "AWS"
  uri                     = "arn:aws:apigateway:us-east-1:s3:path/user-avatar-bucket-dev/{user_id}/{image_name}"
  connection_type         = "INTERNET"
  credentials             = "arn:aws:iam::362643364860:role/LabRole"

  request_parameters = {
    "integration.request.path.user_id"    = "method.request.path.user_id"
    "integration.request.path.image_name" = "method.request.path.image_name"
  }

}


resource "aws_api_gateway_integration_response" "s3_response" {
  rest_api_id       = aws_api_gateway_rest_api.gateway.id
  resource_id       = aws_api_gateway_resource.image_name.id
  http_method       = aws_api_gateway_method.get_image.http_method
  status_code       = aws_api_gateway_method_response.response_200.status_code
  selection_pattern = aws_api_gateway_method_response.response_200.status_code

  content_handling = "CONVERT_TO_TEXT"

  response_templates = {
    "application/json" = "$input.body" # 直接返回 Base64 编码后的字符串
  }
  depends_on = [aws_api_gateway_integration.s3_integration]

}
resource "aws_api_gateway_resource" "backend_proxy" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.backend.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_resource" "html_proxy" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.html.id
  path_part   = "{proxy+}"
}


resource "aws_api_gateway_resource" "orders" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.service_management.id
  path_part   = "orders"
}

resource "aws_api_gateway_resource" "user" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.service_management.id
  path_part   = "user"
}

resource "aws_api_gateway_resource" "upload_avatar" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_resource.user.id
  path_part   = "avatar"
}

resource "aws_api_gateway_method" "backend_proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.gateway.id
  resource_id   = aws_api_gateway_resource.backend_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "backend_proxy_integration" {
  rest_api_id             = aws_api_gateway_rest_api.gateway.id
  resource_id             = aws_api_gateway_resource.backend_proxy.id
  http_method             = aws_api_gateway_method.backend_proxy_method.http_method
  integration_http_method = "ANY"
  type                    = "HTTP_PROXY"
  uri                     = "http://chargingdev.eba-bmzp7bju.us-east-1.elasticbeanstalk.com/{proxy}/"
  connection_type         = "INTERNET"

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }


  passthrough_behavior = "WHEN_NO_MATCH"
  timeout_milliseconds = 29000
}

resource "aws_api_gateway_method" "html_proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.gateway.id
  resource_id   = aws_api_gateway_resource.html_proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}


resource "aws_api_gateway_integration" "html_proxy_integration" {
  rest_api_id             = aws_api_gateway_rest_api.gateway.id
  resource_id             = aws_api_gateway_resource.html_proxy.id
  http_method             = aws_api_gateway_method.html_proxy_method.http_method
  integration_http_method = "GET"
  type                    = "AWS"
  uri                     = "arn:aws:apigateway:us-east-1:s3:path/charging-system/templates/{proxy}"
  connection_type         = "INTERNET"
  credentials             = "arn:aws:iam::362643364860:role/LabRole"

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }

  passthrough_behavior = "WHEN_NO_MATCH"
  timeout_milliseconds = 29000
}



resource "aws_api_gateway_method" "create_order_method" {
  rest_api_id   = aws_api_gateway_rest_api.gateway.id
  resource_id   = aws_api_gateway_resource.orders.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "upload_avatar_method" {
  rest_api_id   = aws_api_gateway_rest_api.gateway.id
  resource_id   = aws_api_gateway_resource.upload_avatar.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "orders_create_integration" {
  rest_api_id             = aws_api_gateway_rest_api.gateway.id
  resource_id             = aws_api_gateway_resource.orders.id
  http_method             = aws_api_gateway_method.create_order_method.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.create_order_function.invoke_arn
  integration_http_method = "POST"
}

resource "aws_lambda_permission" "orders_create_lambda_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_order_function.function_name
  principal     = "apigateway.amazonaws.com"


  source_arn = "${aws_api_gateway_rest_api.gateway.execution_arn}/*"
}

resource "aws_api_gateway_integration" "upload_avatar_integration" {
  rest_api_id             = aws_api_gateway_rest_api.gateway.id
  resource_id             = aws_api_gateway_resource.upload_avatar.id
  http_method             = aws_api_gateway_method.upload_avatar_method.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.upload_avatar_function.invoke_arn
  integration_http_method = "POST"
}

resource "aws_lambda_permission" "upload_avatar_lambda_permission" {
  statement_id  = "AllowUploadAvatarFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_avatar_function.function_name
  principal     = "apigateway.amazonaws.com"


  source_arn = "${aws_api_gateway_rest_api.gateway.execution_arn}/*"
}

resource "aws_api_gateway_deployment" "dev" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.gateway.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.dev.id
  rest_api_id   = aws_api_gateway_rest_api.gateway.id
  stage_name    = "dev"
}


output "api_dev_invoke_url" {
  value = aws_api_gateway_stage.dev.invoke_url
}

output "api_arn" {
  value = aws_api_gateway_rest_api.gateway.arn
}

output "dev_stage_arn" {
  value = aws_api_gateway_stage.dev.arn
}

