# Deploy Mini Kanban to AWS with CloudFormation.
# You create the IAM user; this script only uses whatever `aws` is already configured as.
# Watch the numbered steps.

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$Region = if ($env:AWS_REGION) { $env:AWS_REGION } elseif ($env:AWS_DEFAULT_REGION) { $env:AWS_DEFAULT_REGION } else { "us-east-1" }
$EcrStack = "mini-kanban-ecr"
$AppStack = "mini-kanban-app"

function Step($n, $msg) {
    Write-Host ""
    Write-Host "=== STEP ${n}: $msg ===" -ForegroundColor Cyan
}

function Require-Aws {
    $aws = Get-Command aws -ErrorAction SilentlyContinue
    if (-not $aws) {
        throw "AWS CLI is not installed. Install it, then create a temporary admin IAM user and run: aws configure"
    }
}

Step 0 "Who am I? (sts:GetCallerIdentity)"
Require-Aws
aws sts get-caller-identity --region $Region
if ($LASTEXITCODE -ne 0) {
    throw "No AWS credentials. Create a temporary admin user in the IAM console, then run: aws configure"
}

Step 1 "CloudFormation stack $EcrStack (ECR repository only)"
aws cloudformation deploy `
    --region $Region `
    --stack-name $EcrStack `
    --template-file "$RepoRoot\infra\ecr.yml" `
    --no-fail-on-empty-changeset
if ($LASTEXITCODE -ne 0) { throw "ECR stack failed" }

$ImageUri = aws cloudformation describe-stacks `
    --region $Region `
    --stack-name $EcrStack `
    --query "Stacks[0].Outputs[?OutputKey=='RepositoryUri'].OutputValue" `
    --output text
$ImageTag = "${ImageUri}:latest"
Write-Host "ECR image will be $ImageTag"

Step 2 "Docker login to ECR, build linux/amd64 image, push"
$Account = aws sts get-caller-identity --query Account --output text
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$Account.dkr.ecr.$Region.amazonaws.com"
if ($LASTEXITCODE -ne 0) { throw "ECR login failed" }

docker build --platform linux/amd64 -t $ImageTag $RepoRoot
if ($LASTEXITCODE -ne 0) { throw "docker build failed" }

docker push $ImageTag
if ($LASTEXITCODE -ne 0) { throw "docker push failed" }

Step 3 "CloudFormation stack $AppStack (VPC, RDS, ALB, ECS Fargate)"
aws cloudformation deploy `
    --region $Region `
    --stack-name $AppStack `
    --template-file "$RepoRoot\infra\app.yml" `
    --capabilities CAPABILITY_NAMED_IAM `
    --parameter-overrides "ImageUri=$ImageTag" `
    --no-fail-on-empty-changeset
if ($LASTEXITCODE -ne 0) { throw "App stack failed" }

$AppUrl = aws cloudformation describe-stacks `
    --region $Region `
    --stack-name $AppStack `
    --query "Stacks[0].Outputs[?OutputKey=='AppUrl'].OutputValue" `
    --output text

Step 4 "Wait for /health (ALB + first task can take several minutes)"
$deadline = (Get-Date).AddMinutes(15)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        $body = (Invoke-WebRequest -Uri "$AppUrl/health" -UseBasicParsing -TimeoutSec 10).Content
        if ($body -match '"status"\s*:\s*"ok"') { $ready = $true; break }
    } catch {
        Write-Host "  not ready yet: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds 15
}
if (-not $ready) { throw "Timed out waiting for $AppUrl/health" }

Write-Host ""
Write-Host "Deployed. Open $AppUrl" -ForegroundColor Green
Write-Host "Tear down later: aws cloudformation delete-stack --stack-name $AppStack --region $Region"
Write-Host "                 aws cloudformation delete-stack --stack-name $EcrStack --region $Region"
