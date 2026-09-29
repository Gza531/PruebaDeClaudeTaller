from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EstadoAPIView, ProductoViewSet, StockViewSet, MovimientoStockViewSet


router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'stock', StockViewSet)
router.register(r'movimientos-stock', MovimientoStockViewSet)


urlpatterns = [
    path('estado/', EstadoAPIView.as_view(), name='api-estado'),
    path('', include(router.urls)),
]
