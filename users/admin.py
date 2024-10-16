# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TempUser, Tag

class CustomUserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'phone_number', 'is_verified', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('Personal Info', {'fields': ('name', 'display_picture')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_verified', 'is_superuser', 'groups', 'user_permissions')}),
        ('Tags', {'fields': ('tags',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'phone_number')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions', 'tags',)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(TempUser)
admin.site.register(Tag, TagAdmin)
