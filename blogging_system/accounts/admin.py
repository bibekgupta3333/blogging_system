from django.contrib import admin
from .models import Profile, ResetToken


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ["user"]
    list_display = ["user", "phone"]


@admin.register(ResetToken)
class ResetTokenAdmin(admin.ModelAdmin):
    readonly_fields = ["token"]
    list_display = ["email", "created_date"]
    