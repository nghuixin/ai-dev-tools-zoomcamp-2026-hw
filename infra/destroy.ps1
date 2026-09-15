$ErrorActionPreference = "Stop"
$Region = if ($env:AWS_REGION) { $env:AWS_REGION } elseif ($env:AWS_DEFAULT_REGION) { $env:AWS_DEFAULT_REGION } else { "us-east-1" }

Write-Host "Deleting mini-kanban-app (RDS + Fargate + ALB)..."
aws cloudformation delete-stack --region $Region --stack-name mini-kanban-app
aws cloudformation wait stack-delete-complete --region $Region --stack-name mini-kanban-app

Write-Host "Deleting mini-kanban-ecr..."
aws cloudformation delete-stack --region $Region --stack-name mini-kanban-ecr
aws cloudformation wait stack-delete-complete --region $Region --stack-name mini-kanban-ecr

Write-Host "Stacks gone."
