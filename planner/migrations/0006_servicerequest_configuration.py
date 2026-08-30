from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planner", "0005_servicerequest_work_details")]
    operations = [migrations.AddField(model_name="servicerequest", name="configuration", field=models.TextField(blank=True, verbose_name="בחירות ותוספות"))]
