from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Stock(models.Model):

    class Ubicacion(models.TextChoices):
        SUCURSAL = "Sucursal", "Sucursal"
        DEPOSITO = "Depósito", "Depósito"

    id_stock = models.AutoField(primary_key=True)

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        db_column="id_producto",
        related_name="stocks"
    )

    ubicacion = models.CharField(
        max_length=20,
        choices=Ubicacion.choices
    )

    # Solo se modifica registrando movimientos (ver stock/services.py)
    cantidad_actual = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    stock_minimo = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock"
        verbose_name_plural = "stock"
        ordering = ["producto__nombre", "ubicacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["producto", "ubicacion"],
                name="uq_stock_producto_ubicacion"
            ),
            models.CheckConstraint(
                check=models.Q(cantidad_actual__gte=0),
                name="ck_stock_cantidad"
            ),
            models.CheckConstraint(
                check=models.Q(stock_minimo__gte=0),
                name="ck_stock_minimo"
            ),
        ]

    @property
    def bajo_minimo(self):
        return self.cantidad_actual <= self.stock_minimo

    def __str__(self):
        return f"{self.producto} ({self.ubicacion}): {self.cantidad_actual}"


class MovimientoStock(models.Model):

    class TipoMovimiento(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SALIDA = "salida", "Salida"
        AJUSTE = "ajuste", "Ajuste"
        REPOSICION = "reposicion", "Reposición"

    # Tipos que suman unidades al stock; el resto (salida, ajuste) las restan.
    TIPOS_INGRESO = (TipoMovimiento.ENTRADA, TipoMovimiento.REPOSICION)

    id_movimiento_stock = models.AutoField(primary_key=True)

    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        db_column="id_stock",
        related_name="movimientos"
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="id_usuario"
    )

    compra = models.ForeignKey(
        "compras.Compra",
        on_delete=models.PROTECT,
        db_column="id_compra",
        null=True,
        blank=True
    )

    # TODO: agregar el campo "venta" (FK a ventas, columna id_venta) y el
    # CHECK ck_movstock_origen cuando exista el módulo de ventas.

    fecha = models.DateTimeField(default=timezone.now)

    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TipoMovimiento.choices
    )

    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    motivo = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    referencia = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "movimientos_stock"
        verbose_name = "movimiento de stock"
        verbose_name_plural = "movimientos de stock"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"], name="idx_movstock_fecha"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(cantidad__gt=0),
                name="ck_movstock_cantidad"
            ),
        ]

    @property
    def es_ingreso(self):
        return self.tipo_movimiento in self.TIPOS_INGRESO

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} de {self.cantidad} - {self.stock.producto}"
