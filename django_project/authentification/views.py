from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
import emoji
import requests
import json
import re
from .models import Language, Article
from .forms import ArticleForm
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.urls import reverse

from django.conf import settings
User = get_user_model()

def home(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    
    context = {
        'user_id': user_id,
        'username': username
    }
    return render(request, 'home.html', context)

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            request.session["username"] = username
            next_url = request.session.get('next', 'article_history')
            if 'next' in request.session:
                del request.session['next']

            response = HttpResponseRedirect(reverse(next_url))
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        else:
            return render(request, "login.html", {"error": "Invalid username or password."})

    return render(request, "login.html")

def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not all([first_name, last_name, username, email, password, confirm_password]):
            messages.error(request, "All fields are required!")
            return redirect('/register/')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('/register/')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('/register/')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use!")
            return redirect('/register/')

        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password
        )

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect('/login/')

    return render(request, 'register.html')

@never_cache
@login_required(login_url='/login/')
def logout_view(request):
    # Clear all session data
    request.session.flush()
    # Clear any existing cookies
    response = redirect('/login/')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    # Log the user out
    logout(request)
    messages.success(request, "Logged out successfully!")
    return response


@login_required
def account_view(request):
    return render(request, "account_info.html", {'User': request.user})

@login_required
def delete_account_confirmation(request):
    return render(request, 'delete_confirmation.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        return redirect('/')
    return redirect('delete_account')

def clean_text(text):
    """Clean text by removing emojis and unwanted special characters"""
    text = emoji.replace_emoji(text, replace='')

    text = re.sub(r'["*#`]', '', text)

    text = re.sub(r'\s+', ' ', text).strip()

    return text

@never_cache
@login_required(login_url=reverse_lazy('login_page'))
def generate_article(request):
    """View for the article generation form"""
    form = ArticleForm()
    
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            word = form.cleaned_data['word']
            subject = form.cleaned_data['subject']
            language = form.cleaned_data['language']
            
            prompt = f"Write a small article in {language} about {subject}, focusing on the word '{word}', and containing other words in other languages"

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"          
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }

            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                # Extract raw content from Gemini response
                raw_article_content = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No article found.')
                
                # Clean the content
                cleaned_article_content = clean_text(raw_article_content)

                # Save the article to the database
                article_obj = form.save(commit=False)
                article_obj.user = request.user
                article_obj.source_language = language
                article_obj.keyword = word
                article_obj.content = cleaned_article_content
                article_obj.save()
                
                messages.success(request, "Article generated successfully!")
                return redirect(f'/article/{article_obj.id}/?auto_edit=1')

            except requests.exceptions.RequestException as e:
                messages.error(request, f"Error generating article: {e}")
            except (KeyError, IndexError) as e:
                messages.error(request, f"Error parsing API response: {e}")
        else:
            messages.error(request, "Please correct the errors below.")

    return render(request, 'generator/generate_article.html', {'form': form})

@login_required
def article_delete_view(request, article_id):
    """
    View function for deleting an article
    """
    article = get_object_or_404(Article, id=article_id)
    
    if request.method == 'POST':
        # Store article information before deletion for messaging
        article_subject = article.subject
        
        article.delete()
        
        messages.success(request, _('Article "{}" was deleted successfully').format(article_subject[:30]))
        
        return redirect('article_history')
    
    # If this is a GET request, redirect to the article details page
    # This is to prevent accidental deletion by visiting the URL directly
    return redirect('article_detail', article_id=article.id)

@login_required(login_url="login_page")
def download_article(request, article_id):
    """View for downloading an article"""
    try:
        article = Article.objects.get(id=article_id, user=request.user)
        
        # Create a response with the article content
        response = HttpResponse(article.content, content_type='text/plain')
        
        # Set the filename for download - use the keyword as the filename basis
        filename = f"{article.keyword.replace(' ', '_')}_article.txt"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Article.DoesNotExist:
        messages.error(request, "Article not found.")
        return redirect('generate_article')

