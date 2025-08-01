"""
URL configuration for familybusiness project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.shortcuts import redirect
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

urlpatterns = [
    path('i18n/setlang/', set_language, name='set_language'),
    path('', lambda request: redirect('home/', permanent=False), name='home'),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('home/', include('home.urls')),
    path('account/', include('account.urls')),
    path('wallet/', include('wallet.urls')),
    path('adminpanel/', include('adminpanel.urls'))
)
