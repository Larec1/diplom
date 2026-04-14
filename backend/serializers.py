from django.contrib.auth import authenticate
from rest_framework import serializers

from backend.models import Contact, OrderItem, Product, ProductInfo, ProductParameter, User


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
