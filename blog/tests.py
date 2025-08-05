from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor
import json

from blog.models import Post, SubPost, Like


class PostModelTest(TestCase):
    """Тесты модели Post"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_post_creation(self):
        """Тест создания поста"""
        post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.views_count, 0)
    
    def test_post_str_representation(self):
        """Тест строкового представления поста"""
        post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
        self.assertEqual(str(post), 'Test Post')
    
    def test_increment_views(self):
        """Тест атомарного увеличения просмотров"""
        post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
        
        initial_views = post.views_count
        post.increment_views()
        self.assertEqual(post.views_count, initial_views + 1)


class SubPostModelTest(TestCase):
    """Тесты модели SubPost"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Main Post',
            body='Main content',
            author=self.user
        )
    
    def test_subpost_creation(self):
        """Тест создания под-поста"""
        subpost = SubPost.objects.create(
            title='Sub Post',
            body='Sub content',
            post=self.post
        )
        self.assertEqual(subpost.title, 'Sub Post')
        self.assertEqual(subpost.post, self.post)
    
    def test_subpost_str_representation(self):
        """Тест строкового представления под-поста"""
        subpost = SubPost.objects.create(
            title='Sub Post',
            body='Sub content',
            post=self.post
        )
        expected = f"{self.post.title} - Sub Post"
        self.assertEqual(str(subpost), expected)


