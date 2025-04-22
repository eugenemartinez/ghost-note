from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    """
    Form for creating and editing a Note.
    """
    class Meta:
        model = Note
        # Add 'is_public' to the list of fields
        fields = ['username', 'content', 'is_public']
        widgets = {
            # Keep existing widgets if any, e.g.:
            # 'content': forms.Textarea(attrs={'rows': 10, 'cols': 50}),
        }
        labels = {
            # Keep existing labels if any, e.g.:
            # 'username': 'Display Username',
            # 'content': 'Message',
            'is_public': 'Make this note public?', # Add a clear label for the checkbox
        }
        help_texts = {
            # Add help text to explain what making it public means
            'is_public': 'Public notes may appear in random listings. Private notes are only accessible via their direct URL.',
        }
