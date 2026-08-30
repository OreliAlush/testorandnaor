from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planner", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="quoterequest",
            name="space_photo",
            field=models.FileField(blank=True, upload_to="spaces/%Y/%m/", verbose_name="תמונת השטח"),
        ),
    ]