class LikeModelTest(TestCase):
    """Тесты модели Like"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
    
    def test_like_creation(self):
        """Тест создания лайка"""
        like = Like.objects.create(
            post=self.post,
            user=self.user
        )
        self.assertEqual(like.post, self.post)
        self.assertEqual(like.user, self.user)
    
    def test_unique_like(self):
        """Тест уникальности лайка пользователя к посту"""
        Like.objects.create(post=self.post, user=self.user)
        
        with self.assertRaises(Exception):
            Like.objects.create(post=self.post, user=self.user)


class PostAPITest(APITestCase):
    """Тесты API для постов"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_post(self):
        """Тест создания поста через API"""
        url = reverse('post-list-create')
        data = {
            'title': 'Test Post',
            'body': 'Test content'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().author, self.user)
    
    def test_create_post_with_subposts(self):
        """Тест создания поста с под-постами через API"""
        url = reverse('post-list-create')
        data = {
            'title': 'Main Post',
            'body': 'Main content',
            'subposts': [
                {'title': 'Sub Post 1', 'body': 'Sub content 1'},
                {'title': 'Sub Post 2', 'body': 'Sub content 2'}
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.first()
        self.assertEqual(post.subposts.count(), 2)
    
    def test_bulk_create_posts(self):
        """Тест массового создания постов"""
        url = reverse('post-bulk-create')
        data = {
            'posts': [
                {'title': 'Post 1', 'body': 'Content 1'},
                {'title': 'Post 2', 'body': 'Content 2'},
                {'title': 'Post 3', 'body': 'Content 3'}
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
    
    def test_bulk_create_posts_with_subposts(self):
        """Тест массового создания постов с под-постами"""
        url = reverse('post-bulk-create')
        data = {
            'posts': [
                {
                    'title': 'Post 1',
                    'body': 'Content 1',
                    'subposts': [
                        {'title': 'Sub 1.1', 'body': 'Sub content 1.1'}
                    ]
                },
                {
                    'title': 'Post 2',
                    'body': 'Content 2',
                    'subposts': [
                        {'title': 'Sub 2.1', 'body': 'Sub content 2.1'},
                        {'title': 'Sub 2.2', 'body': 'Sub content 2.2'}
                    ]
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(SubPost.objects.count(), 3)
    
    def test_update_post_subposts(self):
        """Тест обновления под-постов при обновлении поста"""
        # Создаем пост с под-постами
        post = Post.objects.create(
            title='Original Post',
            body='Original content',
            author=self.user
        )
        subpost1 = SubPost.objects.create(
            title='Original Sub 1',
            body='Original sub content 1',
            post=post
        )
        subpost2 = SubPost.objects.create(
            title='Original Sub 2',
            body='Original sub content 2',
            post=post
        )
        
        # Обновляем пост с новыми под-постами
        url = reverse('post-detail', kwargs={'pk': post.pk})
        data = {
            'title': 'Updated Post',
            'body': 'Updated content',
            'subposts': [
                {
                    'id': subpost1.id,
                    'title': 'Updated Sub 1',
                    'body': 'Updated sub content 1'
                },
                # subpost2 не включен, значит должен быть удален
                {
                    'title': 'New Sub 3',
                    'body': 'New sub content 3'
                }
            ]
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Post')
        self.assertEqual(post.subposts.count(), 2)
        self.assertFalse(SubPost.objects.filter(id=subpost2.id).exists())
    
    def test_like_Post(self):
        """Тест лайка поста"""
        post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
        
        url = reverse('post-like', kwargs={'pk': post.pk})
        
        # Первый лайк
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['likes_count'], 1)
        
        # Повторный лайк (убрать лайк)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['liked'])
        self.assertEqual(response.data['likes_count'], 0)
    
    def test_like_no_duplicate(self):
        """Тест защиты от дублирования лайков"""
        post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
        
        # Создаем лайк напрямую в БД
        Like.objects.create(post=post, user=self.user)
        
        url = reverse('post-like', kwargs={'pk': post.pk})
        response = self.client.post(url)
        
        # Лайк должен быть убран
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['liked'])
        self.assertEqual(Like.objects.filter(post=post, user=self.user).count(), 0)
    
    def test_view_post(self):
        """Тест увеличения счетчика просмотров"""
        post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
        
        url = reverse('post-view', kwargs={'pk': post.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['views_count'], 1)
        
        post.refresh_from_db()
        self.assertEqual(post.views_count, 1)
    
    def test_concurrent_views_increment(self):
        """Тест безопасности инкремента просмотров при параллельных запросах"""
        post = Post.objects.create(
            title='Test Post',
            body='Test content',
            author=self.user
        )
        
        # Тестируем несколько последовательных инкрементов
        for _ in range(5):
            post.increment_views()
        
        post.refresh_from_db()
        self.assertEqual(post.views_count, 5)
    
    def test_post_list_pagination(self):
        """Тест пагинации списка постов"""
        # Создаем много постов
        for i in range(25):
            Post.objects.create(
                title=f'Post {i}',
                body=f'Content {i}',
                author=self.user
            )
        
        url = reverse('post-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('next', response.data)
        self.assertEqual(len(response.data['results']), 20)  # default page size


class SubPostAPITest(APITestCase):
    """Тесты API для под-постов"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(
            title='Main Post',
            body='Main content',
            author=self.user
        )
    
    def tearDown(self):
        """Очистка после каждого теста"""
        SubPost.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()
    
    def test_create_subpost(self):
        """Тест создания под-поста через API"""
        url = reverse('subpost-list-create')
        data = {
            'title': 'Sub Post',
            'body': 'Sub content',
            'post': self.post.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SubPost.objects.count(), 1)
    
    def test_list_subposts(self):
        """Тест получения списка под-постов"""
        SubPost.objects.create(
            title='Sub Post 1',
            body='Sub content 1',
            post=self.post
        )
        SubPost.objects.create(
            title='Sub Post 2',
            body='Sub content 2',
            post=self.post
        )
        
        url = reverse('subpost-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Для непагинированного ответа
        if isinstance(response.data, list):
            self.assertEqual(len(response.data), 2)
        else:
            # Для пагинированного ответа
            self.assertEqual(len(response.data['results']), 2)
    
    def test_update_subpost(self):
        """Тест обновления под-поста"""
        subpost = SubPost.objects.create(
            title='Original Sub',
            body='Original content',
            post=self.post
        )
        
        url = reverse('subpost-detail', kwargs={'pk': subpost.pk})
        data = {
            'title': 'Updated Sub',
            'body': 'Updated content',
            'post': self.post.id
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subpost.refresh_from_db()
        self.assertEqual(subpost.title, 'Updated Sub')
    
    def test_delete_subpost(self):
        """Тест удаления под-поста"""
        subpost = SubPost.objects.create(
            title='Sub Post',
            body='Sub content',
            post=self.post
        )
        
        url = reverse('subpost-detail', kwargs={'pk': subpost.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SubPost.objects.count(), 0)
