# 📄 GitHub Pages Frontend-Only Deployment

## ⚠️ Limitations
This deploys ONLY the React frontend as a static site. Backend features won't work.

## What Works
- ✅ **Login UI** (frontend only)
- ✅ **Document display** (mock data)
- ✅ **Navigation and UI**
- ✅ **Responsive design**

## What Won't Work
- ❌ **Real authentication** (no backend)
- ❌ **Document upload** (no server)
- ❌ **OCR processing** (no AI models)
- ❌ **Summarization** (no AI backend)
- ❌ **Database operations**

## 📋 Deployment Steps

### 1. Prepare Frontend for Static Deployment
```bash
cd Frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### 2. Configure for GitHub Pages
```javascript
// Frontend/vite.config.ts - Update for GitHub Pages
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      base: '/KMRL/', // Your repository name
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [react()],
      define: {
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.VITE_API_BASE_URL': JSON.stringify('https://your-backend-url.com'),
      },
      build: {
        outDir: 'dist',
        sourcemap: true,
      }
    };
});
```

### 3. Deploy to GitHub Pages
1. **Go to Repository Settings**
2. **Pages Section**:
   - Source: Deploy from a branch
   - Branch: `main`
   - Folder: `/Frontend/dist`
3. **Access**: https://jishnuvpz.github.io/KMRL/

### 4. GitHub Actions Auto-Deploy (Optional)
```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages
on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: |
        cd Frontend
        npm ci
        
    - name: Build
      run: |
        cd Frontend  
        npm run build
        
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./Frontend/dist
```

## 🎯 Use Case
Perfect for:
- **UI/UX demonstrations**
- **Design showcases** 
- **Frontend portfolio**
- **Client previews**

Not suitable for:
- **Production use**
- **Real document processing**
- **User authentication**
