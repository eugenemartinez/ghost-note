from django.db import models
import uuid # Used for generating unique codes

# Create your models here.
class Note(models.Model):
    """Represents a single GhostNote message."""
    # Replace default integer primary key with a UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FR001, FR002: Message content
    content = models.TextField()
    # FR001, FR002: Display username
    username = models.CharField(max_length=100) # Adjust max_length as needed
    # FR002: Creation timestamp (automatically set when created)
    created_at = models.DateTimeField(auto_now_add=True)
    # FR003: Unique modification code (separate from the primary key/URL id)
    # We use UUID for strong uniqueness. editable=False means it won't show up in default forms.
    modification_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # Field to control public visibility
    is_public = models.BooleanField(default=False, help_text="Allow this note to appear in public listings?")

    def __str__(self):
        """String representation for admin and debugging."""
        # Include public status in string representation
        status = "Public" if self.is_public else "Private"
        # Use self.id (which is now the UUID) in the string representation if desired
        return f"{status} Note ({self.id}) by {self.username} created at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    # The 'id' field defined above is now the primary key used for URLs.
