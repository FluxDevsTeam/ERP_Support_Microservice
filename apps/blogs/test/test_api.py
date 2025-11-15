"""
Blog app tests for ERP Support Microservice

These tests demonstrate the blog functionality including:
- Blog post CRUD operations (superadmin only)
- Public read access to published posts
- Comment functionality (authenticated users)
"""

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
import json
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import BlogPost, Comment


class BlogPostAPITestCase(APITestCase):
    """
    Test case for blog post API functionality
    """
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.superuser = User.objects.create_user(
            username='superadmin',
            email='admin@test.com',
            password='adminpass',
            is_superuser=True,
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='user@test.com',
            password='userpass',
            is_staff=False
        )
        
        # Create sample blog posts
        self.published_post = BlogPost.objects.create(
            title='Published Post',
            content='This is a published blog post content.',
            author_user_id=str(self.superuser.id),
            author_name=self.superuser.username,
            status='published',
            published_at=timezone.now()
        )

        self.draft_post = BlogPost.objects.create(
            title='Draft Post',
            content='This is a draft blog post content.',
            author_user_id=str(self.superuser.id),
            author_name=self.superuser.username,
            status='draft'
        )
        
        # Authenticate as superuser
        refresh = RefreshToken.for_user(self.superuser)
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {refresh.access_token}')
        
        # Store superuser and regular user data for other test methods
        self.superuser_token = refresh.access_token
        self.regular_user_refresh = RefreshToken.for_user(self.regular_user)
    
    def test_public_read_access_to_published_posts(self):
        """Test that anyone can read published posts"""
        # Clear authentication for public access
        self.client.credentials()
        
        url = reverse('blogs:public-post-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only published post should be visible
        
        # Check that draft post is not visible to public
        response_data = response.json()
        post_titles = [post['title'] for post in response_data['results']]
        self.assertNotIn('Draft Post', post_titles)
    
    def test_superuser_crud_operations(self):
        """Test that superuser can create, edit, and delete posts"""
        # Authenticate as superuser
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {self.superuser_token}')
        
        # Create a new post
        url = reverse('blogs:blogpost-list')
        data = {
            'title': 'New Superuser Post',
            'content': 'This is a new post created by superuser.',
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Superuser Post')
        
        # Update the post
        post_id = response.data['id']
        update_url = reverse('blogs:blog_posts_update', kwargs={'pk': post_id})
        update_data = {'title': 'Updated Title', 'status': 'published'}
        
        response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
        self.assertEqual(response.data['status'], 'published')
        
        # Delete the post
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_regular_user_read_only_access(self):
        """Test that regular users cannot create/edit/delete posts"""
        # Authenticate as regular user
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {self.regular_user_refresh.access_token}')
        
        url = reverse('blogs:blogpost-list')
        data = {
            'title': 'Regular User Post',
            'content': 'This should not be allowed.',
            'status': 'draft'
        }
        
        # Regular user should not be able to create posts
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_post_publication_endpoints(self):
        """Test publish/unpublish endpoints for superuser"""
        # Authenticate as superuser
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {self.superuser_token}')
        
        # Test publish endpoint
        publish_url = reverse('blogs:blogpost-publish', kwargs={'pk': self.draft_post.id})
        response = self.client.post(publish_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'published')
        self.assertIsNotNone(response.data['published_at'])
        
        # Test unpublish endpoint
        unpublish_url = reverse('blogs:blogpost-unpublish', kwargs={'pk': self.draft_post.id})
        response = self.client.post(unpublish_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'draft')
        self.assertIsNone(response.data['published_at'])


class CommentAPITestCase(APITestCase):
    """
    Test case for comment API functionality
    """
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.superuser = User.objects.create_user(
            username='superadmin',
            email='admin@test.com',
            password='adminpass',
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='commenter',
            email='commenter@test.com',
            password='userpass'
        )
        
        # Create a published blog post
        self.blog_post = BlogPost.objects.create(
            title='Post for Comments',
            content='This post will have comments.',
            author_user_id=str(self.superuser.id),
            author_name=self.superuser.username,
            status='published',
            published_at=timezone.now()
        )
        
        # Store tokens for authentication
        self.regular_user_refresh = RefreshToken.for_user(self.regular_user)
    
    def test_authenticated_user_can_comment(self):
        """Test that authenticated users can create comments"""
        self.client.credentials(HTTP_AUTHORIZATION=f'JWT {self.regular_user_refresh.access_token}')
        
        url = reverse('blogs:comment-list')
        data = {
            'blog_post': self.blog_post.id,
            'content': 'This is a great post!'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'This is a great post!')
        self.assertEqual(response.data['user']['username'], 'commenter')
    
    def test_unauthenticated_user_cannot_comment(self):
        """Test that unauthenticated users cannot create comments"""
        self.client.credentials()  # Clear authentication
        
        url = reverse('blogs:comment-list')
        data = {
            'blog_post': self.blog_post.id,
            'content': 'This should not be allowed.'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_public_can_read_approved_comments(self):
        """Test that anyone can read approved comments"""
        # Create a comment
        comment = Comment.objects.create(
            blog_post=self.blog_post,
            user_user_id=str(self.regular_user.id),
            user_name=self.regular_user.username,
            content='This is a comment.',
            is_approved=True
        )
        
        # Test public access to comments
        self.client.credentials()  # Clear authentication for public access
        url = reverse('blogs:public_blog_posts_detail', kwargs={'pk': self.blog_post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 1)
        self.assertEqual(response.data['comments'][0]['content'], 'This is a comment.')


class PublicBlogAPITestCase(APITestCase):
    """
    Test case for public blog access
    """
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.superuser = User.objects.create_user(
            username='superadmin',
            email='admin@test.com',
            password='adminpass',
            is_superuser=True
        )
        
        # Create blog posts
        self.published_post1 = BlogPost.objects.create(
            title='First Published Post',
            content='First published content.',
            author_user_id=str(self.superuser.id),
            author_name=self.superuser.username,
            status='published',
            published_at=timezone.now(),
            tags='django,python,web-development'
        )

        self.published_post2 = BlogPost.objects.create(
            title='Second Published Post',
            content='Second published content.',
            author_user_id=str(self.superuser.id),
            author_name=self.superuser.username,
            status='published',
            published_at=timezone.now(),
            tags='javascript,frontend'
        )

        self.draft_post = BlogPost.objects.create(
            title='Draft Post',
            content='Draft content.',
            author_user_id=str(self.superuser.id),
            author_name=self.superuser.username,
            status='draft'
        )
        
        self.client = Client()
    
    def test_public_blog_listing(self):
        """Test public access to blog post listing"""
        url = reverse('blogs:public-post-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Only published posts
        
        # Check tags filtering
        url_with_filter = f"{url}?tags=django"
        response = self.client.get(url_with_filter)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Check search functionality
        url_with_search = f"{url}?search=First"
        response = self.client.get(url_with_search)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'First Published Post')
    
    def test_public_blog_detail(self):
        """Test public access to blog post detail"""
        url = reverse('blogs:public_blog_posts_detail', kwargs={'pk': self.published_post1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'First Published Post')
        self.assertEqual(response.data['status'], 'published')
        self.assertIn('comments', response.data)
    
    def test_draft_post_not_accessible_to_public(self):
        """Test that draft posts are not accessible to public"""
        url = reverse('blogs:public_blog_posts_detail', kwargs={'pk': self.draft_post.id})
        response = self.client.get(url)
        
        # This should return 404 as the post is not published
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)