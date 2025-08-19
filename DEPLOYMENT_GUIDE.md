# OriginFlow Deployment Guide

## Overview

This guide covers the deployment of OriginFlow with all security improvements implemented. The system now includes authentication, secure file uploads, comprehensive error handling, performance optimizations, and CI/CD pipelines.

## Security Improvements Implemented

### ✅ Authentication & Authorization
- FastAPI Users integration with JWT tokens
- Role-based access control
- User management endpoints
- Account lockout after failed attempts
- Password complexity requirements

### ✅ Secure File Upload
- File type validation with MIME type verification
- File size limits (50MB max)
- Path traversal prevention
- Virus scanning capability
- Safe filename sanitization

### ✅ SQL Injection Prevention
- Parameterized queries throughout
- Input validation and sanitization
- Safe search implementations

### ✅ Security Headers
- Content Security Policy (CSP)
- HSTS, X-Frame-Options, X-Content-Type-Options
- CORS security middleware
- Rate limiting

### ✅ Performance Optimizations
- Vector search optimization with numpy
- Database query optimization
- Caching layer for similarity computations
- Connection pooling

### ✅ Error Handling
- Comprehensive exception hierarchy
- Structured error responses
- Security-aware error messages
- Centralized error logging

### ✅ Structured Logging
- JSON formatted logs
- Performance monitoring
- Security event logging
- Audit trails

## Production Deployment

### Prerequisites

1. **Server Requirements**
   - Linux server (Ubuntu 20.04+ recommended)
   - Docker and Docker Compose
   - 4GB+ RAM, 2+ CPU cores
   - 50GB+ storage

2. **External Services**
   - PostgreSQL database
   - Redis cache
   - OpenAI API key
   - Domain name and SSL certificate

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/originflow
sudo chown $USER:$USER /opt/originflow
cd /opt/originflow
```

### Step 2: Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

**Critical Environment Variables:**

```bash
# Security - CHANGE THESE!
SECRET_KEY=$(openssl rand -base64 64)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Database
DATABASE_URL=postgresql://originflow:${POSTGRES_PASSWORD}@postgres:5432/originflow

# OpenAI
OPENAI_API_KEY=your-actual-openai-api-key

# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
JSON_LOGS=true
```

### Step 3: SSL Configuration

```bash
# Create SSL directory
mkdir -p docker/ssl

# Option 1: Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/

# Option 2: Self-signed (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/originflow.key \
  -out docker/ssl/originflow.crt
```

### Step 4: Database Initialization

```bash
# Start only the database first
docker-compose up -d postgres redis qdrant

# Wait for services to be ready
sleep 30

# Run database migrations
docker-compose run --rm backend alembic upgrade head

# Create admin user (optional)
docker-compose run --rm backend python -c "
from backend.auth.models import User
from backend.auth.config import auth_config
from backend.database.session import SessionMaker
import asyncio

async def create_admin():
    async with SessionMaker() as session:
        admin = User(
            email='admin@originflow.com',
            hashed_password='$2b$12$...',  # Use proper hash
            is_superuser=True,
            is_verified=True,
            permissions=auth_config.ADMIN_PERMISSIONS
        )
        session.add(admin)
        await session.commit()

asyncio.run(create_admin())
"
```

### Step 5: Deploy Application

```bash
# Deploy full stack
docker-compose --profile production up -d

# Verify deployment
docker-compose ps
docker-compose logs backend
docker-compose logs frontend
```

### Step 6: Monitoring & Health Checks

```bash
# Check application health
curl -f https://yourdomain.com/health
curl -f https://yourdomain.com/api/v1/

# Monitor logs
docker-compose logs -f --tail=100

# Monitor resource usage
docker stats
```

For Prometheus Operator and Grafana setup, see [docs/DEPLOY_MONITORING.md](docs/DEPLOY_MONITORING.md).

## Security Checklist

### Before Production Deployment

- [ ] Change all default passwords and secrets
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules (only ports 80, 443, 22)
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting
- [ ] Review and update CORS origins
- [ ] Configure rate limiting appropriate for your traffic
- [ ] Set up log rotation
- [ ] Configure automatic security updates

### Security Headers Verification

```bash
# Check security headers
curl -I https://yourdomain.com

