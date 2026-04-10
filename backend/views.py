from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def api_status(request):
    # Провверка  что API подключен
    return Response({'status': 'ok', 'message': 'API backend работает'})
