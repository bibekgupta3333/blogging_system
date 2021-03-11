from django.db import models
from django.urls import reverse
from django.conf import settings
from posts.models import Post
# Create your models here.


class Comment(models.Model):
    email = models.EmailField(max_length=150)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_comments",
        null=True,
        blank=True,
    )
    comment_content = models.TextField(verbose_name="comment")
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comment_post",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return "" + self.email or "" + " " + self.user or ""

    def get_absolute_url(self):
        return reverse(
            "posts:detail",
            kwargs={
                "author": self.post.author.username,
                "author_id": self.post.author.id,
                "slug": self.post.slug,
            },
        )