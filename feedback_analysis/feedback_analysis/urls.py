from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin_django/', admin.site.urls),
    path('', include('feedback.urls')),
    path('', RedirectView.as_view(url='/admin_django/', permanent=False)),
]