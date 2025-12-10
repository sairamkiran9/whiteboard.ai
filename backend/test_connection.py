#!/usr/bin/env python3
"""
Simple connection test for the FastAPI backend
"""

import sys
import subprocess
import requests
import json

def test_local_connection():
    """Test if backend is accessible locally"""
    print("🔍 Testing backend connection...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test basic health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ GET /health: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        
        # Test API health endpoint  
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        print(f"✅ GET /api/v1/health: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Model: {health_data.get('model')}")
        
        # Test providers endpoint
        response = requests.get(f"{base_url}/api/v1/providers", timeout=5)
        print(f"✅ GET /api/v1/providers: {response.status_code}")
        
        # Test suggestion endpoint with minimal request
        test_request = {
            "canvas_elements": [
                {"type": "rectangle", "text": "API Gateway", "x": 100, "y": 100, "width": 100, "height": 50, "id": "test-1"}
            ],
            "context": {"design_type": "api"}
        }
        
        print("🧪 Testing suggestion endpoint...")
        response = requests.post(f"{base_url}/api/v1/suggest", json=test_request, timeout=30)
        print(f"✅ POST /api/v1/suggest: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Reasoning: {result['reasoning'][:100]}...")
            if result.get('suggestion') and result['suggestion'].get('nodes'):
                print(f"   Suggested nodes: {len(result['suggestion']['nodes'])}")
        else:
            print(f"   Error: {response.text}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - backend server not running")
        print("   Start with: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server may be overloaded")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_server_process():
    """Check if uvicorn process is running"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        uvicorn_processes = [line for line in result.stdout.split('\n') if 'uvicorn' in line and 'main:app' in line]
        
        if uvicorn_processes:
            print("🟢 Found uvicorn process(es):")
            for process in uvicorn_processes:
                print(f"   {process.strip()}")
            return True
        else:
            print("🔴 No uvicorn process found")
            return False
    except Exception as e:
        print(f"❌ Could not check processes: {e}")
        return False

def check_port_usage():
    """Check what's running on port 8000"""
    try:
        result = subprocess.run(['lsof', '-i', ':8000'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("🟢 Port 8000 in use:")
            print(result.stdout)
            return True
        else:
            print("🔴 Port 8000 appears to be free")
            return False
    except Exception as e:
        print(f"❌ Could not check port usage: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Backend Connection Diagnostic Tool")
    print("=" * 40)
    
    # Check if server process is running
    process_running = check_server_process()
    
    # Check port usage
    port_in_use = check_port_usage()
    
    # Test connection
    connection_ok = test_local_connection()
    
    print("\n📋 Summary:")
    print(f"   Process running: {'✅' if process_running else '❌'}")
    print(f"   Port 8000 in use: {'✅' if port_in_use else '❌'}")
    print(f"   Connection test: {'✅' if connection_ok else '❌'}")
    
    if not connection_ok:
        print("\n🛠️  To start the backend:")
        print("   cd backend")
        print("   source .venv/bin/activate")  
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")