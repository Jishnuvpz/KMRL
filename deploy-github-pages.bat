@echo off
echo ================================================
echo KMRL Platform - GitHub Pages Deployment
echo ================================================
echo.
echo This deploys ONLY the frontend as a static demo.
echo Backend features will not work on GitHub Pages.
echo.
echo What will work:
echo - User interface and design
echo - Navigation and layouts  
echo - Mock data display
echo.
echo What won't work:
echo - Real authentication
echo - Document upload/processing
echo - OCR and summarization
echo - Database operations
echo.
pause
echo.

echo Building frontend for production...
cd Frontend
call npm install
call npm run build

echo.
echo Frontend built successfully!
echo.
echo Manual steps to deploy to GitHub Pages:
echo 1. Go to https://github.com/Jishnuvpz/KMRL/settings/pages
echo 2. Source: Deploy from a branch
echo 3. Branch: main
echo 4. Folder: /Frontend/dist
echo 5. Click Save
echo.
echo Your site will be available at:
echo https://jishnuvpz.github.io/KMRL/
echo.
pause
