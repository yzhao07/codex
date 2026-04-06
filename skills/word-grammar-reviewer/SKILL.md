---
name: word-grammar-reviewer
description: Review local Microsoft Word `.doc` and `.docx` files for grammar and academic English issues, then return a new `_grammar_revised.docx` copy with real Microsoft Word Track Changes edits and reviewer comments. Use when Codex receives a local Word-document path and must preserve formatting, avoid overwriting the original, convert `.doc` to `.docx` if needed, apply minimal corrections as tracked insertions/deletions/replacements, and add concise Word comments instead of rewriting unclear or ambiguous sentences.
---

# Word Grammar Reviewer

Use Microsoft Word automation for all applied edits and comments. Do not rewrite the `.docx` package directly to create revisions or comments.

## Workflow

1. Run `python3 scripts/word_review.py prepare <input-path>`.
2. Read the emitted JSON and review every non-empty segment in `segments`.
3. Create a review plan JSON that follows [`references/review-plan.md`](./references/review-plan.md).
4. Run `python3 scripts/word_review.py apply --document <output-path> --plan <plan-path>`.
5. Return the final `output_path`.

## Review Rules

- Review all extracted visible text segments, including headings and table-cell paragraphs.
- Prefer minimal edits over rewriting.
- Preserve meaning, technical content, academic tone, layout, and formatting.
- Apply grammar corrections as tracked changes only.
- Add Word comments for unclear, ambiguous, or potentially misleading sentences instead of rewriting them.
- Keep comments concise and professional.
- Do not accept changes.
- Do not remove markup.
- Do not overwrite the original input file.

## Prepare Step

Run:

```bash
python3 scripts/word_review.py prepare "/absolute/path/to/file.docx"
```

The script:

- Opens the source document in Microsoft Word
- Creates `<original_prefix>_grammar_revised.docx` next to the original
- Converts `.doc` inputs to `.docx`
- Turns on Track Changes and markup visibility in the output copy
- Extracts paragraph-level visible text with stable Word character offsets

Use the returned `output_path` for the final deliverable.

## Build The Review Plan

Create a JSON file with two arrays:

- `edits`: tracked replacements
- `comments`: reviewer comments

Use segment-relative offsets from `prepare`. Do not invent offsets; compute them from each segment's exact extracted text.

Rules for edits:

- Keep replacements narrow.
- Do not include overlapping edits.
- Include `original` exactly as it appears in the extracted segment for validation.
- Use edits for grammar, agreement, tense, article, preposition, punctuation, sentence-structure, and minimal idiomatic fixes.

Rules for comments:

- Use comments for unclear phrasing, ambiguous meaning, missing context, or confusing structure.
- Anchor each comment to the smallest phrase or sentence span that signals the issue.

## Apply Step

Run:

```bash
python3 scripts/word_review.py apply --document "/absolute/path/to/output_grammar_revised.docx" --plan "/absolute/path/to/review-plan.json"
```

The script applies:

- comments through Microsoft Word comments
- edits through Microsoft Word selections with `track revisions` enabled

This produces real Word review markup that remains visible in Word.

## Notes

- If `prepare` or `apply` fails, read stderr first; the script validates paths, extensions, offsets, and expected original text.
- If a sentence is both grammatically wrong and semantically unclear, fix only the clearly grammatical issue and comment on the ambiguity.
- If a segment contains nothing worth changing, leave it out of the review plan.
