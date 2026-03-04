#!/usr/bin/env python3
"""
Test all major API endpoints to ensure they're working correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth():
    """Test authentication endpoints"""
    print("🔐 Testing Authentication...")
    
    # Test login
    login_data = {
        "username": "test@example.com",
        "password": "Test123456"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("  ✅ Login successful")
        return token
    else:
        print(f"  ❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_endpoints(token):
    """Test various API endpoints"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    tests = [
        {
            "name": "Get User Info",
            "method": "GET",
            "url": f"{BASE_URL}/api/auth/me",
            "expected": 200
        },
        {
            "name": "List Clients",
            "method": "GET", 
            "url": f"{BASE_URL}/api/clients/",
            "expected": 200
        },
        {
            "name": "List Products",
            "method": "GET",
            "url": f"{BASE_URL}/api/products/",
            "expected": 200
        },
        {
            "name": "Calculate Product Cost",
            "method": "POST",
            "url": f"{BASE_URL}/api/costing/calculate-product-cost",
            "data": {
                "raw_material_cost": 25,
                "labour_cost_per_unit": 22,
                "overhead_percentage": 10,
                "target_margin_percentage": 20,
                "tax_rate": 18
            },
            "expected": 200
        },
        {
            "name": "Evaluate Order",
            "method": "POST",
            "url": f"{BASE_URL}/api/costing/evaluate-order",
            "data": {
                "customer_name": "Test Customer",
                "product_id": 1,
                "selling_price": 100,
                "cost_price": 25,
                "quantity": 100,
                "credit_days": 30
            },
            "expected": 200
        },
        {
            "name": "Get Financial Formulas",
            "method": "GET",
            "url": f"{BASE_URL}/api/financials/formulas",
            "expected": 200
        },
        {
            "name": "List Scenarios",
            "method": "GET",
            "url": f"{BASE_URL}/api/scenarios?client_id=1",
            "expected": 200
        },
        {
            "name": "AI Assistant Chat",
            "method": "POST",
            "url": f"{BASE_URL}/api/assistant/chat",
            "data": {
                "message": "What is my current financial status?",
                "client_id": 1
            },
            "expected": 200
        }
    ]
    
    print("\n📊 Testing API Endpoints...")
    
    for test in tests:
        try:
            if test["method"] == "GET":
                response = requests.get(test["url"], headers=headers)
            else:
                response = requests.post(test["url"], headers=headers, json=test.get("data"))
            
            if response.status_code == test["expected"]:
                print(f"  ✅ {test['name']}")
            else:
                print(f"  ❌ {test['name']}: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ {test['name']}: Error - {str(e)}")

def test_rbac_protection():
    """Test RBAC protection on sensitive endpoints"""
    print("\n🛡️ Testing RBAC Protection...")
    
    # Test without authentication
    response = requests.get(f"{BASE_URL}/api/audit-logs")
    if response.status_code == 401:
        print("  ✅ Audit logs properly protected (no auth)")
    else:
        print(f"  ❌ Audit logs not protected: {response.status_code}")
    
    # Test with authentication but wrong role (if we had a viewer user)
    # For now, just test that Owner role works
    token = test_auth()
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/audit-logs", headers=headers)
        if response.status_code == 200:
            print("  ✅ Audit logs accessible with Owner role")
        else:
            print(f"  ❌ Audit logs not accessible with Owner role: {response.status_code}")

def main():
    """Run all tests"""
    print("🚀 Starting API Endpoint Tests...\n")
    
    # Test authentication
    token = test_auth()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Test endpoints
    test_endpoints(token)
    
    # Test RBAC
    test_rbac_protection()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()