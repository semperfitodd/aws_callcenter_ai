module "cdn" {
  source = "terraform-aws-modules/cloudfront/aws"

  aliases = [local.site_domain]

  comment             = "${title(var.environment)} Site CDN"
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = "PriceClass_100"
  retain_on_delete    = false
  wait_for_deployment = false

  default_root_object = "index.html"

  create_origin_access_identity = true
  origin_access_identities = {
    site_bucket = "Site Bucket Access ID"
  }

  origin = {
    api_gw = {
      domain_name = replace(module.api_gateway.apigatewayv2_api_api_endpoint, "/^https?://([^/]*).*/", "$1")

      custom_origin_config = {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "match-viewer"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }

    s3_one = {
      domain_name = module.site_s3_bucket.s3_bucket_bucket_domain_name

      s3_origin_config = {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "match-viewer"
        origin_ssl_protocols   = ["TLSv1.2"]
        origin_access_identity = "site_bucket"
        viewer_protocol_policy = "redirect-to-https"
      }
    }
  }

  default_cache_behavior = {
    target_origin_id       = "s3_one"
    viewer_protocol_policy = "allow-all"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true
    query_string    = true
  }

  ordered_cache_behavior = [
    {
      path_pattern           = "/data"
      target_origin_id       = "api_gw"
      viewer_protocol_policy = "redirect-to-https"

      allowed_methods = ["GET", "HEAD", "OPTIONS", "POST", "DELETE", "PUT", "PATCH"]
      cached_methods  = ["GET", "HEAD"]
      compress        = true
      query_string    = true
    },
    {
      path_pattern           = "*"
      target_origin_id       = "s3_one"
      viewer_protocol_policy = "redirect-to-https"

      allowed_methods = ["GET", "HEAD", "OPTIONS"]
      cached_methods  = ["GET", "HEAD"]
      compress        = true
      query_string    = true
    }
  ]

  viewer_certificate = {
    acm_certificate_arn = aws_acm_certificate.this.arn
    ssl_support_method  = "sni-only"
  }

  tags = var.tags
}

resource "aws_acm_certificate" "this" {
  domain_name       = local.site_domain
  validation_method = "DNS"

  tags = merge(var.tags,
    {
      Name = local.site_domain
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "verify" {
  for_each = {
    for dvo in aws_acm_certificate.this.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.this.zone_id
}