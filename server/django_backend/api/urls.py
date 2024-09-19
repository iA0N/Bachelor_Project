from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path('v1/highlight_pdf', views.highlight_pdf, name="highlight_pdf"),
]
