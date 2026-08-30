from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("planner", "0007_content_and_experts")]
    operations = [
        migrations.CreateModel(name="GeneralRequest", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=100)), ("phone", models.CharField(max_length=30)), ("email", models.EmailField(blank=True, max_length=254)), ("city", models.CharField(blank=True, max_length=100)), ("address", models.CharField(blank=True, max_length=200)), ("description", models.TextField()), ("work_area", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)), ("budget", models.PositiveIntegerField(blank=True, null=True)), ("preferred_date", models.DateField(blank=True, null=True)), ("urgency", models.CharField(default="רגיל", max_length=20)), ("configuration", models.TextField(blank=True)), ("photo", models.FileField(blank=True, upload_to="general-requests/%Y/%m/")), ("status", models.CharField(choices=[("פתוחה", "פתוחה להצעות"), ("נסגרה", "נסגרה עם בעל עסק")], default="פתוחה", max_length=20)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("awarded_business", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="won_general_requests", to="planner.business", verbose_name="העסק שנבחר")), ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="planner.servicecategory", verbose_name="קטגוריה")), ("invited_businesses", models.ManyToManyField(blank=True, related_name="assigned_general_requests", to="planner.business", verbose_name="עסקים שנבחרו")),
        ], options={"verbose_name": "בקשה כללית להצעת עבודה", "verbose_name_plural": "בקשות כלליות להצעת עבודה", "ordering": ["-created_at"]}),
        migrations.CreateModel(name="GeneralOffer", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("price", models.PositiveIntegerField()), ("message", models.TextField(blank=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="general_offers", to="planner.business")), ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offers", to="planner.generalrequest")),
        ], options={"verbose_name": "הצעה לבקשה כללית", "verbose_name_plural": "הצעות לבקשות כלליות"}),
        migrations.AddConstraint(model_name="generaloffer", constraint=models.UniqueConstraint(fields=("request", "business"), name="one_general_offer_per_business")),
    ]
