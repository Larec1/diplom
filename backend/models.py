from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


ORDER_STATES = (
    ('basket', 'Корзина'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPES = (
    ('buyer', 'Покупатель'),
    ('shop', 'Магазин'),
)


class UserManager(BaseUserManager):
    """Минимальный менеджер для авторизации по email."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Поле email обязательно')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Пользователь сервиса (покупатель или поставщик)."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    objects = UserManager()

    email = models.EmailField('Email', unique=True)
    company = models.CharField('Компания', max_length=60, blank=True)
    position = models.CharField('Должность', max_length=60, blank=True)
    user_type = models.CharField('Тип пользователя', max_length=5, choices=USER_TYPES, default='buyer')

    def __str__(self):
        return self.email

    def is_shop(self):
        return self.user_type == 'shop'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Shop(models.Model):
    name = models.CharField('Название', max_length=80)
    url = models.URLField('Сайт', blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_profile', blank=True, null=True)
    is_open = models.BooleanField('Принимает заказы', default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'


class Category(models.Model):
    name = models.CharField('Название', max_length=80)
    shops = models.ManyToManyField(Shop, related_name='category_set', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Product(models.Model):
    name = models.CharField('Название', max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='offers')
    name = models.CharField('Название в прайсе', max_length=180, blank=True, default='')
    quantity = models.PositiveIntegerField('Количество')
    price = models.PositiveIntegerField('Цена')
    price_rrc = models.PositiveIntegerField('РРЦ')

    def __str__(self):
        return f'{self.shop} / {self.product}'

    class Meta:
        verbose_name = 'Предложение товара'
        verbose_name_plural = 'Предложения товаров'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop', 'name'], name='unique_shop_product_name'),
        ]


class Parameter(models.Model):
    name = models.CharField('Название параметра', max_length=80)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, related_name='params')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name='product_values')
    value = models.CharField('Значение', max_length=255)

    class Meta:
        verbose_name = 'Параметр товара'
        verbose_name_plural = 'Параметры товаров'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_param_pair'),
        ]


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    type = models.CharField('Тип контакта', max_length=30, default='', blank=True)
    value = models.CharField('Значение', max_length=255, default='', blank=True)

    def __str__(self):
        return f'{self.type}: {self.value}'

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    dt = models.DateTimeField('Дата создания', auto_now_add=True)
    status = models.CharField('Статус', max_length=15, choices=ORDER_STATES, default='basket')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    def __str__(self):
        return f'Заказ #{self.id}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='positions')
    product_info = models.ForeignKey(
        ProductInfo,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Предложение',
    )
    quantity = models.PositiveIntegerField('Количество', default=1)

    def __str__(self):
        return f'{self.product_info.product} x {self.quantity}'

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'
        constraints = [
            models.UniqueConstraint(fields=['order', 'product_info'], name='unique_order_product_info'),
        ]
