from django.db import models

from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to user
    file_name = models.CharField(max_length=255)
    file_data = models.TextField()  # Store PDF as BLOB in DB
    summary = models.TextField(blank=True, null=True)  # Store summary
    uploaded_at = models.DateTimeField(auto_now_add=True)
    chat_history = models.TextField(blank=True, null=True)
