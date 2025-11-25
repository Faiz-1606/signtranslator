# Deployment Configuration for Sign Language Detection Server

## Deployment Options

### 1. Heroku Deployment

#### Prerequisites
- Heroku account
- Heroku CLI installed
- Git repository

#### Steps
```bash
# Login to Heroku
heroku login

# Create a new Heroku app
cd server
heroku create your-app-name

# Set buildpacks
heroku buildpacks:add --index 1 heroku/python

# Deploy
git init
git add .
git commit -m "Initial commit"
git push heroku main

# Check logs
heroku logs --tail
```

#### Environment Variables
```bash
heroku config:set FLASK_ENV=production
```

### 2. Railway Deployment

#### Steps
1. Go to [Railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Select the `server` directory
4. Railway will auto-detect Python and deploy
5. Set environment variables in Railway dashboard

### 3. Render Deployment

#### Steps
1. Go to [Render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repository
4. Configure:
   - **Root Directory**: `server`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Deploy

### 4. Google Cloud Run

#### Steps
```bash
# Install gcloud CLI
gcloud auth login

# Build and deploy
cd server
gcloud run deploy sign-language-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 5. AWS EC2 / DigitalOcean / VPS

#### Setup Script
```bash
# SSH into server
ssh user@your-server-ip

# Install dependencies
sudo apt update
sudo apt install python3-pip nginx

# Clone repository
git clone your-repo-url
cd learnsign/server

# Install Python packages
pip3 install -r requirements.txt

# Run with gunicorn (production)
gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120

# Or use systemd service (see below)
```

#### Systemd Service (for VPS)
Create `/etc/systemd/system/signlanguage.service`:
```ini
[Unit]
Description=Sign Language Detection API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/learnsign/server
ExecStart=/usr/bin/gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable signlanguage
sudo systemctl start signlanguage
sudo systemctl status signlanguage
```

#### Nginx Configuration
Create `/etc/nginx/sites-available/signlanguage`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/signlanguage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Docker Deployment

Create `Dockerfile` in server directory:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
```

Build and run:
```bash
docker build -t sign-language-api .
docker run -p 5000:5000 sign-language-api
```

## Update Frontend API URL

After deployment, update the API URL in your React app:

**File**: `client/src/Pages/SignToText.js`
```javascript
// Change this line:
const API_URL = 'http://localhost:5000/api';

// To your deployed URL:
const API_URL = 'https://your-deployed-api.com/api';
```

Or use environment variables:
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
```

Then create `.env` in client directory:
```
REACT_APP_API_URL=https://your-deployed-api.com/api
```

## Important Notes

1. **Model File Size**: The PyTorch model might be large. Consider:
   - Using Git LFS for large files
   - Uploading model to cloud storage and downloading during deployment
   - Compressing the model

2. **Memory Requirements**: The server needs sufficient RAM for:
   - PyTorch model (~100-500MB)
   - MediaPipe (~200MB)
   - Processing overhead

3. **Cold Start**: First request might be slow as model loads. Consider:
   - Keeping server warm with periodic pings
   - Loading model on startup (already implemented)

4. **CORS**: Already configured for all origins. For production, restrict to your domain:
```python
CORS(app, origins=['https://your-frontend-domain.com'])
```

5. **Rate Limiting**: Consider adding rate limiting for production:
```bash
pip install flask-limiter
```

## Recommended: Railway or Render
- Easy deployment
- Free tier available
- Auto-scaling
- Good for Python/ML apps
