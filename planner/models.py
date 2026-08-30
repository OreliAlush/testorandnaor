from django.db import models
import uuid
from django.conf import settings


class QuoteRequest(models.Model):
    PERGOLA_TYPES = [("aluminum", "אלומיניום"), ("wood", "עץ"), ("bioclimatic", "ביוקלימטית")]
    ROOF_TYPES = [("slats", "שלבים מתכווננים"), ("polycarbonate", "פוליקרבונט"), ("fabric", "בד הצללה")]

    name = models.CharField("שם", max_length=100)
    phone = models.CharField("טלפון", max_length=30)
    email = models.EmailField("אימייל", blank=True)
    city = models.CharField("עיר", max_length=100, blank=True)
    space_photo = models.FileField("תמונת השטח", upload_to="spaces/%Y/%m/", blank=True)
    width = models.DecimalField("רוחב (מ׳)", max_digits=5, decimal_places=2)
    length = models.DecimalField("אורך (מ׳)", max_digits=5, decimal_places=2)
    pergola_type = models.CharField("סוג פרגולה", max_length=20, choices=PERGOLA_TYPES)
    roof_type = models.CharField("קירוי", max_length=20, choices=ROOF_TYPES)
    color = models.CharField("צבע", max_length=50)
    lighting = models.BooleanField("תאורה", default=False)
    status = models.CharField("סטטוס", max_length=20, default="חדש")
    assigned_businesses = models.ManyToManyField("Business", blank=True, related_name="manually_assigned_quote_requests", verbose_name="בעלי עסקים שנבחרו")
    created_at = models.DateTimeField("נוצר ב־", auto_now_add=True)

    class Meta:
        verbose_name = "בקשה להצעת מחיר"
        verbose_name_plural = "בקשות להצעת מחיר"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.width}×{self.length} מ׳"


class Business(models.Model):
    name = models.CharField("שם העסק", max_length=120)
    email = models.EmailField("מייל לקבלת בקשות")
    phone = models.CharField("טלפון", max_length=30, blank=True)
    is_active = models.BooleanField("מקבל בקשות חדשות", default=True)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="business_profile", verbose_name="חשבון בעל העסק")
    categories = models.ManyToManyField("ServiceCategory", blank=True, related_name="businesses", verbose_name="קטגוריות שירות")

    class Meta:
        verbose_name = "בעל עסק"
        verbose_name_plural = "בעלי עסקים"

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    name = models.CharField("שם הקטגוריה", max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField("אייקון", max_length=8, default="🛠️")
    description = models.CharField("תיאור קצר", max_length=180, blank=True)
    request_tip = models.CharField("הנחיה בטופס הבקשה", max_length=280, blank=True)
    work_types = models.TextField("סוגי עבודה", blank=True, help_text="אפשרות אחת בכל שורה")
    styles = models.TextField("סגנונות / פתרונות", blank=True, help_text="אפשרות אחת בכל שורה")
    extras = models.TextField("תוספות", blank=True, help_text="אפשרות אחת בכל שורה")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "קטגוריית שירות"
        verbose_name_plural = "קטגוריות שירות"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClientRequestLink(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="client_links")
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT)
    label = models.CharField("שם הקישור", max_length=100, default="קישור ללקוחות")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "קישור ללקוח"
        verbose_name_plural = "קישורים ללקוחות"


class ServiceRequest(models.Model):
    link = models.ForeignKey(ClientRequestLink, on_delete=models.PROTECT, related_name="requests")
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    description = models.TextField("מה צריך לעשות?")
    work_area = models.DecimalField("גודל/כמות", max_digits=8, decimal_places=2, null=True, blank=True)
    budget = models.PositiveIntegerField("תקציב משוער", null=True, blank=True)
    preferred_date = models.DateField("מועד מועדף", null=True, blank=True)
    urgency = models.CharField("דחיפות", max_length=20, default="רגיל")
    configuration = models.TextField("בחירות ותוספות", blank=True)
    photo = models.FileField(upload_to="service-requests/%Y/%m/", blank=True)
    status = models.CharField(max_length=30, default="בקשה חדשה")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "בקשת שירות"
        verbose_name_plural = "בקשות שירות"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.link.category.name}"


class DirectOffer(models.Model):
    request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name="direct_offer")
    price = models.PositiveIntegerField()
    message = models.TextField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, default="הצעה נשלחה")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "הצעה ישירה"
        verbose_name_plural = "הצעות ישירות"


class ExpertProfile(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="expert_profile")
    headline = models.CharField("כותרת מקצועית", max_length=140, blank=True)
    bio = models.TextField("תיאור מקצועי", blank=True)
    photo = models.FileField("תמונת מומחה", upload_to="experts/%Y/%m/", blank=True)
    is_featured = models.BooleanField("להציג באתר", default=True)

    class Meta:
        verbose_name = "פרופיל מומחה"
        verbose_name_plural = "פרופילי מומחים"

    def __str__(self):
        return self.business.name


