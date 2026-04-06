# Review Plan Format

Pass the `segments` array from `prepare` into the plan file unchanged so `apply` can validate offsets.

## Schema

```json
{
  "prepared_document": "/absolute/path/to/file_grammar_revised.docx",
  "segments": [
    {
      "segment_index": 0,
      "start": 0,
      "end": 25,
      "text": "This are a test sentence."
    }
  ],
  "edits": [
    {
      "segment_index": 0,
      "start": 0,
      "end": 4,
      "original": "This",
      "replacement": "These"
    }
  ],
  "comments": [
    {
      "segment_index": 0,
      "start": 0,
      "end": 24,
      "comment": "Meaning is a bit unclear here; consider specifying the intended referent."
    }
  ]
}
```

## Offset Rules

- `start` and `end` are segment-relative character offsets using the exact `text` from `prepare`.
- Offsets are zero-based and `end` is exclusive.
- `original` must exactly match `text[start:end]`.
- Keep edit spans non-overlapping.

## Editing Guidance

- Use one narrow edit per grammatical issue when possible.
- Prefer replacement spans over rewriting the whole sentence.
- Comment rather than rewrite when the issue is semantic clarity instead of grammar.
