from django.urls import path

from . import api_views

urlpatterns = [
    # Post URLs
    path("posts/", api_views.PostListCreateView.as_view(), name="post-list-create"),
    path("posts/<int:pk>/", api_views.PostDetailView.as_view(), name="post-detail"),
    path("posts/bulk/", api_views.bulk_create_posts, name="post-bulk-create"),
    path("posts/<int:pk>/like/", api_views.like_post, name="post-like"),
    path("posts/<int:pk>/view/", api_views.view_post, name="post-view"),
    # SubPost URLs
    path("subposts/", api_views.SubPostListCreateView.as_view(), name="subpost-list-create"),
    path("subposts/<int:pk>/", api_views.SubPostDetailView.as_view(), name="subpost-detail"),
]
