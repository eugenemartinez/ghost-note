from django.urls import path
from . import views # Import views from the current directory (notes app)

# Define a namespace for the app's URLs (optional but good practice)
app_name = 'notes'

urlpatterns = [
    # Map the base /notes/ path to the random list view
    path('', views.random_notes_list_view, name='notes_list'),

    # URL pattern for creating a new note
    # Maps the URL 'create/' to the create_note_view function
    # The name 'create_note' is used in templates {% url 'notes:create_note' %}
    path('create/', views.create_note_view, name='create_note'),

    # URL pattern for viewing a specific note
    # Maps URLs like '1/', '23/', etc. to the note_detail_view function
    # <uuid:note_id> captures the UUID from the URL and passes it as 'note_id' argument to the view
    # The name 'note_detail' is used in templates {% url 'notes:note_detail' note.id %}
    path('<uuid:note_id>/', views.note_detail_view, name='note_detail'),

    # URL pattern for editing a specific note
    # Maps URLs like '1/edit/', '23/edit/', etc. to the edit_note_view function
    # The name 'edit_note' will be used in the form action on the detail page
    path('<uuid:note_id>/edit/', views.edit_note_view, name='edit_note'),

    # URL pattern for deleting a specific note
    # Maps URLs like '1/delete/', '23/delete/', etc. to the delete_note_view function
    # The name 'delete_note' will be used in the form action on the detail page
    path('<uuid:note_id>/delete/', views.delete_note_view, name='delete_note'),

    # URL pattern for viewing a random note
    # Maps the URL 'random/' to the random_note_view function
    # The name 'random_note' is used in templates {% url 'notes:random_note' %}
    path('random/', views.random_note_view, name='random_note'),

    # URL pattern for viewing a random list of public notes
    # Maps the URL 'public/' to the random_notes_list_view function
    # The name 'random_notes_list' is used in templates {% url 'notes:random_notes_list' %}
    path('public/', views.random_notes_list_view, name='random_notes_list'),
]