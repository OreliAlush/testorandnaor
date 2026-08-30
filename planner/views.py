import json
from django.core.mail import send_mail
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Business, BusinessOffer, ClientRequestLink, ContentPage, DirectOffer, ExpertProfile, GeneralOffer, GeneralRequest, QuoteInvitation, QuoteRequest, ServiceCategory, ServiceRequest, SiteSettings


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
    return render(request, "planner/home.html", {"categories": ServiceCategory.objects.filter(is_active=True), "site": site_settings(), "menu_pages": ContentPage.objects.filter(is_published=True, show_in_menu=True)})


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
    return get_object_or_404(Business, owner=request.user)


@login_required
def business_dashboard(request):
    business = _business_for_user(request)
    general_requests = GeneralRequest.objects.filter(status=GeneralRequest.STATUS_OPEN, category__in=business.categories.all()).filter(Q(invited_businesses__isnull=True) | Q(invited_businesses=business)).distinct()
    return render(request, "planner/business_dashboard.html", {
        "business": business,
        "links": business.client_links.all(),
        "service_requests": ServiceRequest.objects.filter(link__business=business),
        "general_requests": general_requests,
        "direct_offers": DirectOffer.objects.filter(request__link__business=business).select_related("request"),
        "general_offers": GeneralOffer.objects.filter(business=business).select_related("request"),
    })


@login_required
def create_client_link(request):
    business = _business_for_user(request)
    if request.method == "POST":
        category = get_object_or_404(business.categories, id=request.POST.get("category"))
        ClientRequestLink.objects.create(business=business, category=category, label=request.POST.get("label", "קישור ללקוחות"))
    return redirect("business_dashboard")


def client_request(request, token):
    link = get_object_or_404(ClientRequestLink, token=token, is_active=True, business__is_active=True)
    options = category_options(link.category.slug)
    if request.method == "POST":
        photo = request.FILES.get("photo")
        if photo and (photo.size > 10 * 1024 * 1024 or photo.content_type not in {"image/jpeg", "image/png", "image/webp"}):
            return render(request, "planner/client_request.html", {"link": link, "options": options, "error": "נא להעלות תמונת JPG, PNG או WEBP עד 10MB."})
        ServiceRequest.objects.create(link=link, name=request.POST["name"], phone=request.POST["phone"], email=request.POST.get("email", ""), city=request.POST.get("city", ""), address=request.POST.get("address", ""), description=request.POST["description"], work_area=request.POST.get("work_area") or None, budget=request.POST.get("budget") or None, preferred_date=request.POST.get("preferred_date") or None, urgency=request.POST.get("urgency", "רגיל"), configuration=request_configuration(request), photo=photo)
        return render(request, "planner/client_request_done.html", {"business": link.business})
    return render(request, "planner/client_request.html", {"link": link, "options": options})


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
        photo = request.FILES.get("photo")
        if photo and (photo.size > 10 * 1024 * 1024 or photo.content_type not in {"image/jpeg", "image/png", "image/webp"}):
            return render(request, "planner/category_request.html", {"category": category, "tip": tip, "options": options, "error": "נא להעלות תמונת JPG, PNG או WEBP עד 10MB."})
        GeneralRequest.objects.create(category=category, name=request.POST["name"], phone=request.POST["phone"], email=request.POST.get("email", ""), city=request.POST.get("city", ""), address=request.POST.get("address", ""), description=request.POST["description"], work_area=request.POST.get("work_area") or None, budget=request.POST.get("budget") or None, preferred_date=request.POST.get("preferred_date") or None, urgency=request.POST.get("urgency", "רגיל"), configuration=request_configuration(request), photo=photo)
        count = Business.objects.filter(is_active=True, categories=category).distinct().count()
        return render(request, "planner/category_request_done.html", {"category": category, "count": count})
    return render(request, "planner/category_request.html", {"category": category, "tip": tip, "options": options})


@login_required
def business_request(request, pk):
    business = _business_for_user(request)
    service_request = get_object_or_404(ServiceRequest, pk=pk, link__business=business)
    if request.method == "POST":
        try:
            price = int(request.POST["price"])
            if price < 1:
                raise ValueError
        except (KeyError, ValueError):
            return render(request, "planner/business_request.html", {"service_request": service_request, "error": "נא להזין מחיר תקין."})
        offer, _ = DirectOffer.objects.update_or_create(request=service_request, defaults={"price": price, "message": request.POST.get("message", ""), "status": "הצעה נשלחה"})
        service_request.status = "הצעה נשלחה"
        service_request.save(update_fields=["status"])
        send_customer_offer_email(request, offer, False)
        return redirect("business_dashboard")
    return render(request, "planner/business_request.html", {"service_request": service_request})


@login_required
def general_offer(request, pk):
    business = _business_for_user(request)
    general_request = get_object_or_404(GeneralRequest, pk=pk, status=GeneralRequest.STATUS_OPEN)
    eligible = general_request.category in business.categories.all() and (not general_request.invited_businesses.exists() or general_request.invited_businesses.filter(pk=business.pk).exists())
    if not eligible:
        return redirect("business_dashboard")
    if request.method == "POST":
        try:
            price = int(request.POST["price"])
            if price < 1:
                raise ValueError
        except (KeyError, ValueError):
            return render(request, "planner/general_offer.html", {"general_request": general_request, "error": "נא להזין מחיר תקין."})
        offer, _ = GeneralOffer.objects.update_or_create(request=general_request, business=business, defaults={"price": price, "message": request.POST.get("message", ""), "status": "הצעה נשלחה"})
        send_customer_offer_email(request, offer, True)
        return redirect("business_dashboard")
    return render(request, "planner/general_offer.html", {"general_request": general_request})


def send_customer_offer_email(request, offer, is_general):
    customer = offer.request
    if not customer.email:
        return
    route = "public_general_offer" if is_general else "public_direct_offer"
    offer_url = request.build_absolute_uri(reverse(route, args=[offer.token]))
    business = offer.business if is_general else customer.link.business
    send_mail(
        f"הצעת מחיר מ־{business.name}",
        f"שלום {customer.name},\n\nקיבלת הצעת מחיר מ־{business.name}.\nלצפייה בהצעה: {offer_url}\n\nליצירת קשר: {business.phone or business.email}",
        None,
        [customer.email],
        fail_silently=True,
    )


def public_direct_offer(request, token):
    offer = get_object_or_404(DirectOffer, token=token)
    return render(request, "planner/public_offer.html", {"offer": offer, "business": offer.request.link.business, "customer": offer.request})


def public_general_offer(request, token):
    offer = get_object_or_404(GeneralOffer, token=token)
    return render(request, "planner/public_offer.html", {"offer": offer, "business": offer.business, "customer": offer.request})


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
