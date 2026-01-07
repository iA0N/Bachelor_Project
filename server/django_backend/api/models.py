from django.db import models

from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to user
    file_name = models.CharField(max_length=255)
    file_data = models.BinaryField()  # Store PDF as BLOB in DB
    content_type = models.CharField(max_length=255)
    summary = models.JSONField(blank=True, null=True)  # Store summary
    uploaded_at = models.DateTimeField(auto_now_add=True)
    chat_history = models.TextField(blank=True, null=True)
    used_model = models.CharField(max_length=255, default="")

class UserAIModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    repo_id = models.CharField(max_length=255, default="")
    filename = models.CharField(max_length=255, default="")
