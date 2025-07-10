"""
URL configuration for config project.

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
# Import necessary modules
from django.contrib import admin
from django.urls import path,include
from authentification.views import *  
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

urlpatterns = [
    
    path('', home, name="recipes"),        
    path('home/', home, name='home'),      
    path("admin/", admin.site.urls),       
    path('login/', login_view, name='login_page'),  
    path('register/', register_page, name='register'), 
    path('logout/', logout_view, name='logout'),
    path('account/', account_view, name='account'), 
    path('delete-account/confirm/', delete_account, name='delete_account_confirm'),
    path('delete-account/', delete_account_confirmation, name='delete_account'),
    path('download-article/<int:article_id>/', download_article, name='download_article'),
    path('generate-article/', generate_article, name='generate_article'),
    path('view-article/<int:article_id>/', view_article, name='view_article'),
    path('translate_word/', translate_word, name='translate_word'),
    path('translate_simple/', translate_simple, name='translate_simple'),
    path('update_article_content/', update_article_content, name='update_article_content'),
    path('detect/', detect_language, name='detect_language'),
    path('article_history/', article_history_view, name='article_history'),
    path('articles/<int:article_id>/delete/', article_delete_view, name='article_delete'),
    path('articles/edit/<int:article_id>/', edit_article, name='edit_article'),
    path('article/<int:article_id>/', view_article, name='view_article'),
    path('tinymce/', include('tinymce.urls')),
    path('auth/', include('social_django.urls', namespace='social')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
