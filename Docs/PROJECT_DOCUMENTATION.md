# PROJECT_DOCUMENTATION.md

# Self-Service Deployment Portal

## Engineering Documentation, Architecture, Design Decisions & Development Journal

---

# Table of Contents

1. Introduction
2. System Architecture
3. Request Lifecycle
4. Database Design
5. Deployment Lifecycle
6. Rollback Design
7. Service Layer Architecture
8. API Design
9. Docker Integration
10. Authentication & Security
11. Audit Logging
12. Deployment State Management
13. Engineering Decisions
14. Troubleshooting Guide
15. Detailed Error History
16. Development Journal
17. Future Improvements

---

# Introduction

This document contains the technical details behind the Self-Service Deployment Portal.

While the public README focuses on project overview and setup, this document explains:

* Internal architecture
* Database relationships
* Deployment execution flow
* Rollback implementation
* Service design
* Engineering tradeoffs
* Root cause analysis of bugs encountered during development
* Lessons learned while building the platform

The goal of this document is to provide transparency into how the system works and why certain implementation choices were made.

---

# System Architecture

The application consists of four primary components:

```text
Browser
   │
   ▼
FastAPI Backend
   │
   ├── PostgreSQL
   │
   └── Docker CLI
            │
            ▼
      Docker Daemon
            │
            ▼
       Containers
```

---

## Component Responsibilities

### Browser

Responsible for:

* User authentication
* Application management
* Version registration
* Deployment triggering
* Deployment monitoring

The frontend is intentionally lightweight and implemented using:

* HTML
* Bootstrap 5
* Vanilla JavaScript

---

### FastAPI Backend

Acts as the orchestration layer.

Responsibilities:

* Authentication
* Authorization
* Database operations
* Deployment orchestration
* Rollback orchestration
* Audit logging
* API responses

---

### PostgreSQL

Stores:

* Users
* Applications
* Versions
* Deployments
* Deployment logs

The database acts as the source of truth for deployment history.

---

### Docker CLI

Responsible for interacting with Docker Engine.

Used operations include:

```bash
docker pull
docker inspect
docker stop
docker rm
docker run
```

The backend never manipulates containers directly.

All container operations are delegated to Docker.

---

# Request Lifecycle

Example: User clicks Deploy.

```text
User
 │
 ▼
Frontend
 │
 ▼
POST /deployments
 │
 ▼
Create Deployment Record
 │
 ▼
Status = pending
 │
 ▼
Start Background Task
 │
 ▼
Docker Operations
 │
 ▼
Update Status
 │
 ▼
Frontend Polling
 │
 ▼
UI Updated
```

---

# Database Design

The database is designed around deployment traceability.

---

## users

Stores registered users.

Fields:

```text
id
username
email
hashed_password
created_at
```

Purpose:

* Authentication
* Ownership tracking
* Deployment attribution

---

## applications

Represents deployable projects.

Fields:

```text
id
name
description
repository_url
owner_id
created_at
```

Relationship:

```text
User
  │
  └── Applications
```

---

## versions

Represents Docker image versions.

Fields:

```text
id
application_id
version_tag
image_name
created_at
```

Example:

```text
v1.0 → nginx:alpine
v2.0 → nginx:latest
```

---

## deployments

Most important table in the system.

Fields:

```text
id
application_id
version_id
user_id

status

started_at
completed_at

previous_deployment_id

rollback_of_deployment_id

error_message
```

Purpose:

Track every deployment ever performed.

---

## deployment_logs

Stores deployment events.

Fields:

```text
id
deployment_id
timestamp
level
message
```

Example:

```text
INFO  Pulling image nginx:alpine
INFO  Container stopped
INFO  Container removed
INFO  Container started
INFO  Deployment successful
```

---

# Deployment Lifecycle

When a user clicks Deploy, the following process occurs.

---

## Step 1

Frontend sends:

```http
POST /api/v1/applications/{id}/deployments
```

Payload:

```json
{
  "version_id": "..."
}
```

---

## Step 2

Backend creates:

```text
Deployment
status = pending
```

Record saved to PostgreSQL.

---

## Step 3

Background task starts.

Purpose:

Avoid blocking the API request.

User receives immediate response.

---

## Step 4

Docker image pulled.

```bash
docker pull nginx:alpine
```

---

## Step 5

Existing container checked.

```bash
docker inspect container_name
```

---

## Step 6

If running:

```bash
docker stop container_name
```

---

## Step 7

Container removed.

```bash
docker rm -f container_name
```

---

## Step 8

New container started.

```bash
docker run \
  --detach \
  --name container_name \
  -p 8081:80 \
  nginx:alpine
```

---

## Step 9

Container status verified.

```bash
docker inspect container_id
```

Expected:

```text
running
```

---

## Step 10

Deployment marked successful.

```text
status = success
```

---

# Rollback Design

Rollback was intentionally designed as a deployment operation rather than a simple status change.

---

## Why?

Suppose:

```text
D1 → nginx:v1

D2 → nginx:v2
```

User wants to rollback D2.

A naïve approach would:

```text
D2 status = rolled_back
```

But this doesn't actually restore the old version.

---

## Implemented Approach

Rollback creates a brand-new deployment.

Example:

```text
D1 → nginx:v1

D2 → nginx:v2

Rollback(D2)

↓

D3 → nginx:v1
```

New deployment:

```text
version_id = D1.version_id

rollback_of_deployment_id = D2.id

previous_deployment_id = D1.id
```

Advantages:

* Full audit trail
* Deployment history preserved
* No hidden state changes
* Clear rollback lineage

---

# Service Layer Architecture

Services isolate business logic from API endpoints.

---

## Auth Service

Responsibilities:

* Register users
* Verify passwords
* Generate JWT tokens

