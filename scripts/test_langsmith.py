#!/usr/bin/env python3
"""
Test LangSmith API connectivity and API key validity
"""

import os
import sys
import requests
sys.path.append('src')

def test_langsmith_api():
    """Test LangSmith API connectivity"""
    print("=== LangSmith API Test ===\n")
    
    try:
        from config.vector_config import (
            LANGSMITH_API_KEY, LANGSMITH_ENDPOINT, LANGSMITH_PROJECT
        )
        
        print(f"API Endpoint: {LANGSMITH_ENDPOINT}")
        print(f"Project: {LANGSMITH_PROJECT}")
        print(f"API Key: {'✓ Set' if LANGSMITH_API_KEY else '✗ Missing'}")
        
        if not LANGSMITH_API_KEY:
            print("\n✗ No API key found. Please set LANGSMITH_API_KEY environment variable.")
            return
        
        # Test API connectivity
        print("\n1. Testing API connectivity...")
        
        # Test the projects endpoint - use the correct path
        projects_url = f"{LANGSMITH_ENDPOINT}/projects"
        headers = {
            "Authorization": f"Bearer {LANGSMITH_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(projects_url, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ API key is valid and can access projects")
                projects = response.json()
                print(f"Found {len(projects)} projects")
                
                # Check if our project exists
                project_names = [p.get('name') for p in projects]
                if LANGSMITH_PROJECT in project_names:
                    print(f"✓ Project '{LANGSMITH_PROJECT}' exists")
                else:
                    print(f"⚠ Project '{LANGSMITH_PROJECT}' not found. Available projects: {project_names[:5]}")
                    
            elif response.status_code == 401:
                print("✗ API key is invalid (401 Unauthorized)")
            elif response.status_code == 403:
                print("✗ API key lacks permissions (403 Forbidden)")
            elif response.status_code == 404:
                print("✗ API endpoint not found (404) - check if endpoint URL is correct")
            else:
                print(f"✗ Unexpected response: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Network error: {e}")
            
        # Test the runs endpoint (where the error occurred)
        print("\n2. Testing runs endpoint...")
        runs_url = f"{LANGSMITH_ENDPOINT}/runs"
        
        try:
            response = requests.get(runs_url, headers=headers, timeout=10)
            print(f"Runs endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Can access runs endpoint")
            elif response.status_code == 401:
                print("✗ API key is invalid for runs endpoint (401)")
            else:
                print(f"✗ Cannot access runs endpoint: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Runs endpoint error: {e}")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

def suggest_fixes():
    """Suggest fixes for common LangSmith issues"""
    print("\n=== Suggested Fixes ===\n")
    
    print("1. **Invalid API Key**:")
    print("   - Go to https://smith.langchain.com/")
    print("   - Navigate to Settings > API Keys")
    print("   - Create a new API key or copy an existing one")
    print("   - Update your environment variable: LANGSMITH_API_KEY=your_new_key")
    
    print("\n2. **Project Doesn't Exist**:")
    print("   - Create the project in LangSmith dashboard")
    print("   - Or change LANGSMITH_PROJECT to an existing project name")
    
    print("\n3. **Temporary Disable Tracing**:")
    print("   - Set LANGSMITH_TRACING=false in your environment")
    print("   - This will disable tracing without affecting LLM functionality")
    
    print("\n4. **Check API Key Permissions**:")
    print("   - Ensure your API key has 'write' permissions")
    print("   - Some keys might be read-only")

if __name__ == "__main__":
    test_langsmith_api()
    suggest_fixes() 