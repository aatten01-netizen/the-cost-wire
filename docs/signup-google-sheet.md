# Signup form -> Google Sheet (free)

One Sheet holds both the free brief signups and the price-alert choices.

1. Make a new Google Sheet called "Cost Wire signups". Row 1: `time`, `email`, `alert_item`, `alert_region`, `alert_threshold`.
2. In the sheet: Extensions > Apps Script. Replace the code with:

```js
function doPost(e) {
  var p = e.parameter || {};
  if (p.website) return ContentService.createTextOutput("ok");   // bot trap
  var email = (p.email || "").trim();
  if (!/^[^@\s,]+@[^@\s,]+\.[^@\s,]+$/.test(email)) {
    return HtmlService.createHtmlOutput("<p style='font-family:Georgia'>That email didn't look right. <a href='javascript:history.back()'>Back</a></p>");
  }
  // Alert choice (from alerts.html) is optional; the free signup sends only email.
  var pick = (p.alert_pick || "").split("|");
  var item = /^[a-z0-9_]{1,20}$/.test(pick[0] || "") ? pick[0] : "";
  var region = /^[A-Z0-9]{2,6}$/.test(pick[1] || "") ? pick[1] : "";
  var amount = /^[0-9]{1,4}$/.test(p.alert_threshold || "") ? p.alert_threshold : "";
  if (!(item && region && amount)) { item = ""; region = ""; amount = ""; }
  SpreadsheetApp.getActiveSheet().appendRow([new Date(), email, item, region, amount]);
  var msg = item ? "Thanks! Your alert is saved and you are on the Monday list." : "Thanks! You are on the list.";
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

Later, copy the sheet's emails into Resend as an audience for sending.
