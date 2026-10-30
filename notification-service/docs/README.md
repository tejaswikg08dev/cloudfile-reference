# Notification Service Documentation

Documentation for the standalone notification microservice. This service lives
in its own repository to demonstrate the **separate-repo (polyrepo)** pattern
alongside the `cloudfile-platform` monorepo.

| # | Doc | What it covers |
|---|-----|----------------|
| 00 | [00-overview.md](00-overview.md) | What it does, where it fits, pitch |
| 01 | [01-design.md](01-design.md) | API, data model, providers, decisions |
| 02 | [02-local-deployment.md](02-local-deployment.md) | Run it locally, step by step |
| 03 | [03-testing.md](03-testing.md) | What's tested, how to run |
| 04 | [04-cloud-deployment.md](04-cloud-deployment.md) | Kubernetes + AWS notes |
| 05 | [05-real-email-setup.md](05-real-email-setup.md) | Real email: Mailtrap (local) + AWS SES (production) |

See also the top-level [README.md](../README.md).
