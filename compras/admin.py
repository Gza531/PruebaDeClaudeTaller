from django.contrib import admin
from .models import Proveedor, Compra, DetalleCompra, ProveedorXProducto


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("id_compra", "fecha", "proveedor", "numero_factura", "total", "estado")
    list_filter = ("estado",)
    inlines = [DetalleCompraInline]


admin.site.register(Proveedor)
admin.site.register(DetalleCompra)
admin.site.register(ProveedorXProducto)
