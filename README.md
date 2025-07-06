# Trading API - VPS Production Environment

## 📝 Mô tả
Folder này chứa phiên bản **VPS PRODUCTION** của hệ thống Trading API, được tối ưu cho triển khai production trên VPS.

## 🚀 Tính năng Production
- ✅ API server với Gunicorn (production WSGI)
- ✅ Data collector với auto-reconnect và error handling
- ✅ Logging rotation và monitoring
- ✅ Caching để tối ưu performance
- ✅ CORS support
- ✅ Pagination và filtering
- ✅ Systemd service auto-restart
- ✅ Theo dõi 10 symbol crypto chính
- ✅ Data rotation tự động (max 10,000 records)

## 📋 Yêu cầu VPS
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Debian 10+
- **RAM:** Tối thiểu 1GB (khuyến nghị 2GB+)
- **CPU:** 1 vCPU (khuyến nghị 2+ vCPU)
- **Storage:** 10GB+ free space
- **Network:** Public IP với port 5000 mở
- **Python:** 3.8+

## ⚡ Triển khai Production

### 1. Upload files lên VPS:
```bash
# Sử dụng SCP
scp -r vps_production/* user@your-vps-ip:/home/user/trading-api/

# Hoặc clone từ git
git clone <your-repo> /home/user/trading-api/
cd /home/user/trading-api/vps_production
```

### 2. Chạy script setup:
```bash
chmod +x *.sh
./setup_vps.sh
```

### 3. Khởi động services:
```bash
# Data collector
./start_data_collector.sh

# API server  
./start_api_server.sh
```

## 🔧 Quản lý Services

### Manual Start/Stop:
```bash
# Data Collector
./start_data_collector.sh
./stop_data_collector.sh

# API Server
./start_api_server.sh
./stop_api_server.sh
```

### Systemd Services (Auto-restart):
```bash
# Setup systemd
sudo cp trading-data-collector.service /etc/systemd/system/
sudo cp trading-api-server.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable trading-data-collector
sudo systemctl enable trading-api-server

# Start services
sudo systemctl start trading-data-collector
sudo systemctl start trading-api-server

# Check status
sudo systemctl status trading-data-collector
sudo systemctl status trading-api-server
```

## 🌐 API Endpoints

| Endpoint | Method | Mô tả | Pagination |
|----------|--------|-------|-----------|
| `/` | GET | Server info, quick stats | - |
| `/api/health` | GET | Health check chi tiết | - |
| `/api/info` | GET | Server configuration | - |
| `/api/trading` | GET | Tất cả dữ liệu | ✅ (limit, offset) |
| `/api/trading/latest` | GET | Dữ liệu mới nhất | ✅ (limit) |
| `/api/trading/symbol/<symbol>` | GET | Dữ liệu theo symbol | ✅ (limit) |
| `/api/trading/stats` | GET | Thống kê toàn diện | - |

### Parameters:
- `limit`: Số records trả về (max 1000)
- `offset`: Vị trí bắt đầu (cho pagination)
- `symbol`: Filter theo symbol cụ thể

### Example requests:
```bash
# Production API URL
API_URL="http://your-vps-ip:5000"

# Get latest 100 trades
curl "$API_URL/api/trading/latest?limit=100"

# Get BTCUSDT trades with pagination
curl "$API_URL/api/trading/symbol/BTCUSDT?limit=50&offset=0"

# Get trading statistics
curl "$API_URL/api/trading/stats"

# Health check
curl "$API_URL/api/health"
```

## 📊 Configuration Production

```python
PRODUCTION_CONFIG = {
    "max_records_per_request": 1000,
    "default_limit": 100,
    "cache_timeout": 60,  # seconds
    "enable_cors": True
}

# Symbols tracked
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT",
    "BNBUSDT", "XRPUSDT", "MATICUSDT", "LINKUSDT", "AVAXUSDT"
]

# Data management
MAX_RECORDS = 10000
AUTO_BACKUP = True
ROTATION_ENABLED = True
```

## 📁 Cấu trúc Production

