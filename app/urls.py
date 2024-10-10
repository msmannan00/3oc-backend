from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/friends/', include('friendship.urls')),  # Include friendship-related URLs
    # path('', include('IRL.urls')),
    path('api/users/', include('users.urls')),

]
