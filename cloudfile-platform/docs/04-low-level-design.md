# 04 — Low-Level Design (LLD)

This maps the design onto the actual code. Every service follows the same
layered pattern:

```
router.py      HTTP layer (FastAPI) — no business logic
  │ depends on
service.py     business logic — no HTTP, no SQL framework details leak out
  │ depends on
repository.py  data access — only SQLAlchemy queries, no business rules
  │ depends on
models.py      ORM models (SQLAlchemy)
schemas.py     Pydantic request/response types
config.py      env-based settings
database.py    async engine + session + get_db dependency
dependencies.py FastAPI Depends wiring (DI)
```

## Auth Service

### models.py
```python
class User(Base):
    id: str (uuid)        # PK
    email: str            # unique, indexed
    hashed_password: str
    full_name: str
    is_active: bool = True
    created_at: datetime
```

### security.py
```python
hash_password(plain) -> str                    # bcrypt
verify_password(plain, hashed) -> bool
create_access_token(user_id, email) -> (token, expires_in)   # JWT HS256
```

### repository.py — `UserRepository`
```python
get_by_email(email) -> User | None
get_by_id(user_id) -> User | None
create(user) -> User
```

### service.py — `AuthService`
```python
register(UserCreate) -> User        # 409 if email exists
login(UserLogin) -> Token           # 401 on bad creds / inactive
```

### router.py
```
POST /register  -> 201 UserOut
POST /login     -> Token
GET  /me        -> UserOut           (get_current_token)
GET  /verify    -> TokenVerifyResponse
```

## Files Service

### models.py
```python
class FileMetadata(Base):
    id, owner_id (indexed), filename, content_type,
    size_bytes, s3_key (unique), status, thumbnail_key, created_at
```

### s3_client.py — `S3Client` (boto3 wrapper)
```python
generate_upload_url(key, content_type) -> str   # presigned PUT
generate_download_url(key) -> str                # presigned GET
delete_object(key) -> None
ensure_bucket() -> None                          # dev/LocalStack
```
boto3 is synchronous → called via `run_in_threadpool` in the service layer.

### service.py — `FileService`
```python
initiate_upload(owner_id, filename, content_type, size) -> (FileMetadata, upload_url)
confirm_upload(file_id, owner_id, user_email, token) -> FileMetadata  # notifies
get_download_url(file_id, owner_id) -> str          # 404/403 enforced
list_files(owner_id) -> list[FileMetadata]
delete_file(file_id, owner_id) -> None              # S3 + thumbnail + row
_get_owned(file_id, owner_id) -> FileMetadata       # NotFound/Forbidden
```

### notifier.py
```python
notify_upload_complete(user_email, filename, token) -> None  # fire-and-forget
```

### key sequence: confirm_upload
```
router.confirm_upload
  → service.confirm_upload
      → _get_owned (ownership check)
      → repo.update(status='ready')
      → notifier.notify_upload_complete (httpx, swallow errors)
  → FileOut
```

## Search Service

### models.py — `FileRecord` (read model over the same `files` table)
### repository.py — `SearchRepository`
```python
search(owner_id, name?, content_type?, offset, limit) -> (rows, total)
  # filters: owner_id = ?, filename ILIKE %name%, content_type = ?
  # returns COUNT(*) as total + the page slice ordered by created_at desc
```
### service.py — `SearchService`
```python
search(owner_id, name, content_type, PaginationParams) -> Page[FileResult]
```

## Processor Lambda

### handler.py
```python
handler(event, context):
  for record in event["Records"]:
    key = unquote(record.s3.object.key)
    if key.startswith("thumbnails/"): continue      # avoid recursion
    head = s3.head_object(...)
    if content_type in IMAGE_TYPES:
        data = s3.get_object(...).read()
        thumb = make_thumbnail(data)                 # Pillow
        s3.put_object(thumbnails/<key>, thumb)
    update_database(key, content_type, size, thumb_key)  # psycopg2
```

## Notification Service

### providers (Strategy pattern)
```
NotificationProvider (ABC).send(recipient, subject, message)
  ├─ ConsoleProvider  (logs; free; default)
  └─ SESProvider      (AWS SES; boto3 via threadpool)
factory.get_provider() -> provider based on NOTIFICATION_PROVIDER
```

### service.py — `NotificationService`
```python
notify(NotifyRequest) -> Notification   # send via provider, record row (sent|failed)
list_for(recipient) -> list[Notification]
```

## Shared Library (monorepo)

| Module | Contents |
|--------|----------|
| responses.py | SuccessResponse, ErrorResponse, ok(), err() |
| exceptions.py | AppError + subclasses, install_exception_handlers() |
| logging_config.py | JSON formatter, configure_logging(), get_logger() |
| auth_utils.py | verify_token(), TokenData, TokenVerificationError |
| pagination.py | PaginationParams, Page[T].create() |

## Error Handling Strategy

Service layer raises domain errors (`NotFoundError`, `ForbiddenError`,
`ConflictError`, `UnauthorizedError`). `install_exception_handlers` converts
them to the standard error envelope with the right HTTP status. Unexpected
exceptions become a 500 with a generic message (details are logged, not leaked).
