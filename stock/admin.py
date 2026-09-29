from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Stock, MovimientoStock
from .services import registrar_movimiento


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("producto", "ubicacion", "cantidad_actual", "stock_minimo", "bajo_minimo", "ultima_actualizacion")
    list_filter = ("ubicacion",)
    search_fields = ("producto__nombre", "producto__codigo_barras")
    # La cantidad solo cambia registrando movimientos de stock.
    readonly_fields = ("cantidad_actual", "ultima_actualizacion")

    @admin.display(boolean=True, description="Bajo mínimo")
    def bajo_minimo(self, obj):
        return obj.bajo_minimo


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo_movimiento", "stock", "cantidad", "usuario", "motivo", "referencia")
    list_filter = ("tipo_movimiento", "stock__ubicacion")
    search_fields = ("stock__producto__nombre", "motivo", "referencia")
    fields = ("stock", "tipo_movimiento", "cantidad", "compra", "motivo", "referencia")

    def get_readonly_fields(self, request, obj=None):
        # Un movimiento ya registrado no se edita: se corrige con otro movimiento.
        return self.fields if obj else ()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        class MovimientoForm(form):
            def clean(self):
                datos = super().clean()
                stock = datos.get("stock")
                cantidad = datos.get("cantidad")
                tipo = datos.get("tipo_movimiento")
                if obj is None and stock and cantidad and tipo not in MovimientoStock.TIPOS_INGRESO:
                    if stock.cantidad_actual < cantidad:
                        raise ValidationError(
                            f"Stock insuficiente: hay {stock.cantidad_actual} unidades."
                        )
                return datos

        return MovimientoForm

    def save_model(self, request, obj, form, change):
        if change:
            return
        movimiento = registrar_movimiento(
            obj.stock,
            obj.tipo_movimiento,
            obj.cantidad,
            request.user,
            motivo=obj.motivo,
            referencia=obj.referencia,
            compra=obj.compra,
        )
        obj.pk = movimiento.pk
