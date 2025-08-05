from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Post, SubPost, Like
from .serializers import (
    PostSerializer, PostCreateManySerializer, SubPostDetailSerializer, 
    LikeSerializer
)


class PostPagination(PageNumberPagination):
    """Пагинация для постов"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PostListCreateView(generics.ListCreateAPIView):
    """Список постов с пагинацией и создание поста"""
    queryset = Post.objects.all().prefetch_related('subposts', 'likes')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление поста"""
    queryset = Post.objects.all().prefetch_related('subposts', 'likes')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SubPostListCreateView(generics.ListCreateAPIView):
    """Список и создание под-постов"""
    queryset = SubPost.objects.all().select_related('post')
    serializer_class = SubPostDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SubPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление под-поста"""
    queryset = SubPost.objects.all().select_related('post')
    serializer_class = SubPostDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_posts(request):
    """Массовое создание постов"""
    serializer = PostCreateManySerializer(data=request.data)
    if serializer.is_valid():
        # Добавляем автора ко всем постам
        posts_data = serializer.validated_data['posts']
        for post_data in posts_data:
            post_data['author'] = request.user
        
        result = serializer.save()
        posts_serializer = PostSerializer(result['posts'], many=True)
        return Response(posts_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, pk):
    """Лайкнуть/убрать лайк с поста"""
    post = get_object_or_404(Post, pk=pk)
    
    with transaction.atomic():
        like, created = Like.objects.get_or_create(
            post=post, 
            user=request.user
        )
        
        if created:
            liked = True
        else:
            like.delete()
            liked = False
        
        likes_count = post.likes.count()
    
    return Response({
        'liked': liked,
        'likes_count': likes_count
    })


@api_view(['GET'])
def view_post(request, pk):
    """Увеличить счетчик просмотров поста"""
    post = get_object_or_404(Post, pk=pk)
    post.increment_views()
    
    return Response({
        'views_count': post.views_count
    })
