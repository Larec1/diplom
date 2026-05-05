"""
Кастомный throttle: родной ScopedRateThrottle на старте протыкивает
api_settings один раз, из-за этого в тестах override_settings не видел новые лимиты.
"""
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle


class SettingsScopedThrottle(ScopedRateThrottle):
    """Берём словарь лимитов из settings.REST_FRAMEWORK каждый раз — удобно для тестов."""

    def get_rate(self):
        rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {})
        return rates[self.scope]