# Expected headers:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# X-Frame-Options: DENY
# Content-Security-Policy: default-src 'self'; ...
```

### Authentication Testing

```bash
# Test user registration
curl -X POST https://yourdomain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepassword123"}'

# Test login
curl -X POST https://yourdomain.com/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=securepassword123"

# Test protected endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://yourdomain.com/api/v1/components/
```

## Maintenance

### Regular Tasks

```bash
# Update application
git pull
docker-compose build
docker-compose up -d

# Database backup
docker-compose exec postgres pg_dump -U originflow originflow > backup_$(date +%Y%m%d).sql

# Clean up Docker resources
docker system prune -f
docker volume prune -f

# Rotate logs
docker-compose exec backend logrotate /etc/logrotate.conf

# Update SSL certificates (if using Let's Encrypt)
sudo certbot renew
docker-compose restart nginx
```

### Monitoring

```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check database performance
docker-compose exec postgres psql -U originflow -c "
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose logs postgres
   
   # Reset database connection
   docker-compose restart backend
   ```

2. **File Upload Issues**
   ```bash
   # Check upload directory permissions
   docker-compose exec backend ls -la /app/backend/static/uploads
   
   # Fix permissions
   docker-compose exec backend chown -R appuser:appuser /app/backend/static/uploads
   ```

3. **Authentication Errors**
   ```bash
   # Check JWT secret configuration
   docker-compose exec backend env | grep SECRET_KEY
   
   # Restart authentication service
   docker-compose restart backend
   ```

4. **Performance Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Analyze slow queries
   docker-compose exec postgres psql -U originflow -c "
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   WHERE mean_time > 1000 
   ORDER BY mean_time DESC;"
   ```

### Security Incident Response

1. **Immediate Actions**
   - Isolate affected systems
   - Change all authentication tokens
   - Review access logs
   - Document the incident

2. **Investigation**
   ```bash
   # Review security logs
   docker-compose logs backend | grep -i "security\|suspicious\|failed"
   
   # Check failed login attempts
   docker-compose exec postgres psql -U originflow -c "
   SELECT * FROM ai_action_log 
   WHERE action_type = 'authentication' 
   AND created_at > NOW() - INTERVAL '24 hours'
   ORDER BY created_at DESC;"
   ```

3. **Recovery**
   - Apply security patches
   - Update configurations
   - Restore from known good backup if needed
   - Monitor for continued suspicious activity

## Performance Tuning

### Database Optimization

```sql
-- Create additional indexes for performance
CREATE INDEX CONCURRENTLY idx_file_asset_user_uploaded 
ON file_asset (uploaded_by, uploaded_at);

CREATE INDEX CONCURRENTLY idx_ai_action_log_user_timestamp 
ON ai_action_log (user_id, timestamp);

-- Update table statistics
ANALYZE;
```

### Application Optimization

```bash
# Increase worker processes
docker-compose exec backend sed -i 's/workers=1/workers=4/' /app/gunicorn.conf.py
docker-compose restart backend

# Configure Redis for better performance
docker-compose exec redis redis-cli CONFIG SET maxmemory 1gb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Setup**
   - Use nginx or HAProxy
   - Configure session affinity for WebSocket connections
   - Health check endpoints

2. **Database Scaling**
   - Read replicas for query scaling
   - Connection pooling (PgBouncer)
   - Database sharding for large datasets

3. **Caching Strategy**
   - Redis cluster for high availability
   - CDN for static assets
   - Application-level caching

4. **Container Orchestration**
   - Kubernetes deployment
   - Auto-scaling based on metrics
   - Service mesh for microservices

This deployment guide ensures a secure, performant, and maintainable production deployment of OriginFlow with all the security improvements implemented.
