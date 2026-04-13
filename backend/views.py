from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import Order, OrderItem, Product, ProductInfo
from backend.serializers import (
    BasketAddSerializer,
    BasketItemSerializer,
    LoginSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    RegisterSerializer,
)


@api_view(['GET'])
def api_status(request):
    # Проверка, что API подключен.
    return Response({'status': 'ok', 'message': 'API backend работает'})


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                'status': 'ok',
                'id': user.id,
                'email': user.email,
                'token': token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'status': 'ok', 'token': token.key})


class ProductListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = ProductInfo.objects.all().order_by('id')
        serializer = ProductListSerializer(queryset, many=True)
        return Response({'status': 'ok', 'items': serializer.data})


class ProductDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductDetailSerializer(product)
        return Response({'status': 'ok', 'item': serializer.data})


class BasketAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_basket(self, user):
        basket, _ = Order.objects.get_or_create(user=user, status='basket')
        return basket

    def get(self, request):
        basket = self.get_basket(request.user)
        items = OrderItem.objects.filter(order=basket).order_by('id')
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
            product=product_info.product,
            shop=product_info.shop,
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
