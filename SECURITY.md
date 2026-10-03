# Security Policy

Credential Scrubber exists to help keep secrets out of places they
shouldn't be, so vulnerabilities in it are treated seriously and
privately until a fix is available.

## Reporting a vulnerability

**Preferred: GitHub private vulnerability reporting.** Use the
[Security tab](https://github.com/Mugilan718/credential-scrubber/security)
on this repository and select **"Report a vulnerability"**. This opens a
private advisory visible only to the maintainer and you, and is the
fastest way to get a response.

**Alternative: email.** If you'd rather not use GitHub's reporting flow,
you can reach the maintainer at the GitHub-provided noreply address for
this account, `<github-user-id>+Mugilan718@users.noreply.github.com`
(visible on the [maintainer's GitHub profile](https://github.com/Mugilan718)
under "Keep my email address private," or by checking the author address
on any of their commits - this file intentionally doesn't hardcode the
numeric ID, since it isn't guessable and would otherwise go stale
silently). Include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (a minimal code sample or input that triggers
  the issue is ideal).
- The version/commit you tested against.

**Please do not open a public GitHub issue for a security
vulnerability** - that discloses it to everyone before a fix exists.

## What to expect

- Acknowledgement of your report within a few days.
- An assessment of severity and, if confirmed, a plan for a fix.
- Credit in the release notes/changelog if you'd like it (or anonymity,
  if you'd prefer).

This is a small, independently maintained open-source project, not a
funded security team - response times are best-effort, not SLA-backed.

## Scope

In scope:

- The detection/sanitization engine (`engine.py`) producing an incorrect
  or incomplete redaction that could leak a real secret.
- The desktop app (`app.py`, `static/`, `templates/`) mishandling,
  logging, or persisting a secret value it shouldn't.
- The ignore-list or scan-history storage (`db.py`) retaining a raw
  secret value it's documented not to.

Out of scope (but still worth a regular issue, not a security report):

- Detection gaps for secret shapes the tool doesn't yet recognize (a
  correctness/coverage issue, not a vulnerability in the usual sense -
  see the README's "Known limitations").
- Issues in the unsigned `.exe` release's code-signing status - this is
  a known, documented tradeoff (see the README's "Verifying your
  download" section), not a vulnerability to report.

## Supported versions

As a small project without parallel release branches, only the most
recent release is supported. If you're on an older version, please
upgrade before (or as part of) reporting an issue.
