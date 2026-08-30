from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planner", "0008_general_requests")]
    operations = [
        migrations.AddField(model_name="servicecategory", name="extras", field=models.TextField(blank=True, help_text="אפשרות אחת בכל שורה", verbose_name="תוספות")),
        migrations.AddField(model_name="servicecategory", name="request_tip", field=models.CharField(blank=True, max_length=280, verbose_name="הנחיה בטופס הבקשה")),
        migrations.AddField(model_name="servicecategory", name="styles", field=models.TextField(blank=True, help_text="אפשרות אחת בכל שורה", verbose_name="סגנונות / פתרונות")),
        migrations.AddField(model_name="servicecategory", name="work_types", field=models.TextField(blank=True, help_text="אפשרות אחת בכל שורה", verbose_name="סוגי עבודה")),
        migrations.CreateModel(name="SiteSettings", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("brand_name", models.CharField(default="OrProServices", max_length=80, verbose_name="שם המותג")), ("home_kicker", models.CharField(default="פלטפורמת השירותים לבית", max_length=120, verbose_name="כותרת קטנה בדף הבית")), ("home_title", models.CharField(default="כל בעל מקצוע. כל פרויקט. במקום אחד.", max_length=240, verbose_name="כותרת ראשית בדף הבית")), ("home_lead", models.TextField(default="שולחים בקשה מדויקת עם בחירות, תמונות ופרטי עבודה—ומקבלים הצעות מבעלי מקצוע.", verbose_name="טקסט פתיחה בדף הבית")), ("home_cta", models.CharField(default="לבחירת תחום שירות", max_length=80, verbose_name="טקסט כפתור ראשי")), ("footer_text", models.CharField(default="OrProServices .כל הזכויות שמורות לאור עלוש", max_length=180, verbose_name="טקסט תחתון")), ("experts_title", models.CharField(default="המומחים שלנו והעבודות שלהם.", max_length=180, verbose_name="כותרת דף מומחים")), ("experts_lead", models.TextField(default="הכירו בעלי מקצוע נבחרים והתרשמו מפרויקטים אמיתיים.", verbose_name="טקסט דף מומחים")), ("pergola_title", models.CharField(default="הפרגולה שלכם, מתחילה נכון.", max_length=180, verbose_name="כותרת פרגולות")), ("pergola_lead", models.TextField(default="בחירות, מידות ותמונה—כדי שבעלי המקצוע יבינו בדיוק מה אתם צריכים.", verbose_name="טקסט פרגולות")),
        ], options={"verbose_name": "הגדרות תוכן האתר", "verbose_name_plural": "הגדרות תוכן האתר"}),
    ]
