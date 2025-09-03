# Face-Sense Production Deployment Guide

## 🚀 Cloud Deployment Options

### Option 1: Docker Compose (Recommended for VPS/Cloud VM)

1. **Prepare Environment Variables**
```bash
# Copy the example environment file
cp env.example .env

# Edit with your actual values
nano .env
```

2. **Configure Your Camera**
```bash
# For IP cameras
CAMERA_TYPE=ip_camera
CAMERA_SOURCE=http://192.168.1.100:8080/video

# For RTSP cameras
CAMERA_TYPE=rtsp
CAMERA_SOURCE=rtsp://192.168.1.100:554/stream

# With authentication
CAMERA_USERNAME=admin
CAMERA_PASSWORD=your-camera-password
```

3. **Deploy with Docker Compose**
```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f face-sense

# Check health
curl http://localhost:5000/health
```

### Option 2: Google Cloud Platform (GCP)

#### **Cloud Run Deployment**
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/face-sense

# Deploy to Cloud Run
gcloud run deploy face-sense \
  --image gcr.io/PROJECT_ID/face-sense \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,CAMERA_SOURCE=your-camera-url
```

#### **Compute Engine (VM)**
```bash
# Create VM instance
gcloud compute instances create face-sense-vm \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-standard-2 \
  --boot-disk-size=20GB

# SSH into VM and deploy
gcloud compute ssh face-sense-vm
```

### Option 3: Amazon Web Services (AWS)

#### **Elastic Beanstalk**
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init face-sense

# Create environment
eb create production

# Deploy
eb deploy
```

#### **ECS with Fargate**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

docker build -t face-sense .
docker tag face-sense:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/face-sense:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/face-sense:latest
```

## 📹 Camera Configuration

### IP Camera Setup

#### **HTTP Cameras**
```bash
# Most IP cameras support HTTP streaming
export CAMERA_TYPE=ip_camera
export CAMERA_SOURCE=http://192.168.1.100:8080/video

# With authentication
export CAMERA_USERNAME=admin
export CAMERA_PASSWORD=password123
```

#### **RTSP Cameras**
```bash
# Professional IP cameras often use RTSP
export CAMERA_TYPE=rtsp
export CAMERA_SOURCE=rtsp://192.168.1.100:554/stream1

# With authentication
export CAMERA_USERNAME=admin
export CAMERA_PASSWORD=password123
```

#### **Popular Camera Brands**
- **Hikvision**: `rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101`
- **Dahua**: `rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0`
- **Axis**: `rtsp://192.168.1.100/axis-media/media.amp`
- **Foscam**: `http://192.168.1.100:88/cgi-bin/CGIProxy.fcgi?cmd=snapPicture2&usr=admin&pwd=password`

### Office Network Setup

1. **Configure Camera with Static IP**
   - Access camera web interface
   - Set static IP address
   - Configure port forwarding if needed
   - Test connectivity

2. **Network Security**
   - Configure firewall rules
   - Use VPN for remote access
   - Enable camera authentication
   - Regular firmware updates

3. **Test Connectivity**
```bash
# Test HTTP camera
curl -I http://192.168.1.100:8080/video

# Test RTSP camera
ffprobe rtsp://192.168.1.100:554/stream
```

## 🔒 Security Configuration

### Production Security Checklist

- [ ] Change default admin credentials
- [ ] Use strong secret keys (256-bit)
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Database encryption
- [ ] Backup strategy

### Environment Variables for Production

```bash
# Required for production
SECRET_KEY=your-256-bit-secret-key-here
ADMIN_PASSWORD=strong-password-with-special-chars-123!
JWT_SECRET=your-jwt-secret-key-256-bits

# Database
DB_TYPE=postgresql
DB_HOST=your-db-host
DB_NAME=face_sense_prod
DB_USERNAME=db_user
DB_PASSWORD=secure-db-password

# Camera
CAMERA_TYPE=ip_camera
CAMERA_SOURCE=your-camera-url
CAMERA_USERNAME=camera_user
CAMERA_PASSWORD=camera_password
```

### SSL Certificate Setup

```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
```

## 📊 Monitoring & Logging

### Health Checks

- **Application Health**: `GET /health`
- **Camera Status**: `GET /health/camera`
- **Database Status**: `GET /health/db`

### Monitoring Setup

