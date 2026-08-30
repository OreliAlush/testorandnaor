# Generated manually for the initial MVP schema.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="QuoteRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="שם")),
                ("phone", models.CharField(max_length=30, verbose_name="טלפון")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="אימייל")),
                ("city", models.CharField(blank=True, max_length=100, verbose_name="עיר")),
                ("width", models.DecimalField(decimal_places=2, max_digits=5, verbose_name="רוחב (מ׳)")),
                ("length", models.DecimalField(decimal_places=2, max_digits=5, verbose_name="אורך (מ׳)")),
                ("pergola_type", models.CharField(choices=[("aluminum", "אלומיניום"), ("wood", "עץ"), ("bioclimatic", "ביוקלימטית")], max_length=20, verbose_name="סוג פרגולה")),
                ("roof_type", models.CharField(choices=[("slats", "שלבים מתכווננים"), ("polycarbonate", "פוליקרבונט"), ("fabric", "בד הצללה")], max_length=20, verbose_name="קירוי")),
                ("color", models.CharField(max_length=50, verbose_name="צבע")),
                ("lighting", models.BooleanField(default=False, verbose_name="תאורה")),
                ("estimate", models.PositiveIntegerField(blank=True, null=True, verbose_name="הערכת מחיר")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="נוצר ב־")),
            ],
            options={"verbose_name": "בקשה להצעת מחיר", "verbose_name_plural": "בקשות להצעת מחיר", "ordering": ["-created_at"]},
        ),
    ]
