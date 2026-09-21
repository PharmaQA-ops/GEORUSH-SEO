# GEORUSH Security Checklist --- v1.0.0

## Before release

-   [ ] No API keys committed
-   [ ] No service-account JSON committed
-   [ ] No `.env` committed
-   [ ] Ollama bound to localhost
-   [ ] Backend not exposed without authentication
-   [ ] CORS restricted for shared production
-   [ ] GitHub repository access reviewed
-   [ ] Production secrets stored outside Git
-   [ ] Test data removed where required
-   [ ] Previous release archived

## Operational

-   [ ] Marketing users use named accounts where the deployment supports
    authentication
-   [ ] GA4/GSC access is least privilege
-   [ ] Credentials are rotated
-   [ ] Logs do not contain tokens
-   [ ] Ollama is not exposed publicly
-   [ ] Backup/rollback package retained
