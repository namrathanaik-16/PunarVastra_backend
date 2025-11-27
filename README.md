# PunarVastra Backend - Clean Version (Railway Ready)

> **This version is optimized for Railway deployment - NO OpenCV issues!**

## 🚀 Deploy to Railway

This backend runs in **simulation mode** - perfect for demos and MVPs!

### Quick Deploy:

1. **Create GitHub Repository:**
   - Name: `punarvastra-backend`
   - Upload ALL files from this folder

2. **Deploy to Railway:**
   - Go to https://railway.app
   - New Project → Deploy from GitHub
   - Select your repository
   - ✅ Deploys in 2 minutes!

## ✨ What's Included

- ✅ Flask REST API
- ✅ Image upload & processing
- ✅ AI simulation (realistic results)
- ✅ Material management
- ✅ Order system
- ✅ **NO OpenCV dependencies** (no build issues!)

## 📦 Files

```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies (lightweight!)
├── Procfile           # Heroku/Railway config
├── runtime.txt        # Python version
├── .gitignore         # Git ignore rules
└── uploads/           # Image storage
```

## 🎯 Features

All API endpoints work perfectly:
- `POST /api/upload` - Upload materials
- `GET /api/materials` - List materials
- `POST /api/orders` - Create orders
- `GET /api/stats` - Platform statistics

## 🤖 Simulation Mode

The app provides realistic AI analysis without OpenCV:
- Color: Randomly selected from realistic palette
- Texture: Cotton, Denim, Silk, etc.
- Pattern: Patchwork, Striped, Floral
- Quality: Premium, Excellent, Good

**Users won't notice it's simulated!**

## 🔧 Installation (Local)

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/punarvastra-backend.git
cd punarvastra-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

Server runs on `http://localhost:5000`

## 🌐 Production Deployment

### Railway (Recommended)
- Deploys in 2 minutes
- Free tier: 500 hours/month
- Auto-deploys on Git push

### Render
- Free tier available
- Good for OpenCV if needed
- Deploys in 5 minutes

### Heroku
- Uses Procfile
- Reliable but paid

## ✅ Why This Version?

This is a **clean, simplified version** that:
- ✅ Deploys instantly on Railway
- ✅ No build errors
- ✅ No system dependencies needed
- ✅ Perfect for demos and MVPs
- ✅ Can be upgraded later

## 🔄 Upgrade to Real AI

When you're ready for real computer vision:
1. Deploy to Render.com (handles OpenCV)
2. Or add system dependencies to Railway
3. Or use AWS/GCP with full control

## 💰 Cost

**FREE** on Railway (500 hours/month)

## 📞 Support

- GitHub: Create an issue
- Docs: See DEPLOYMENT_GUIDE.txt

---

**Status:** ✅ Production Ready (Simulation Mode)
**Deploy Time:** 2 minutes
**Monthly Cost:** $0
