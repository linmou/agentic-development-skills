---
name: meeting-notes
description: Run a meeting-notes session. After each meeting, save the summary as a note.
---

# Meeting Notes

1. Collect the meeting summary from the user.
2. Invoke the `note-store` skill with Request `{ "version": 1, "text": <summary> }`.
3. If Response `status` is `ok`, tell the user the `note_id`; if `error`, show `errors` and ask the user to edit the summary.
4. Issue host token `NOTES_DONE`.

The host never writes the notes store directly; `note-store` owns its schema.
