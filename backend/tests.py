"""
Тесты. Пока только throttling — остальное гоняю руками через postman.
"""
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from backend.models import User


def _rf_with_rates(register=None, login=None, order_confirm=None):
    """подменяю лимиты чтобы не ждать час в тестах"""
    r = dict(settings.REST_FRAMEWORK)
    rates = dict(r.get('DEFAULT_THROTTLE_RATES', {}))
    if register is not None:
        rates['register'] = register
    if login is not None:
        rates['login'] = login
    if order_confirm is not None:
        rates['order_confirm'] = order_confirm
    r['DEFAULT_THROTTLE_RATES'] = rates
    return r


@override_settings(
    REST_FRAMEWORK=_rf_with_rates(register='3/minute'),
    CELERY_TASK_ALWAYS_EAGER=True,
)
class RegisterThrottleTests(APITestCase):
    """Слишком частая регистрация должна отстреливать 429."""

    @patch('backend.views.send_registration_welcome_email.delay')
    def test_too_many_register_429(self, _mock_delay):
        url = reverse('api-register')
        for i in range(3):
            payload = {
                'email': f'u{i}@mail.ru',
                'username': f'user{i}',
                'password': 'secret1234',
                'password_confirm': 'secret1234',
                'user_type': 'buyer',
            }
            resp = self.client.post(url, payload, format='json')
            self.assertEqual(resp.status_code, 201, resp.content)
        resp = self.client.post(
            url,
            {
                'email': 'last@mail.ru',
                'username': 'lastuser',
                'password': 'secret1234',
                'password_confirm': 'secret1234',
                'user_type': 'buyer',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 429)


@override_settings(REST_FRAMEWORK=_rf_with_rates(login='2/minute'))
class LoginThrottleTests(APITestCase):
    """Лимит на логин — защита от перебора пароля (грубо)."""

    def setUp(self):
        User.objects.create_user(
            email='a@a.ru',
            username='aaa',
            password='rightpass123',
        )

    def test_login_throttle_429(self):
        url = reverse('api-login')
        for _ in range(2):
            r = self.client.post(
                url,
                {'email': 'a@a.ru', 'password': 'wrong'},
                format='json',
            )
            self.assertEqual(r.status_code, 400)
        r = self.client.post(
            url,
            {'email': 'a@a.ru', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(r.status_code, 429)


# smoke на случай если сломаю urls
class SmokeTest(TestCase):
    def test_status_200(self):
        r = self.client.get(reverse('api-status'))
        self.assertEqual(r.status_code, 200)
