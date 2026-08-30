from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("planner", "0006_servicerequest_configuration")]
    operations = [
        migrations.CreateModel(name="ContentPage", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(max_length=160, verbose_name="כותרת")), ("slug", models.SlugField(unique=True, verbose_name="כתובת עמוד")), ("summary", models.CharField(blank=True, max_length=240, verbose_name="תקציר")), ("body", models.TextField(blank=True, verbose_name="תוכן העמוד")), ("cover_image", models.FileField(blank=True, upload_to="pages/%Y/%m/", verbose_name="תמונת שער")), ("is_published", models.BooleanField(default=True, verbose_name="מפורסם")), ("show_in_menu", models.BooleanField(default=False, verbose_name="להציג בקישורי האתר")), ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"verbose_name": "עמוד תוכן", "verbose_name_plural": "עמודי תוכן", "ordering": ["title"]}),
        migrations.CreateModel(name="ExpertProfile", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("headline", models.CharField(blank=True, max_length=140, verbose_name="כותרת מקצועית")), ("bio", models.TextField(blank=True, verbose_name="תיאור מקצועי")), ("photo", models.FileField(blank=True, upload_to="experts/%Y/%m/", verbose_name="תמונת מומחה")), ("is_featured", models.BooleanField(default=True, verbose_name="להציג באתר")), ("business", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="expert_profile", to="planner.business")),
        ], options={"verbose_name": "פרופיל מומחה", "verbose_name_plural": "פרופילי מומחים"}),
        migrations.CreateModel(name="PortfolioProject", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(max_length=140, verbose_name="שם העבודה")), ("description", models.TextField(blank=True, verbose_name="תיאור")), ("image", models.FileField(blank=True, upload_to="portfolio/%Y/%m/", verbose_name="תמונת עבודה")), ("completed_at", models.DateField(blank=True, null=True, verbose_name="תאריך סיום")), ("is_published", models.BooleanField(default=True, verbose_name="להציג באתר")), ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="planner.servicecategory")), ("expert", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="planner.expertprofile")),
        ], options={"verbose_name": "עבודת מומחה", "verbose_name_plural": "עבודות מומחים", "ordering": ["-completed_at", "-id"]}),
    ]
