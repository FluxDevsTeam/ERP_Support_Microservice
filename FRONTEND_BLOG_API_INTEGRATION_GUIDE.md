# Frontend Blog API Integration Guide

## Base API Information
- **Base URL**: `https://support-microservice-api.fluxdevs.com/`
- **API Version**: `v1`
- **API Prefix**: `/api/blogs/`
- **Authentication**: JWT Token required for admin operations
- **Content Type**: `application/json`

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: JWT <your-jwt-token>
```

## Standard Response Format

### Success Response (200/201)
```json
{
  "data": {...} or [...],
  "message": "Success message",
  "status": "success"
}
```

### Paginated Response (List Endpoints)
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

### Error Response (400/401/403/404/500)
```json
{
  "error": "Error message",
  "details": {...},
  "status": "error"
}
```

---

## API Endpoints

### 1. Blog Posts Management (Admin Only)

#### 1.1 List All Blog Posts
- **Endpoint**: `GET /api/blogs/posts/`
- **Description**: Retrieve all blog posts (admin view)
- **Authentication**: Required (Admin)
- **Permissions**: Superuser only
- **Query Parameters**:
  - `page` (int): Page number for pagination
  - `page_size` (int): Number of items per page (max 100)
  - `search` (string): Search in title, content, excerpt, tags, author name
  - `status` (string): Filter by status (`draft`, `published`, `archived`)
  - `author` (string): Filter by author user ID
  - `ordering` (string): Order by field (`-created_at`, `created_at`, `title`, `published_at`)

**Example Request**:
```bash
GET /api/blogs/posts/?page=1&page_size=10&status=published&ordering=-created_at
Authorization: JWT <token>
```

**Response**:
```json
{
  "count": 25,
  "next": "https://support-microservice-api.fluxdevs.com/api/blogs/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Sample Blog Post",
      "slug": "sample-blog-post",
      "content": "This is the full content of the blog post...",
      "excerpt": "This is a brief summary of the blog post...",
      "author_user_id": "user_123",
      "author_name": "John Doe",
      "status": "published",
      "featured_image": "/media/blog_images/sample.jpg",
      "tags": "django,api,backend",
      "meta_title": "SEO Title",
      "meta_description": "SEO description for search engines",
      "created_at": "2025-11-10T13:00:00Z",
      "updated_at": "2025-11-10T13:30:00Z",
      "published_at": "2025-11-10T13:00:00Z",
      "comment_count": 5,
      "is_published": true
    }
  ]
}
```

#### 1.2 Create Blog Post
- **Endpoint**: `POST /api/blogs/posts/create/`
- **Description**: Create a new blog post
- **Authentication**: Required (Admin)
- **Permissions**: Superuser only

**Example Request**:
```bash
POST /api/blogs/posts/create/
Authorization: JWT <token>
Content-Type: application/json

{
  "title": "My New Blog Post",
  "content": "This is the full content of my blog post...",
  "excerpt": "Brief summary of the blog post",
  "author_user_id": "user_123",
  "author_name": "John Doe",
  "featured_image": null,
  "tags": "django,python,api",
  "meta_title": "SEO Title",
  "meta_description": "SEO description",
  "status": "draft"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My New Blog Post",
  "slug": "my-new-blog-post",
  "content": "This is the full content of my blog post...",
  "excerpt": "Brief summary of the blog post",
  "author_user_id": "user_123",
  "author_name": "John Doe",
  "status": "draft",
  "featured_image": null,
  "tags": "django,python,api",
  "meta_title": "SEO Title",
  "meta_description": "SEO description",
  "created_at": "2025-11-10T13:00:00Z",
  "updated_at": "2025-11-10T13:00:00Z",
  "published_at": null,
  "comment_count": 0,
  "is_published": false
}
```

#### 1.3 Get Blog Post Details
- **Endpoint**: `GET /api/blogs/posts/{uuid}/`
- **Description**: Retrieve specific blog post details
- **Authentication**: Required (Admin)
- **Permissions**: Superuser only

**Example Request**:
```bash
GET /api/blogs/posts/550e8400-e29b-41d4-a716-446655440000/
Authorization: JWT <token>
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Sample Blog Post",
  "slug": "sample-blog-post",
  "content": "This is the full content of the blog post...",
  "excerpt": "This is a brief summary of the blog post...",
  "author_user_id": "user_123",
  "author_name": "John Doe",
  "status": "published",
  "featured_image": "/media/blog_images/sample.jpg",
  "tags": "django,api,backend",
  "meta_title": "SEO Title",
  "meta_description": "SEO description for search engines",
  "created_at": "2025-11-10T13:00:00Z",
  "updated_at": "2025-11-10T13:30:00Z",
  "published_at": "2025-11-10T13:00:00Z",
  "comment_count": 5,
  "is_published": true
}
```

#### 1.4 Update Blog Post
- **Endpoint**: `PATCH /api/blogs/posts/{uuid}/update/`
- **Description**: Update a blog post (partial update)
- **Authentication**: Required (Admin)
- **Permissions**: Superuser only
- **Note**: Only PATCH method allowed, no PUT

**Example Request**:
```bash
PATCH /api/blogs/posts/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: JWT <token>
Content-Type: application/json

