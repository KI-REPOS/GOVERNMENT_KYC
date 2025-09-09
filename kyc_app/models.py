# backend/kyc_app/models.py
import uuid
import base64
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    gov_id = models.CharField(max_length=20, unique=True)
    # We'll store minimal data in SQLite, most data in MongoDB
    mongo_id = models.CharField(max_length=100, blank=True, null=True)
    
    @property
    def wallet_address(self):
        # Example: generate a fake wallet address based on gov_id
        return f"WALLET-{self.gov_id}"

    def __str__(self):
        return f"{self.gov_id} - {self.first_name} {self.last_name}"

class APIToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=3)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.gov_id} - {self.id} - {'Valid' if self.is_valid() else 'Expired'}"