# Signup form -> Google Sheet (free)

1. Make a new Google Sheet called "Cost Wire signups". Row 1: `time`, `email`.
2. In the sheet: Extensions > Apps Script. Replace the code with:

```js
function doPost(e) {
  var p = e.parameter || {};
  if (p.website) return ContentService.createTextOutput("ok");   // bot trap
  var email = (p.email || "").trim();
  if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    SpreadsheetApp.getActiveSheet().appendRow([new Date(), email]);
  }
  return HtmlService.createHtmlOutput("<p style='font-family:Georgia'>Thanks! You are on the list. <a href='javascript:history.back()'>Back</a></p>");
}
```
3. Deploy > New deployment > type "Web app" > Execute as: Me > Who has access: Anyone > Deploy. Copy the `/exec` link.
4. In GitHub repo settings > Secrets and variables > Actions > Variables, add `SIGNUP_FORM_URL` = that link.
5. When you are ready to go live, add variable `SIGNUP_LIVE` = `yes`. Until then the site shows the "coming soon" box.

Later, copy the sheet's emails into Resend as an audience for sending.
