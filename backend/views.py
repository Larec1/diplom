from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.throttles import SettingsScopedThrottle

from backend.models import Contact, Order, OrderItem, Product, ProductInfo, Shop
from backend.tasks import send_order_confirmation_emails, send_registration_welcome_email
from backend.serializers import (
    BasketAddOkSerializer,
    BasketAddSerializer,
    BasketItemSerializer,
    BasketListWrapSerializer,
    ContactAddOkSerializer,
    ContactAddSerializer,
    ContactListWrapSerializer,
    ContactSerializer,
    IdDeletedOkSerializer,
    LoginOkSerializer,
    LoginSerializer,
    OrderConfirmOkSerializer,
    OrderConfirmSerializer,
    OrderDetailSerializer,
    OrderDetailWrapSerializer,
    OrderListSerializer,
    OrderListWrapSerializer,
    OrderStatusPatchOkSerializer,
    OrderStatusSerializer,
    ProductDetailSerializer,
    ProductDetailWrapSerializer,
    ProductListSerializer,
    ProductListWrapSerializer,
    RegisterOkSerializer,
    RegisterSerializer,
    SocialTokenOutSerializer,
    StatusOkMessageSerializer,
    order_total_price,
)


@extend_schema(responses={200: StatusOkMessageSerializer})
@api_view(['GET'])
@permission_classes([AllowAny])
def api_status(request):
    """Для отладки, смотрим что сервер поднялся."""
    return Response({'status': 'ok', 'message': 'API backend работает'})


