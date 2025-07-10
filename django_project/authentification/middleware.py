from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class AuthenticationMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # List of paths that don't require authentication
        public_paths = [
            '/login/',
            '/register/',
            '/static/',
            '/media/',
            '/admin/login/',
            '/',
        ]
        
        # Check if the current path is public
        is_public_path = any(request.path.startswith(path) for path in public_paths)
        
        # If user is authenticated and in article_history, prevent back navigation
        if request.user.is_authenticated and request.path.startswith('/article_history/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['X-Frame-Options'] = 'DENY'
            return response
        
        # If user is authenticated and trying to access login page, redirect to article_history
        if request.user.is_authenticated and request.path.startswith('/login/'):
            return redirect('article_history')
        
        # Only redirect to login if:
        # 1. User is not authenticated
        # 2. Path is not public
        # 3. Not accessing static/media files
        # 4. Not already on the login page
        if (not request.user.is_authenticated and 
            not is_public_path and 
            request.path != reverse('login_page')):
            
            # Store the current path in session for redirect after login
            request.session['next'] = request.path
            return redirect('login_page')
        
        return response 