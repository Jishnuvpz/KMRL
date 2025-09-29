# 🚀 Deploy KMRL Platform to Render.com

## 📋 Step-by-Step Deployment Guide

### **Step 1: Commit and Push Deployment Config**
```bash
# We've prepared deployment files, let's commit them
git add .
git commit -m "feat: Add Render.com deployment configuration"
git push origin main
```

### **Step 2: Sign Up to Render**
1. **Go to**: https://render.com
2. **Click "Get Started"**
3. **Sign up with GitHub** (recommended)
4. **Authorize Render** to access your repositories

### **Step 3: Create Backend Web Service**
1. **Click "New +"** → **"Web Service"**
2. **Connect Repository**: Select `Jishnuvpz/KMRL`
3. **Configure Service**:
   ```
   Name: kmrl-backend
   Runtime: Python 3
   Build Command: cd Backend && pip install -r requirements-minimal.txt
   Start Command: cd Backend && python -m uvicorn app.demo_main:app --host 0.0.0.0 --port $PORT
   ```

### **Step 4: Add Environment Variables**
In the **Environment** section, add:
```
SECRET_KEY = your-super-secret-key-here
ENVIRONMENT = production
DATABASE_URL = (will be auto-filled when you add database)
```

### **Step 5: Create Database**
1. **Click "New +"** → **"PostgreSQL"**
2. **Name**: `kmrl-database`
3. **Plan**: Free
4. **Create Database**
5. **Copy the DATABASE_URL** and add it to your backend service

### **Step 6: Create Frontend Static Site**
1. **Click "New +"** → **"Static Site"**
2. **Connect Repository**: Select `Jishnuvpz/KMRL`
3. **Configure**:
   ```
   Name: kmrl-frontend
   Build Command: cd Frontend && npm ci && npm run build
   Publish Directory: Frontend/dist
   ```

### **Step 7: Configure Frontend Environment**
Add environment variable:
```
VITE_API_BASE_URL = https://your-backend-name.onrender.com
```

### **Step 8: Deploy!**
1. **Click "Create Web Service"** (for backend)
2. **Click "Create Static Site"** (for frontend)
3. **Wait for deployment** (5-15 minutes)

## 🎯 **Expected URLs**
- **Backend**: https://kmrl-backend-xxxx.onrender.com
- **Frontend**: https://kmrl-frontend-xxxx.onrender.com
- **API Docs**: https://kmrl-backend-xxxx.onrender.com/api/docs

## ⚡ **Quick Deploy Commands**
Run these locally first to test:

```bash
# Test backend
cd Backend
pip install -r requirements-minimal.txt
python -m uvicorn app.demo_main:app --host 0.0.0.0 --port 8000

# Test frontend
cd Frontend
npm install
npm run build
```

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Build Fails**:
   ```bash
   # Check logs in Render dashboard
   # Usually missing dependencies
   ```

2. **CORS Errors**:
   ```bash
   # Update backend CORS origins with your Render URLs
   # Already configured in demo_main.py
   ```

3. **Environment Variables**:
   ```bash
   # Make sure VITE_API_BASE_URL points to your backend URL
   # Check Render environment variables section
   ```

## 💰 **Free Tier Limitations**
- **Spins down** after 15 minutes of inactivity
- **Cold start** delay (10-30 seconds)
- **750 hours/month** (about 31 days)
- **Limited resources** (512MB RAM)

## 🎯 **After Deployment**

### **Test Your Deployment:**
1. **Visit Frontend URL**
2. **Try Login**: admin@kmrl.co.in / password123
3. **Test Document Upload**
4. **Check API Docs**: /api/docs
5. **Verify Database**: User data should persist

### **Custom Domain (Optional):**
1. **Go to Settings** in your Render service
2. **Add Custom Domain**
3. **Configure DNS** with your domain provider

## 📞 **Need Help?**

If deployment fails:
1. **Check Render logs** in the dashboard
2. **Verify GitHub repository** is accessible
3. **Test build commands locally** first
4. **Check environment variables** are set correctly

## 🚀 **Next Steps**

Once deployed:
- **Share the URLs** with stakeholders
- **Test all features** in production environment  
- **Monitor usage** in Render dashboard
- **Consider upgrading** to paid plan for production use

---

**Your KMRL Platform will be live and accessible worldwide!** 🌍
