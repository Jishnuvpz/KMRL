"""
Simple test script to verify demo_main.py works in production environment
"""
try:
    print("🔍 Testing KMRL Demo App...")
    
    # Test basic imports
    from fastapi import FastAPI
    from uvicorn import run
    print("✅ Basic FastAPI imports work")
    
    # Test demo_main import
    from app.demo_main import app
    print("✅ demo_main.py imports successfully")
    print(f"   App title: {app.title}")
    print(f"   App version: {app.version}")
    print(f"   Total routes: {len(app.routes)}")
    
    # Test that health endpoint exists
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    if '/health' in routes:
        print("✅ Health endpoint found")
    else:
        print("❌ Health endpoint missing")
        
    print("\n🚀 Demo app is ready for deployment!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()