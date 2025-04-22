from django.test import TestCase, Client # Import Client
from django.urls import reverse # To look up URLs by name
from .models import Note # Import the model to test
from .forms import NoteForm # Import the form to test
import uuid # To check the type of the modification code
import re # Import regular expression module
from django.utils import timezone # Import timezone
# Import patch from unittest.mock for later
from unittest.mock import patch

# Create a class for Note model tests, inheriting from TestCase
class NoteModelTests(TestCase):

    def test_modification_code_generated_on_create(self):
        """
        Tests that a UUID modification_code is automatically generated
        when a Note object is created and saved.
        """
        # Create a Note instance without specifying id or modification_code
        note = Note.objects.create(
            username="TestUser",
            content="Some test content for the note."
            # is_public defaults to False, created_at defaults to now
        )

        # Assertions: Check the state of the created object
        self.assertIsNotNone(note.modification_code, "Modification code should not be None after creation.")
        self.assertIsInstance(note.modification_code, uuid.UUID, "Modification code should be a UUID instance.")
        # Optional: Check other defaults or values
        self.assertEqual(note.username, "TestUser")
        self.assertFalse(note.is_public)

    def test_note_string_representation(self):
        """
        Tests the __str__ method of the Note model.
        """
        # Create a note with known values
        now = timezone.now() # Get current time
        note = Note(
            username="StrUser",
            content="Content for str test.",
            is_public=True,
            created_at=now # Set created_at explicitly for predictable output
            # id and modification_code will be generated on save if needed,
            # but we can test __str__ before saving if we assign an ID manually
        )
        note.id = uuid.uuid4() # Assign a UUID manually for the test

        # Expected string format based on the __str__ method
        expected_str = f"Public Note ({note.id}) by StrUser created at {now.strftime('%Y-%m-%d %H:%M')}"

        # Assert that calling str() on the note produces the expected string
        self.assertEqual(str(note), expected_str)

        # Test the private case too
        note.is_public = False
        expected_str_private = f"Private Note ({note.id}) by StrUser created at {now.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(note), expected_str_private)

    # We can add more test methods here later, like test_string_representation, etc.

# --- Add this new test class for NoteForm ---
class NoteFormTests(TestCase):

    def test_note_form_valid_data(self):
        """
        Tests that the NoteForm is valid when provided with correct data.
        """
        form_data = {
            'username': 'ValidUser',
            'content': 'This is valid content.',
            'is_public': True # Can be True or False
        }
        form = NoteForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form should be valid with correct data. Errors: {form.errors.as_json()}")

    def test_note_form_missing_content(self):
        """
        Tests that the NoteForm is invalid if the 'content' field is missing.
        """
        form_data = {
            'username': 'UserWithoutContent',
            # 'content' is missing
            'is_public': False
        }
        form = NoteForm(data=form_data)
        self.assertFalse(form.is_valid(), "Form should be invalid when content is missing.")
        self.assertIn('content', form.errors, "There should be an error associated with the 'content' field.")
        self.assertTrue(any('required' in error for error in form.errors['content']), "The 'content' error should mention it's required.")

    def test_note_form_missing_username(self):
        """
        Tests that the NoteForm is invalid if the 'username' field is missing.
        """
        form_data = {
            # 'username' is missing
            'content': 'Content without username.',
            'is_public': False
        }
        form = NoteForm(data=form_data)
        self.assertFalse(form.is_valid(), "Form should be invalid when username is missing.")
        self.assertIn('username', form.errors, "There should be an error associated with the 'username' field.")
        self.assertTrue(any('required' in error for error in form.errors['username']), "The 'username' error should mention it's required.")

    def test_note_form_is_public_optional(self):
        """
        Tests that the NoteForm is valid even if 'is_public' is not provided
        (it should default to False).
        """
        form_data = {
            'username': 'UserNoPublic',
            'content': 'Content with default privacy.',
            # 'is_public' is missing
        }
        form = NoteForm(data=form_data)
        # Check if the form is valid
        self.assertTrue(form.is_valid(), f"Form should be valid even without 'is_public'. Errors: {form.errors.as_json()}")
        # Check if the cleaned data has 'is_public' as False (the default)
        if form.is_valid(): # Only check cleaned_data if form is valid
            self.assertFalse(form.cleaned_data.get('is_public'), "'is_public' should default to False in cleaned_data.")

