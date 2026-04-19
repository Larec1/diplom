from django.contrib.auth import authenticate
from rest_framework import serializers

from backend.models import Contact, Order, OrderItem, ORDER_STATES, Product, ProductInfo, ProductParameter, User


class RegisterSerializer(serializers.ModelSerializer):
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
    parameter = serializers.CharField(source='parameter.name')

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductListSerializer(serializers.ModelSerializer):
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
    shop = serializers.CharField(source='shop.name')
    parameters = ProductParameterSerializer(source='params', many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'name', 'shop', 'quantity', 'price', 'price_rrc', 'parameters')


class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    offers = ProductOfferSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'offers')


class BasketAddSerializer(serializers.Serializer):
    product_info = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class BasketItemSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.name')
    shop = serializers.CharField(source='shop.name')

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'shop', 'quantity')


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'type', 'value')


class ContactAddSerializer(serializers.Serializer):
    value = serializers.CharField()
    type = serializers.CharField(required=False, default='address')


class OrderConfirmSerializer(serializers.Serializer):
    basket_id = serializers.IntegerField()
    contact_id = serializers.IntegerField()


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[c for c in ORDER_STATES if c[0] != 'basket'])


def order_total_price(order):
    """Считаем сумму заказа: цена из прайса * количество по каждой позиции."""
    total = 0
    for position in order.positions.all():
        info = ProductInfo.objects.filter(product=position.product, shop=position.shop).first()
        if info:
            total += info.price * position.quantity
    return total


class OrderListSerializer(serializers.ModelSerializer):
    """Список заказов: номер, дата, сумма, статус (как в screens.md)."""

    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'dt', 'status', 'total')

    def get_total(self, obj):
        return order_total_price(obj)


class OrderPositionSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.name')
    shop = serializers.CharField(source='shop.name')
    price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'shop', 'quantity', 'price', 'line_total')

    def get_price(self, obj):
        info = ProductInfo.objects.filter(product=obj.product, shop=obj.shop).first()
        return info.price if info else 0

    def get_line_total(self, obj):
        info = ProductInfo.objects.filter(product=obj.product, shop=obj.shop).first()
        if info:
            return info.price * obj.quantity
        return 0


class OrderDetailSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    contact = ContactSerializer(read_only=True)
    items = OrderPositionSerializer(source='positions', many=True)

    class Meta:
        model = Order
        fields = ('id', 'dt', 'status', 'contact', 'total', 'items')

    def get_total(self, obj):
        return order_total_price(obj)
