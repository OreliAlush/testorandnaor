from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


def seed_categories(apps, schema_editor):
    Category = apps.get_model("planner", "ServiceCategory")
    for name, slug, icon, description in [
        ("פרגולות", "pergolas", "🌿", "תכנון והתקנת פרגולות"),
        ("מטבחים", "kitchens", "🍳", "תכנון, נגרות והתקנת מטבחים"),
        ("אינסטלציה", "plumbing", "🔧", "תיקונים והתקנות מים וביוב"),
        ("חשמל", "electricity", "⚡", "עבודות חשמל לבית ולעסק"),
        ("שיפוצים", "renovations", "🏠", "שיפוצים ועבודות גמר"),
    ]:
        Category.objects.get_or_create(slug=slug, defaults={"name": name, "icon": icon, "description": description})


class Migration(migrations.Migration):
    dependencies = [("planner", "0003_business_quotations"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="ServiceCategory", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=80, unique=True, verbose_name="שם הקטגוריה")),
            ("slug", models.SlugField(unique=True)), ("icon", models.CharField(default="🛠️", max_length=8, verbose_name="אייקון")),
            ("description", models.CharField(blank=True, max_length=180, verbose_name="תיאור קצר")), ("is_active", models.BooleanField(default=True)),
        ], options={"verbose_name": "קטגוריית שירות", "verbose_name_plural": "קטגוריות שירות", "ordering": ["name"]}),
        migrations.AddField(model_name="business", name="owner", field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="business_profile", to=settings.AUTH_USER_MODEL, verbose_name="חשבון בעל העסק")),
        migrations.AddField(model_name="business", name="categories", field=models.ManyToManyField(blank=True, related_name="businesses", to="planner.servicecategory", verbose_name="קטגוריות שירות")),
        migrations.CreateModel(name="ClientRequestLink", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("label", models.CharField(default="קישור ללקוחות", max_length=100, verbose_name="שם הקישור")),
            ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)), ("is_active", models.BooleanField(default=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="client_links", to="planner.business")), ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="planner.servicecategory")),
        ], options={"verbose_name": "קישור ללקוח", "verbose_name_plural": "קישורים ללקוחות"}),
        migrations.CreateModel(name="ServiceRequest", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=100)), ("phone", models.CharField(max_length=30)), ("email", models.EmailField(blank=True, max_length=254)), ("city", models.CharField(blank=True, max_length=100)),
            ("description", models.TextField(verbose_name="מה צריך לעשות?")), ("photo", models.FileField(blank=True, upload_to="service-requests/%Y/%m/")), ("status", models.CharField(default="בקשה חדשה", max_length=30)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("link", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="requests", to="planner.clientrequestlink")),
        ], options={"verbose_name": "בקשת שירות", "verbose_name_plural": "בקשות שירות", "ordering": ["-created_at"]}),
        migrations.CreateModel(name="DirectOffer", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("price", models.PositiveIntegerField()), ("message", models.TextField(blank=True)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("request", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="direct_offer", to="planner.servicerequest")),
        ], options={"verbose_name": "הצעה ישירה", "verbose_name_plural": "הצעות ישירות"}),
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
