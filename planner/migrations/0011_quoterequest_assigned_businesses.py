from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planner", "0010_offer_delivery_and_status")]
    operations = [
        migrations.AddField(model_name="quoterequest", name="assigned_businesses", field=models.ManyToManyField(blank=True, related_name="manually_assigned_quote_requests", to="planner.business", verbose_name="בעלי עסקים שנבחרו")),
    ]
