from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import Like, Post, SubPost


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""

    class Meta:
        model = User
        fields = ["id", "username", "email"]


class SubPostSerializer(serializers.ModelSerializer):
    """Сериализатор под-поста"""

    class Meta:
        model = SubPost
        fields = ["id", "title", "body", "created_at", "updated_at"]


class PostSerializer(serializers.ModelSerializer):
    """Сериализатор поста с поддержкой под-постов"""

    author = UserSerializer(read_only=True)
    subposts = SubPostSerializer(many=True, required=False)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "body",
            "author",
            "created_at",
            "updated_at",
            "views_count",
            "likes_count",
            "subposts",
        ]

    def create(self, validated_data):
        """Создание поста с под-постами"""
        subposts_data = validated_data.pop("subposts", [])

        with transaction.atomic():
            post = Post.objects.create(**validated_data)

            for subpost_data in subposts_data:
                SubPost.objects.create(post=post, **subpost_data)

            return post

    def update(self, instance, validated_data):
        """Обновление поста с управлением под-постами"""
        subposts_data = validated_data.pop("subposts", None)

        with transaction.atomic():
            # Обновляем поля поста
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Обрабатываем под-посты если они переданы
            if subposts_data is not None:
                # Получаем ID существующих под-постов из запроса
                existing_ids = set()
                for subpost_data in subposts_data:
                    subpost_id = subpost_data.get("id")
                    if subpost_id:
                        # Обновляем существующий под-пост
                        try:
                            subpost = instance.subposts.get(id=subpost_id)
                            for attr, value in subpost_data.items():
                                if attr != "id":
                                    setattr(subpost, attr, value)
                            subpost.save()
                            existing_ids.add(subpost_id)
                        except SubPost.DoesNotExist:
                            pass
                    else:
                        # Создаем новый под-пост
                        subpost = SubPost.objects.create(post=instance, **subpost_data)
                        existing_ids.add(subpost.id)

                # Удаляем под-посты, которых нет в новом списке
                instance.subposts.exclude(id__in=existing_ids).delete()

            return instance


class PostCreateManySerializer(serializers.Serializer):
    """Сериализатор для массового создания постов"""

    posts = PostSerializer(many=True)

    def create(self, validated_data):
        """Массовое создание постов"""
        posts_data = validated_data["posts"]
        posts = []

        with transaction.atomic():
            for post_data in posts_data:
                subposts_data = post_data.pop("subposts", [])
                post = Post.objects.create(**post_data)

                for subpost_data in subposts_data:
                    SubPost.objects.create(post=post, **subpost_data)

                posts.append(post)

        return {"posts": posts}


class SubPostDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор под-поста"""

    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = SubPost
        fields = ["id", "title", "body", "post", "created_at", "updated_at"]


class LikeSerializer(serializers.ModelSerializer):
    """Сериализатор лайка"""

    user = UserSerializer(read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Like
        fields = ["id", "post", "user", "created_at"]
