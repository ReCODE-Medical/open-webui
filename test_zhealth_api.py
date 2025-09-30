#!/usr/bin/env python3
"""
Test script for the Zhealth API endpoint.

This script tests the /api/chat/zhealth/completions endpoint to verify:
1. API key authentication works
2. Requests are processed correctly
3. Logs are written to Supabase

Usage:
    python test_zhealth_api.py --api-key <your-api-key> --base-url <base-url>

Example:
    python test_zhealth_api.py --api-key sk-abc123 --base-url http://localhost:8080
"""

import argparse
import requests
import json
import sys


def test_zhealth_completion(base_url, api_key, stream=False):
    """Test the zhealth completion endpoint"""
    url = f"{base_url}/api/chat/zhealth/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-3.5-turbo",  # Adjust this to match your available models
        "messages": [
            {
                "role": "user",
                "content": "What is the capital of France? Please provide a brief answer."
            }
        ],
        "stream": stream,
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print(f"Testing {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print("-" * 80)
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print("-" * 80)
        
        if response.status_code == 200:
            if stream:
                print("Response (streaming):")
                for line in response.iter_lines():
                    if line:
                        print(line.decode('utf-8'))
            else:
                result = response.json()
                print("Response:")
                print(json.dumps(result, indent=2))
            print("-" * 80)
            print("✓ Test PASSED - Request completed successfully")
            return True
        else:
            print(f"Error Response: {response.text}")
            print("-" * 80)
            print("✗ Test FAILED - Request returned error status")
            return False
            
    except Exception as e:
        print(f"✗ Test FAILED - Exception occurred: {e}")
        return False


def test_zhealth_auth_failure(base_url):
    """Test that authentication is required"""
    url = f"{base_url}/api/chat/zhealth/completions"
    
    headers = {
        "Content-Type": "application/json"
        # No Authorization header
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Test"}]
    }
    
    print("Testing authentication requirement...")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 401:
            print("✓ Authentication test PASSED - Request correctly rejected without API key")
            return True
        else:
            print(f"✗ Authentication test FAILED - Expected 401, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Authentication test FAILED - Exception occurred: {e}")
        return False


def verify_database_schema(supabase_url, supabase_key):
    """Verify the zhealth schema exists in Supabase"""
    if not supabase_url or not supabase_key:
        print("Skipping database verification - no Supabase credentials provided")
        return None
    
    print("Verifying database schema...")
    # This would require Supabase client library
    # For now, just indicate that manual verification is needed
    print("! Manual verification needed - check that zhealth.zhealth_logs table exists in Supabase")
    return None


def main():
    parser = argparse.ArgumentParser(description='Test the Zhealth API endpoint')
    parser.add_argument('--api-key', required=True, help='API key for authentication')
    parser.add_argument('--base-url', required=True, help='Base URL of the API (e.g., http://localhost:8080)')
    parser.add_argument('--stream', action='store_true', help='Test streaming response')
    parser.add_argument('--supabase-url', help='Supabase URL for database verification')
    parser.add_argument('--supabase-key', help='Supabase key for database verification')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Zhealth API Test Suite")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Authentication failure
    print("Test 1: Authentication Requirement")
    print("-" * 80)
    results.append(test_zhealth_auth_failure(args.base_url))
    print()
    
    # Test 2: Successful completion (non-streaming)
    print("Test 2: Successful Completion (Non-Streaming)")
    print("-" * 80)
    results.append(test_zhealth_completion(args.base_url, args.api_key, stream=False))
    print()
    
    # Test 3: Successful completion (streaming) - if requested
    if args.stream:
        print("Test 3: Successful Completion (Streaming)")
        print("-" * 80)
        results.append(test_zhealth_completion(args.base_url, args.api_key, stream=True))
        print()
    
    # Database verification
    if args.supabase_url and args.supabase_key:
        print("Database Verification")
        print("-" * 80)
        verify_database_schema(args.supabase_url, args.supabase_key)
        print()
    
    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())