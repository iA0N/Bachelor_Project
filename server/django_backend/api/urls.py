from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    path('v1/get_highlighted_pdf', views.get_highlighted_pdf, name="get_highlighted_pdf"),
    path('v1/username', views.get_username, name="get_username"),
    path('v1/store_and_summarize', views.store_and_summarize_document, name="store_and_summarize"),
    path('v1/get_user_documents', views.get_user_documents, name="get_user_documents"),
    path('v1/get_user_document/<int:doc_id>', views.get_user_document, name="get_user_documents"),
    path('v1/delete_user_document/<int:doc_id>', views.delete_user_document, name="delete_user_document"),
    path('v1/send_chat', views.send_chat, name="send_chat"),
    path('v1/csrf', views.get_csrf_token, name="csrf"),
    path('v1/login_status', views.get_login_status, name="get_login_status"),
    path('v1/get_user_models', views.get_user_models, name="get_user_models"),
    path('v1/create_user_model', views.create_user_model, name="create_user_model"),
    path('v1/remove_user_model/<str:model>', views.remove_user_model, name="remove_user_model"),
]
