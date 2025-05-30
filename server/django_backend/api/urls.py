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
]
