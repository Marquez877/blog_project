from django.contrib.auth.models import User
from django.db import models
from django.db.models import F


class Post(models.Model):
    """Модель поста"""

    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def increment_views(self):
        """Атомарно увеличить счетчик просмотров"""
        Post.objects.filter(pk=self.pk).update(views_count=F("views_count") + 1)
        # Обновляем объект
        self.refresh_from_db()


class SubPost(models.Model):
    """Модель под-поста"""

    title = models.CharField(max_length=200)
    body = models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="subposts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.post.title} - {self.title}"


class Like(models.Model):
    """Модель лайка поста"""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"
