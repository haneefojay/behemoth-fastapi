# 🎯 Event Management API - Senior Backend Assessment

A production-ready Event Management API built with FastAPI, featuring JWT authentication, Role-Based Access Control (RBAC), advanced querying, and comprehensive event/task/attendee management.

## ✨ Features

### Authentication & Authorization
- **JWT Authentication**: Access tokens (15 min) + Refresh tokens (7 days)
- **RBAC System**: Three roles - User, Organizer, Admin
- **Secure Password Hashing**: Argon2 algorithm
- **Token Management**: Refresh token rotation and revocation

### Event Management
- **CRUD Operations**: Full event lifecycle management
- **Status Workflow**: DRAFT → UPCOMING → ONGOING → COMPLETED → CANCELLED
- **Multi-Organizer Support**: Events can have multiple organizers
- **Capacity Management**: Track attendees and enforce limits
- **Advanced Filtering**: By status, location, date range, organizer, capacity
- **Full-Text Search**: Search events by title and description
- **Advanced Sorting**: Sort events by date, popularity (attendance), title, or creation date
- **Pagination**: Efficient data retrieval with customizable page sizes

### Task Management
- **Event Tasks**: Create and assign tasks to events
- **Assignment System**: Assign tasks to users
- **Completion Tracking**: Mark tasks as complete/incomplete
- **Business Rules**: Prevent modifications on completed/cancelled events

### Attendee Management
- **Registration System**: Users can register for events
- **Capacity Enforcement**: Automatic waitlist when event is full
- **Waitlist Management**: Automatic promotion when spots open
- **Attendance Tracking**: View registered attendees and waitlist

### Performance & Security
- **Dynamic Rate Limiting**: Role-based limits (Admin: 500/hr, Organizer: 200/hr, User: 100/hr, Guest: 30/hr)
- **Redis Caching**: Cache-aside implementation for frequent event list queries
- **Live Health Monitoring**: `/health` endpoint with live DB and Redis connectivity verification
- **Search Optimization**: Native Postgres Full-Text search for scalability
- **Security Handlers**: Global exception handling that sanitizes sensitive DB errors in production

## 🏗️ Architecture

### Project Structure
```
app/
├── users/              # User authentication & management
│   ├── models.py       # User, RefreshToken models
│   ├── schemas/        # Request/response schemas
│   ├── services.py     # Business logic
│   └── routes/         # API endpoints
├── events/             # Event management
│   ├── models.py       # Event model with status workflow
│   ├── schemas/        # Event schemas with validation
│   ├── services.py     # Event CRUD and business rules
│   ├── selectors.py    # Query builders with filtering
│   └── routes/         # Event API endpoints
├── tasks/              # Task management
│   ├── models.py       # Task model
│   ├── schemas/        # Task schemas
│   ├── services.py     # Task business logic
│   └── routes/         # Task API endpoints
├── attendees/          # Attendee management
│   ├── models.py       # Attendee model with waitlist
│   ├── schemas/        # Attendee schemas
│   ├── services.py     # Registration & waitlist logic
│   └── routes/         # Attendee API endpoints
├── common/             # Shared utilities
│   ├── auth.py         # JWT token implementation
│   ├── permissions.py  # RBAC & ownership logic
│   ├── cache.py        # Redis caching implementation
│   ├── dependencies.py # Shared FastAPI dependencies
│   ├── exceptions.py   # Custom exception system
│   └── types.py        # Shared type definitions
└── core/               # Core configuration
    ├── database.py     # SQLAlchemy async setup
    ├── settings.py     # Pydantic settings (env)
    ├── rate_limit.py   # Role-based rate limiting
    ├── redis_utils.py  # Redis client management
    └── handlers.py     # Global exception handlers
```

### Database Schema

#### Users & Authentication
- `users`: User accounts with roles (USER, ORGANIZER, ADMIN)
- `refresh_tokens`: JWT refresh token management

#### Events & Management
- `events`: Events with status, capacity, organizers
- `event_organizers`: Many-to-many relationship for multi-organizer support
- `tasks`: Event tasks with assignment
- `attendees`: Event registrations with waitlist support

### Key Design Decisions

1. **RBAC Implementation**: Permission-based access control using FastAPI dependencies and JWT role claims for performance
2. **Search Architecture**: Utilized Postgres `TSVECTOR` with GIN indexing for efficient, scalable full-text search
3. **Health Monitoring**: Implemented deep health checks that verify live connectivity to both PostgreSQL and Redis
4. **Security Logic**: Automated sanitization of `IntegrityError` responses to prevent internal SQL database leakage
5. **Waitlist System**: Automatic promotion when capacity becomes available via atomic database operations
6. **Token Strategy**: Short-lived access tokens with long-lived refresh tokens and rotation

