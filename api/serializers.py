from rest_framework import serializers
from catalogo.models import Producto
from stock.models import Stock, MovimientoStock


class ProductoSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.CharField(
        source="marca.nombre",
        read_only=True
    )

    categoria_nombre = serializers.CharField(
        source="categoria.nombre",
        read_only=True
    )

    class Meta:
        model = Producto
        fields = "__all__"


class StockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(
        source="producto.nombre",
        read_only=True
    )

    bajo_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Stock
        fields = "__all__"
        # La cantidad solo cambia registrando movimientos (/api/movimientos-stock/).
        read_only_fields = ["cantidad_actual", "ultima_actualizacion"]


class MovimientoStockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(
        source="stock.producto.nombre",
        read_only=True
    )

    ubicacion = serializers.CharField(
        source="stock.ubicacion",
        read_only=True
    )

    usuario_nombre = serializers.CharField(
        source="usuario.username",
        read_only=True
    )

    class Meta:
        model = MovimientoStock
        fields = "__all__"
        # El usuario es el que está logueado y la fecha la pone el sistema.
        read_only_fields = ["usuario", "fecha"]


class TransferenciaStockSerializer(serializers.Serializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    desde = serializers.ChoiceField(choices=Stock.Ubicacion.choices)
    hacia = serializers.ChoiceField(choices=Stock.Ubicacion.choices)
    cantidad = serializers.IntegerField(min_value=1)
    motivo = serializers.CharField(max_length=255, required=False, default="Reposición")
    referencia = serializers.CharField(max_length=50, required=False, allow_null=True, default=None)
