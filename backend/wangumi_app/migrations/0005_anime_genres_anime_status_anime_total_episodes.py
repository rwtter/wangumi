from django.db import migrations, models


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

    _add_field_if_missing(
        schema_editor,
        Anime,
        "genres",
        models.JSONField(default=list, blank=True),
    )
    _add_field_if_missing(
        schema_editor,
        Anime,
        "status",
        models.CharField(max_length=32, blank=True),
    )
    _add_field_if_missing(
        schema_editor,
        Anime,
        "total_episodes",
        models.IntegerField(default=0),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("wangumi_app", "0004_anime_extra_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(forwards, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="anime",
                    name="genres",
                    field=models.JSONField(blank=True, default=list),
                ),
                migrations.AddField(
                    model_name="anime",
                    name="status",
                    field=models.CharField(blank=True, max_length=32),
                ),
                migrations.AddField(
                    model_name="anime",
                    name="total_episodes",
                    field=models.IntegerField(default=0),
                ),
            ],
        ),
    ]
