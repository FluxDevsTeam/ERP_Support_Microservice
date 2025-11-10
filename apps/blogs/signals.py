from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Comment


@receiver(post_save, sender=Comment)
def update_comment_count_on_save(sender, instance, created, **kwargs):
    """
    Update the comment count on the related blog post when a comment is saved.
    """
    blog_post = instance.blog_post
    blog_post.comment_count = blog_post.comments.filter(is_approved=True).count()
    blog_post.save(update_fields=['comment_count'])


@receiver(post_delete, sender=Comment)
def update_comment_count_on_delete(sender, instance, **kwargs):
    """
    Update the comment count on the related blog post when a comment is deleted.
    """
    try:
        blog_post = instance.blog_post
        blog_post.comment_count = blog_post.comments.filter(is_approved=True).count()
        blog_post.save(update_fields=['comment_count'])
    except Exception:
        # In case the blog post was also deleted, just pass
        pass