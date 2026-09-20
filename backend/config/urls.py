from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def home(request):
    return JsonResponse({
        "message": "Price Tracker API is running",
        "status": "ok",
    })


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("tracker.urls")),
]