#### **Prometheus + Grafana**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'face-sense'
    static_configs:
      - targets: ['face-sense:5000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

#### **Log Management**
```bash
# Docker logging
docker-compose logs -f face-sense

# Log rotation
sudo logrotate -f /etc/logrotate.d/face-sense
```

### Alerting

```bash
# Health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
if [ $response != "200" ]; then
    echo "Face-Sense is down!" | mail -s "Alert" admin@company.com
fi
```

## 🔄 Backup Strategy

### Database Backups

#### **PostgreSQL**
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h $DB_HOST -U $DB_USERNAME $DB_NAME > backup_$DATE.sql
gzip backup_$DATE.sql
aws s3 cp backup_$DATE.sql.gz s3://your-backup-bucket/
```

#### **SQLite**
```bash
# SQLite backup
cp attendance_data/attendance.db backup_$(date +%Y%m%d).db
```

### Model Data Backups

```bash
# Backup model files
tar -czf model_backup_$(date +%Y%m%d).tar.gz model_data/
aws s3 cp model_backup_$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/face-sense"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
if [ "$DB_TYPE" = "postgresql" ]; then
    pg_dump -h $DB_HOST -U $DB_USERNAME $DB_NAME > $BACKUP_DIR/db_$DATE.sql
else
    cp $DB_NAME $BACKUP_DIR/db_$DATE.db
fi

# Model data backup
tar -czf $BACKUP_DIR/models_$DATE.tar.gz model_data/

# Employee photos backup
tar -czf $BACKUP_DIR/photos_$DATE.tar.gz employee_photos/

# Upload to cloud storage
aws s3 sync $BACKUP_DIR/ s3://your-backup-bucket/face-sense/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

## 🚨 Troubleshooting

### Common Issues

#### **1. Camera Connection Failed**
```bash
# Check camera connectivity
ping 192.168.1.100
curl -I http://192.168.1.100:8080/video

# Check camera credentials
# Verify username/password in camera settings
```

#### **2. Database Connection Issues**
```bash
# Check database status
docker-compose logs postgres

# Test database connection
psql -h localhost -U $DB_USERNAME -d $DB_NAME -c "SELECT 1;"
```

#### **3. Performance Issues**
```bash
# Monitor system resources
docker stats

# Check application logs
docker-compose logs -f face-sense

# Adjust camera resolution if needed
# Lower resolution = better performance
```

#### **4. Memory Issues**
```bash
# Check memory usage
free -h
docker system df

# Clean up Docker
docker system prune -a
```

### Debug Mode

```bash
# Enable debug logging
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG

# Run with debug
python engine.py
```

## 📈 Scaling Options

### Horizontal Scaling

#### **Load Balancer Configuration**
```nginx
upstream face_sense {
    server face-sense-1:5000;
    server face-sense-2:5000;
    server face-sense-3:5000;
}
```

#### **Kubernetes Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-sense
spec:
  replicas: 3
  selector:
    matchLabels:
      app: face-sense
  template:
    metadata:
      labels:
        app: face-sense
    spec:
      containers:
      - name: face-sense
        image: face-sense:latest
        ports:
        - containerPort: 5000
        env:
        - name: ENVIRONMENT
          value: "production"
```

### Vertical Scaling

- **CPU**: Increase to 4+ cores for better face recognition performance
- **Memory**: 8GB+ RAM for handling multiple video streams
- **Storage**: SSD for faster database operations
- **Network**: High bandwidth for camera streams

## 🎯 Performance Optimization

### Camera Settings
- **Resolution**: 1280x720 for optimal performance
- **FPS**: 15-30 FPS depending on hardware
- **Compression**: H.264 for better streaming

### Application Settings
- **Frame Processing**: Skip frames during high load
- **Database**: Use connection pooling
- **Caching**: Redis for session management
- **CDN**: For static assets

### Hardware Recommendations

#### **Minimum Requirements**
- **CPU**: 2 cores, 2.4GHz
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: 100Mbps

#### **Recommended for Production**
- **CPU**: 4+ cores, 3.0GHz
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: 1Gbps

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Test camera connectivity
- [ ] Verify database setup
- [ ] Configure environment variables
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Test backup procedures

### Deployment
- [ ] Deploy application
- [ ] Verify health checks
- [ ] Test face recognition
- [ ] Monitor system resources
- [ ] Check logs for errors
- [ ] Verify attendance logging

### Post-Deployment
- [ ] Set up monitoring
- [ ] Configure alerting
- [ ] Test backup procedures
- [ ] Document access procedures
- [ ] Train users
- [ ] Schedule maintenance

## 🔧 Maintenance

### Regular Tasks
- **Daily**: Check health endpoints
- **Weekly**: Review logs and performance
- **Monthly**: Update dependencies
- **Quarterly**: Security audit
- **Annually**: Full system review

### Updates
```bash
# Update application
git pull origin main
docker-compose build
docker-compose up -d

# Update dependencies
pip install -r requirements.txt --upgrade
```

This deployment guide provides everything needed to deploy Face-Sense in a production environment with proper security, monitoring, and scalability considerations.
