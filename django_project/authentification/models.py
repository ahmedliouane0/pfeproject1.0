from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError


class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    est_actif = models.BooleanField(default=True)
    date_inscrit = models.DateTimeField(default=timezone.now)
    email = models.EmailField(max_length=254)
    
    def create_article(self):
        pass
        
    def edit_article(self):
        pass
    
    class Meta:
        db_table = 'users'

class Language(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=10,unique=True)
    nom = models.CharField(max_length=100)
    
    def get_grammar_rules(self):
        pass

    def __str__(self):
        return self.nom 
    
    class Meta:
        db_table = 'languages'

class Article(models.Model):
    id = models.AutoField(primary_key=True)  
    keyword = models.CharField(max_length=200,null=False,blank=False)
    subject = models.TextField(null=False, blank=False)
    créer_le = models.DateTimeField(auto_now_add=True)
    modifier_le = models.DateTimeField(auto_now=True)
    is_translated = models.BooleanField(default=False)
    content = models.TextField(null=True, blank=True)
    
    source_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='source_articles'
    )
    
    user = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='articles'
)
   
    def get_errors(self):
        pass
        
    def translate(self):
        pass
        
    def save_correction(self):
        pass
    
    class Meta:
        db_table = 'articles'

class ErrorType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def get_correction_rules(self):
        pass
    
    class Meta:
        db_table = 'error_types'

class Error(models.Model):
    id = models.AutoField(primary_key=True)  
    start_position = models.IntegerField()
    end_position = models.IntegerField()
    incorrect_text = models.TextField()
    suggested_correction = models.TextField()
    explanation = models.TextField()
    detected_at = models.DateTimeField(auto_now_add=True)
    is_fixed = models.BooleanField(default=False)
    
   
    article = models.ForeignKey(
    Article,
    on_delete=models.CASCADE,
    related_name='errors'
    )
    error_type = models.ForeignKey(
        ErrorType,
        on_delete=models.CASCADE,
        related_name='errors'
    )
    
    def apply_correction(self):
        pass
        
    def ignore_error(self):
        pass
    
    class Meta:
        db_table = 'errors'

class Correction(models.Model):
    id = models.AutoField(primary_key=True)  
    corrected_text = models.TextField()
    correction_time = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    
    
    error = models.ForeignKey(
    Error,
    on_delete=models.CASCADE,
    related_name='corrections'
    )

    corrected_by = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='corrections'
    )

    
    def apply_to_article(self):
        pass
        
    def revert_correction(self):
        pass
    
    class Meta:
        db_table = 'corrections'