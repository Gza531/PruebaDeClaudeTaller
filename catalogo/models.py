from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Marca(models.Model):
    id_marca = models.AutoField(primary_key=True)

    nombre = models.CharField(
        max_length=80,
        unique=True
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "marcas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)

    nombre = models.CharField(
        max_length=80,
        unique=True
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "categorias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):

    class VersionProducto(models.TextChoices):
        ORIGINAL = "Original", "Original"
        REPLICA = "Réplica", "Réplica"

    class GeneroProducto(models.TextChoices):
        MASCULINO = "Masculino", "Masculino"
        FEMENINO = "Femenino", "Femenino"
        UNISEX = "Unisex", "Unisex"
        NO_APLICA = "No aplica", "No aplica"

    class OrigenProducto(models.TextChoices):
        NACIONAL = "Nacional", "Nacional"
        IMPORTADO = "Importado", "Importado"

    id_producto = models.AutoField(primary_key=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        db_column="id_categoria"
    )

    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        db_column="id_marca"
    )

    codigo_barras = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    nombre = models.CharField(max_length=120)

    descripcion = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    volumen = models.CharField(
        max_length=60,
        null=True,
        blank=True
    )

    # Ruta relativa de la imagen (ej: "productos/kaiak-clasico-edt-100ml.jpg")
    imagen = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    version_producto = models.CharField(
        max_length=20,
        choices=VersionProducto.choices,
        default=VersionProducto.ORIGINAL
    )

    genero_producto = models.CharField(
        max_length=20,
        choices=GeneroProducto.choices,
        null=True,
        blank=True
    )

    origen = models.CharField(
        max_length=20,
        choices=OrigenProducto.choices,
    )

    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    fecha_alta = models.DateField(default=timezone.localdate)

    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "productos"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"], name="idx_productos_nombre"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(precio_venta__gte=0),
                name="ck_productos_precio_venta"
            ),
        ]

    def __str__(self):
        return self.nombre
