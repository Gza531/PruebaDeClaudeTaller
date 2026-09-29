from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)

    razon_social = models.CharField(max_length=120)

    cuit = models.CharField(
        max_length=13,
        unique=True
    )

    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    email = models.EmailField(
        max_length=100,
        null=True,
        blank=True
    )

    direccion = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    observaciones = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "proveedores"
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social


class ProveedorXProducto(models.Model):
    id_proveedor_producto = models.AutoField(primary_key=True)

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column="id_proveedor"
    )

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        db_column="id_producto"
    )

    precio_compra_referencia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    codigo_producto_proveedor = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    observaciones = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "proveedores_x_productos"
        constraints = [
            models.UniqueConstraint(
                fields=["proveedor", "producto"],
                name="uq_proveedor_producto"
            ),
            models.CheckConstraint(
                check=models.Q(precio_compra_referencia__gte=0),
                name="ck_pxp_precio"
            ),
        ]

    def __str__(self):
        return f"{self.proveedor} - {self.producto}"


class Compra(models.Model):

    class EstadoCompra(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        RECIBIDA = "recibida", "Recibida"
        ANULADA = "anulada", "Anulada"

    id_compra = models.AutoField(primary_key=True)

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column="id_proveedor"
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="id_usuario"
    )

    fecha = models.DateTimeField(default=timezone.now)

    numero_factura = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )

    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoCompra.choices,
        default=EstadoCompra.PENDIENTE
    )

    observaciones = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "compras"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"], name="idx_compras_fecha"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total__gte=0),
                name="ck_compras_total"
            ),
        ]

    def __str__(self):
        return f"Compra {self.id_compra} - {self.proveedor}"


class DetalleCompra(models.Model):
    id_detalle_compra = models.AutoField(primary_key=True)

    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        db_column="id_compra",
        related_name="detalles"
    )

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        db_column="id_producto"
    )

    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        db_table = "detalles_compras"
        constraints = [
            models.CheckConstraint(
                check=models.Q(cantidad__gt=0),
                name="ck_detcompra_cantidad"
            ),
            models.CheckConstraint(
                check=models.Q(precio_unitario__gte=0),
                name="ck_detcompra_precio"
            ),
            models.CheckConstraint(
                check=models.Q(subtotal__gte=0),
                name="ck_detcompra_subtotal"
            ),
        ]

    def __str__(self):
        return f"Detalle {self.id_detalle_compra} - {self.producto}"
