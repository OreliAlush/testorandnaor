import base64
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Business, ClientRequestLink, DirectOffer, GeneralOffer, GeneralRequest, MeasurementImage, ServiceCategory, ServiceRequest


PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aN1sAAAAASUVORK5CYII=")


def photo(name="project.png"):
    return SimpleUploadedFile(name, PNG, content_type="image/png")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class IntakeFlowTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory(prefix="orpro-test-media-")
        self.addCleanup(self.media.cleanup)
        self.storage_override = override_settings(MEDIA_ROOT=self.media.name)
        self.storage_override.enable()
        self.addCleanup(self.storage_override.disable)
        self.category = ServiceCategory.objects.get_or_create(slug="renovations", defaults={"name": "שיפוצים"})[0]
        self.unrelated = ServiceCategory.objects.get_or_create(slug="electricity", defaults={"name": "חשמל"})[0]
        User = get_user_model()
        self.owner = User.objects.create_user("owner-test", password="test-password-only")
        self.other_owner = User.objects.create_user("other-owner-test", password="test-password-only")
        self.admin = User.objects.create_superuser("admin-test", "admin@example.test", "test-password-only")
        self.business = Business.objects.create(name="עסק בדיקה", email="business@example.test", owner=self.owner)
        self.business.categories.add(self.category)
        self.other = Business.objects.create(name="עסק נוסף", email="other@example.test", owner=self.other_owner)
        self.other.categories.add(self.unrelated)
        self.link = ClientRequestLink.objects.create(business=self.business, category=self.category, customer_name="דנה בדיקה", label="שיפוץ המטבח")

    def payload(self, **changes):
        data = {"name": "דנה בדיקה", "phone": "0500000000", "email": "client@example.test", "city": "חיפה", "description": "שיפוץ המטבח והחלפת ארונות", "category": self.category.slug, "submission_id": str(uuid.uuid4()), "estimated_width": "", "estimated_length": "", "estimated_height": ""}
        data.update(changes)
        return data

    def submit(self, *, direct=False, data=None):
        route = reverse("client_request", args=[self.link.token]) if direct else reverse("assistant_submit")
        return self.client.post(route, data or self.payload(), HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_general_request_without_dimensions_or_photos(self):
        response = self.submit()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        request = GeneralRequest.objects.get(pk=response.json()["requestId"])
        self.assertIsNone(request.estimated_width)
        self.assertEqual(request.measurement_confidence, "לא נמסרו מידות")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.business.email])
        self.client.force_login(self.owner)
        dashboard = self.client.get(reverse("business_dashboard"))
        self.assertContains(dashboard, reverse("general_offer", args=[request.pk]))
        self.client.force_login(self.other_owner)
        self.assertNotContains(self.client.get(reverse("business_dashboard")), "דנה בדיקה")
        self.assertEqual(self.client.get(reverse("general_offer", args=[request.pk])).status_code, 404)

    def test_personalized_link_creation_and_full_direct_round_trip(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("create_client_link"), {"customer_name": "יובל בדיקה", "label": "פרויקט יובל", "category": self.category.pk})
        self.assertEqual(response.status_code, 302)
        self.link = ClientRequestLink.objects.get(customer_name="יובל בדיקה")
        dashboard = self.client.get(reverse("business_dashboard"))
        self.assertContains(dashboard, str(self.link.token))
        self.client.logout()
        page = self.client.get(reverse("client_request", args=[self.link.token]))
        self.assertContains(page, "יובל בדיקה")
        self.assertEqual(page.context["assistant_config"]["submitUrl"], reverse("client_request", args=[self.link.token]))
        photos = [photo(f"angle-{i}.png") for i in range(4)]
        response = self.submit(direct=True, data=self.payload(name="יובל בדיקה", measurement_photos=photos, photo_captions=["מבט כללי", "צד ימין", "צד שמאל", "תקריב"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(GeneralRequest.objects.count(), 0)
        request = ServiceRequest.objects.get()
        self.assertEqual(request.link.business, self.business)
        self.assertEqual(request.measurement_images.count(), 4)
        self.assertEqual(request.measurement_images.first().caption, "מבט כללי")
        self.assertEqual(mail.outbox[-1].to, [self.business.email])
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse("business_dashboard")), "פרויקט יובל")
        detail = self.client.get(reverse("business_request", args=[request.pk]))
        self.assertContains(detail, "שיפוץ המטבח")
        self.assertContains(detail, "מבט כללי")
        url = reverse("request_photo", args=["direct", request.pk, request.measurement_images.first().pk])
        with override_settings(DEBUG=False):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), PNG)
        response = self.client.post(reverse("business_request", args=[request.pk]), {"price": "1200", "message": "כולל עבודה וחומרים", "visualization": photo("preview.png")})
        self.assertEqual(response.status_code, 302)
        offer = DirectOffer.objects.get()
        self.assertIn(str(offer.token), mail.outbox[-1].body)
        self.assertEqual(mail.outbox[-1].to, ["client@example.test"])
        self.client.logout()
        response = self.client.get(reverse("public_direct_offer", args=[offer.token]))
        self.assertContains(response, "1200")
        self.assertContains(response, "כולל עבודה וחומרים")
        with override_settings(DEBUG=False):
            image = self.client.get(reverse("offer_image", args=["direct", offer.token]))
            self.assertEqual(image.status_code, 200)
            self.assertEqual(b"".join(image.streaming_content), PNG)
        self.client.force_login(self.other_owner)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(reverse("business_request", args=[request.pk])).status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("admin:planner_servicerequest_change", args=[request.pk])).status_code, 200)

    def test_bad_dimensions_do_not_crash_or_save_partial_request(self):
        for value in ["undefined", "NaN", "Infinity", "-4", "9999999"]:
            with self.subTest(value=value):
                response = self.submit(data=self.payload(estimated_width=value))
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json()["ok"])
        self.assertEqual(GeneralRequest.objects.count(), 0)

    def test_missing_required_fields_and_bad_email(self):
        for change in [{"name": ""}, {"phone": "abc"}, {"email": "broken"}, {"description": ""}]:
            response = self.submit(data=self.payload(**change))
            self.assertEqual(response.status_code, 400)
        self.assertEqual(GeneralRequest.objects.count(), 0)

    def test_duplicate_submit_is_idempotent(self):
        data = self.payload()
        first = self.submit(direct=True, data=data)
        second = self.submit(direct=True, data=data)
        self.assertEqual(first.json()["requestId"], second.json()["requestId"])
        self.assertEqual(ServiceRequest.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_image_rejects_entire_request(self):
        invalid = SimpleUploadedFile("fake.png", b"<html>bad</html>", content_type="image/png")
        response = self.submit(data=self.payload(measurement_photos=[photo(), invalid]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GeneralRequest.objects.count(), 0)
        self.assertEqual(MeasurementImage.objects.count(), 0)

    def test_storage_database_failure_rolls_back_and_retry_succeeds(self):
        identifier = str(uuid.uuid4())
        with patch.object(MeasurementImage, "save", side_effect=DatabaseError("simulated SQL failure")):
            response = self.submit(data=self.payload(submission_id=identifier, measurement_photos=[photo()]))
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["ok"])
        self.assertEqual(GeneralRequest.objects.count(), 0)
        self.assertFalse([p for p in Path(self.media.name).rglob("*") if p.is_file()])
        response = self.submit(data=self.payload(submission_id=identifier, measurement_photos=[photo()]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MeasurementImage.objects.count(), 1)

    def test_link_cannot_be_redirected_to_another_business(self):
        response = self.submit(direct=True, data=self.payload(business=self.other.pk, category=self.unrelated.slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ServiceRequest.objects.get().link.business, self.business)
        self.client.force_login(self.owner)
        self.client.post(reverse("create_client_link"), {"customer_name": "לקוח", "label": "בדיקה", "category": self.unrelated.pk})
        self.assertEqual(ClientRequestLink.objects.count(), 1)

    def test_disabled_link_and_business(self):
        self.link.is_active = False
        self.link.save()
        self.assertEqual(self.submit(direct=True).status_code, 404)
        self.business.is_active = False
        self.business.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("business_dashboard")).status_code, 404)

    def test_email_failure_does_not_lose_saved_request(self):
        with patch("planner.intake.send_mail", side_effect=OSError("SMTP unavailable")):
            response = self.submit(direct=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ServiceRequest.objects.count(), 1)

    def test_legacy_category_request_is_validated(self):
        response = self.client.post(reverse("category_request", args=[self.category.slug]), self.payload(estimated_width="undefined"))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(reverse("category_request", args=[self.category.slug]), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(GeneralRequest.objects.count(), 1)

    def test_general_quote_and_close(self):
        self.submit()
        request = GeneralRequest.objects.get()
        self.client.force_login(self.owner)
        response = self.client.post(reverse("general_offer", args=[request.pk]), {"price": "2000", "message": "הצעה כללית"})
        self.assertEqual(response.status_code, 302)
        offer = GeneralOffer.objects.get()
        self.assertEqual(self.client.get(reverse("public_general_offer", args=[offer.token])).status_code, 200)
        self.client.post(reverse("update_offer_status", args=["general", offer.token, "בוצע"]))
        request.refresh_from_db()
        self.assertEqual(request.awarded_business, self.business)
        self.assertEqual(request.status, GeneralRequest.STATUS_AWARDED)
        self.assertNotIn(request, self.client.get(reverse("business_dashboard")).context["general_requests"])

    def test_admin_assignment_overrides_category(self):
        self.submit()
        request = GeneralRequest.objects.get()
        request.invited_businesses.add(self.other)
        self.client.force_login(self.other_owner)
        self.assertEqual(self.client.get(reverse("general_offer", args=[request.pk])).status_code, 200)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("general_offer", args=[request.pk])).status_code, 404)

    def test_invalid_quote_dimensions_do_not_crash(self):
        self.submit(direct=True)
        request = ServiceRequest.objects.get()
        self.client.force_login(self.owner)
        response = self.client.post(reverse("business_request", args=[request.pk]), {"price": "1200", "confirmed_width": "undefined"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["quote_form"].errors)
        self.assertEqual(DirectOffer.objects.count(), 0)
