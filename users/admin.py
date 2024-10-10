from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Referral, Friendship, OTP

class UserAdmin(BaseUserAdmin):
    list_display = ('phone_number', 'email', 'profile_name', 'is_verified', 'is_staff')
    search_fields = ('phone_number', 'email', 'profile_name')
    ordering = ('phone_number',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('profile_name', 'email', 'profile_picture')}),
        ('Permissions', {'fields': ('is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'profile_name', 'email', 'password1', 'password2'),
        }),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Referral)
admin.site.register(Friendship)
admin.site.register(OTP)