from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planner", "0004_service_marketplace")]
    operations = [
        migrations.AddField(model_name="servicerequest", name="address", field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name="servicerequest", name="budget", field=models.PositiveIntegerField(blank=True, null=True, verbose_name="תקציב משוער")),
        migrations.AddField(model_name="servicerequest", name="preferred_date", field=models.DateField(blank=True, null=True, verbose_name="מועד מועדף")),
        migrations.AddField(model_name="servicerequest", name="urgency", field=models.CharField(default="רגיל", max_length=20, verbose_name="דחיפות")),
        migrations.AddField(model_name="servicerequest", name="work_area", field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name="גודל/כמות")),
    ]