```
vps_production/
├── data_collector.py              # Data collector với production features
├── api_server.py                  # API server với Gunicorn support
├── trading_data.json              # File dữ liệu chính
├── requirements.txt               # Dependencies (includes Gunicorn)
├── setup_vps.sh                   # Script setup VPS
├── start_data_collector.sh        # Start data collector
├── stop_data_collector.sh         # Stop data collector
├── start_api_server.sh            # Start API server
├── stop_api_server.sh             # Stop API server
├── trading-data-collector.service # Systemd service collector
├── trading-api-server.service     # Systemd service API
├── logs/                          # Logs directory
│   ├── data_collector_stdout.log
│   ├── api_access.log
│   ├── api_error.log
│   └── api_server_stdout.log
├── backups/                       # Data backups
└── README.md                      # File này
```

## 🔍 Monitoring Production

### Logs real-time:
```bash
# Data collector
tail -f logs/data_collector_stdout.log
tail -f data_collector.log

# API server
tail -f logs/api_access.log
tail -f logs/api_error.log
tail -f api_server.log

# System logs
sudo journalctl -u trading-data-collector -f
sudo journalctl -u trading-api-server -f
```

### Performance monitoring:
```bash
# Check processes
ps aux | grep -E "(data_collector|gunicorn)"

# Memory usage
free -h

# Disk usage
df -h

# Network connections
netstat -tulpn | grep :5000

# API performance test
curl -w "@curl-format.txt" -o /dev/null http://your-vps-ip:5000/api/health
```

### Health checks:
```bash
# Automated health check script
#!/bin/bash
API_URL="http://localhost:5000"
response=$(curl -s $API_URL/api/health)
status=$(echo $response | jq -r '.status')

if [ "$status" = "healthy" ]; then
    echo "API is healthy"
else
    echo "API is unhealthy: $response"
    # Restart services if needed
fi
```

## 🔧 Maintenance

### Data backup:
```bash
# Manual backup
cp trading_data.json backups/trading_data_$(date +%Y%m%d_%H%M%S).json

# Automated backup (cron)
0 */6 * * * cd /home/user/trading-api && cp trading_data.json backups/trading_data_$(date +\%Y\%m\%d_\%H\%M\%S).json
```

### Log rotation:
```bash
# Setup logrotate
sudo nano /etc/logrotate.d/trading-api

# Content:
/home/user/trading-api/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### Updates:
```bash
# Update code
git pull origin main

# Restart services
sudo systemctl restart trading-data-collector
sudo systemctl restart trading-api-server
```

## 🔒 Security

### Firewall:
```bash
# UFW setup
sudo ufw allow 22          # SSH
sudo ufw allow 5000        # API
sudo ufw enable
```

### SSL/HTTPS (optional):
```bash
# Nginx reverse proxy với SSL
sudo apt install nginx certbot python3-certbot-nginx

# Cấu hình nginx
sudo nano /etc/nginx/sites-available/trading-api

# Content:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/trading-api /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 🚨 Troubleshooting Production

### Common issues:

1. **Service won't start:**
   ```bash
   # Check logs
   sudo journalctl -u trading-data-collector --since "5 minutes ago"
   
   # Check file permissions
   ls -la /home/user/trading-api/
   
   # Check virtual environment
   source vps_env/bin/activate
   which python
   ```

2. **High memory usage:**
   ```bash
   # Check data file size
   ls -lh trading_data.json
   
   # Force data rotation
   python -c "
   import json
   with open('trading_data.json') as f: data = json.load(f)
   with open('trading_data.json', 'w') as f: json.dump(data[-5000:], f)
   "
   ```

3. **API slow response:**
   ```bash
   # Clear cache and restart
   sudo systemctl restart trading-api-server
   
   # Check database size
   wc -l trading_data.json
   ```

4. **WebSocket disconnections:**
   ```bash
   # Check network
   ping bitget.com
   
   # Check firewall
   sudo ufw status
   
   # Restart collector
   sudo systemctl restart trading-data-collector
   ```

## 📈 Performance Tuning

### Gunicorn optimization:
```bash
# More workers for high traffic
ExecStart=/home/ubuntu/trading-api/vps_env/bin/gunicorn --bind 0.0.0.0:5000 --workers 8 --worker-class gevent --worker-connections 1000 --timeout 120 api_server:app
```

### System optimization:
```bash
# Increase file descriptors
echo "fs.file-max = 65536" >> /etc/sysctl.conf

# Network optimization
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
sysctl -p
```

## 📞 Production Support
- Monitor logs thường xuyên
- Setup alerts cho downtime
- Backup dữ liệu định kỳ
- Update security patches
- Monitor disk space và memory usage
