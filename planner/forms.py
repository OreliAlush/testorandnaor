from django import forms
from django.contrib.auth import get_user_model
from .models import Business


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