{
  "title": "Updated Blog Post Title",
  "content": "Updated content...",
  "tags": "django,python,api,updated"
}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Blog Post Title",
  "slug": "updated-blog-post-title",
  "content": "Updated content...",
  "excerpt": "Brief summary of the blog post",
  "author_user_id": "user_123",
  "author_name": "John Doe",
  "status": "draft",
  "featured_image": null,
  "tags": "django,python,api,updated",
  "meta_title": "SEO Title",
  "meta_description": "SEO description",
  "created_at": "2025-11-10T13:00:00Z",
  "updated_at": "2025-11-10T13:30:00Z",
  "published_at": null,
  "comment_count": 0,
  "is_published": false
}
```

#### 1.5 Delete Blog Post
- **Endpoint**: `DELETE /api/blogs/posts/{uuid}/delete/`
- **Description**: Delete a blog post
- **Authentication**: Required (Admin)
- **Permissions**: Superuser only
- **Response**: 204 No Content (no body)

**Example Request**:
```bash
DELETE /api/blogs/posts/550e8400-e29b-41d4-a716-446655440000/delete/
Authorization: JWT <token>
```

#### 1.6 Publish Blog Post
- **Endpoint**: `POST /api/blogs/posts/{uuid}/publish/`
- **Description**: Publish a draft blog post
- **Authentication**: Required (Admin)
- **Permissions**: Superuser only
- **Effect**: Sets status to 'published' and published_at timestamp

**Example Request**:
```bash
POST /api/blogs/posts/550e8400-e29b-41d4-a716-446655440000/publish/
Authorization: JWT <token>
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Published Blog Post",
  "slug": "published-blog-post",
  "content": "This is the full content...",
  "status": "published",
  "published_at": "2025-11-10T13:30:00Z",
  "is_published": true
}
```

#### 1.7 Unpublish Blog Post
- **Endpoint**: `POST /api/blogs/posts/{uuid}/unpublish/`
- **Description**: Unpublish a published blog post
- **Authentication**: Required (Admin)
- **Permissions**: Superuser only
- **Effect**: Sets status to 'draft' and clears published_at timestamp

**Example Request**:
```bash
POST /api/blogs/posts/550e8400-e29b-41d4-a716-446655440000/unpublish/
Authorization: JWT <token>
```

#### 1.8 Get Post Comments
- **Endpoint**: `GET /api/blogs/posts/{uuid}/comments/`
- **Description**: Get all comments for a blog post
- **Authentication**: Not required (public can view published posts)
- **Permissions**: Public access for published posts, Admin for all posts

**Example Request**:
```bash
GET /api/blogs/posts/550e8400-e29b-41d4-a716-446655440000/comments/
```

**Response**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "blog_post": "550e8400-e29b-41d4-a716-446655440000",
    "user_user_id": "user_456",
    "user_name": "Jane Smith",
    "content": "Great post!",
    "is_approved": true,
    "parent": null,
    "created_at": "2025-11-10T14:00:00Z",
    "updated_at": "2025-11-10T14:00:00Z"
  }
]
```

---

### 2. Public Blog Posts (Read-Only)