## 🚀 Setup Instructions

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Redis 7+
- [`uv`](https://docs.astral.sh/uv/) package manager

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd behemoth-fastapi
uv venv
uv sync
```

### 2. Environment Configuration

Create a `.env` file:

```env
# Application
DEBUG=True

# Database
POSTGRES_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/event_management

# Redis
REDIS_BROKER_URL=redis://localhost:6379/0

# JWT Secret (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here

# Optional: Logfire for observability
LOGFIRE_TOKEN=your-logfire-token
```

### 3. Start Redis

```bash
# Using Docker
docker run -d --name event-redis -p 6379:6379 redis:latest

# Or install locally
# Windows: Download from https://redis.io/download
# Mac: brew install redis && brew services start redis
# Linux: sudo apt-get install redis-server && sudo systemctl start redis
```

### 4. Database Setup

```bash
# Run migrations
uv run alembic upgrade head
```

### 5. Run the Application

```bash
# Development mode (with auto-reload)
uv run fastapi dev

# Production mode
uv run fastapi run
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000` (in DEBUG mode)
- **ReDoc**: `http://localhost:8000/redoc` (in DEBUG mode)

### Quick Start Examples

#### 1. Register a User
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "SecurePass123!",
    "role": "organizer"
  }'
```

#### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### 3. Create an Event
```bash
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tech Conference 2024",
    "description": "Annual technology conference",
    "start_date": "2024-06-01T09:00:00",
    "end_date": "2024-06-01T17:00:00",
    "location": "Convention Center",
    "capacity": 500
  }'
```

#### 4. Register for Event
```bash
curl -X POST http://localhost:8000/events/{event_id}/register \
  -H "Authorization: Bearer <access_token>"
```

## 🔐 RBAC Permission Matrix

| Endpoint | User | Organizer | Admin |
|----------|------|-----------|-------|
| Create Event | ✅ | ✅ | ✅ |
| Update Own Event | ✅ | ✅ | ✅ |
| Update Any Event | ❌ | ❌ | ✅ |
| Delete Own Event | ✅ | ✅ | ✅ |
| Delete Any Event | ❌ | ❌ | ✅ |
| Create Task | ❌ | ✅ | ✅ |
| Update Task | Assignee* | ✅ | ✅ |
| View Attendees | ❌ | ✅ | ✅ |
| Update User Roles | ❌ | ❌ | ✅ |

\* Assignees can only update the completion status of a task.

## 🧪 Testing

⚠️ **IMPORTANT**: Tests clear the database between runs! You MUST use a separate test database.

1. Create a test database: `createdb behemoth_test`
2. Add the URL to your `.env` file:
   ```env
   POSTGRES_TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/behemoth_test
   ```

```bash
# Run all tests
uv run pytest -v tests/
```

## 📊 Rate Limiting

The system implements a **configurable role-based** rate limiting policy:
- **Admin**: 500 requests per hour.
- **Organizer**: 200 requests per hour.
- **User/Guest**: 100 requests per hour.
- **Identifier**: Custom logic that prioritizes JWT `sub` (User ID) to ensure per-user limiting, falling back to IP address for anonymous traffic.
- **Configuration**: Limits are configurable via `.env` (`REQ_RATE_ADMIN`, `REQ_RATE_ORGANIZER`, `REQ_RATE_USER`, `REQ_RATE`, etc)
- **Implementation**: Built with `FastAPILimiter` and Redis.

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## 🔧 Advanced Configuration

### Caching Strategy
Redis caching is configured but not fully implemented. To enable caching for event listings:

```python
from app.common.cache import CacheManager

event_cache = CacheManager(ttl=300, model_class=Event)
# Use in selectors for frequent queries
```

### Database Indexes
Key indexes for performance:
- `users.email` (unique)
- `users.role`
- `events.status`
- `events.start_date`
- `events.location`
- `event_organizers(event_id, user_id)`
- `attendees(event_id, user_id)` (unique)
- `attendees(event_id, status)`

## 📝 Business Rules

### Event Status Transitions
- DRAFT → UPCOMING, CANCELLED
- UPCOMING → ONGOING, CANCELLED
- ONGOING → COMPLETED, CANCELLED
- COMPLETED → (no transitions)
- CANCELLED → (no transitions)

### Task Management
- Tasks cannot be created/modified on COMPLETED or CANCELLED events
- Organizers and assignees can update tasks
- Only organizers can delete tasks

### Attendee Management
- Registration and unregistration only allowed for UPCOMING events
- Automatic waitlist when capacity reached
- Automatic promotion from waitlist when spots available
- Cannot register twice for the same event

## 🎓 Key Learnings & Decisions

1. **Argon2 for Password Hashing**: More secure than bcrypt, resistant to GPU attacks
2. **Refresh Token Strategy**: Prevents frequent re-authentication while maintaining security
3. **Eager Loading**: Used `selectinload` to prevent N+1 queries
4. **Status Workflow**: Prevents invalid state transitions
5. **Waitlist Automation**: Reduces manual intervention for event management

## 📬 Contact

- **Candidate**: Haneef
- **GitHub**: [haneefojay](https://github.com/haneefojay)

## 📄 License

MIT License - see LICENSE file for details

---

**Built with ❤️ for the Senior Backend Engineer Assessment**
