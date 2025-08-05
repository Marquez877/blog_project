from django.contrib import admin

from .models import Like, Post, SubPost


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at", "views_count"]
    list_filter = ["created_at", "author"]
    search_fields = ["title", "body"]
    readonly_fields = ["created_at", "updated_at", "views_count"]


@admin.register(SubPost)
class SubPostAdmin(admin.ModelAdmin):
    list_display = ["title", "post", "created_at"]
    list_filter = ["created_at", "post"]
    search_fields = ["title", "body"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "created_at"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at"]
