import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planner", "0009_editable_content")]
    operations = [
        migrations.AddField(model_name="directoffer", name="status", field=models.CharField(default="הצעה נשלחה", max_length=20)),
        migrations.AddField(model_name="directoffer", name="token", field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        migrations.AddField(model_name="generaloffer", name="status", field=models.CharField(default="הצעה נשלחה", max_length=20)),
        migrations.AddField(model_name="generaloffer", name="token", field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
    ]
