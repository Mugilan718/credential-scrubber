# Contributing

Thanks for your interest in Credential Scrubber. This is a small,
independently maintained project - contributions are welcome, but please
read this before opening a PR so your time isn't wasted on something
that won't be merged.

## Reporting a bug

Open a [GitHub issue](https://github.com/Mugilan718/credential-scrubber/issues)
and include:

- What you expected to happen, and what happened instead.
- The smallest input that reproduces it - ideally a short code snippet
  or config fixture (use fake/synthetic values, never a real secret).
- Your OS and how you're running the app (`run.bat`/`run.sh`, manual
  `python app.py`, or the packaged `.exe`).
- The output of `git log -1 --format=%H` (or the release version, if
  you're using a packaged build) so the exact code you tested against is
  clear.

**Found a security vulnerability instead of a regular bug?** Don't open
a public issue for it - see [SECURITY.md](SECURITY.md).

## Suggesting a feature

Open an issue describing the problem you're trying to solve, not just
the feature itself - it's easier to evaluate "I want to exclude certain
folders from a scan" than "add a folder picker." If it overlaps with
something in the README's "Future work" or "Known limitations" sections,
mention that too.

## Submitting a change

1. **Open an issue first for anything non-trivial** (new detection
   rules, a new feature, a behavior change) before writing code - this
   avoids spending time on a PR that doesn't fit the project's direction.
   Trivial fixes (typos, obviously broken links, a clear off-by-one) can
   skip straight to a PR.
2. **Fork the repo and branch from `main`.**
3. **Install dev dependencies and run the test suite before you start,
   so you know it's green on a clean checkout:**
   ```text
   pip install -r requirements-dev.txt
   python -m pytest tests/
   ```
4. **Make your change.** A few conventions this codebase follows
   consistently - matching them makes review faster:
   - `engine.py` is pure - no Flask/DB dependency, importable standalone.
     Keep it that way; app-specific glue belongs in `app.py`/`db.py`.
   - Never commit a real secret value, even a test one copied from
     somewhere - all fixtures use obviously fake values (e.g.
     `fake-Sup3rSecret123`), and comments in the test files call this
     convention out explicitly.
   - If you touch detection/redaction logic, add or update a test in
     `tests/` that would have caught the bug/regression you're fixing -
     see `tests/test_regressions.py` for the existing pattern (one test
     per pinned issue, named after what it guards against).
5. **Run the full test suite again** and make sure it's still green:
   ```text
   python -m pytest tests/
   ```
6. **Open a pull request** against `main`, describing what changed and
   why (not just what - the diff already shows what). Link the issue it
   addresses, if there is one.

## What this project is and isn't looking for

- **Detection/sanitization correctness fixes** and **new detection
  patterns** (with a test) are very welcome.
- **New integrations or UI features** are welcome if discussed in an
  issue first (see above) - this keeps the project's scope deliberate
  rather than accumulating unused options.
- This project does **not** accept contributions that would send scanned
  content anywhere over the network, by design (see the README's
  "Privacy and security properties" section) - a PR that introduces a
  network call for anything other than loading the page's own static
  assets will be declined regardless of its stated purpose.

## License

By contributing, you agree your contribution is licensed under this
project's [GNU AGPLv3 license](LICENSE), same as the rest of the codebase.
