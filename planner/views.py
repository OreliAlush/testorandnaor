import json
from django.core.mail import send_mail
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .forms import ClientLinkForm, QuoteForm
from .intake import chat_context, client_chat, eligible_general_requests, receive_intake, send_notification
from .models import Business, BusinessOffer, ClientRequestLink, ContentPage, DirectOffer, ExpertProfile, GeneralOffer, GeneralRequest, MeasurementImage, QuoteInvitation, QuoteRequest, ServiceCategory, ServiceRequest, SiteSettings


def site_settings():
    settings, _ = SiteSettings.objects.get_or_create(pk=1)
    return settings


def configurator(request):
    if request.method == "POST":
        data = request.POST
        try:
            photo = request.FILES.get("space_photo")
            if photo and photo.size > 10 * 1024 * 1024:
                raise ValueError("הקובץ גדול מ־10MB")
            if photo and photo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise ValueError("סוג הקובץ אינו תמונה נתמכת")
            quote_request = QuoteRequest.objects.create(
                name=data["name"], phone=data["phone"], email=data.get("email", ""), city=data.get("city", ""),
                width=data["width"], length=data["length"], pergola_type=data["pergola_type"], roof_type=data["roof_type"],
                color=data["color"], lighting="lighting" in data,
                space_photo=photo,
            )
        except (KeyError, ValueError):
            return render(request, "planner/configurator.html", {"site": site_settings(), "error": "נא למלא את כל שדות החובה בצורה תקינה."})
        for business in Business.objects.filter(is_active=True, categories__slug="pergolas").distinct():
            invitation = QuoteInvitation.objects.create(request=quote_request, business=business)
            offer_url = request.build_absolute_uri(reverse("offer", args=[invitation.token]))
            send_mail(
                "בקשה חדשה להצעת מחיר לפרגולה",
                f"שלום {business.name},\n\nנכנסה בקשה חדשה לתמחור פרגולה.\nלקוח: {quote_request.name}\nמידות: {quote_request.width}×{quote_request.length} מ׳\n\nלהגשת הצעה: {offer_url}",
                None,
                [business.email],
                fail_silently=True,
            )
        return redirect("thanks")
    return render(request, "planner/configurator.html", {"site": site_settings()})


def home(request):
    return render(request, "planner/home.html", chat_context())


def experts(request):
    return render(request, "planner/experts.html", {"site": site_settings(), "experts": ExpertProfile.objects.filter(is_featured=True).select_related("business").prefetch_related("projects")})


def content_page(request, slug):
    page = get_object_or_404(ContentPage, slug=slug, is_published=True)
    return render(request, "planner/content_page.html", {"page": page})


def thanks(request):
    return render(request, "planner/thanks.html")


def offer(request, token):
    invitation = get_object_or_404(QuoteInvitation, token=token)
    if invitation.completed:
        return render(request, "planner/offer_done.html")
    if request.method == "POST":
        try:
            price = int(request.POST["price"])
            if price < 1:
                raise ValueError
        except (KeyError, ValueError):
            return render(request, "planner/offer.html", {"invitation": invitation, "error": "נא להזין מחיר תקין."})
        BusinessOffer.objects.create(invitation=invitation, price=price, message=request.POST.get("message", ""))
        invitation.completed = True
        invitation.save(update_fields=["completed"])
        return redirect("offer_thanks")
    return render(request, "planner/offer.html", {"invitation": invitation})


def offer_thanks(request):
    return render(request, "planner/offer_done.html")


def services(request):
    return render(request, "planner/services.html", {"categories": ServiceCategory.objects.filter(is_active=True)})


def business_signup(request):
    categories = ServiceCategory.objects.filter(is_active=True)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        name = request.POST.get("business_name", "").strip()
        email = request.POST.get("email", "").strip()
        selected = request.POST.getlist("categories")
        if not (username and password and name and email and selected) or User.objects.filter(username=username).exists():
            return render(request, "planner/business_signup.html", {"categories": categories, "error": "נא למלא את כל השדות. שם המשתמש חייב להיות ייחודי."})
        user = User.objects.create_user(username=username, password=password, email=email)
        business = Business.objects.create(name=name, email=email, owner=user)
        business.categories.set(categories.filter(id__in=selected))
        login(request, user)
        return redirect("business_dashboard")
    return render(request, "planner/business_signup.html", {"categories": categories})


def _business_for_user(request):
    return get_object_or_404(Business, owner=request.user, is_active=True)


