from django.db import migrations


# Valores que usaban los choices antes de alinearlos con la base guinda_db.
VALORES_NUEVOS = {
    "version_producto": {"ORIGINAL": "Original", "REPLICA": "Réplica"},
    "genero_producto": {
        "MASCULINO": "Masculino",
        "FEMENINO": "Femenino",
        "UNISEX": "Unisex",
        "NO_APLICA": "No aplica",
    },
    "origen": {"NACIONAL": "Nacional", "IMPORTADO": "Importado"},
}


def convertir_choices(apps, schema_editor):
    Producto = apps.get_model("catalogo", "Producto")
    for campo, valores in VALORES_NUEVOS.items():
        for viejo, nuevo in valores.items():
            Producto.objects.filter(**{campo: viejo}).update(**{campo: nuevo})


def revertir_choices(apps, schema_editor):
    Producto = apps.get_model("catalogo", "Producto")
    for campo, valores in VALORES_NUEVOS.items():
        for viejo, nuevo in valores.items():
            Producto.objects.filter(**{campo: nuevo}).update(**{campo: viejo})


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0002_ajustes_guinda_db"),
    ]

    operations = [
        migrations.RunPython(convertir_choices, revertir_choices),
    ]
