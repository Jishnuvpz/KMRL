"""
Test the production server
"""
from app.main_production_clean import app
from fastapi.testclient import TestClient


def test_production_server():
    client = TestClient(app)

    # Test root endpoint
    response = client.get('/')
    assert response.status_code == 200
    data = response.json()
    print("✅ Root endpoint working:", data['data']['system'])

    # Test health endpoint
    response2 = client.get('/health')
    assert response2.status_code == 200
    health_data = response2.json()
    print("✅ Health endpoint working:", health_data['data']['status'])

    # Test documents endpoint
    response3 = client.get('/api/documents/')
    assert response3.status_code == 200
    docs_data = response3.json()
    print(f"✅ Documents endpoint working: {len(docs_data['data'])} documents")

    # Test login endpoint
    response4 = client.post(
        '/api/auth/login', data={'username': 'admin@kmrl.co.in', 'password': 'password123'})
    assert response4.status_code == 200
    login_data = response4.json()
    print("✅ Login endpoint working:", login_data['data']['user']['role'])

    # Test dashboard stats
    response5 = client.get('/api/dashboard/stats')
    assert response5.status_code == 200
    stats_data = response5.json()
    print(
        f"✅ Dashboard endpoint working: {stats_data['data']['total_documents']} total docs")

    print("\n🎉 PRODUCTION SERVER FULLY OPERATIONAL! 🎉")
    print("All endpoints tested successfully!")


if __name__ == "__main__":
    test_production_server()
