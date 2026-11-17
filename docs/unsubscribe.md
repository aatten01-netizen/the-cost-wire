# Unsubscribe + mailing address (Step 24)

US email law (CAN-SPAM) says every email to readers needs **a working unsubscribe** and **your mailing address**, and anyone who unsubscribes must stop getting email within 10 business days. Every email The Cost Wire builds (weekly brief, state editions, price alerts) now has a footer with both, plus a `List-Unsubscribe` header so Gmail/Outlook show their own "Unsubscribe" button.

Nothing here costs money. Do it before any real reader gets an email.

## 1. Make the unsubscribe link (pick one, both free)
- **Google Form (easiest):** forms.google.com > Blank form > title "Unsubscribe from The Cost Wire" > one short-answer question "Your email" (required) > optional second question from `marketing/unsubscribe-exit-survey.md`. Send > link icon > copy the `https://docs.google.com/forms/...` link. Responses > link to Sheets.
- **Or email:** `mailto:YOUR-ADDRESS?subject=unsubscribe` (readers click, their mail app opens, they hit send).

## 2. Pick the mailing address
A real postal address you get mail at: a business address, a USPS PO box, or a registered mailbox. It is printed in every email, so don't use a home address unless you're OK with that. (Decision for Andy.)

## 3. Set them (never commit them)
In `.env` on the computer that sends, and as GitHub secrets if the Action ever sends:
```
UNSUBSCRIBE_URL=https://docs.google.com/forms/d/e/.../viewform
MAIL_POSTAL_ADDRESS=The Cost Wire, PO Box 123, Ames, IA 50010
```
Only `https://` or `mailto:` links are accepted. Until both are set, the footer shows "[unsubscribe link not set]" / "[mailing address not set]" (test emails still work) and `python -m costwire.launch_check` lists it as missing.

## 4. Honor unsubscribes
Download the unsubscribe Form's Sheet as CSV and save it **outside this repo**, e.g. `~/costwire/unsubscribes.csv` (it holds emails). Any CSV with an email column works; one email per line works too. Then:
```
UNSUBSCRIBES_FILE=~/costwire/unsubscribes.csv
```
The state-edition email (`costwire.state_email`) and price alerts (`costwire.alerts`) skip everyone on that list before anything else happens. Refresh the file before each send.

## Try it
```
PYTHONPATH=src python3 -m pytest -q tests/test_unsubscribe.py
UNSUBSCRIBE_URL=https://example.com/u MAIL_POSTAL_ADDRESS="PO Box 1, Ames, IA" PYTHONPATH=src python3 -m costwire.email_brief --to you@example.com --dry-run
```
