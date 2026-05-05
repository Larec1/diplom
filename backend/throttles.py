from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle


class SettingsScopedThrottle(ScopedRateThrottle):
    def get_rate(self):
        rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {})
        return rates[self.scope]