@extend_schema_view(
    post=extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterOkSerializer},
    ),
)
class RegisterAPIView(APIView):
    """Новый пользователь. В ответе токен для заголовка Authorization."""

    permission_classes = [AllowAny]
    throttle_classes = [SettingsScopedThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        send_registration_welcome_email.delay(user.email)

        return Response(
            {
                'status': 'ok',
                'id': user.id,
                'email': user.email,
                'token': token.key,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(
        request=LoginSerializer,
        responses={200: LoginOkSerializer},
    ),
)
class LoginAPIView(APIView):
    """Логин по email и паролю, отдаём токен."""

    permission_classes = [AllowAny]
    throttle_classes = [SettingsScopedThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'status': 'ok', 'token': token.key})


@extend_schema_view(
    get=extend_schema(
        summary='Список товаров в разрезе магазинов',
        responses={200: ProductListWrapSerializer},
    ),
)
class ProductListAPIView(APIView):
    """Список предложений из прайсов (ProductInfo)."""

    permission_classes = [AllowAny]

    def get(self, request):
        queryset = ProductInfo.objects.all().order_by('id')
        serializer = ProductListSerializer(queryset, many=True)
        return Response({'status': 'ok', 'items': serializer.data})


@extend_schema_view(
    get=extend_schema(
        summary='Карточка товара',
        responses={200: ProductDetailWrapSerializer},
    ),
)
class ProductDetailAPIView(APIView):
    """Один продукт и все его предложения."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductDetailSerializer(product)
        return Response({'status': 'ok', 'item': serializer.data})


_basket_remove = inline_serializer(
    name='BasketRemove',
    fields={'item_id': serializers.IntegerField(help_text='id позиции из get корзины')},
)


@extend_schema_view(
    get=extend_schema(
        summary='Что в корзине',
        responses={200: BasketListWrapSerializer},
    ),
    post=extend_schema(
        request=BasketAddSerializer,
        responses={200: BasketAddOkSerializer},
    ),
    delete=extend_schema(
        request=_basket_remove,
        responses={200: IdDeletedOkSerializer},
    ),
)
class BasketAPIView(APIView):
    """Корзина. Нужен токен."""

    permission_classes = [IsAuthenticated]

    def get_basket(self, user):
        basket, _ = Order.objects.get_or_create(user=user, status='basket')
        return basket

    def get(self, request):
        basket = self.get_basket(request.user)
        items = (
            OrderItem.objects.filter(order=basket)
            .select_related('product_info__product', 'product_info__shop')
            .order_by('id')
        )
        serializer = BasketItemSerializer(items, many=True)
        return Response({'status': 'ok', 'items': serializer.data})

    def post(self, request):
        serializer = BasketAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_info_id = serializer.validated_data['product_info']
        quantity = serializer.validated_data['quantity']
        product_info = get_object_or_404(ProductInfo, pk=product_info_id)

        basket = self.get_basket(request.user)
        item, created = OrderItem.objects.get_or_create(
            order=basket,
            product_info=product_info,
            defaults={'quantity': quantity},
        )

        if not created:
            item.quantity += quantity
            item.save()

        return Response({'status': 'ok', 'item_id': item.id})

    def delete(self, request):
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'status': 'error', 'error': 'Передайте item_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        basket = self.get_basket(request.user)
        deleted, _ = OrderItem.objects.filter(order=basket, id=item_id).delete()

        if not deleted:
            return Response(
                {'status': 'error', 'error': 'Позиция не найдена'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({'status': 'ok', 'deleted': item_id})


_contact_remove = inline_serializer(
    name='ContactRemove',
    fields={'contact_id': serializers.IntegerField()},
)


@extend_schema_view(
    get=extend_schema(
        summary='Список контактов',
        responses={200: ContactListWrapSerializer},
    ),
    post=extend_schema(
        request=ContactAddSerializer,
        responses={200: ContactAddOkSerializer},
    ),
    delete=extend_schema(
        request=_contact_remove,
        responses={200: IdDeletedOkSerializer},
    ),
)
class ContactAPIView(APIView):
    """Адреса и контакты пользователя."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user).order_by('id')
        serializer = ContactSerializer(contacts, many=True)
        return Response({'status': 'ok', 'items': serializer.data})

    def post(self, request):
        serializer = ContactAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact = Contact.objects.create(
            user=request.user,
            type=serializer.validated_data['type'],
            value=serializer.validated_data['value'],
        )
        return Response({'status': 'ok', 'contact_id': contact.id})

    def delete(self, request):
        contact_id = request.data.get('contact_id')
        if not contact_id:
            return Response(
                {'status': 'error', 'error': 'Передайте contact_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted, _ = Contact.objects.filter(user=request.user, id=contact_id).delete()
        if not deleted:
            return Response(
                {'status': 'error', 'error': 'Адрес не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({'status': 'ok', 'deleted': contact_id})


@extend_schema_view(
    post=extend_schema(
        request=OrderConfirmSerializer,
        responses={200: OrderConfirmOkSerializer},
    ),
)
class OrderConfirmAPIView(APIView):
    """Оформить корзину в заказ. Письма уходят в фоне (celery)."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [SettingsScopedThrottle]
    throttle_scope = 'order_confirm'

    def post(self, request):
        serializer = OrderConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        basket_id = serializer.validated_data['basket_id']
        contact_id = serializer.validated_data['contact_id']

        basket = Order.objects.filter(
            id=basket_id,
            user=request.user,
            status='basket',
        ).first()
        if not basket:
            return Response(
                {'status': 'error', 'error': 'Корзина не найдена или уже оформлена'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not OrderItem.objects.filter(order=basket).exists():
            return Response(
                {'status': 'error', 'error': 'Корзина пустая'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contact = Contact.objects.filter(user=request.user, id=contact_id).first()
        if not contact:
            return Response(
                {'status': 'error', 'error': 'Адрес доставки не найден'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        basket.contact = contact
        basket.status = 'new'
        basket.save()

        total = order_total_price(basket)
        admin_email = getattr(settings, 'ORDER_NOTIFY_EMAIL', settings.DEFAULT_FROM_EMAIL)
        send_order_confirmation_emails.delay(
            basket.id,
            request.user.email,
            contact.value,
            total,
            admin_email,
        )

        return Response({'status': 'ok', 'order_id': basket.id})


@extend_schema_view(
    get=extend_schema(
        summary='Мои заказы',
        responses={200: OrderListWrapSerializer},
    ),
)
class OrderListAPIView(APIView):
    """Заказы без строки basket."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .exclude(status='basket')
            .prefetch_related(
                Prefetch(
                    'positions',
                    queryset=OrderItem.objects.select_related('product_info'),
                ),
            )
            .order_by('-dt')
        )
        serializer = OrderListSerializer(orders, many=True)
        return Response({'status': 'ok', 'items': serializer.data})


@extend_schema_view(
    get=extend_schema(
        summary='Детали заказа',
        responses={200: OrderDetailWrapSerializer},
    ),
)
class OrderDetailAPIView(APIView):
    """Один заказ с позициями."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.prefetch_related(
                Prefetch(
                    'positions',
                    queryset=OrderItem.objects.select_related(
                        'product_info__product',
                        'product_info__shop',
                    ),
                ),
            ),
            pk=pk,
            user=request.user,
        )
        if order.status == 'basket':
            return Response(
                {'status': 'error', 'error': 'Это корзина, не заказ'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = OrderDetailSerializer(order)
        return Response({'status': 'ok', 'item': serializer.data})


@extend_schema_view(
    patch=extend_schema(
        request=OrderStatusSerializer,
        responses={200: OrderStatusPatchOkSerializer},
    ),
)
class OrderStatusUpdateAPIView(APIView):
    """PATCH статуса. Разрешено только аккаунту типа shop и если в заказе есть их товар."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.user_type != 'shop':
            return Response(
                {'status': 'error', 'error': 'Доступно только магазину'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            shop = request.user.shop_profile
        except Shop.DoesNotExist:
            return Response(
                {'status': 'error', 'error': 'У аккаунта нет магазина'},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = get_object_or_404(Order, pk=pk)
        if order.status == 'basket':
            return Response(
                {'status': 'error', 'error': 'Это корзина, не заказ'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not order.positions.filter(product_info__shop=shop).exists():
            return Response(
                {'status': 'error', 'error': 'В заказе нет товаров вашего магазина'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order.status = serializer.validated_data['status']
        order.save()
        return Response({'status': 'ok', 'order_id': order.id, 'new_status': order.status})


@extend_schema_view(
    get=extend_schema(
        summary='После oauth в браузере — забрать api-токен',
        responses={200: SocialTokenOutSerializer},
    ),
)
class SocialSessionTokenAPIView(APIView):
    """Когда зашли через google/github, django держит сессию — тут отдаю токен как у обычного логина."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response(
            {
                'status': 'ok',
                'token': token.key,
                'email': request.user.email,
            }
        )
