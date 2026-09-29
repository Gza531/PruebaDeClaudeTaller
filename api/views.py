from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from catalogo.models import Producto
from stock.models import Stock, MovimientoStock
from stock.services import registrar_movimiento, transferir
from .serializers import (
    ProductoSerializer,
    StockSerializer,
    MovimientoStockSerializer,
    TransferenciaStockSerializer,
)

class EstadoAPIView(APIView):
    """
    Endpoint de ejemplo para confirmar que la API REST esta funcionando.

    Prueben visitarlo desde el navegador en:
        http://localhost:8000/api/estado/

    Sirve como punto de partida: reemplacen/amplien esta carpeta "api" con
    los serializers y vistas de los modelos reales de su organizacion
    (por ejemplo, ClienteSerializer, ClienteViewSet, etc.).
    """

    def get(self, request):
        return Response(
            {
                "estado": "ok",
                "mensaje": "La API REST del proyecto esta funcionando correctamente.",
            },
            status=status.HTTP_200_OK,
        )

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related("marca", "categoria")
    serializer_class = ProductoSerializer


class StockViewSet(viewsets.ModelViewSet):
    """
    Stock por producto y ubicación.

    Filtros opcionales: ?producto=<id>&ubicacion=Sucursal|Depósito
    Extra: /api/stock/bajo-minimo/ lista lo que está en o por debajo del mínimo.
    """
    queryset = Stock.objects.select_related("producto")
    serializer_class = StockSerializer
    # Sin DELETE: un stock con movimientos no se puede borrar.
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        producto = self.request.query_params.get("producto")
        ubicacion = self.request.query_params.get("ubicacion")
        if producto:
            queryset = queryset.filter(producto_id=producto)
        if ubicacion:
            queryset = queryset.filter(ubicacion=ubicacion)
        return queryset

    @action(detail=False, url_path="bajo-minimo")
    def bajo_minimo(self, request):
        queryset = self.get_queryset().filter(cantidad_actual__lte=F("stock_minimo"))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def transferir(self, request):
        serializer = TransferenciaStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            movimientos = transferir(usuario=request.user, **serializer.validated_data)
        except DjangoValidationError as error:
            raise ValidationError(error.messages)
        return Response(
            MovimientoStockSerializer(movimientos, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class MovimientoStockViewSet(mixins.CreateModelMixin,
                             mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """
    Historial de movimientos de stock. Se pueden crear y consultar, pero no
    editar ni borrar: un error se corrige registrando otro movimiento.

    Filtros opcionales: ?stock=<id>&producto=<id>&tipo_movimiento=<tipo>
    """
    queryset = MovimientoStock.objects.select_related("stock__producto", "usuario")
    serializer_class = MovimientoStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        filtros = {
            "stock_id": self.request.query_params.get("stock"),
            "stock__producto_id": self.request.query_params.get("producto"),
            "tipo_movimiento": self.request.query_params.get("tipo_movimiento"),
        }
        return queryset.filter(**{campo: valor for campo, valor in filtros.items() if valor})

    def perform_create(self, serializer):
        datos = serializer.validated_data
        try:
            serializer.instance = registrar_movimiento(
                datos["stock"],
                datos["tipo_movimiento"],
                datos["cantidad"],
                self.request.user,
                motivo=datos.get("motivo"),
                referencia=datos.get("referencia"),
                compra=datos.get("compra"),
            )
        except DjangoValidationError as error:
            raise ValidationError(error.messages)
