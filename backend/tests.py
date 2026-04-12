from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.models import Category, Product, ProductInfo, Shop, User


class AuthAPITests(APITestCase):
    def test_register_smoke(self):
        payload = {
            'email': 'new_user@example.com',
            'username': 'new_user',
            'password': 'StrongPass123',
            'password_confirm': 'StrongPass123',
        }

        response = self.client.post(reverse('api-register'), payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_login_smoke(self):
        User.objects.create_user(
            email='login@example.com',
            username='login_user',
            password='StrongPass123',
        )

        response = self.client.post(
            reverse('api-login'),
            {'email': 'login@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertIn('token', response.data)


class ProductListAPITests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            email='shop@example.com',
            username='shop_user',
            password='StrongPass123',
            user_type='shop',
        )
        shop = Shop.objects.create(name='Test Shop', user=user)
        category = Category.objects.create(name='Смартфоны')
        product = Product.objects.create(name='Телефон', category=category)
        ProductInfo.objects.create(
            product=product,
            shop=shop,
            name='Телефон 8/256',
            quantity=5,
            price=20000,
            price_rrc=22000,
        )

    def test_products_list_smoke(self):
        response = self.client.get(reverse('api-products'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data.get('items', [])) > 0)
