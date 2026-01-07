from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    #path('admin/', admin.site.urls),
    path("api/", include("api.urls")),
    path("accounts/", include("allauth.urls")),
    path("logout/", RedirectView.as_view(url="/accounts/logout/", permanent=False)),
    path("", RedirectView.as_view(url="/accounts/login/", permanent=False)),
]
