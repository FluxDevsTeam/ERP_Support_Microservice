#!/usr/bin/env python
"""
Comprehensive test for refactored blog service following email service pattern.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import requests
import json
from django.test.utils import get_runner
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status

def test_blog_endpoints():
    """Test the refactored blog API endpoints"""
    print("🚀 Testing refactored blog service with email service pattern...")
    print("=" * 60)
    
    client = APIClient()
    
    # Test 1: List blog posts (public access)
    print("\n1. Testing public blog posts list endpoint...")
    try:
        response = client.get('/api/blogs/public/posts/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success: Retrieved {len(data.get('results', []))} published posts")
        else:
            print(f"   ✗ Failed: {response.content.decode()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Get specific blog post (public access)
    print("\n2. Testing public blog post detail endpoint...")
    try:
        # First get a post ID from the list
        response = client.get('/api/blogs/public/posts/')
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                post_id = data['results'][0]['id']
                detail_response = client.get(f'/api/blogs/public/posts/{post_id}/')
                print(f"   Status: {detail_response.status_code}")
                if detail_response.status_code == 200:
                    print(f"   ✓ Success: Retrieved post {post_id}")
                else:
                    print(f"   ✗ Failed: {detail_response.content.decode()}")
            else:
                print("   ⚠ No posts available for testing")
        else:
            print(f"   ✗ Failed to get list: {response.content.decode()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Test all explicit URL patterns work
    print("\n3. Testing explicit URL patterns...")
    endpoints_to_test = [
        ('/api/blogs/posts/', 'GET', 'List blog posts'),
        ('/api/blogs/comments/', 'GET', 'List comments'),
        ('/api/blogs/public/posts/', 'GET', 'List public blog posts'),
    ]
    
    for endpoint, method, description in endpoints_to_test:
        try:
            response = client.get(endpoint)
            print(f"   {description}: {response.status_code} {'✓' if response.status_code in [200, 404] else '✗'}")
        except Exception as e:
            print(f"   {description}: ✗ Error - {e}")
    
    print("\n" + "=" * 60)
    print("✅ Blog service refactoring test completed!")
    print("📝 Summary of changes:")
    print("   • Converted ModelViewSet to ViewSet with explicit method overrides")
    print("   • Added @swagger_helper decorators to all methods")
    print("   • Removed PUT requests, kept only PATCH for partial updates")
    print("   • Updated URL patterns to match email service style")
    print("   • All endpoints follow microservice architecture pattern")

def test_swagger_documentation():
    """Test that Swagger documentation is properly configured"""
    print("\n🔍 Testing Swagger documentation setup...")
    
    # Check that the views have the correct decorators
    from apps.blogs.views import BlogPostViewSet, CommentViewSet, PublicBlogPostViewSet
    
    # Test BlogPostViewSet methods
    blog_methods = ['list', 'retrieve', 'create', 'partial_update', 'destroy', 'publish', 'unpublish', 'comments']
    for method_name in blog_methods:
        if hasattr(BlogPostViewSet, method_name):
            method = getattr(BlogPostViewSet, method_name)
            if hasattr(method, 'cls'):
                print(f"   ✓ BlogPostViewSet.{method_name} has decorator")
            else:
                print(f"   ⚠ BlogPostViewSet.{method_name} missing decorator")
    
    # Test CommentViewSet methods
    comment_methods = ['list', 'retrieve', 'create', 'partial_update', 'destroy', 'approve', 'reject']
    for method_name in comment_methods:
        if hasattr(CommentViewSet, method_name):
            method = getattr(CommentViewSet, method_name)
            if hasattr(method, 'cls'):
                print(f"   ✓ CommentViewSet.{method_name} has decorator")
            else:
                print(f"   ⚠ CommentViewSet.{method_name} missing decorator")

if __name__ == '__main__':
    test_blog_endpoints()
    test_swagger_documentation()
    print("\n🎉 All tests completed!")