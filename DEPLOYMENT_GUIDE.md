# Health Services API - Setup & Deployment Guide

## Local Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Git
- pip (Python package manager)

### Step 1: Clone Repository
```bash
git clone https://github.com/amanjogiris/health.git
cd health
```

### Step 2: Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirement.txt
```

### Step 4: Setup PostgreSQL Database

#### Option A: Using PostgreSQL CLI
```bash
# Create database
createdb health_db

# Create user (if needed)
# createuser -P aman  # Prompts for password

# Login to PostgreSQL
psql -U aman -d health_db
```

#### Option B: Using pgAdmin GUI
1. Open pgAdmin
2. Right-click on Databases → Create → Database
3. Name: health_db
4. Click Save

### Step 5: Update Database Configuration
Edit `app/database.py`:
```python
# Update the DATABASE_URL with your PostgreSQL credentials
DATABASE_URL = "postgresql+asyncpg://username:password@localhost:5432/health_db"
```

### Step 6: Run Database Migrations
```bash
# Run all migrations
alembic upgrade head

# Verify tables were created
psql -U aman -d health_db -c "\dt"
```

### Step 7: Create Environment File
Copy `.env.example` to `.env` and update values:
```bash
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql+asyncpg://aman:123@localhost:5432/health_db
SECRET_KEY=your-super-secret-key-here
DEBUG=False
```

### Step 8: Start Development Server
```bash
# Option 1: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Python module
python -m uvicorn app.main:app --reload

# Option 3: Using Python script (if __main__ is configured)
python app/main.py
```

Server will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Testing the API

### Using cURL

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. Register a Patient
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "role": "patient",
    "mobile_no": "9876543210",
    "address": "123 Main St"
  }'
```

#### 3. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

#### 4. Get Profile (with token)
```bash
curl "http://localhost:8000/api/v1/auth/profile?token=YOUR_JWT_TOKEN" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Using Postman

1. Open Postman
2. Create new collection "Health API"
3. Add requests:
   - POST /api/v1/auth/register
   - POST /api/v1/auth/login
   - GET /api/v1/auth/profile
   - POST /api/v1/clinics
   - POST /api/v1/doctors
   - GET /api/v1/doctors
   - POST /api/v1/slots
   - POST /api/v1/appointments/book

4. In each request:
   - Set token in Authorization header as "Bearer TOKEN"
   - Or add token as query parameter: ?token=TOKEN

### Using Swagger UI

1. Navigate to http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in required parameters
5. Click "Execute"

## Database Backup & Restore

### Backup Database
```bash
# Backup to file
pg_dump -U aman -d health_db > health_db_backup.sql

# With compression
pg_dump -U aman -d health_db | gzip > health_db_backup.sql.gz
```

### Restore Database
```bash
# From SQL file
psql -U aman -d health_db < health_db_backup.sql

# From compressed file
gunzip -c health_db_backup.sql.gz | psql -U aman -d health_db
```

## Running Tests

### Setup Test Environment
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Create tests directory
mkdir tests
```

### Run Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestAuthenticationEndpoints::test_register
```

## Production Deployment

### Docker Deployment

#### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Build Docker Image
```bash
docker build -t health-api:latest .
```

#### 3. Run Docker Container
```bash
docker run -d \
  --name health-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/health_db" \
  -e SECRET_KEY="your-secret-key" \
  health-api:latest
```

### Docker Compose Setup

#### 1. Create docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_USER: aman
      POSTGRES_PASSWORD: 123
      POSTGRES_DB: health_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: "postgresql+asyncpg://aman:123@db:5432/health_db"
      SECRET_KEY: "your-secret-key-here"
    depends_on:
      - db
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

volumes:
  postgres_data:
```

#### 2. Run with Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### AWS Deployment (Example)

#### 1. Create RDS PostgreSQL Instance
- Engine: PostgreSQL 13+
- Instance class: db.t3.micro (for testing)
- Storage: 20 GB
- Multi-AZ: No (for testing)

#### 2. Deploy to AWS Lambda (Optional for FastAPI)
```bash
# Package application
pip install -r requirement.txt -t package
cp -r app package/
cd package && zip -r ../lambda.zip . && cd ..

# Upload to Lambda
aws lambda create-function \
  --function-name health-api \
  --runtime python3.9 \
  --handler app.main.app \
  --zip-file fileb://lambda.zip
```

#### 3. Deploy to AWS EC2
```bash
# SSH into instance
ssh -i key.pem ubuntu@instance-ip

# Install dependencies
sudo apt update
sudo apt install -y python3.9 python3-pip postgresql-client

# Clone repo
git clone <repo-url>
cd health

# Setup application
python3 -m venv venv
source venv/bin/activate
pip install -r requirement.txt

# Start application (using systemd or supervisor)
```

## Troubleshooting

### Database Connection Issues
```
Error: "could not translate host name 'localhost' to address"

Solution:
- Ensure PostgreSQL is running: brew services start postgresql (macOS)
- Check connection string in app/database.py
- Verify database exists: psql -l
```

### Alembic Migration Issues
```
Error: "Target database is not up to date"

Solution:
- Reset database: alembic downgrade base
- Re-run migrations: alembic upgrade head
- Check migration files in alembic/versions/
```

### JWT Token Errors
```
Error: "Invalid token"

Solution:
- Token may be expired (default: 30 minutes)
- Regenerate token by logging in again
- Check SECRET_KEY in app/main.py and .env match
```

### Port Already in Use
```
Error: "Address already in use"

Solution:
# macOS/Linux
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Monitoring & Logging

### Check Application Logs
```bash
# Real-time logs
tail -f logs/app_*.log

# Filter by log level
grep ERROR logs/app_*.log
```

### Database Monitoring
```bash
# Connected users
psql -U aman -d health_db -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Database size
psql -U aman -d health_db -c "\l+"

# Table sizes
psql -U aman -d health_db -c "\d+ users;"
```

### API Performance
- Monitor response times in application logs
- Use Swagger UI to test endpoints
- Check database query performance

## Security Checklist

- [ ] Change SECRET_KEY to a strong value
- [ ] Set DEBUG=False in production
- [ ] Use HTTPS instead of HTTP
- [ ] Set CORS_ORIGINS to specific domains
- [ ] Implement rate limiting
- [ ] Use environment variables for sensitive data
- [ ] Enable CSRF protection
- [ ] Implement input validation (done with Pydantic)
- [ ] Use parameterized queries (done with SQLAlchemy)
- [ ] Implement API authentication (done with JWT)
- [ ] Set secure password requirements
- [ ] Regular database backups
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated

## Performance Tuning

### Database Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM appointments WHERE patient_id = 1;

-- Create indexes for frequently queried columns
CREATE INDEX idx_appointments_patient_id ON appointments(patient_id);

-- Vacuum and analyze
VACUUM ANALYZE;
```

### Application Optimization
- Enable connection pooling in SQLAlchemy
- Implement caching for frequently accessed data
- Use async operations (already implemented)
- Optimize N+1 queries with eager loading

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 100 http://localhost:8000/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/health
```

## Maintenance Schedule

- **Daily**: Monitor logs and errors
- **Weekly**: Backup database
- **Monthly**: Review and optimize slow queries
- **Quarterly**: Update dependencies
- **Quarterly**: Security audit
- **Annually**: Capacity planning review

---

**Document Version**: 1.0.0
**Last Updated**: February 24, 2024
