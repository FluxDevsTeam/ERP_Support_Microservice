from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import BlogPost, Comment


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """
    Admin interface for BlogPost model.
    """
    list_display = [
        'title', 'author', 'status', 'is_published', 'comment_count', 
        'created_at', 'published_at'
    ]
    list_filter = ['status', 'created_at', 'published_at', 'author']
    search_fields = ['title', 'content', 'excerpt', 'tags', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'created_at', 'updated_at', 'published_at', 'comment_count', 'is_published',
        'view_on_site_link'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'content', 'excerpt')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'view_on_site_link')
        }),
        ('Author & SEO', {
            'fields': ('author', 'meta_title', 'meta_description', 'tags')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Statistics', {
            'fields': ('comment_count', 'is_published')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def view_on_site_link(self, obj):
        """Add a link to view the post on the public site"""
        if obj.pk and obj.status == 'published':
            url = reverse('blogs:public_blog_posts_detail', kwargs={'pk': obj.pk})
            return format_html(
                '<a href="{}" target="_blank">View on Site</a>',
                url
            )
        return "Post not published yet"
    view_on_site_link.short_description = "Public Link"
    
    def is_published(self, obj):
        """Display whether the post is published"""
        return obj.status == 'published' and obj.published_at is not None
    is_published.boolean = True
    is_published.short_description = "Published"
    
    def save_model(self, request, obj, form, change):
        """Auto-assign author if not set"""
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['publish_posts', 'unpublish_posts']
    
    def publish_posts(self, request, queryset):
        """Action to publish selected posts"""
        count = queryset.update(status='published')
        self.message_user(
            request, 
            f"{count} post(s) have been published.",
            level='success'
        )
    publish_posts.short_description = "Publish selected posts"
    
    def unpublish_posts(self, request, queryset):
        """Action to unpublish selected posts"""
        count = queryset.update(status='draft')
        self.message_user(
            request, 
            f"{count} post(s) have been unpublished.",
            level='warning'
        )
    unpublish_posts.short_description = "Unpublish selected posts"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin interface for Comment model.
    """
    list_display = [
        'blog_post', 'user', 'content_preview', 'is_approved', 
        'is_reply', 'created_at'
    ]
    list_filter = ['is_approved', 'created_at', 'blog_post', 'user']
    search_fields = ['content', 'user__username', 'blog_post__title']
    readonly_fields = ['created_at', 'updated_at', 'is_reply']
    actions = ['approve_comments', 'reject_comments']
    
    fieldsets = (
        ('Comment Details', {
            'fields': ('blog_post', 'user', 'content', 'is_reply')
        }),
        ('Moderation', {
            'fields': ('is_approved',)
        }),
        ('Threading', {
            'fields': ('parent',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Display a preview of the comment content"""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"
    
    def is_reply(self, obj):
        """Display whether this is a reply to another comment"""
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = "Is Reply"
    
    def approve_comments(self, request, queryset):
        """Action to approve selected comments"""
        count = queryset.update(is_approved=True)
        self.message_user(
            request, 
            f"{count} comment(s) have been approved.",
            level='success'
        )
    approve_comments.short_description = "Approve selected comments"
    
    def reject_comments(self, request, queryset):
        """Action to reject selected comments"""
        count = queryset.update(is_approved=False)
        self.message_user(
            request, 
            f"{count} comment(s) have been rejected.",
            level='warning'
        )
    reject_comments.short_description = "Reject selected comments"