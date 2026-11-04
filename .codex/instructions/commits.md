# Commit messages

Conventional Commits with a short subject and a **bullet changelog**. This format wins over one-liners, "why-only" subjects, and caveman-commit compression.

When the user asks for a commit message, **format it this way**. Do not invent a shorter rewrite.

## Shape

```
<type>: <imperative summary>

- Past-tense sentence describing one change.
- Past-tense sentence describing another change.
```

- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`, `style`, `revert`
- Subject: lowercase after the colon, no scope parens, no trailing period
- Blank line, then `-` bullets (not `*`)
- Each bullet = one complete past-tense sentence (`Added`, `Introduced`, `Updated`, `Enhanced`, …)
- Keep the user's substance. Split their paragraph into bullets. Do not drop files, flags, tests, or docs they named.

## Example

❌ One-liner:

```
feat(security): add DJANGO_PERMISSIONS_ENABLED flag
```

❌ Paragraph with no type / no bullets:

```
Add catalog permission checks: introduced DJANGO_PERMISSIONS_ENABLED configuration to control role/permission gates in the application. Updated relevant settings, utility functions, and tests to integrate this feature. Enhanced documentation to clarify the new permissions behavior and its impact on authorization checks.
```

✅

```
feat: add catalog permission checks

- Introduced DJANGO_PERMISSIONS_ENABLED configuration to control role/permission gates in the application.
- Updated relevant settings, utility functions, and tests to integrate this feature.
- Enhanced documentation to clarify the new permissions behavior and its impact on authorization checks.
```
