from django import forms
from django.core.validators import RegexValidator
from .models import Language, Article


letter_validator = RegexValidator(
    regex=r'^(?!\s*$)(?!^"+$)(?:"?[^\x00-\x1F\x7F]+(?:[^\x00-\x1F\x7F]*[^\x00-\x1F\x7F])?"?|[^\x00-\x1F\x7F]+)$',
    message='This field must contain only letters, spaces, and other characters. It can be enclosed in quotes but cannot be empty or only quotes.'
)

class ArticleForm(forms.ModelForm):
    word = forms.CharField(
        label="Keyword",
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500',
            'pattern': '.*\S.*',
            'required': True,
            'id': 'word'
        }),
        min_length=2,
        validators=[letter_validator]
    )
    
    subject = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500',
            'pattern': '.*\S.*',
            'required': True,
            'id': 'subject'
        }),
        min_length=2,
        validators=[letter_validator]
    )
    
    language = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        empty_label="Select a Language",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500',
            'required': True,
            'id': 'language'
        })
    )

    class Meta:
        model = Article
        fields = ['word', 'subject', 'language']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['word'].label = "Keyword"
        self.fields['language'].label = "Language"

    def clean_word(self):
        word = self.cleaned_data.get('word', '').strip()
        if not word or word in ['""', "''"] or word.replace('"', '').replace("'", "").strip() == "":
            raise forms.ValidationError("This field cannot be empty, contain only spaces, or just quotes.")
        return word

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject or subject in ['""', "''"] or subject.replace('"', '').replace("'", "").strip() == "":
            raise forms.ValidationError("This field cannot be empty, contain only spaces, or just quotes.")
        return subject
