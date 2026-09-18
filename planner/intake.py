"""Shared, validated intake for the chat and the existing request forms."""
import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import IntakeForm
from .models import Business, ClientRequestLink, ContentPage, DirectOffer, GeneralOffer, GeneralRequest, MeasurementImage, ServiceCategory, ServiceRequest, SiteSettings

logger = logging.getLogger(__name__)


def eligible_general_requests(business):
    return GeneralRequest.objects.filter(
        Q(invited_businesses=business)
        | Q(invited_businesses__isnull=True, category__in=business.categories.all())
    ).distinct()


def chat_context(link=None):
    categories = list(ServiceCategory.objects.filter(is_active=True))
    site, _ = SiteSettings.objects.get_or_create(pk=1)
    return {
        "site": site,
        "categories": categories,
        "menu_pages": ContentPage.objects.filter(is_published=True, show_in_menu=True),
        "client_link": link,
        "assistant_config": {
            "submitUrl": reverse("client_request", args=[link.token]) if link else reverse("assistant_submit"),
            "submissionId": str(uuid.uuid4()),
            "customerName": link.customer_name if link else "",
            "businessName": link.business.name if link else "",
            "projectLabel": link.label if link else "",
            "categorySlug": link.category.slug if link else "",
            "categories": [{"slug": item.slug, "name": item.name} for item in categories],
        },
    }


def send_notification(subject, body, email):
    # Console delivery is useful locally, but must never be presented as real email.
    if not email:
        return False
    try:
        sent = send_mail(subject, body, None, [email], fail_silently=False)
        return bool(sent) and settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
    except Exception:
        logger.exception("Email notification failed; the saved request remains available in the dashboard.")
        return False


def notify_businesses(request, item):
    if isinstance(item, ServiceRequest):
        businesses = [item.link.business]
        url = reverse("business_request", args=[item.pk])
    else:
        businesses = Business.objects.filter(is_active=True, categories=item.category).distinct()
        url = reverse("general_offer", args=[item.pk])
    for business in businesses:
        send_notification(
            "בקשה חדשה להצעת מחיר",
            f"שלום {business.name},\nנכנסה בקשה מ־{item.name}.\n"
            f"הפרטים והתמונות זמינים לאחר כניסה לחשבון העסק:\n{request.build_absolute_uri(url)}",
            business.email,
        )


def save_intake(request, form, *, category=None, link=None):
    """All rows commit together. A repeated submission ID cannot create another lead."""
    model = ServiceRequest if link else GeneralRequest
    data = dict(form.cleaned_data)
    identifier = data.get("submission_id")
    existing = model.objects.filter(submission_id=identifier).first() if identifier else None
    if existing:
        same_destination = existing.link_id == link.pk if link else existing.category_id == category.pk
        if not same_destination:
            raise ValueError("קוד השליחה אינו מתאים לבקשה. נא לרענן את הדף.")
        return existing, False
    primary_photo = data.pop("photo", None)
    data["urgency"] = data.get("urgency") or "רגיל"
    measured = any(data.get(f"estimated_{dimension}") is not None for dimension in ("width", "length", "height"))
    data["measurement_confidence"] = "הערכה ראשונית — טרם אומתה" if measured else "לא נמסרו מידות"
    data["measurement_method"] = data.get("measurement_method") or "ללא מדידה"
    data["configuration"] = json.dumps({
        "סוג עבודה": request.POST.get("service_type", "")[:1000],
        "סגנון/פתרון": request.POST.get("style", "")[:1000],
        "תוספות": request.POST.getlist("extras")[:20],
    }, ensure_ascii=False)
    saved_files = []
    try:
        with transaction.atomic():
            item = model(**data, **({"link": link} if link else {"category": category}))
            if primary_photo:
                item.photo.save(primary_photo.name, primary_photo, save=False)
                saved_files.append((item.photo.storage, item.photo.name))
            item.save()
            captions = request.POST.getlist("photo_captions")
            for index, upload in enumerate(request.FILES.getlist("measurement_photos")):
                relation = {"service_request": item} if link else {"general_request": item}
                photo = MeasurementImage(**relation, caption=(captions[index][:140] if index < len(captions) else f"תמונת פרויקט {index + 1}"))
                photo.image.save(upload.name, upload, save=False)
                saved_files.append((photo.image.storage, photo.image.name))
                photo.save()
    except Exception:
        for storage, filename in saved_files:
            storage.delete(filename)
        raise
    notify_businesses(request, item)
    return item, True


def receive_intake(request, *, category=None, link=None, as_json=False):
    form = IntakeForm(request.POST, request.FILES)
    if not form.is_valid():
        if as_json:
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return render(request, "planner/intake_errors.html", {"form": form}, status=400)
    try:
        item, _ = save_intake(request, form, category=category, link=link)
    except (DatabaseError, OSError, ValueError):
        logger.exception("Intake could not be stored.")
        if as_json:
            return JsonResponse({"ok": False, "message": "לא הצלחנו לשמור את הבקשה. הפרטים נשארו כאן; אפשר לנסות שוב."}, status=503)
        return render(request, "planner/intake_errors.html", {"save_error": True}, status=503)
    if as_json:
        recipient = link.business.name if link else "בעלי המקצוע הפעילים בתחום"
        return JsonResponse({"ok": True, "requestId": item.pk, "recipient": recipient, "direct": bool(link)})
    if link:
        return render(request, "planner/client_request_done.html", {"business": link.business})
    return render(request, "planner/category_request_done.html", {
        "category": category, "count": Business.objects.filter(is_active=True, categories=category).distinct().count(),
    })


@require_POST
def assistant_submit(request):
    category = ServiceCategory.objects.filter(slug=request.POST.get("category"), is_active=True).first()
    if not category:
        return JsonResponse({"ok": False, "errors": {"category": ["נא לבחור תחום פעיל לבקשה."]}}, status=400)
    return receive_intake(request, category=category, as_json=True)


def client_chat(request, token):
    link = get_object_or_404(ClientRequestLink.objects.select_related("business", "category"), token=token, is_active=True, business__is_active=True, category__is_active=True)
    if request.method == "POST":
        return receive_intake(request, link=link, as_json=request.headers.get("X-Requested-With") == "XMLHttpRequest")
    response = render(request, "planner/home.html", chat_context(link))
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
def request_photo(request, kind, pk, image_id):
    if kind not in {"direct", "general"}:
        raise Http404
    model = ServiceRequest if kind == "direct" else GeneralRequest
    item = get_object_or_404(model, pk=pk)
    if not request.user.is_staff:
        business = get_object_or_404(Business, owner=request.user, is_active=True)
        if kind == "direct":
            allowed = item.link.business_id == business.pk
        else:
            allowed = eligible_general_requests(business).filter(pk=pk).exists() or item.offers.filter(business=business).exists()
        if not allowed:
            raise Http404
    file = item.photo if image_id == 0 else get_object_or_404(item.measurement_images, pk=image_id).image
    try:
        response = FileResponse(file.open("rb"))
    except (ValueError, OSError):
        raise Http404("התמונה אינה זמינה באחסון")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def offer_image(request, kind, token):
    if kind not in {"direct", "general"}:
        raise Http404
    model = DirectOffer if kind == "direct" else GeneralOffer
    offer = get_object_or_404(model, token=token)
    try:
        response = FileResponse(offer.visualization.open("rb"))
    except (ValueError, OSError):
        raise Http404
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
