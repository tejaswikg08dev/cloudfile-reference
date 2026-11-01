# 21g — Inside Each Runbook Phase (what really happens)

The runbook (doc 19) gives commands. Here's what each command does **under the
hood** — the AWS API calls and state changes.

---

## `terraform init`

What you run:
```bash
terraform init
```

What happens internally:
1. Terraform reads `providers.tf` to see which plugins are needed.
2. Downloads them into a hidden `.terraform/` folder (the AWS, random, archive
   providers).
3. Sets up the **backend** (where state is stored — local file by default).
4. Creates a lock file (`.terraform.lock.hcl`) pinning provider versions.

No AWS resources are touched. It's just setup. You run it once per project (and
again if you add a provider).

---

## `terraform plan`

What you run:
```bash
terraform plan
```

What happens internally:
1. **Parse** all `.tf` files → the desired state.
2. **Refresh** → read the current state file; for existing resources, query AWS
   to see their real current state.
3. **Diff** → compare desired vs. actual, build the dependency graph.
4. **Print** the plan: `+` to create, `~` to change, `-` to destroy, with a
   summary like `Plan: 25 to add, 0 to change, 0 to destroy`.

`plan` changes **nothing**. It's a dry run. Always read it before `apply`.

> On the first run, state is empty → everything shows `+` (to add).

---

## `terraform apply` (Phase 1: infra, services at 0)

What you run:
```bash
export TF_VAR_db_password=...
export TF_VAR_jwt_secret_key=...
terraform apply          # type: yes
```

What happens internally:
1. Does a `plan` first and shows it; you type `yes`.
2. Walks the dependency graph and makes **AWS API calls** in order:
   - `CreateVpc`, `CreateSubnet` ×2, `CreateInternetGateway`,
     `CreateRouteTable`, `AssociateRouteTable`
   - `CreateSecurityGroup` (ecs, then rds which references ecs)
   - `CreateRepository` ×3 (ECR)
   - `CreateRole` / `PutRolePolicy` (IAM)
   - `CreateDBSubnetGroup`, `CreateDBInstance` (RDS — **this is the slow one,
     ~5–10 min**; AWS provisions a managed Postgres server)
   - `CreateBucket` + `PutBucketNotification` (S3)
   - `CreateFunction` (Lambda) + `AddPermission`
   - `CreateCluster`, `RegisterTaskDefinition` ×3, `CreateService` ×3
     (services at **desired_count 0** → no tasks launched yet)
3. After each successful call, writes the resource's real ID into
   `terraform.tfstate`.
4. Prints the `outputs` (ECR URLs, RDS endpoint, bucket name).

End state: all infrastructure exists, **nothing is running yet** (0 tasks).

---

## Build & push images (Docker + ECR, not Terraform)

What you run:
```bash
aws ecr get-login-password ... | docker login ...
docker build -t <registry>/cloudfile-auth:latest -f services/auth/Dockerfile .
docker push <registry>/cloudfile-auth:latest
# (repeat for files, search)
```

What happens internally:
1. `aws ecr get-login-password` → asks AWS for a temporary Docker password for
   your account's ECR. `docker login` uses it to authenticate.
2. `docker build` → runs the multi-stage Dockerfile: installs deps in a builder
   stage, copies app + shared code into a slim runtime image. Produces a local
   image.
3. `docker push` → uploads the image **layers** to the ECR repository. Only
   changed layers upload (content-addressed), so repeats are fast.

Now the ECR repos (created by Terraform) actually contain images.

---

## `terraform apply -var="service_desired_count=1"` (Phase 2: start)

What you run:
```bash
terraform apply -var="service_desired_count=1"   # type: yes
```

What happens internally:
1. `plan` sees only ONE thing changed: `desired_count` on the 3 ECS services
   (0 → 1). Everything else matches state → unchanged.
2. Makes 3 `UpdateService` calls setting desired count to 1.
3. ECS reacts: for each service it launches a **Fargate task**:
   - allocates a micro VM behind the scenes (you never see it),
   - pulls the image from ECR (using the **execution role**),
   - injects the env vars (DB URL, JWT, S3 bucket),
   - starts the container, which connects to RDS and begins serving,
   - assigns a **public IP** (because `assign_public_ip = true`),
   - streams logs to **CloudWatch**.
4. Within 1–3 minutes each service shows `running: 1`.

> Why so little changed: Terraform only touches the diff. Changing one variable
> → one field update → fast.

---

## Testing (Phase 4)

Not Terraform — just HTTP calls to the task public IPs (see doc 20). Internally:
your curl → IGW → ECS SG allows 8001–8003 → container → RDS/S3 as needed → back.

---

## `terraform destroy` (Phase 6)

What you run:
```bash
terraform destroy      # type: yes
```

What happens internally:
1. Reads the state file to know exactly what exists.
2. Builds the dependency graph and walks it **in REVERSE** (delete dependents
   before their dependencies):
   - `DeleteService` ×3 (stops tasks → **Fargate billing stops here**)
   - `DeregisterTaskDefinition`, `DeleteCluster`
   - `DeleteFunction` (Lambda), `DeleteBucket` (works because `force_destroy`)
   - `DeleteDBInstance` (RDS — works because `skip_final_snapshot` +
     `deletion_protection = false`)
   - `DeleteRepository` ×3 (works because `force_delete`)
   - delete IAM roles/policies, SGs, subnets, route table, IGW, VPC
3. Empties the state file as each resource is removed.

End state: back to zero. **The meter stops.** Verify with the `aws ... list`
commands in the runbook's Phase 6.

---

## Timing expectations

| Phase | Typical time | Why |
|-------|--------------|-----|
| init | 10–30s | downloading providers |
| plan | a few seconds | just diffing |
| apply (phase 1) | **5–10 min** | RDS provisioning dominates |
| build + push images | 3–8 min | Docker build + upload |
| apply (phase 2) | 1–3 min | ECS launches tasks |
| destroy | 5–10 min | RDS deletion is slow too |

---

## Check your understanding

- *Q: Does `plan` change anything?* → No, it's a dry run.
- *Q: Why is apply slow?* → RDS takes several minutes to provision.
- *Q: Why two applies?* → Create ECR empty → push images → then start tasks.
- *Q: When does billing stop on destroy?* → As soon as the ECS services (tasks)
  are deleted; RDS deletion follows.

Next: [21h — A request's journey through live AWS →](21h-request-journey.md)
