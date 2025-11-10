import uuid
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class BlogPost(models.Model):
    """
    Blog post model for the ERP Support Microservice
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Use UUID as primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True, help_text="Brief summary of the blog post")
    # Author information stored directly (like billing service pattern)
    author_user_id = models.CharField(max_length=255, help_text="User ID from identity microservice")
    author_name = models.CharField(max_length=255, null=True, blank=True, help_text="Author display name (first_name + last_name)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    image_1 = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    
    # SEO and social media
    meta_title = models.CharField(max_length=255, blank=True, help_text="SEO title")
    meta_description = models.TextField(max_length=160, blank=True, help_text="SEO description")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    comment_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['author_user_id']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            
        # Auto-generate excerpt from content if not provided
        if not self.excerpt and self.content:
            self.excerpt = self.content[:200] + "..." if len(self.content) > 200 else self.content
            
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status != 'published':
            self.published_at = None
            
        super().save(*args, **kwargs)
        
        # Update comment count
        self.comment_count = self.comments.filter(is_approved=True).count()
        super().save(update_fields=['comment_count'])
    
    @property
    def is_published(self):
        return self.status == 'published' and self.published_at is not None
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blogs:blog_posts_detail', kwargs={'pk': self.id})


class Comment(models.Model):
    """
    Comment model for blog posts
    """
    # Use UUID as primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    # User information stored directly (like billing service pattern)
    user_user_id = models.CharField(max_length=255, help_text="User ID from identity microservice")
    user_name = models.CharField(max_length=255, null=True, blank=True, help_text="User display name (first_name + last_name)")
    content = models.TextField()
    is_approved = models.BooleanField(default=True)  # Auto-approve for now, can be moderated later
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['blog_post', 'is_approved']),
            models.Index(fields=['user_user_id']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user_name} on {self.blog_post.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.blog_post.comment_count = self.blog_post.comments.filter(is_approved=True).count()
        self.blog_post.save(update_fields=['comment_count'])
    
    @property
    def is_reply(self):
        return self.parent is not None