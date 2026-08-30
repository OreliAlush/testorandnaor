from django.contrib import admin
from django.core.mail import send_mail
from django.urls import reverse
from .forms import BusinessAdminForm
from .models import Business, BusinessOffer, ClientRequestLink, ContentPage, DirectOffer, ExpertProfile, GeneralOffer, GeneralRequest, PortfolioProject, QuoteInvitation, QuoteRequest, ServiceCategory, ServiceRequest, SiteSettings


class InvitationInline(admin.TabularInline):
    model = QuoteInvitation
    extra = 0
    readonly_fields = ("token", "completed", "created_at")


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "city", "pergola_type", "status", "created_at")
    readonly_fields = ("created_at", "space_preview")
    inlines = (InvitationInline,)
    filter_horizontal = ("assigned_businesses",)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        quote_request = form.instance
        for business in quote_request.assigned_businesses.filter(is_active=True):
            invitation, created = QuoteInvitation.objects.get_or_create(request=quote_request, business=business)
            if created:
                offer_url = request.build_absolute_uri(reverse("offer", args=[invitation.token]))
                send_mail(
                    "בקשה חדשה להצעת מחיר לפרגולה",
                    f"שלום {business.name},\n\nנבחרת להגיש הצעה לבקשה חדשה.\nלקוח: {quote_request.name}\nמידות: {quote_request.width}×{quote_request.length} מ׳\n\nלהגשת הצעה: {offer_url}",
                    None,
                    [business.email],
                    fail_silently=True,
                )
    list_filter = ("pergola_type", "roof_type", "lighting", "created_at")
    search_fields = ("name", "phone", "email", "city")
    def space_preview(self, obj):
        if obj.space_photo:
            return f"תמונה נשמרה: {obj.space_photo.name}"
        return "לא הועלתה תמונה"
    space_preview.short_description = "תמונת השטח"


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    form = BusinessAdminForm
    list_display = ("name", "email", "phone", "owner", "is_active")
    list_filter = ("is_active",)
    filter_horizontal = ("categories",)
    fields = ("name", "email", "phone", "categories", "is_active", "login_username", "login_password")


@admin.register(BusinessOffer)
class BusinessOfferAdmin(admin.ModelAdmin):
    list_display = ("business_name", "request_name", "price", "created_at")
    readonly_fields = ("created_at",)

    @admin.display(description="בעל העסק")
    def business_name(self, obj):
        return obj.invitation.business.name

    @admin.display(description="לקוח")
    def request_name(self, obj):
        return obj.invitation.request.name


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ClientRequestLink)
class ClientRequestLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "business", "category", "is_active", "created_at")
    list_filter = ("category", "is_active")


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "category", "business", "urgency", "status", "created_at")
    list_filter = ("status", "link__category")
    search_fields = ("name", "phone", "city")
    readonly_fields = ("configuration",)

    @admin.display(description="קטגוריה")
    def category(self, obj):
        return obj.link.category.name

    @admin.display(description="בעל העסק")
    def business(self, obj):
        return obj.link.business.name


@admin.register(DirectOffer)
class DirectOfferAdmin(admin.ModelAdmin):
    list_display = ("request", "price", "created_at")


class PortfolioProjectInline(admin.TabularInline):
    model = PortfolioProject
    extra = 0


@admin.register(ExpertProfile)
class ExpertProfileAdmin(admin.ModelAdmin):
    list_display = ("business", "headline", "is_featured")
    list_filter = ("is_featured",)
    inlines = (PortfolioProjectInline,)


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "expert", "category", "is_published", "completed_at")
    list_filter = ("category", "is_published")


@admin.register(ContentPage)
class ContentPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_menu")
    list_filter = ("is_published", "show_in_menu")
    prepopulated_fields = {"slug": ("title",)}


class GeneralOfferInline(admin.TabularInline):
    model = GeneralOffer
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(GeneralRequest)
class GeneralRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "city", "status", "awarded_business", "created_at")
    list_filter = ("category", "status", "urgency")
    search_fields = ("name", "phone", "city")
    filter_horizontal = ("invited_businesses",)
    inlines = (GeneralOfferInline,)


@admin.register(GeneralOffer)
class GeneralOfferAdmin(admin.ModelAdmin):
    list_display = ("request", "business", "price", "created_at")
    list_filter = ("business",)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
