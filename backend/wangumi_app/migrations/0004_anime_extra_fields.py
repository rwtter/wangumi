from django.db import connection, migrations, models


def _add_field_if_missing(schema_editor, model, field_name, field):
    table = model._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        existing = {
            col.name
            for col in schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if field_name not in existing:
        field.set_attributes_from_name(field_name)
        schema_editor.add_field(model, field)


def forwards(apps, schema_editor):
    Anime = apps.get_model("wangumi_app", "Anime")
    json_field = models.JSONField(default=list, blank=True)
    _add_field_if_missing(schema_editor, Anime, "genres", json_field)

    status_field = models.CharField(max_length=32, blank=True)
    _add_field_if_missing(schema_editor, Anime, "status", status_field)

    episodes_field = models.IntegerField(default=0)
    _add_field_if_missing(schema_editor, Anime, "total_episodes", episodes_field)


class Migration(migrations.Migration):

    dependencies = [
        ("wangumi_app", "0003_verificationcode"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
