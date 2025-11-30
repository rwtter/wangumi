from django.db import migrations, models


def move_cover_to_url(apps, schema_editor):
    Anime = apps.get_model("wangumi_app", "Anime")
    updated = []
    for anime in Anime.objects.all():
        cover_value = getattr(anime, "cover_image", "")
        if cover_value and isinstance(cover_value, str) and cover_value.startswith(("http://", "https://")):
            anime.cover_url = cover_value
            anime.cover_image = ""
            updated.append(anime)
    if updated:
        Anime.objects.bulk_update(updated, ["cover_url", "cover_image"])


def move_url_back(apps, schema_editor):
    Anime = apps.get_model("wangumi_app", "Anime")
    updated = []
    for anime in Anime.objects.exclude(cover_url=""):
        if not getattr(anime, "cover_image", ""):
            anime.cover_image = anime.cover_url
            anime.cover_url = ""
            updated.append(anime)
    if updated:
        Anime.objects.bulk_update(updated, ["cover_image", "cover_url"])


class Migration(migrations.Migration):

    dependencies = [
        ("wangumi_app", "0006_anime_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="anime",
            name="cover_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.RunPython(move_cover_to_url, move_url_back),
    ]
