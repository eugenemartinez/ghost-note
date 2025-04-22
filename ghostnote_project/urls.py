"""
URL configuration for ghostnote_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# Remove RedirectView and reverse_lazy imports if no longer needed elsewhere
# from django.views.generic.base import RedirectView
# from django.urls import reverse_lazy
from notes import views as notes_views # Import the views from the notes app

urlpatterns = [
    path('admin/', admin.site.urls),
    # Any URL starting with 'notes/' will be handled by notes/urls.py
    path('notes/', include('notes.urls')),
    # Map the root URL ('/') to the landing_page_view
    path('', notes_views.landing_page_view, name='home'),
]