class PortfolioProject(models.Model):
    expert = models.ForeignKey(ExpertProfile, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField("שם העבודה", max_length=140)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField("תיאור", blank=True)
    image = models.FileField("תמונת עבודה", upload_to="portfolio/%Y/%m/", blank=True)
    completed_at = models.DateField("תאריך סיום", null=True, blank=True)
    is_published = models.BooleanField("להציג באתר", default=True)

    class Meta:
        verbose_name = "עבודת מומחה"
        verbose_name_plural = "עבודות מומחים"
        ordering = ["-completed_at", "-id"]

    def __str__(self):
        return self.title


class ContentPage(models.Model):
    title = models.CharField("כותרת", max_length=160)
    slug = models.SlugField("כתובת עמוד", unique=True)
    summary = models.CharField("תקציר", max_length=240, blank=True)
    body = models.TextField("תוכן העמוד", blank=True)
    cover_image = models.FileField("תמונת שער", upload_to="pages/%Y/%m/", blank=True)
    is_published = models.BooleanField("מפורסם", default=True)
    show_in_menu = models.BooleanField("להציג בקישורי האתר", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "עמוד תוכן"
        verbose_name_plural = "עמודי תוכן"
        ordering = ["title"]

    def __str__(self):
        return self.title


class GeneralRequest(models.Model):
    STATUS_OPEN = "פתוחה"
    STATUS_AWARDED = "נסגרה"
    STATUS_CHOICES = [(STATUS_OPEN, "פתוחה להצעות"), (STATUS_AWARDED, "נסגרה עם בעל עסק")]
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, verbose_name="קטגוריה")
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    work_area = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    budget = models.PositiveIntegerField(null=True, blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    urgency = models.CharField(max_length=20, default="רגיל")
    configuration = models.TextField(blank=True)
    photo = models.FileField(upload_to="general-requests/%Y/%m/", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    invited_businesses = models.ManyToManyField(Business, blank=True, related_name="assigned_general_requests", verbose_name="עסקים שנבחרו")
    awarded_business = models.ForeignKey(Business, null=True, blank=True, on_delete=models.SET_NULL, related_name="won_general_requests", verbose_name="העסק שנבחר")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "בקשה כללית להצעת עבודה"
        verbose_name_plural = "בקשות כלליות להצעת עבודה"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.category.name}"


class GeneralOffer(models.Model):
    request = models.ForeignKey(GeneralRequest, on_delete=models.CASCADE, related_name="offers")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="general_offers")
    price = models.PositiveIntegerField()
    message = models.TextField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, default="הצעה נשלחה")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "הצעה לבקשה כללית"
        verbose_name_plural = "הצעות לבקשות כלליות"
        constraints = [models.UniqueConstraint(fields=["request", "business"], name="one_general_offer_per_business")]


class SiteSettings(models.Model):
    brand_name = models.CharField("שם המותג", max_length=80, default="OrProServices")
    home_kicker = models.CharField("כותרת קטנה בדף הבית", max_length=120, default="פלטפורמת השירותים לבית")
    home_title = models.CharField("כותרת ראשית בדף הבית", max_length=240, default="כל בעל מקצוע. כל פרויקט. במקום אחד.")
    home_lead = models.TextField("טקסט פתיחה בדף הבית", default="שולחים בקשה מדויקת עם בחירות, תמונות ופרטי עבודה—ומקבלים הצעות מבעלי מקצוע.")
    home_cta = models.CharField("טקסט כפתור ראשי", max_length=80, default="לבחירת תחום שירות")
    footer_text = models.CharField("טקסט תחתון", max_length=180, default="OrProServices .אתר דמו)
    experts_title = models.CharField("כותרת דף מומחים", max_length=180, default="המומחים שלנו והעבודות שלהם.")
    experts_lead = models.TextField("טקסט דף מומחים", default="הכירו בעלי מקצוע נבחרים והתרשמו מפרויקטים אמיתיים.")
    pergola_title = models.CharField("כותרת פרגולות", max_length=180, default="הפרגולה שלכם, מתחילה נכון.")
    pergola_lead = models.TextField("טקסט פרגולות", default="בחירות, מידות ותמונה—כדי שבעלי המקצוע יבינו בדיוק מה אתם צריכים.")

    class Meta:
        verbose_name = "הגדרות תוכן האתר"
        verbose_name_plural = "הגדרות תוכן האתר"

    def __str__(self):
        return "הגדרות האתר"


class QuoteInvitation(models.Model):
    request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="invitations", verbose_name="בקשת לקוח")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="invitations", verbose_name="בעל עסק")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "הזמנה להצעת מחיר"
        verbose_name_plural = "הזמנות להצעות מחיר"
        constraints = [models.UniqueConstraint(fields=["request", "business"], name="one_invitation_per_business")]


class BusinessOffer(models.Model):
    invitation = models.OneToOneField(QuoteInvitation, on_delete=models.CASCADE, related_name="offer", verbose_name="הזמנה")
    price = models.PositiveIntegerField("מחיר כולל בש״ח")
    message = models.TextField("הודעה ללקוח", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "הצעת מחיר מבעל עסק"
        verbose_name_plural = "הצעות מחיר מבעלי עסקים"
