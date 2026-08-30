from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from planner.views import business_dashboard, business_request, business_signup, category_request, client_request, configurator, content_page, create_client_link, experts, general_offer, home, offer, offer_thanks, public_direct_offer, public_general_offer, services, thanks, update_offer_status

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("פרגולות/", configurator, name="configurator"),
    path("תודה/", thanks, name="thanks"),
    path("הצעה/<uuid:token>/", offer, name="offer"),
    path("הצעה/תודה/", offer_thanks, name="offer_thanks"),
    path("שירותים/", services, name="services"),
    path("שירותים/<slug:slug>/", category_request, name="category_request"),
    path("מומחים/", experts, name="experts"),
    path("עמודים/<slug:slug>/", content_page, name="content_page"),
    path("לעסקים/הרשמה/", business_signup, name="business_signup"),
    path("לעסקים/כניסה/", auth_views.LoginView.as_view(template_name="planner/business_login.html"), name="business_login"),
    path("לעסקים/יציאה/", auth_views.LogoutView.as_view(next_page="business_login"), name="business_logout"),
    path("לעסקים/", business_dashboard, name="business_dashboard"),
    path("לעסקים/קישור-חדש/", create_client_link, name="create_client_link"),
    path("לקוח/<uuid:token>/", client_request, name="client_request"),
    path("לעסקים/בקשה/<int:pk>/", business_request, name="business_request"),
    path("לעסקים/בקשה-כללית/<int:pk>/", general_offer, name="general_offer"),
    path("הצעה/לקוח/<uuid:token>/", public_direct_offer, name="public_direct_offer"),
    path("הצעה/כללית/<uuid:token>/", public_general_offer, name="public_general_offer"),
    path("לעסקים/סטטוס/<str:offer_type>/<uuid:token>/<str:status>/", update_offer_status, name="update_offer_status"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