@login_required
def article_history_view(request):
    """
    View function for displaying the article history
    """
    # Get all articles ordered by modification date
    articles_list = Article.objects.all().order_by('-modifier_le')
    
    # Handle filtering
    keyword = request.GET.get('keyword', '')
    subject = request.GET.get('subject', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply filters if provided
    if keyword:
        articles_list = articles_list.filter(keyword__icontains=keyword)
    if subject:
        articles_list = articles_list.filter(subject__icontains=subject)
    if date_from:
        articles_list = articles_list.filter(créer_le__gte=date_from)
    if date_to:
        articles_list = articles_list.filter(créer_le__lte=date_to)
    
    # Pagination
    paginator = Paginator(articles_list, 10)  # Show 10 articles per page
    page = request.GET.get('page')
    
    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        articles = paginator.page(paginator.num_pages)
    
    context = {
        'articles': articles,
        'title': _('Article History'),
        'keyword': keyword,
        'subject': subject,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'article_history.html', context)


def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated successfully.")
            return redirect('article_history')  # or wherever you list articles
    else:
        form = ArticleForm(instance=article)

    return render(request, 'view_article.html', {'form': form, 'article': article})


@require_POST
@ensure_csrf_cookie
def translate_simple(request):
    """API endpoint to translate entities using FastAPI service"""
    try:
        # Parse the JSON data from frontend
        try:
            data = json.loads(request.body)
            print("Received request data:", data)  # Debug log
        except json.JSONDecodeError:
            print("Invalid JSON received:", request.body)  # Debug log
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        # Extract data - frontend sends: text, target_language, entities
        text = data.get('text', '').strip()
        target_language = data.get('target_language', 'en')
        entities = data.get('entities', [])
        
        print(f"Processing translation request - Text: {text}, Target: {target_language}, Entities: {entities}")  # Debug log
        
        if not text or not entities:
            print("Missing text or entities in request")  # Debug log
            return JsonResponse({'error': 'Missing text or entities'}, status=400)
        
        # Language mapping from your system to standard codes
        language_map = {
            'ar': 'arabic',
            'en': 'english', 
            'fr': 'french',
            'es': 'spanish',
            'it': 'italian',
            'de': 'german',
            'pt': 'portuguese',
            'cs': 'czech',
            'ja': 'japanese',
            'ko': 'korean',
            'pl': 'polish',
            'ru': 'russian',
            'zh': 'chinese',
            'hr': 'croatian',
            'et': 'estonian',
            'fi': 'finnish',
            'hu': 'hungarian',
            'nl': 'dutch',
            'sv': 'swedish',
            'no': 'norwegian',
            'da': 'danish',
            'ro': 'romanian',
            'bg': 'bulgarian',
            'sr': 'serbian',
            'sl': 'slovenian',
            'sk': 'slovak',
            'lt': 'lithuanian',
            'lv': 'latvian',
            'uk': 'ukrainian',
            'be': 'belarusian',
            'el': 'greek',
            'he': 'hebrew',
            'th': 'thai',
            'vi': 'vietnamese',
            'id': 'indonesian',
            'ms': 'malay',
            'ta': 'tamil',
            'bn': 'bengali',
            'gu': 'gujarati',
            'pa': 'punjabi',
            'ur': 'urdu',
            'fa': 'persian',
            'sw': 'swahili',
            'am': 'amharic',
            'yo': 'yoruba',
            'ig': 'igbo',
            'ha': 'hausa'
        }
        
        # Convert target language to full name for FastAPI
        target_lang_full = language_map.get(target_language.lower(), target_language.lower())
        print(f"Converted language code {target_language} to {target_lang_full}")  # Debug log
        
        # Prepare request for FastAPI
        fastapi_request = {
            "text": text,
            "target_language": target_lang_full,
            "entities": entities
        }
        print("Sending request to FastAPI:", fastapi_request)  # Debug log
        
        # Call FastAPI service
        try:
            response = requests.post(
                "http://127.0.0.1:8002/translate_simple/",
                json=fastapi_request,
                timeout=40,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"FastAPI response status: {response.status_code}")  # Debug log
            print(f"FastAPI response content: {response.text}")  # Debug log
            
            if response.status_code != 200:
                print(f"FastAPI error: {response.status_code}, {response.text}")
                return JsonResponse({
                    'error': f'Translation service returned status code: {response.status_code}',
                    'details': response.text
                }, status=500)
                
            # Parse the FastAPI response
            result = response.json()
            print("Parsed FastAPI response:", result)  # Debug log
            
            # For single word translation
            if len(entities) == 1 and 'translation_results' in result and result['translation_results']:
                first_result = result['translation_results'][0]
                response_data = {
                    'translation': first_result.get('translated_text', ''),
                    'translation_results': result.get('translation_results', []),
                    'success': result.get('success', True),
                    'message': result.get('message', '')
                }
                print("Sending response to frontend:", response_data)  # Debug log
                return JsonResponse(response_data)
            
            return JsonResponse(result)
            
        except requests.exceptions.ConnectionError:
            print("Cannot connect to FastAPI translation service")
            return JsonResponse({
                'error': 'Translation service unavailable. Please check if the FastAPI service is running on port 8002.'
            }, status=503)
            
        except requests.exceptions.Timeout:
            print("Translation service timed out")
            return JsonResponse({'error': 'Translation service timed out'}, status=504)
            
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            return JsonResponse({'error': f'Translation service error: {str(e)}'}, status=500)
            
    except Exception as e:
        import traceback
        print(f"Unexpected error in translate_simple: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_POST
@ensure_csrf_cookie  
def translate_word(request):
    """Legacy API endpoint for single word translation"""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        word = data.get('word', '').strip()
        target_lang = data.get('target_lang', 'en') 
        
        if not word:
            return JsonResponse({'error': 'No word provided'}, status=400)
            
        # Convert to the new format and call translate_simple
        new_request_data = {
            'text': word,
            'target_language': target_lang,
            'entities': [{'text': word}]
        }
        
        # Create a new request object
        from django.http import HttpRequest
        import io
        
        new_request = HttpRequest()
        new_request.method = 'POST'
        new_request._body = json.dumps(new_request_data).encode('utf-8')
        new_request.META = request.META.copy()
        
        # Call the new translate_simple function
        return translate_simple(new_request)
        
    except Exception as e:
        import traceback
        print(f"Unexpected error in translate_word: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': 'Internal server error'}, status=500)



def highlight_translated_words(text, words_to_highlight):
    """Wrap target words in a span with highlight class"""
    pattern = r'\b(' + '|'.join(re.escape(word) for word in words_to_highlight) + r')\b'
    highlighted = re.sub(pattern, r'<span class="highlight">\1</span>', text, flags=re.IGNORECASE)
    return mark_safe(highlighted)  # Prevent Django from escaping the HTML

from django.utils.html import strip_tags

@login_required(login_url="login_page")
def view_article(request, article_id):
    """View for displaying and editing a single article"""
    article = get_object_or_404(Article, id=article_id, user=request.user)

    # Handle article edit submission
    if request.method == 'POST' and 'edited_content' in request.POST:
        edited_content = request.POST.get('edited_content')
        article.content = edited_content
        article.save()
        messages.success(request, "Article updated successfully!")

    auto_edit = request.GET.get('auto_edit') == '1'

    return render(request, 'generator/view_article.html', {
        'article': article,
        'article_content': article.content,  # Plain for editing
        'auto_edit': auto_edit
    })


@require_POST
@ensure_csrf_cookie
def update_article_content(request):
    """API endpoint to update article content after word replacements"""
    try:
        # Parse the JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        # Check if required fields are present
        article_id = data.get('article_id')
        updated_content = data.get('content')
        
        if not article_id or updated_content is None:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get the article
        try:
            article = Article.objects.get(id=article_id, user=request.user)
        except Article.DoesNotExist:
            return JsonResponse({'error': 'Article not found'}, status=404)
        
        # Update the article content
        article.content = updated_content
        article.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Article content updated successfully'
        })
        
    except Exception as e:
        import traceback
        print(f"Unexpected error in update_article_content: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_POST
@ensure_csrf_cookie
def detect_language(request):
    """API endpoint to detect language of text fragments"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        article_language = data.get('article_language', 'en')

        if not content:
            return JsonResponse({'error': 'No content provided'}, status=400)

        # Prepare request for FastAPI
        fastapi_request = {
            "content": content,
            "article_language": article_language
        }

        # Make request to FastAPI service
        response = requests.post('http://127.0.0.1:8002/detect/', json=fastapi_request)
        response.raise_for_status()
        
        result = response.json()
        
        # Return the response directly since it already matches our expected format
        return JsonResponse(result)

    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Error communicating with detection service: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error processing request: {str(e)}'
        }, status=500)