#### 2.1 List Published Blog Posts
- **Endpoint**: `GET /api/blogs/public/posts/`
- **Description**: Get all published blog posts (public access)
- **Authentication**: Not required
- **Query Parameters**:
  - `page` (int): Page number for pagination
  - `page_size` (int): Number of items per page (max 100)
  - `search` (string): Search in title, content, excerpt, tags
  - `tags` (string): Filter by tags
  - `ordering` (string): Order by field (`-published_at`, `published_at`, `title`)

**Example Request**:
```bash
GET /api/blogs/public/posts/?page=1&page_size=10&search=django&ordering=-published_at
```

**Response**:
```json
{
  "count": 15,
  "next": "https://support-microservice-api.fluxdevs.com/api/blogs/public/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Django REST API Guide",
      "slug": "django-rest-api-guide",
      "content": "This is the full content of the blog post...",
      "excerpt": "Learn how to build REST APIs with Django...",
      "author_user_id": "user_123",
      "author_name": "John Doe",
      "featured_image": "/media/blog_images/django.jpg",
      "tags": "django,python,api",
      "meta_title": "Django REST API Guide",
      "meta_description": "Complete guide to Django REST Framework",
      "created_at": "2025-11-10T13:00:00Z",
      "updated_at": "2025-11-10T13:30:00Z",
      "published_at": "2025-11-10T13:00:00Z",
      "comment_count": 8,
      "is_published": true
    }
  ]
}
```

#### 2.2 Get Public Blog Post Details
- **Endpoint**: `GET /api/blogs/public/posts/{uuid}/`
- **Description**: Get specific published blog post details
- **Authentication**: Not required
- **Note**: Only published posts are accessible

**Example Request**:
```bash
GET /api/blogs/public/posts/550e8400-e29b-41d4-a716-446655440000/
```

**Response**: Same as admin detail but only for published posts

---

### 3. Comments Management

#### 3.1 List Comments
- **Endpoint**: `GET /api/blogs/comments/`
- **Description**: Get all comments
- **Authentication**: Not required (public can view)
- **Query Parameters**:
  - `page` (int): Page number
  - `page_size` (int): Items per page
  - `blog_post` (uuid): Filter by blog post ID
  - `ordering` (string): Order by (`-created_at`, `created_at`)

**Example Request**:
```bash
GET /api/blogs/comments/?blog_post=550e8400-e29b-41d4-a716-446655440000&ordering=-created_at
```

**Response**:
```json
{
  "count": 25,
  "next": null,
  "previous": "https://support-microservice-api.fluxdevs.com/api/blogs/comments/?page=1",
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "blog_post": "550e8400-e29b-41d4-a716-446655440000",
      "user_user_id": "user_456",
      "user_name": "Jane Smith",
      "content": "Great post! Very helpful.",
      "is_approved": true,
      "parent": null,
      "created_at": "2025-11-10T14:00:00Z",
      "updated_at": "2025-11-10T14:00:00Z"
    }
  ]
}
```

#### 3.2 Create Comment
- **Endpoint**: `POST /api/blogs/comments/create/`
- **Description**: Create a new comment
- **Authentication**: Required (authenticated users)
- **Permissions**: Any authenticated user can comment

**Example Request**:
```bash
POST /api/blogs/comments/create/
Authorization: JWT <token>
Content-Type: application/json

{
  "blog_post": "550e8400-e29b-41d4-a716-446655440000",
  "user_user_id": "user_456",
  "user_name": "Jane Smith",
  "content": "This post really helped me understand Django!",
  "parent": null
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "blog_post": "550e8400-e29b-41d4-a716-446655440000",
  "user_user_id": "user_456",
  "user_name": "Jane Smith",
  "content": "This post really helped me understand Django!",
  "is_approved": true,
  "parent": null,
  "created_at": "2025-11-10T14:00:00Z",
  "updated_at": "2025-11-10T14:00:00Z"
}
```

#### 3.3 Get Comment Details
- **Endpoint**: `GET /api/blogs/comments/{uuid}/`
- **Description**: Get specific comment details
- **Authentication**: Not required (public can view)

**Example Request**:
```bash
GET /api/blogs/comments/550e8400-e29b-41d4-a716-446655440001/
```

