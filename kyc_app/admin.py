# backend/kyc_app/admin.py
from django.contrib import admin
from .models import User, APIToken

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('gov_id', 'first_name', 'last_name', 'email', 'wallet_address')
    search_fields = ('gov_id', 'first_name', 'last_name', 'email')

@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'expires_at', 'used', 'is_valid')
    list_filter = ('used', 'created_at')
    search_fields = ('user__gov_id', 'user__first_name', 'user__last_name')