@login_required
def business_dashboard(request, link_form=None):
    business = _business_for_user(request)
    general_requests = eligible_general_requests(business).filter(status=GeneralRequest.STATUS_OPEN).exclude(offers__business=business, offers__status="לא מעוניין").select_related("category")
    links = list(business.client_links.select_related("category").annotate(request_count=Count("requests")).order_by("-created_at"))
    for link in links:
        link.share_url = request.build_absolute_uri(reverse("client_request", args=[link.token]))
    return render(request, "planner/business_dashboard.html", {
        "business": business,
        "links": links,
        "link_form": link_form or ClientLinkForm(business=business),
        "service_requests": ServiceRequest.objects.filter(link__business=business).exclude(status__in=["בוצע", "לא מעוניין"]).select_related("link__category").prefetch_related("measurement_images"),
        "general_requests": general_requests,
        "direct_offers": DirectOffer.objects.filter(request__link__business=business).select_related("request"),
        "general_offers": GeneralOffer.objects.filter(business=business).select_related("request"),
    })


@login_required
def create_client_link(request):
    business = _business_for_user(request)
    if request.method == "POST":
        form = ClientLinkForm(request.POST, business=business)
        if not form.is_valid():
            return business_dashboard(request, link_form=form)
        link = form.save(commit=False)
        link.business = business
        link.save()
        messages.success(request, f"הקישור האישי עבור {link.customer_name} נוצר. אפשר להעתיק ולשלוח ללקוח.")
    return redirect("business_dashboard")


def client_request(request, token):
    return client_chat(request, token)


def category_options(slug):
    values = {
        "pergolas": {"type": ["אלומיניום", "עץ", "ביוקלימטית", "תיקון פרגולה"], "style": ["שלבים מתכווננים", "פוליקרבונט", "בד הצללה", "עדיין לא בטוח/ה"], "extras": ["תאורה", "סגירת צד", "מרזב", "הצללה חשמלית"]},
        "kitchens": {"type": ["מטבח חדש", "שיפוץ מטבח", "החלפת חזיתות", "נגרות משלימה"], "style": ["מודרני", "כפרי", "קלאסי", "עדיין לא בטוח/ה"], "extras": ["אי למטבח", "שיש", "ארונות גבוהים", "תאורה"]},
        "plumbing": {"type": ["נזילה", "פתיחת סתימה", "התקנת כלים סניטריים", "צנרת חדשה"], "style": ["תיקון נקודתי", "שדרוג חדר רחצה", "בדיקת איתור נזילה", "אחר"], "extras": ["הגעה דחופה", "מצלמת ביוב", "החלפת ברז", "איטום"]},
        "electricity": {"type": ["תיקון תקלה", "נקודות חשמל", "לוח חשמל", "תאורה"], "style": ["דירה", "בית פרטי", "עסק", "חוץ"], "extras": ["חשמל חכם", "עמדת טעינה", "גופי תאורה", "אישור חשמלאי"]},
        "renovations": {"type": ["שיפוץ מלא", "חדר רחצה", "צביעה וגבס", "ריצוף"], "style": ["דירה", "בית פרטי", "משרד", "חנות"], "extras": ["הריסה ופינוי", "עיצוב פנים", "נגרות", "ניקיון אחרי שיפוץ"]},
    }
    category = ServiceCategory.objects.filter(slug=slug).first()
    if category and any([category.work_types, category.styles, category.extras]):
        split = lambda text: [line.strip() for line in text.splitlines() if line.strip()]
        return {"type": split(category.work_types) or ["עבודה חדשה", "תיקון", "שדרוג"], "style": split(category.styles) or ["סטנדרטי"], "extras": split(category.extras)}
    return values.get(slug, {"type": ["עבודה חדשה", "תיקון", "שדרוג"], "style": ["סטנדרטי"], "extras": []})


def request_configuration(request):
    return json.dumps({"סוג עבודה": request.POST.get("service_type", ""), "סגנון/פתרון": request.POST.get("style", ""), "תוספות": request.POST.getlist("extras")}, ensure_ascii=False)


def measurement_data(request):
    return {
        "estimated_width": request.POST.get("estimated_width") or None,
        "estimated_length": request.POST.get("estimated_length") or None,
        "estimated_height": request.POST.get("estimated_height") or None,
        "measurement_method": request.POST.get("measurement_method", "צילום והזנה ידנית"),
        "measurement_confidence": "הערכה ראשונית לפי תמונות",
    }


def save_measurement_images(request, **relations):
    for image in request.FILES.getlist("measurement_photos"):
        if image.content_type in {"image/jpeg", "image/png", "image/webp"} and image.size <= 10 * 1024 * 1024:
            MeasurementImage.objects.create(image=image, **relations)


def offer_measurements(request):
    return {
        "confirmed_width": request.POST.get("confirmed_width") or None,
        "confirmed_length": request.POST.get("confirmed_length") or None,
        "confirmed_height": request.POST.get("confirmed_height") or None,
    }


