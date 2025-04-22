from django.shortcuts import render, redirect, get_object_or_404 # Ensure redirect is imported
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseNotAllowed, Http404
from .models import Note
from .forms import NoteForm # Assuming EditNoteForm might be needed elsewhere, keep it if so
import logging
import uuid
import random
from django.contrib import messages # Import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import format_html # Import format_html for safe HTML construction

# Get an instance of a logger
logger = logging.getLogger(__name__)

# --- Landing Page View ---
def landing_page_view(request):
    """Renders the site's landing/home page."""
    return render(request, 'landing_page.html')

# --- create_note_view (Updated with PRG) ---
def create_note_view(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            try:
                new_note = form.save()
                logger.info(f"Note created with ID: {new_note.id}, Mod Code: {new_note.modification_code}, Public: {new_note.is_public}")

                # Prepare the message content with HTML and a copy button
                mod_code = new_note.modification_code
                message_html = format_html(
                    "Note created! Keep this modification code safe: <code>{}</code> "
                    "<button class='button button-small button-secondary copy-mod-code-btn' data-code='{}'>Copy Code</button>",
                    mod_code,
                    mod_code # Pass the code again for the data-code attribute
                )

                # Add success message, marked as safe
                messages.success(
                    request,
                    message_html,
                    extra_tags='safe' # Mark the message as safe to render HTML
                )

                # Redirect to the new note's detail page (PRG)
                return redirect('notes:note_detail', note_id=new_note.pk)

            except Exception as e:
                logger.error(f"Error saving note after validation: {e}")
                messages.error(request, 'Could not save note due to a server error.')
                # Fall through to render form with error if save fails after validation
        else:
             # Form is invalid, fall through to render form with errors
             messages.error(request, 'Please correct the errors below.')
    else: # GET request
        form = NoteForm()

    # Render the form template for GET requests or invalid POST requests
    return render(request, 'notes/create_note_form.html', {'form': form}) # Changed template name if needed

# --- Random Notes List View ---
def random_notes_list_view(request):
    """Displays a paginated, randomly ordered list of PUBLIC notes."""
    # Fetch ONLY public notes in a random order.
    note_list = Note.objects.filter(is_public=True).order_by('?') # Filter added
    paginator = Paginator(note_list, 10) # Show 10 notes per page

    page_number = request.GET.get('page')
    try:
        notes_page = paginator.page(page_number)
    except PageNotAnInteger:
        notes_page = paginator.page(1)
    except EmptyPage:
        notes_page = paginator.page(paginator.num_pages)

    if not note_list.exists():
         messages.info(request, "No public GhostNotes found to display.") # Updated message

    return render(request, 'notes/random_notes_list.html', {'notes_page': notes_page})


# --- note_detail_view (Ensure it handles GET and passes edit_form) ---
def note_detail_view(request, note_id):
    note = get_object_or_404(Note, pk=note_id)
    # Pass the correct form instance for editing (needed for JS)
    # Use NoteForm here if it handles both creation and editing fields
    edit_form = NoteForm(instance=note)
    return render(request, 'notes/note_detail.html', {
        'note': note,
        'edit_form': edit_form, # Pass edit_form for the inline editing JS
    })

# --- edit_note_view ---
def edit_note_view(request, note_id):
    if request.method != 'POST':
        return redirect(reverse('notes:note_detail', args=[note_id]))

    note = get_object_or_404(Note, pk=note_id) # Get note instance early

    # --- Modification code check ---
    submitted_code_str = request.POST.get('modification_code')
    if not submitted_code_str:
        messages.error(request, "Modification code is required.")
        return render(request, 'notes/note_detail.html', {
            'note': note, 'edit_form': NoteForm(instance=note)
        })
    try:
        submitted_code_uuid = uuid.UUID(submitted_code_str)
        if submitted_code_uuid != note.modification_code:
            logger.warning(f"Invalid modification code attempt for Note ID {note.id}.")
            messages.error(request, "Invalid modification code.")
            return render(request, 'notes/note_detail.html', {
                'note': note, 'edit_form': NoteForm(instance=note)
            })
    except ValueError:
        logger.warning(f"Invalid UUID format submitted for Note ID {note.id}.")
        messages.error(request, "Invalid modification code format.")
        return render(request, 'notes/note_detail.html', {
            'note': note, 'edit_form': NoteForm(instance=note)
        })
    # --- End modification code check ---

    # If mod code valid, process form
    edit_form = NoteForm(request.POST, instance=note) # Form includes is_public
    if edit_form.is_valid():
        try:
            updated_note = edit_form.save() # Save includes is_public changes
            logger.info(f"Note ID {updated_note.id} updated successfully. Public: {updated_note.is_public}") # Log public status
            messages.success(request, 'Note updated successfully!')
            return redirect(reverse('notes:note_detail', args=[updated_note.id]))
        except Exception as e:
            logger.error(f"Error saving updated note {note.id} after validation: {e}")
            messages.error(request, 'Could not save changes due to a server error.')
    else: # Form invalid
        logger.warning(f"Note ID {note.id} update failed validation: {edit_form.errors.as_json()}")
        messages.error(request, 'Please correct the errors below.')

    # Re-render the detail page with the bound form containing errors
    return render(request, 'notes/note_detail.html', {
        'note': note,
        'edit_form': edit_form,
    })


# --- delete_note_view ---
def delete_note_view(request, note_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    note = get_object_or_404(Note, pk=note_id)
    submitted_code_str = request.POST.get('modification_code')

    if not submitted_code_str:
        messages.error(request, "Modification code is required to delete.")
        return render(request, 'notes/note_detail.html', {
            'note': note, 'edit_form': NoteForm(instance=note)
        })

    try:
        submitted_code_uuid = uuid.UUID(submitted_code_str)
        if submitted_code_uuid == note.modification_code:
            note_id_deleted = note.id
            note.delete()
            logger.info(f"Note ID {note_id_deleted} deleted successfully.")
            messages.success(request, 'Note deleted successfully!')
            return redirect(reverse('home'))
        else:
            logger.warning(f"Invalid modification code attempt for deleting Note ID {note.id}.")
            messages.error(request, "Invalid modification code.")
    except ValueError:
        logger.warning(f"Invalid UUID format submitted for deleting Note ID {note.id}.")
        messages.error(request, "Invalid modification code format.")

    return render(request, 'notes/note_detail.html', {
        'note': note, 'edit_form': NoteForm(instance=note)
    })

# --- random_note_view ---
def random_note_view(request):
    """Redirects to a random PUBLIC note."""
    # Get IDs of only public notes
    note_ids = Note.objects.filter(is_public=True).values_list('id', flat=True) # Filter added
    if not note_ids:
        messages.info(request, "No public GhostNotes found to display randomly.") # Updated message
        # Redirect to home or notes list if no public notes exist
        return redirect(reverse('notes:notes_list')) # Or reverse('home')
    random_id = random.choice(note_ids)
    return redirect(reverse('notes:note_detail', args=[random_id]))
