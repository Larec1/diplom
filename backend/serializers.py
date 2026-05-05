from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from backend.models import Contact, Order, OrderItem, ORDER_STATES, Product, ProductInfo, ProductParameter, User


class RegisterSerializer(serializers.ModelSerializer):
    """Тело запроса для регистрации."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'company',
            'position',
            'user_type',
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Логин: email как username в нашей модели."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs.get('email'),
            password=attrs.get('password'),
        )
        if not user:
            raise serializers.ValidationError('Неверный email или пароль')
        attrs['user'] = user
        return attrs


class ProductParameterSerializer(serializers.ModelSerializer):
    """Параметр в составе оффера."""

    parameter = serializers.CharField(source='parameter.name')

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductListSerializer(serializers.ModelSerializer):
    """Одна строка прайса для списка на главной."""

    product_id = serializers.IntegerField(source='product.id')
    product_name = serializers.CharField(source='product.name')
    category = serializers.CharField(source='product.category.name')
    shop = serializers.CharField(source='shop.name')
    parameters = ProductParameterSerializer(source='params', many=True)

    class Meta:
        model = ProductInfo
        fields = (
            'id',
            'product_id',
            'product_name',
            'name',
            'category',
            'shop',
            'quantity',
            'price',
            'price_rrc',
            'parameters',
        )


class ProductOfferSerializer(serializers.ModelSerializer):
    """Вложенное предложение в карточке товара."""

    shop = serializers.CharField(source='shop.name')
    parameters = ProductParameterSerializer(source='params', many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'name', 'shop', 'quantity', 'price', 'price_rrc', 'parameters')


class ProductDetailSerializer(serializers.ModelSerializer):
    """Ответ GET /products/:id/."""

    category = serializers.CharField(source='category.name')
    offers = ProductOfferSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'offers')


class BasketAddSerializer(serializers.Serializer):
    """Добавить в корзину — id из ProductInfo."""

    product_info = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class BasketItemSerializer(serializers.ModelSerializer):
    """Элемент корзины в json."""

    product = serializers.CharField(source='product_info.product.name')
    shop = serializers.CharField(source='product_info.shop.name')

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'shop', 'quantity')


class ContactSerializer(serializers.ModelSerializer):
    """Контакт пользователя."""

    class Meta:
        model = Contact
        fields = ('id', 'type', 'value')


class ContactAddSerializer(serializers.Serializer):
    """Создать контакт (обычно адрес)."""

    value = serializers.CharField()
    type = serializers.CharField(required=False, default='address')


class OrderConfirmSerializer(serializers.Serializer):
    """Подтверждение корзины."""

    basket_id = serializers.IntegerField()
    contact_id = serializers.IntegerField()


class OrderStatusSerializer(serializers.Serializer):
    """Новый статус заказа (не basket)."""

    status = serializers.ChoiceField(choices=[c for c in ORDER_STATES if c[0] != 'basket'])


def order_total_price(order):
    """Считаем сумму заказа: цена из прайса * количество по каждой позиции."""
    total = 0
    for position in order.positions.select_related('product_info').all():
        total += position.product_info.price * position.quantity
    return total


class OrderListSerializer(serializers.ModelSerializer):
    """Список заказов: номер, дата, сумма, статус (как в screens.md)."""

    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'dt', 'status', 'total')

    @extend_schema_field(serializers.IntegerField())
    def get_total(self, obj):
        return order_total_price(obj)


class OrderPositionSerializer(serializers.ModelSerializer):
    """Строка внутри заказа (детальный просмотр)."""

    product = serializers.CharField(source='product_info.product.name')
    shop = serializers.CharField(source='product_info.shop.name')
    price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'shop', 'quantity', 'price', 'line_total')

    @extend_schema_field(serializers.IntegerField())
    def get_price(self, obj):
        return obj.product_info.price

    @extend_schema_field(serializers.IntegerField())
    def get_line_total(self, obj):
        return obj.product_info.price * obj.quantity


class OrderDetailSerializer(serializers.ModelSerializer):
    """Полный заказ с контактом и позициями."""

    total = serializers.SerializerMethodField()
    contact = ContactSerializer(read_only=True)
    items = OrderPositionSerializer(source='positions', many=True)

    class Meta:
        model = Order
        fields = ('id', 'dt', 'status', 'contact', 'total', 'items')

    @extend_schema_field(serializers.IntegerField())
    def get_total(self, obj):
        return order_total_price(obj)


# --- Упаковки ответов {status, items} для openapi / swagger ---


class StatusOkMessageSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()


class RegisterOkSerializer(serializers.Serializer):
    status = serializers.CharField()
    id = serializers.IntegerField()
    email = serializers.EmailField()
    token = serializers.CharField()


class LoginOkSerializer(serializers.Serializer):
    status = serializers.CharField()
    token = serializers.CharField()


class ProductListWrapSerializer(serializers.Serializer):
    status = serializers.CharField()
    items = ProductListSerializer(many=True)


class ProductDetailWrapSerializer(serializers.Serializer):
    status = serializers.CharField()
    item = ProductDetailSerializer()


class BasketListWrapSerializer(serializers.Serializer):
    status = serializers.CharField()
    items = BasketItemSerializer(many=True)


class BasketAddOkSerializer(serializers.Serializer):
    status = serializers.CharField()
    item_id = serializers.IntegerField()


class IdDeletedOkSerializer(serializers.Serializer):
    status = serializers.CharField()
    deleted = serializers.IntegerField()


class ContactListWrapSerializer(serializers.Serializer):
    status = serializers.CharField()
    items = ContactSerializer(many=True)


class ContactAddOkSerializer(serializers.Serializer):
    status = serializers.CharField()
    contact_id = serializers.IntegerField()


class OrderConfirmOkSerializer(serializers.Serializer):
    status = serializers.CharField()
    order_id = serializers.IntegerField()


class OrderListWrapSerializer(serializers.Serializer):
    status = serializers.CharField()
    items = OrderListSerializer(many=True)


class OrderDetailWrapSerializer(serializers.Serializer):
    status = serializers.CharField()
    item = OrderDetailSerializer()


class OrderStatusPatchOkSerializer(serializers.Serializer):
    status = serializers.CharField()
    order_id = serializers.IntegerField()
    new_status = serializers.CharField()


class SocialTokenOutSerializer(serializers.Serializer):
    status = serializers.CharField()
    token = serializers.CharField()
    email = serializers.EmailField()