def category_request(request, slug):
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    tips = {
        "kitchens": "ציינו מידות קיר, סגנון מועדף ומוצרי חשמל קיימים.",
        "plumbing": "ציינו היכן הבעיה, מתי התחילה והאם מדובר במקרה דחוף.",
        "electricity": "ציינו מה נדרש וכמה נקודות/חדרים מעורבים.",
        "renovations": "ציינו אילו חדרים לשיפוץ, גודל משוער ומועד רצוי.",
        "pergolas": "ציינו מידות, סוג החצר וצפו באשף הפרגולות לתכנון מפורט.",
    }
    options = category_options(slug)
    tip = category.request_tip or tips.get(slug, "")
    if request.method == "POST":
        return receive_intake(request, category=category)
    return render(request, "planner/category_request.html", {"category": category, "tip": tip, "options": options})


def _quote_workspace(request, business, item, kind):
    model = DirectOffer if kind == "direct" else GeneralOffer
    lookup = {"request": item}
    if kind == "general":
        lookup["business"] = business
    existing = model.objects.filter(**lookup).first()
    closed = item.status in {"בוצע", "לא מעוניין", GeneralRequest.STATUS_AWARDED}
    fields = ("price", "message", "confirmed_width", "confirmed_length", "confirmed_height")
    initial = {field: getattr(existing, field) for field in fields} if existing else {}
    form = QuoteForm(request.POST if request.method == "POST" else None, request.FILES or None, initial=initial)
    if request.method == "POST" and not closed and form.is_valid():
        defaults = dict(form.cleaned_data)
        if not defaults.get("visualization"):
            defaults.pop("visualization", None)
        defaults["status"] = "הצעה נשלחה"
        offer, _ = model.objects.update_or_create(**lookup, defaults=defaults)
        if kind == "direct":
            item.status = "הצעה נשלחה"
            item.save(update_fields=["status"])
        delivered = send_customer_offer_email(request, offer, kind == "general")
        if delivered:
            messages.success(request, "ההצעה נשמרה והקישור נשלח במייל ללקוח.")
        else:
            messages.warning(request, "ההצעה נשמרה. לא נשלח מייל חיצוני; אפשר להעתיק את קישור ההצעה מהפאנל ולשלוח ללקוח.")
        return redirect("business_dashboard")
    try:
        configuration = json.loads(item.configuration or "{}")
    except (ValueError, TypeError):
        configuration = {}
    return render(request, "planner/offer_workspace.html", {
        "item": item, "kind": kind, "business": business, "quote_form": form,
        "existing_offer": existing, "closed": closed, "configuration": configuration,
    })


@login_required
def business_request(request, pk):
    business = _business_for_user(request)
    item = get_object_or_404(ServiceRequest.objects.select_related("link__category"), pk=pk, link__business=business)
    return _quote_workspace(request, business, item, "direct")


@login_required
def general_offer(request, pk):
    business = _business_for_user(request)
    allowed = GeneralRequest.objects.filter(
        Q(pk__in=eligible_general_requests(business).values("pk"), status=GeneralRequest.STATUS_OPEN)
        | Q(offers__business=business)
    )
    item = get_object_or_404(allowed.distinct(), pk=pk)
    return _quote_workspace(request, business, item, "general")


def send_customer_offer_email(request, offer, is_general):
    customer = offer.request
    route = "public_general_offer" if is_general else "public_direct_offer"
    offer_url = request.build_absolute_uri(reverse(route, args=[offer.token]))
    business = offer.business if is_general else customer.link.business
    return send_notification(
        f"הצעת מחיר מ־{business.name}",
        f"שלום {customer.name},\n\nקיבלת הצעת מחיר מ־{business.name}.\nלצפייה בהצעה: {offer_url}\n\nליצירת קשר: {business.phone or business.email}",
        customer.email,
    )


def public_direct_offer(request, token):
    offer = get_object_or_404(DirectOffer, token=token)
    return render(request, "planner/public_offer.html", {"offer": offer, "business": offer.request.link.business, "customer": offer.request, "kind": "direct"})


def public_general_offer(request, token):
    offer = get_object_or_404(GeneralOffer, token=token)
    return render(request, "planner/public_offer.html", {"offer": offer, "business": offer.business, "customer": offer.request, "kind": "general"})


@login_required
def update_offer_status(request, offer_type, token, status):
    business = _business_for_user(request)
    if request.method != "POST" or status not in {"בוצע", "לא מעוניין"}:
        return redirect("business_dashboard")
    if offer_type == "general":
        offer = get_object_or_404(GeneralOffer, token=token, business=business)
        offer.status = status
        offer.save(update_fields=["status"])
        if status == "בוצע":
            offer.request.status = GeneralRequest.STATUS_AWARDED
            offer.request.awarded_business = business
            offer.request.save(update_fields=["status", "awarded_business"])
    else:
        offer = get_object_or_404(DirectOffer, token=token, request__link__business=business)
        offer.status = status
        offer.save(update_fields=["status"])
        offer.request.status = status
        offer.request.save(update_fields=["status"])
    return redirect("business_dashboard")
