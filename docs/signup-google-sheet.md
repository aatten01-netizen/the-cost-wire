# Signup form -> Google Sheet (free)

One Sheet holds both the free brief signups and the price-alert choices.

1. Make a new Google Sheet called "Cost Wire signups". Row 1: `time`, `email`, `alert_item`, `alert_region`, `alert_threshold`, `state`, `pro_plan`.
   (Already made the sheet? Just type `state` in cell F1 and `pro_plan` in cell G1.)
2. In the sheet: Extensions > Apps Script. Replace the code with:

```js
function doPost(e) {
  var p = e.parameter || {};
  if (p.website) return ContentService.createTextOutput("ok");   // bot trap
  var email = (p.email || "").trim();
  if (!/^[^@\s,]+@[^@\s,]+\.[^@\s,]+$/.test(email)) {
    return HtmlService.createHtmlOutput("<p style='font-family:Georgia'>That email didn't look right. <a href='javascript:history.back()'>Back</a></p>");
  }
  // Alert choice (from alerts.html) is optional; the free signup sends email + state.
  var pick = (p.alert_pick || "").split("|");
  var item = /^[a-z0-9_]{1,20}$/.test(pick[0] || "") ? pick[0] : "";
  var region = /^[A-Z0-9]{2,6}$/.test(pick[1] || "") ? pick[1] : "";
  var amount = /^[0-9]{1,4}$/.test(p.alert_threshold || "") ? p.alert_threshold : "";
  if (!(item && region && amount)) { item = ""; region = ""; amount = ""; }
  // State choice (from the free signup) is optional: IA, IL, MN or WI, else blank.
  var state = /^(IA|IL|MN|WI)$/.test(p.state || "") ? p.state : "";
  // Pro waitlist answer (from pricing.html) is optional: monthly, yearly or maybe, else blank.
  var plan = /^(monthly|yearly|maybe)$/.test(p.pro_plan || "") ? p.pro_plan : "";
  SpreadsheetApp.getActiveSheet().appendRow([new Date(), email, item, region, amount, state, plan]);
  var msg = item ? "Thanks! Your alert is saved and you are on the Monday list."
          : plan ? "Thanks! You are on the Pro waitlist and the free Monday list. Nothing was charged."
          : "Thanks! You are on the list.";
  return HtmlService.createHtmlOutput("<p style='font-family:Georgia'>" + msg + " <a href='javascript:history.back()'>Back</a></p>");
}
```
3. Deploy > New deployment > type "Web app" > Execute as: Me > Who has access: Anyone > Deploy. Copy the `/exec` link.
   (Already deployed the old version? Deploy > Manage deployments > edit > Version: New version, so the link stays the same.)
4. In GitHub repo settings > Secrets and variables > Actions > Variables, add `SIGNUP_FORM_URL` = that link.
5. When you are ready to go live, add variable `SIGNUP_LIVE` = `yes`. Until then the site shows the "coming soon" box.
6. Alert sign-up (site/alerts.html) is a separate go-ahead: add variable `ALERTS_SIGNUP_LIVE` = `yes` only when you want readers to pick alerts. Until then that page is a "coming soon" preview.

## Turning the Sheet into the alert list
1. File > Download > Comma-separated values. Save it OUTSIDE the repo folder (it has reader emails).
2. Run: `PYTHONPATH=src python -m costwire.alert_signup ~/Downloads/signups.csv ~/costwire-private/alerts.csv`
   It keeps only rows with a valid alert choice for an item and state we publish (newest choice wins per reader + item + state) and refuses to write inside the repo.
3. Use that file as `ALERTS_FILE` for `python -m costwire.alerts` (mock sender for now; no real email).

## Turning the Sheet into the per-state reader list
1. Download the Sheet as CSV OUTSIDE the repo (same as above).
2. Run: `PYTHONPATH=src python -m costwire.state_list ~/Downloads/signups.csv ~/costwire-private/readers.csv`
   It writes `email,state`, one row per reader (newest signup wins; a later alert-only row keeps their state). Blank state = the main brief. It prints how many readers picked each state and refuses to write inside the repo.
3. Check who would get which edition (dry run, sends nothing): `READERS_FILE=~/costwire-private/readers.csv PYTHONPATH=src python -m costwire.state_email`
4. To see each edition in your own inbox: add `STATE_EMAIL_LIVE=yes RESEND_API_KEY=... BRIEF_TEST_EMAIL=you@example.com`. It sends ONE test email per edition to that address only (max 5). Readers are never emailed by this.

Later, copy the sheet's emails into Resend as an audience for sending.

## Pro waitlist tally ("would you pay?")
When the signup is live (and Pro checkout is not), the pricing page shows a "Tell me when Pro opens" form that saves a `pro_plan` answer (monthly / yearly / maybe) in column G. Nothing is charged.
1. Download the Sheet as CSV OUTSIDE the repo.
2. Run: `PYTHONPATH=src python -m costwire.pro_waitlist ~/Downloads/signups.csv`
   It prints counts only (never emails): clear yes (monthly + yearly) vs the goal of 5, maybe, and clear yes per state. Writes no file.
3. Put the numbers (no names) in LOG.md. At 5 clear yes, make the Stripe Payment Link and set `PRO_CHECKOUT_URL` + `PRO_CHECKOUT_LIVE=yes`; the waitlist form then disappears and the real checkout button shows.
