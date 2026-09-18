from django import forms
from django.contrib.auth import get_user_model
from pathlib import Path
import re
from .models import Business, ClientRequestLink


def validate_project_image(upload):
    if upload is None:
        return None
    if upload.size > 10 * 1024 * 1024:
        raise forms.ValidationError("כל תמונה צריכה להיות עד 10MB.")
    header = upload.read(12)
    upload.seek(0)
    formats = {
        "image/jpeg": (header.startswith(b"\xff\xd8\xff"), {".jpg", ".jpeg"}),
        "image/png": (header.startswith(b"\x89PNG\r\n\x1a\n"), {".png"}),
        "image/webp": (header[:4] == b"RIFF" and header[8:12] == b"WEBP", {".webp"}),
    }
    valid, extensions = formats.get(upload.content_type, (False, set()))
    if not valid or Path(upload.name).suffix.lower() not in extensions:
        raise forms.ValidationError("נא לצרף תמונה תקינה בפורמט JPG, PNG או WEBP.")
    return upload


class ClientLinkForm(forms.ModelForm):
    customer_name = forms.CharField(label="שם הלקוח", max_length=100)

    class Meta:
        model = ClientRequestLink
        fields = ("customer_name", "label", "category")
        labels = {"label": "שם הפרויקט", "category": "תחום העבודה"}

    def __init__(self, *args, business, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = business.categories.filter(is_active=True)
        self.fields["label"].initial = ""
        self.fields["label"].widget.attrs["placeholder"] = "למשל: שיפוץ המטבח"


class IntakeForm(forms.Form):
    name = forms.CharField(label="שם", max_length=100)
    phone = forms.CharField(label="טלפון", max_length=30)
    email = forms.EmailField(label="אימייל", required=False)
    city = forms.CharField(label="עיר", max_length=100, required=False)
    address = forms.CharField(label="כתובת", max_length=200, required=False)
    description = forms.CharField(label="תיאור העבודה", max_length=10000)
    work_area = forms.DecimalField(required=False, max_digits=8, decimal_places=2, min_value=0)
    budget = forms.IntegerField(required=False, min_value=0, max_value=2147483647)
    preferred_date = forms.DateField(required=False)
    urgency = forms.CharField(required=False, max_length=20)
    estimated_width = forms.DecimalField(label="רוחב", required=False, min_value=0.01, max_digits=6, decimal_places=2)
    estimated_length = forms.DecimalField(label="אורך", required=False, min_value=0.01, max_digits=6, decimal_places=2)
    estimated_height = forms.DecimalField(label="גובה", required=False, min_value=0.01, max_digits=6, decimal_places=2)
    measurement_method = forms.CharField(required=False, max_length=50)
    photo = forms.FileField(required=False, validators=[validate_project_image])
    submission_id = forms.UUIDField(required=False)

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not re.fullmatch(r"[+\d\s()\-]+", phone) or not 8 <= len(re.sub(r"\D", "", phone)) <= 15:
            raise forms.ValidationError("נא להזין מספר טלפון מלא ותקין.")
        return phone

    def clean(self):
        data = super().clean()
        images = self.files.getlist("measurement_photos")
        if len(images) > 12:
            raise forms.ValidationError("אפשר לצרף עד 12 תמונות לבקשה.")
        for upload in images:
            validate_project_image(upload)
        return data


class QuoteForm(forms.Form):
    price = forms.IntegerField(label="מחיר כולל בש״ח", min_value=1, max_value=2147483647)
    message = forms.CharField(label="מה כלול בהצעה", required=False, max_length=10000, widget=forms.Textarea(attrs={"rows": 5}))
    confirmed_width = forms.DecimalField(label="רוחב שאומת במטרים", required=False, min_value=0.01, max_digits=6, decimal_places=2)
    confirmed_length = forms.DecimalField(label="אורך שאומת במטרים", required=False, min_value=0.01, max_digits=6, decimal_places=2)
    confirmed_height = forms.DecimalField(label="גובה שאומת במטרים", required=False, min_value=0.01, max_digits=6, decimal_places=2)
    visualization = forms.FileField(label="הדמיה ללקוח", required=False, validators=[validate_project_image])


class BusinessAdminForm(forms.ModelForm):
    login_username = forms.CharField(label="שם משתמש לכניסת העסק")
    login_password = forms.CharField(label="סיסמה לכניסת העסק", required=False, widget=forms.PasswordInput(render_value=True))

    class Meta:
        model = Business
        fields = ("name", "email", "phone", "categories", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.owner_id:
            self.fields["login_username"].initial = self.instance.owner.username
            self.fields["login_password"].help_text = "השאר ריק כדי לא לשנות את הסיסמה."
        else:
            self.fields["login_password"].required = True

    def clean_login_username(self):
        username = self.cleaned_data["login_username"].strip()
        User = get_user_model()
        query = User.objects.filter(username=username)
        if self.instance.owner_id:
            query = query.exclude(pk=self.instance.owner_id)
        if query.exists():
            raise forms.ValidationError("שם המשתמש כבר קיים.")
        return username

    def save(self, commit=True):
        business = super().save(commit=False)
        User = get_user_model()
        username = self.cleaned_data["login_username"]
        password = self.cleaned_data["login_password"]
        user = business.owner
        if user is None:
            user = User.objects.create_user(username=username, password=password, email=business.email)
            business.owner = user
        else:
            user.username = username
            user.email = business.email
            if password:
                user.set_password(password)
            user.save()
        if commit:
            business.save()
            self.save_m2m()
        return business