#### 3.4 Update Comment
- **Endpoint**: `PATCH /api/blogs/comments/{uuid}/update/`
- **Description**: Update a comment
- **Authentication**: Required
- **Permissions**: Comment owner or admin
- **Note**: Only PATCH method allowed

**Example Request**:
```bash
PATCH /api/blogs/comments/550e8400-e29b-41d4-a716-446655440001/update/
Authorization: JWT <token>
Content-Type: application/json

{
  "content": "Updated comment content"
}
```

#### 3.5 Delete Comment
- **Endpoint**: `DELETE /api/blogs/comments/{uuid}/delete/`
- **Description**: Delete a comment
- **Authentication**: Required
- **Permissions**: Comment owner or admin
- **Response**: 204 No Content

---

## Data Models

### BlogPost Model
```json
{
  "id": "uuid-string",
  "title": "string (required, max 255)",
  "slug": "string (auto-generated, max 255)",
  "content": "text (required)",
  "excerpt": "text (max 500, optional)",
  "author_user_id": "string (required, max 255)",
  "author_name": "string (max 255, optional)",
  "status": "string (draft|published|archived, default: draft)",
  "featured_image": "url or null",
  "tags": "string (comma-separated, optional)",
  "meta_title": "string (max 255, optional)",
  "meta_description": "text (max 160, optional)",
  "created_at": "datetime (read-only)",
  "updated_at": "datetime (read-only)",
  "published_at": "datetime or null (read-only)",
  "comment_count": "integer (read-only)",
  "is_published": "boolean (read-only)"
}
```

### Comment Model
```json
{
  "id": "uuid-string",
  "blog_post": "uuid (required)",
  "user_user_id": "string (required, max 255)",
  "user_name": "string (max 255, optional)",
  "content": "text (required)",
  "is_approved": "boolean (default: true, read-only for now)",
  "parent": "uuid or null (for replies)",
  "created_at": "datetime (read-only)",
  "updated_at": "datetime (read-only)"
}
```

---

## Important Notes

### Restrictions & Limitations
1. **Authentication**: Admin endpoints require JWT token
2. **User IDs**: Use string user IDs (UUIDs from identity service)
3. **No PUT method**: Only PATCH allowed for updates
4. **Auto-approval**: Comments are auto-approved
5. **Published posts only**: Public endpoints only return published posts
6. **Pagination**: Maximum 100 items per page
7. **Content limits**: Title max 255 chars, excerpt max 500 chars
8. **Unique constraints**: Title and slug must be unique

### Error Status Codes
- `200`: Success
- `201`: Created successfully
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `500`: Internal server error

### Security Requirements
- Always use HTTPS in production
- Validate JWT tokens on every authenticated request
- Sanitize user input for XSS prevention
- Rate limiting may be applied
- CORS configured for frontend domains

### Performance Tips
- Use pagination for list endpoints
- Include only needed fields in requests
- Cache public posts list for better performance
- Use search parameters instead of filtering client-side

---

## Quick Reference

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/blogs/posts/` | GET | Admin | List all posts |
| `/api/blogs/posts/create/` | POST | Admin | Create post |
| `/api/blogs/posts/{uuid}/` | GET | Admin | Get post details |
| `/api/blogs/posts/{uuid}/update/` | PATCH | Admin | Update post |
| `/api/blogs/posts/{uuid}/delete/` | DELETE | Admin | Delete post |
| `/api/blogs/posts/{uuid}/publish/` | POST | Admin | Publish post |
| `/api/blogs/posts/{uuid}/unpublish/` | POST | Admin | Unpublish post |
| `/api/blogs/public/posts/` | GET | None | List published posts |
| `/api/blogs/public/posts/{uuid}/` | GET | None | Get published post |
| `/api/blogs/comments/` | GET | None | List comments |
| `/api/blogs/comments/create/` | POST | User | Create comment |
| `/api/blogs/comments/{uuid}/` | GET | None | Get comment |
| `/api/blogs/comments/{uuid}/update/` | PATCH | Owner/Admin | Update comment |
| `/api/blogs/comments/{uuid}/delete/` | DELETE | Owner/Admin | Delete comment |

This guide provides everything needed to integrate the blog service into your frontend application.