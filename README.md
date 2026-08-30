# iPergola MVP

אתר Django בעברית לתכנון פרגולה וקבלת בקשות להצעות מחיר.

## הפעלה מקומית

```bash
cd pergola_mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations planner
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

פתחו את `http://127.0.0.1:8000`. בקשות שהתקבלו זמינות ב־`/admin/`.

## זרימת הצעות המחיר מבעלי עסקים

1. מנהל המערכת מוסיף ב־`/admin/` רשומה תחת **בעלי עסקים** עם שם ומייל.
2. לקוח שולח בקשת תכנון. אין באתר מחיר אוטומטי.
3. כל בעל עסק שמסומן כ־**מקבל בקשות חדשות** מקבל מייל עם קישור אישי להגשת מחיר.
4. בעל העסק פותח את הקישור, רואה מידות, בחירות ותמונת שטח (אם עלתה), ומגיש מחיר והודעה.
5. ההצעות מופיעות ב־`/admin/` תחת **הצעות מחיר מבעלי עסקים**.

בפיתוח מקומי המיילים מודפסים למסוף בלבד. כדי לשלוח מיילים אמיתיים בפרודקשן יש להגדיר משתני SMTP: `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS=True`, ו־`DEFAULT_FROM_EMAIL`.

## העלאה ל־Render

1. העלו את התיקייה ל־GitHub.
2. ב־Render בחרו **New → Web Service** וחברו את המאגר.
3. הגדירו Root Directory: `pergola_mvp`.
4. Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`.
5. Start Command: `gunicorn config.wsgi`.
6. צרו ב־Render גם **PostgreSQL** והעתיקו את ה־Internal Database URL שלו אל משתנה הסביבה `DATABASE_URL` של השירות.
7. הגדירו משתני סביבה נוספים: `SECRET_KEY` (ערך ארוך ואקראי), `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`.

לגרסה מסחרית השתמשו ב־PostgreSQL במקום SQLite כדי שהנתונים לא יאבדו בהפעלה מחדש של השירות.
