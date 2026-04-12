from django.db.models import Prefetch
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import ProductInfo, ProductParameter
from backend.serializers import LoginSerializer, ProductListSerializer, RegisterSerializer


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
        queryset = (
            ProductInfo.objects.select_related('product', 'product__category', 'shop')
            .prefetch_related(
                Prefetch(
                    'params',
                    queryset=ProductParameter.objects.select_related('parameter'),
                )
            )
            .order_by('id')
        )
        serializer = ProductListSerializer(queryset, many=True)
        return Response({'status': 'ok', 'items': serializer.data})