# --- Add this new test class for Views ---
class NoteViewTests(TestCase):

    def setUp(self):
        """Set up test client and sample data."""
        self.client = Client()
        self.home_url = reverse('home')
        self.create_url = reverse('notes:create_note')
        self.notes_list_url = reverse('notes:notes_list') # URL for the public list
        self.random_note_url = reverse('notes:random_note') # URL for random redirect

        # Create multiple notes for list/random tests
        self.public_note1 = Note.objects.create(
            username="PublicUser1", content="Public Note One.", is_public=True
        )
        self.public_note2 = Note.objects.create(
            username="PublicUser2", content="Public Note Two.", is_public=True
        )
        self.private_note = Note.objects.create(
            username="PrivateUser", content="Private Note.", is_public=False
        )
        # Keep the original test_note for edit/delete tests
        self.test_note = Note.objects.create(
            username="DetailUser",
            content="Content for detail/edit/delete tests.",
            is_public=True # Make this one public too for list testing
        )
        self.correct_mod_code = str(self.test_note.modification_code)
        self.detail_url = reverse('notes:note_detail', args=[self.test_note.pk])
        self.edit_url = reverse('notes:edit_note', args=[self.test_note.pk])
        self.delete_url = reverse('notes:delete_note', args=[self.test_note.pk])

    def test_landing_page_view(self):
        """Tests the landing page."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing_page.html')
        self.assertContains(response, "Simple, Anonymous Notes Online")

    def test_create_note_view_get(self):
        """Tests GET request to create_note."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/create_note_form.html')
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_create_note_view_post_valid(self):
        """Tests POST with valid data creates note and redirects."""
        note_data = {
            'username': 'PostUser',
            'content': 'Content created via POST test.',
            'is_public': False
        }
        initial_note_count = Note.objects.count()
        response = self.client.post(self.create_url, data=note_data, follow=True)
        self.assertEqual(Note.objects.count(), initial_note_count + 1)
        new_note = Note.objects.latest('created_at')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Note created!")
        self.assertContains(response, f"<code>{new_note.modification_code}</code>")
        self.assertContains(response, "copy-mod-code-btn")

    def test_create_note_view_post_invalid(self):
        """Tests POST with invalid data re-renders form."""
        note_data = { 'username': 'InvalidPostUser' } # Missing content
        initial_note_count = Note.objects.count()
        response = self.client.post(self.create_url, data=note_data)
        self.assertEqual(Note.objects.count(), initial_note_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/create_note_form.html')
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('content', response.context['form'].errors)
        self.assertContains(response, "Please correct the errors below.")

    # --- Add tests for note_detail_view ---

    def test_note_detail_view_get_existing(self):
        """
        Tests GET request for an existing note's detail page.
        """
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        # Check that the note from the context matches our test note
        self.assertEqual(response.context['note'], self.test_note)
        # Check if the note's content is present in the response
        self.assertContains(response, self.test_note.content)
        self.assertContains(response, self.test_note.username)
        # Check if edit/delete buttons are present (assuming they always are initially)
        self.assertContains(response, 'Edit Note')
        self.assertContains(response, 'Delete Note')

    def test_note_detail_view_get_nonexistent(self):
        """
        Tests GET request for a non-existent note's detail page (should 404).
        """
        # Generate a valid, random UUID that is unlikely to exist
        non_existent_uuid = uuid.uuid4()
        # Use this UUID string to generate the URL
        non_existent_url = reverse('notes:note_detail', args=[str(non_existent_uuid)])
        response = self.client.get(non_existent_url)

        # Check if the response status code is 404 (Not Found)
        self.assertEqual(response.status_code, 404)

    # --- Add tests for edit_note_view ---

    def test_edit_note_view_get_not_allowed(self):
        """
        Tests that GET request to edit_note redirects to detail view.
        """
        response = self.client.get(self.edit_url)
        # Check for redirect (302) to the detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.detail_url)

    def test_edit_note_view_post_valid_correct_code(self):
        """
        Tests POST with valid data and correct mod code updates note and redirects.
        """
        updated_content = "This content has been updated."
        edit_data = {
            'username': self.test_note.username, # Username shouldn't change via edit form
            'content': updated_content,
            'is_public': False, # Change privacy setting
            'modification_code': self.correct_mod_code
        }

        response = self.client.post(self.edit_url, data=edit_data, follow=True)

        # Check the final response after redirect
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Note updated successfully!")

        # Verify the note in the database was actually updated
        self.test_note.refresh_from_db() # Reload data from DB
        self.assertEqual(self.test_note.content, updated_content)
        self.assertFalse(self.test_note.is_public) # Check if privacy changed

    def test_edit_note_view_post_valid_incorrect_code(self):
        """
        Tests POST with valid data but incorrect mod code does not update.
        """
        original_content = self.test_note.content
        incorrect_mod_code = str(uuid.uuid4()) # Generate a random wrong code
        edit_data = {
            'username': self.test_note.username,
            'content': "Attempted update with wrong code.",
            'is_public': False,
            'modification_code': incorrect_mod_code
        }

        response = self.client.post(self.edit_url, data=edit_data) # No follow=True needed

        # Check response re-renders detail page with error (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Invalid modification code.")

        # Verify the note in the database was NOT updated
        self.test_note.refresh_from_db()
        self.assertEqual(self.test_note.content, original_content) # Should be unchanged
        self.assertTrue(self.test_note.is_public) # Should be unchanged

    def test_edit_note_view_post_invalid_data_correct_code(self):
        """
        Tests POST with invalid data (empty content) but correct mod code.
        """
        original_content = self.test_note.content
        edit_data = {
            'username': self.test_note.username,
            'content': "", # Invalid: content is required
            'is_public': False,
            'modification_code': self.correct_mod_code
        }

        response = self.client.post(self.edit_url, data=edit_data)

        # Check response re-renders detail page with form errors (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        # Check form in context has errors
        self.assertFalse(response.context['edit_form'].is_valid())
        self.assertIn('content', response.context['edit_form'].errors)
        self.assertContains(response, "Please correct the errors below.") # General form error message

        # Verify the note in the database was NOT updated
        self.test_note.refresh_from_db()
        self.assertEqual(self.test_note.content, original_content)

    def test_edit_note_view_post_missing_code(self):
        """
        Tests POST without providing a modification code.
        """
        original_content = self.test_note.content
        edit_data = {
            'username': self.test_note.username,
            'content': "Attempted update without code.",
            'is_public': False,
            # 'modification_code' is missing
        }

        response = self.client.post(self.edit_url, data=edit_data)

        # Check response re-renders detail page with error (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Modification code is required.") # Specific error message

        # Verify the note in the database was NOT updated
        self.test_note.refresh_from_db()
        self.assertEqual(self.test_note.content, original_content)

    # --- Add tests for delete_note_view ---

    def test_delete_note_view_get_not_allowed(self):
        """
        Tests that GET request to delete_note is not allowed (should return 405).
        """
        response = self.client.get(self.delete_url)
        # Check for Method Not Allowed status code
        self.assertEqual(response.status_code, 405)

    def test_delete_note_view_post_correct_code(self):
        """
        Tests POST with correct mod code deletes the note and redirects to home.
        """
        # Ensure the note exists before deletion
        note_pk = self.test_note.pk
        self.assertTrue(Note.objects.filter(pk=note_pk).exists())

        delete_data = {
            'modification_code': self.correct_mod_code
        }

        response = self.client.post(self.delete_url, data=delete_data, follow=True)

        # Check the final response after redirect (should be home page)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing_page.html') # Assuming redirect goes to home
        self.assertContains(response, "Note deleted successfully!")

        # Verify the note no longer exists in the database
        self.assertFalse(Note.objects.filter(pk=note_pk).exists())

    def test_delete_note_view_post_incorrect_code(self):
        """
        Tests POST with incorrect mod code does not delete the note.
        """
        note_pk = self.test_note.pk
        incorrect_mod_code = str(uuid.uuid4())
        delete_data = {
            'modification_code': incorrect_mod_code
        }

        response = self.client.post(self.delete_url, data=delete_data) # No follow=True

        # Check response re-renders detail page with error (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Invalid modification code.")

        # Verify the note still exists in the database
        self.assertTrue(Note.objects.filter(pk=note_pk).exists())

    def test_delete_note_view_post_missing_code(self):
        """
        Tests POST without providing a modification code does not delete.
        """
        note_pk = self.test_note.pk
        delete_data = {
            # 'modification_code' is missing
        }

        response = self.client.post(self.delete_url, data=delete_data)

        # Check response re-renders detail page with error (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Modification code is required to delete.") # Specific error

        # Verify the note still exists in the database
        self.assertTrue(Note.objects.filter(pk=note_pk).exists())

    # --- Add tests for notes_list_view ---

    def test_notes_list_view_get(self):
        """
        Tests GET request for the public notes list page.
        """
        response = self.client.get(self.notes_list_url)
        self.assertEqual(response.status_code, 200)
        # Assuming the template name is 'random_notes_list.html' based on view code
        self.assertTemplateUsed(response, 'notes/random_notes_list.html')

    def test_notes_list_view_shows_public_only(self):
        """
        Tests that the notes list view only displays public notes.
        """
        response = self.client.get(self.notes_list_url)
        self.assertEqual(response.status_code, 200)

        # Check that public notes' content/username are present
        self.assertContains(response, self.public_note1.content)
        self.assertContains(response, self.public_note1.username)
        self.assertContains(response, self.public_note2.content)
        self.assertContains(response, self.public_note2.username)
        self.assertContains(response, self.test_note.content) # The other public note
        self.assertContains(response, self.test_note.username)

        # Check that private note's content/username are NOT present
        self.assertNotContains(response, self.private_note.content)
        self.assertNotContains(response, self.private_note.username)

    def test_notes_list_view_no_public_notes(self):
        """
        Tests the message shown when no public notes exist.
        """
        # Delete all public notes created in setUp
        Note.objects.filter(is_public=True).delete()

        response = self.client.get(self.notes_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/random_notes_list.html')

        # Check for the "no notes" message
        self.assertContains(response, "No public GhostNotes found to display.")
        # Check that no note content is displayed
        self.assertNotContains(response, "Note by:") # Check for absence of typical note display elements

    # --- Add tests for random_note_view ---

    def test_random_note_view_redirects_when_public_exist(self):
        """
        Tests that random_note view redirects (302) when public notes exist.
        """
        response = self.client.get(self.random_note_url)
        # Check for redirect status code
        self.assertEqual(response.status_code, 302)

    def test_random_note_view_redirects_to_public_note_detail(self):
        """
        Tests that the random_note view redirects to a valid public note detail URL.
        """
        response = self.client.get(self.random_note_url)
        self.assertEqual(response.status_code, 302)

        # Extract the redirected URL
        redirect_url = response['Location']

        # Use regex to extract the UUID from the redirected URL
        match = re.search(r'/notes/([0-9a-f\-]+)/$', redirect_url)
        self.assertIsNotNone(match, "Redirect URL should match the note detail pattern.")

        if match:
            redirected_note_pk_str = match.group(1)
            try:
                # Check if the extracted PK corresponds to an existing Note
                redirected_note = Note.objects.get(pk=redirected_note_pk_str)
                # Check if the note it redirected to is actually public
                self.assertTrue(redirected_note.is_public, "Redirected note should be public.")
            except (Note.DoesNotExist, ValueError):
                self.fail(f"Redirect URL '{redirect_url}' does not point to a valid Note PK.")

    def test_random_note_view_no_public_notes(self):
        """
        Tests random_note view redirects to notes list when no public notes exist.
        """
        # Delete all public notes
        Note.objects.filter(is_public=True).delete()

        response = self.client.get(self.random_note_url, follow=True) # Follow the redirect

        # Check the final response (should be notes list page)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/random_notes_list.html') # Assuming redirect goes to notes_list
        # Check for the message indicating no random notes found
        self.assertContains(response, "No public GhostNotes found to display randomly.")

    # --- Test for Pagination Error ---
    def test_notes_list_view_invalid_page_number(self):
        """
        Tests accessing the notes list with a non-integer page number.
        """
        # Access with an invalid page parameter
        response = self.client.get(self.notes_list_url + '?page=abc')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/random_notes_list.html')
        # Check if it correctly falls back to page 1 (assuming notes exist)
        self.assertEqual(response.context['notes_page'].number, 1)

    # --- Test for Edit Invalid UUID Format ---
    def test_edit_note_view_post_invalid_code_format(self):
        """
        Tests POST to edit view with an invalidly formatted modification code.
        """
        invalid_code_format = "this-is-not-a-uuid"
        edit_data = {
            'username': self.test_note.username,
            'content': "Attempted update with invalid code format.",
            'is_public': False,
            'modification_code': invalid_code_format
        }

        response = self.client.post(self.edit_url, data=edit_data)

        # Check response re-renders detail page with error (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Invalid modification code format.")

        # Verify the note in the database was NOT updated
        self.test_note.refresh_from_db()
        self.assertTrue(self.test_note.is_public) # Should be unchanged

    # --- Test for Delete Invalid UUID Format ---
    def test_delete_note_view_post_invalid_code_format(self):
        """
        Tests POST to delete view with an invalidly formatted modification code.
        """
        note_pk = self.test_note.pk
        invalid_code_format = "this-is-not-a-uuid-either"
        delete_data = {
            'modification_code': invalid_code_format
        }

        response = self.client.post(self.delete_url, data=delete_data)

        # Check response re-renders detail page with error (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, "Invalid modification code format.")

        # Verify the note still exists in the database
        self.assertTrue(Note.objects.filter(pk=note_pk).exists())

    # --- Tests for save() exceptions can be added below ---
    # --- Test for save() exception during create ---
    @patch('notes.views.NoteForm.save') # Target the save method where it's used
    def test_create_note_view_post_save_exception(self, mock_save):
        """
        Tests the exception handling during form.save() in create_note_view.
        """
        # Configure the mock_save to raise an Exception when called
        mock_save.side_effect = Exception("Database connection failed")

        note_data = {
            'username': 'SaveFailUser',
            'content': 'This content should not be saved.',
            'is_public': False
        }
        initial_note_count = Note.objects.count()

        response = self.client.post(self.create_url, data=note_data)

        # Check that no note was created
        self.assertEqual(Note.objects.count(), initial_note_count)

        # Check that the response re-renders the form page (status code 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/create_note_form.html')
        # Check that the generic error message is displayed
        self.assertContains(response, "Could not save note due to a server error.")
        # Check that the form instance in the context is the one submitted
        self.assertIsInstance(response.context['form'], NoteForm)
        self.assertEqual(response.context['form'].data['content'], note_data['content'])

    # --- Test for save() exception during edit can be added similarly ---
    @patch('notes.views.NoteForm.save') # Target the save method where it's used
    def test_edit_note_view_post_save_exception(self, mock_save):
        """
        Tests the exception handling during form.save() in edit_note_view.
        """
        # Configure the mock_save to raise an Exception when called
        mock_save.side_effect = Exception("Simulated DB error during edit")

        original_content = self.test_note.content
        edit_data = {
            'username': self.test_note.username,
            'content': "This edit should fail during save.",
            'is_public': False,
            'modification_code': self.correct_mod_code # Need correct code to pass initial checks
        }

        response = self.client.post(self.edit_url, data=edit_data)

        # Check response re-renders detail page with error (status 200)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        # Check that the generic error message is displayed
        self.assertContains(response, "Could not save changes due to a server error.")

        # Verify the note in the database was NOT updated
        self.test_note.refresh_from_db()
        self.assertEqual(self.test_note.content, original_content) # Should be unchanged
        # Check that the form instance in the context is the one submitted (with errors if any)
        self.assertIsInstance(response.context['edit_form'], NoteForm)
        self.assertEqual(response.context['edit_form'].data['content'], edit_data['content'])
