# 21d — Networking Deep Dive

Networking is where most AWS confusion lives. Let's make it concrete using our
actual setup.

---

## The layers, from outside in

```
Internet
   │
   ▼
[ Internet Gateway (IGW) ]        ← the door to our VPC
   │
   ▼
┌──────────────── VPC  10.0.0.0/16 ────────────────┐   ← our private network
│                                                   │
│   Route Table (0.0.0.0/0 → IGW)                   │   ← "to reach internet, go to IGW"
│                                                   │
│   ┌── public subnet 10.0.0.0/24 (AZ a) ──┐        │
│   │   ECS task (has a public IP)          │        │
│   └───────────────────────────────────────┘        │
│   ┌── public subnet 10.0.1.0/24 (AZ b) ──┐        │
│   │   RDS lives across these 2 subnets    │        │
│   └───────────────────────────────────────┘        │
│                                                   │
│   Security Groups (firewalls on each resource)    │
└───────────────────────────────────────────────────┘
```

---

## IP addresses & CIDR (the `10.0.0.0/16` thing)

Every machine on a network has an **IP address** (like `10.0.0.5`). A **CIDR
block** describes a *range* of IPs.

- `10.0.0.0/16` = our whole VPC = IPs `10.0.0.0` → `10.0.255.255` (65,536 addresses).
- `10.0.0.0/24` = subnet 1 = IPs `10.0.0.0` → `10.0.0.255` (256 addresses).
- `10.0.1.0/24` = subnet 2 = the next 256.

> The `/number` means "how many bits are fixed." Smaller number = bigger range.
> `/16` is big (the whole plot); `/24` is a smaller section (one subnet).

From our `vpc.tf`:
```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"     # the whole private network
}
resource "aws_subnet" "public" {
  count      = 2
  cidr_block = "10.0.${count.index}.0/24"   # => 10.0.0.0/24 and 10.0.1.0/24
  availability_zone = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true            # resources here get a public IP
}
```
`count = 2` makes Terraform create the block twice (subnet 0 and subnet 1), each
in a different AZ.

---

## Public vs private subnets

- **Public subnet:** has a route to the Internet Gateway, so resources can have
  public IPs and be reached from (and reach) the internet.
- **Private subnet:** no direct internet route. Safer, but to reach the internet
  (e.g. to download updates) it needs a **NAT Gateway** — which **costs ~$32/mo**.

> Our choice: we put everything in **public subnets** with public IPs. This is
> less "textbook secure" but **free** (no NAT Gateway). For a short-lived demo,
> that's the right trade-off. In a real company you'd use private subnets + NAT.

---

## The route table (how traffic knows where to go)

A **route table** is a set of "to reach X, send traffic to Y" rules attached to
subnets.

From `vpc.tf`:
```hcl
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"               # "any destination (the internet)"
    gateway_id = aws_internet_gateway.main.id   # "send it to the IGW"
  }
}
```
`0.0.0.0/0` means "everything not inside the VPC" → route it to the IGW. This
is what makes the subnets "public."

Then we attach this route table to both subnets:
```hcl
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
```

---

## Security Groups (the firewalls)

Security groups control traffic **to and from a resource**. They're "default
deny" — nothing gets in unless a rule allows it.

### ECS security group (from `ecs_fargate.tf`)
```hcl
resource "aws_security_group" "ecs" {
  vpc_id = aws_vpc.main.id
  ingress {                      # INBOUND rules
    from_port   = 8001
    to_port     = 8003
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # allow from anywhere (so you can curl it)
  }
  egress {                       # OUTBOUND rules
    from_port = 0
    to_port   = 0
    protocol  = "-1"             # allow all outbound (to reach ECR, S3, RDS)
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```
This says: "anyone on the internet may connect to ports 8001–8003; the tasks may
connect out to anything."

### RDS security group (from `rds.tf`)
```hcl
resource "aws_security_group" "rds" {
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]   # <-- the key line
  }
  egress { ... all ... }
}
```
The crucial bit: RDS allows inbound Postgres (5432) **only from the ECS security
group**, NOT from the internet. So:
- Your app (ECS) → can reach the database ✅
- A random person on the internet → cannot reach the database ❌

> This is "security group referencing" — instead of IP addresses, you say "allow
> from whoever wears the ECS badge." Clean and dynamic.

---

## How a request actually flows in

1. You run `curl http://<public-ip>:8002/health`.
2. Traffic hits the **Internet Gateway** of the VPC.
3. The route table sends it to the ECS task's **public IP** in a public subnet.
4. The **ECS security group** checks: is this port 8001–8003? Yes → allowed in.
5. The container (files service) handles it and responds back out through the IGW.

And when the app talks to the database:
1. files task opens a connection to the RDS endpoint on port 5432.
2. The **RDS security group** checks: is this from the ECS SG? Yes → allowed.
3. Postgres responds.

No traffic from the open internet can reach Postgres directly — only the app can.

---

## Why no NAT Gateway (the money saver)

A NAT Gateway lets resources in **private** subnets reach the internet outbound.
It costs ~$0.045/hour **plus** data processing — roughly **$32+/month**, and
it's **not** free tier.

By using **public subnets with public IPs**, our ECS tasks reach ECR/S3 directly
through the (free) Internet Gateway — no NAT needed. That single decision keeps
the deploy near-free.

---

## Check your understanding

- *Q: VPC vs subnet?* → VPC = whole private network; subnet = a section of it.
- *Q: What makes a subnet "public"?* → A route table sending `0.0.0.0/0` to the IGW.
- *Q: How is the DB protected?* → Its SG only allows 5432 from the ECS SG, not
  the internet.
- *Q: Why no NAT Gateway?* → It costs ~$32/mo; public subnets + IGW are free and
  enough for a demo.

Next: [21e — Our Terraform files, line by line →](21e-terraform-files-line-by-line.md)
