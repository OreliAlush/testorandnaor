from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [("planner", "0002_quoterequest_space_photo")]

    operations = [
        migrations.RemoveField(model_name="quoterequest", name="estimate"),
        migrations.AddField(model_name="quoterequest", name="status", field=models.CharField(default="חדש", max_length=20, verbose_name="סטטוס")),
        migrations.CreateModel(
            name="Business",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="שם העסק")),
                ("email", models.EmailField(max_length=254, verbose_name="מייל לקבלת בקשות")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="טלפון")),
                ("is_active", models.BooleanField(default=True, verbose_name="מקבל בקשות חדשות")),
            ],
            options={"verbose_name": "בעל עסק", "verbose_name_plural": "בעלי עסקים"},
        ),
        migrations.CreateModel(
            name="QuoteInvitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("completed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="planner.business", verbose_name="בעל עסק")),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="planner.quoterequest", verbose_name="בקשת לקוח")),
            ],
            options={"verbose_name": "הזמנה להצעת מחיר", "verbose_name_plural": "הזמנות להצעות מחיר"},
        ),
        migrations.CreateModel(
            name="BusinessOffer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price", models.PositiveIntegerField(verbose_name="מחיר כולל בש״ח")),
                ("message", models.TextField(blank=True, verbose_name="הודעה ללקוח")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("invitation", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="offer", to="planner.quoteinvitation", verbose_name="הזמנה")),
            ],
            options={"verbose_name": "הצעת מחיר מבעל עסק", "verbose_name_plural": "הצעות מחיר מבעלי עסקים"},
        ),
        migrations.AddConstraint(model_name="quoteinvitation", constraint=models.UniqueConstraint(fields=("request", "business"), name="one_invitation_per_business")),
    ]