---

## Application Service

Responsibilities:

* Create applications
* Retrieve applications
* Delete applications

---

## Version Service

Responsibilities:

* Register versions
* Retrieve versions

---

## Deployment Service

Responsibilities:

* Create deployments
* Execute deployments
* Execute rollbacks
* Update deployment status

---

## Docker Service

Responsibilities:

* Docker CLI execution
* Output collection
* Error handling

Acts as the abstraction layer around Docker.

---

# API Design

All endpoints:

```text
/api/v1
```

Protected endpoints require:

```http
Authorization: Bearer <token>
```

---

## Authentication

### Register

```http
POST /auth/register
```

---

### Login

```http
POST /auth/login
```

Returns:

```json
{
  "access_token": "...",
  "user": {}
}
```

---

## Applications

```http
GET    /applications
POST   /applications
GET    /applications/{id}
DELETE /applications/{id}
```

---

## Versions

```http
GET  /applications/{id}/versions
POST /applications/{id}/versions
```

---

## Deployments

```http
POST /deployments
GET  /deployments
GET  /deployments/{id}
POST /rollback
```

---

# Docker Integration

The platform communicates with Docker using the Docker CLI.

Example:

```python
subprocess.run(
    ["docker", "pull", image_name],
    capture_output=True,
    text=True
)
```

Benefits:

* Stable behavior
* Compatible across Docker versions
* Easy debugging
* Predictable output

---

# Authentication & Security

Current security measures:

* JWT authentication
* bcrypt password hashing
* User-owned resources
* Protected endpoints

Current limitations:

* No RBAC
* No SSO
* No MFA
* No OAuth providers

---

# Audit Logging

Every deployment event is recorded.

Example:

```text
Deployment Started
Image Pulled
Container Stopped
Container Removed
Container Started
Deployment Successful
```

Purpose:

* Troubleshooting
* Auditing
* Historical visibility

---

# Deployment State Management

Supported states:

```text
pending
in_progress
success
failed
rolled_back
```

State transitions:

```text
pending
   │
   ▼
in_progress
   │
   ├── success
   │
   └── failed
```

---

# Engineering Decisions

## Why PostgreSQL Instead of SQLite?

Reasons:

* Better concurrency
* Production readiness
* Stronger relational support
* Future scalability

---

## Why JWT Instead of Sessions?

Reasons:

* Stateless authentication
* Simpler API architecture
* Easy frontend integration

---

## Why Docker CLI Instead of Docker SDK?

Originally:

```python
docker.from_env()
```

was used.

Issue encountered:

```text
Not supported URL scheme http+docker
```

Multiple compatibility issues appeared across environments.

Final decision:

Use Docker CLI directly.

Advantages:

* More reliable
* Easier troubleshooting
* Better Docker version compatibility

Tradeoff:

* Less elegant than SDK usage
* Requires Docker binary inside container

---

# Troubleshooting Guide

## API Container Crashes

Check:

```bash
docker compose logs api
```

---

## Database Connection Issues

Verify:

```bash
docker compose ps
```

Database must show:

```text
healthy
```

---

## Deployment Failures

Verify Docker access:

```bash
docker ps
```

inside API container.

---

# Detailed Error History

## pydantic_settings Import Error

Error:

```text
ModuleNotFoundError:
No module named 'pydantic_settings'
```

Fix:

Added:

```text
pydantic-settings==2.2.1
```

---

## email-validator Missing

Error:

```text
email-validator is not installed
```

Fix:

Added dependency.

---

## Passlib bcrypt Issue

Error:

```text
password cannot be longer than 72 bytes
```

Fix:

Replaced passlib with bcrypt directly.

---

## Docker SDK HTTP+docker Error

Error:

```text
Not supported URL scheme http+docker
```

Fix:

Removed Docker SDK entirely.

Implemented Docker CLI.

---

## Docker Version Mismatch

Error:

```text
client version is too old
```

Fix:

Upgraded Docker CLI binary.

---

## docker create --detach

Error:

```text
unknown flag --detach
```

Fix:

Switched to:

```bash
docker run --detach
```

---

# Development Journal

## Iteration 1

Goal:

Build authentication and application management.

Completed:

* JWT Authentication
* CRUD Operations

Limitation:

No deployment functionality.

---

## Iteration 2

Goal:

Introduce Docker deployments.

Completed:

* Docker SDK integration

Issue:

SDK compatibility failures.

---

## Iteration 3

Goal:

Reliable deployment execution.

Completed:

* Docker CLI implementation
* Deployment status tracking

---

## Iteration 4

Goal:

Deployment visibility.

Completed:

* Deployment logs
* Error tracking
* Audit trail

---

## Iteration 5

Goal:

Rollback support.

Completed:

* Deployment chain model
* Rollback lineage tracking

---

# Future Improvements

## Health Checks

Automatically verify deployed containers.

Potential behavior:

```text
Deploy
↓
Health Check
↓
Healthy → Success

Unhealthy → Auto Rollback
```

---

## CI/CD Integration

Support automated deployments from GitHub Actions.

---

## Kubernetes Support

Replace Docker runtime with Kubernetes deployments.

---

## Monitoring

Add:

* Prometheus
* Grafana

---

## Real-Time Logs

WebSocket-based deployment log streaming.

---

## Role-Based Access Control

Introduce:

* Admin
* Developer
* Viewer

roles.

---

# Conclusion

This project started as a deployment automation experiment and evolved into a small internal deployment platform.

Beyond the technical implementation, the project provided experience in:

* Deployment orchestration
* Container lifecycle management
* Database design
* Audit logging
* Authentication
* Docker integration
* Troubleshooting production-like issues
* Designing rollback systems

The lessons learned from building and debugging the platform were ultimately as valuable as the final application itself.
