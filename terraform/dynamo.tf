module "dynamo" {
  source = "terraform-aws-modules/dynamodb-table/aws"

  name = var.environment

  server_side_encryption_enabled = false
  deletion_protection_enabled    = false

  hash_key    = "UniqueId"
  table_class = "STANDARD"

  ttl_enabled = false

  attributes = [
    {
      name = "UniqueId"
      type = "S"
    }
  ]

  tags = var.tags
}
