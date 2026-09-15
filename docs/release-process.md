# Release process

1. **PR to main.** `.github/workflows/ci.yml` runs frontend and backend tests in parallel, then Compose integration + e2e.
2. **Merge.** Push to `main` runs CI again. If `AWS_ROLE_ARN` is set, it deploys via OIDC and checks `GET /health`.
3. **Version tag** (optional extra publish):

   ```bash
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin v0.1.0
   ```

   That starts `deploy.yml` the same way (ECR + CloudFormation + health).
4. **Confirm.** Actions log shows the ALB URL; `curl -fsS "$URL/health"` is `{"status":"ok"}`.
5. **Hotfix.** PR to main, merge (auto-deploy). Patch tag if you want a named image (`v0.1.1`). Do not retag.

Manual deploy: **Actions → Deploy → Run workflow**, or `.\infra\deploy.ps1` with a local admin user.

OIDC role setup is in [deployment.md](deployment.md).
