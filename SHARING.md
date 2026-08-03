# Handing cal2xl to non-technical people

## Easiest: send the web app

Host the `site/` folder from `./build-web.sh` anywhere static — GitHub Pages,
Cloudflare, Netlify — and send the link. No download, no install, no security warning
on any operating system, and it works on a phone or a locked-down work laptop. The
calendar file is processed in their own browser and never gets uploaded anywhere.

> Here's the calendar converter: **[link]**
>
> Open it and give it a few seconds the first time — it loads itself into your browser.
> Then click the box to pick your `.ics` file, check the table looks right, and click
> **Download CSV**. Open the result in Excel.
>
> The table is fully editable before you download: click any cell to change it, use
> **New row** / **Delete row** underneath, and hover a column heading for a small `▾`
> menu that lets you rename a column, delete one, or add your own.

Everything below is the fallback: the downloadable apps, for anyone who needs to work
offline.

## Send a link, not an attachment

Gmail and Outlook **block `.exe` attachments outright**, including inside `.zip` — they
scan archive contents. The Mac and Linux files are 18–22 MB, which also crowds Gmail's
25 MB ceiling.

So: upload the files to Google Drive / Dropbox / OneDrive, and email the share link.
For the recipient this is still download → double-click.

Send each person only the file for their machine:

| Their computer | Send them |
| --- | --- |
| Windows | `cal2xl-windows.exe` |
| Mac (2020 or newer) | `cal2xl-mac-apple-silicon.zip` |
| Mac (2019 or older) | `cal2xl-mac-intel.zip` |
| Linux | `cal2xl-linux.tar.gz` |

Not sure which Mac someone has? Apple menu → About This Mac. "Apple M1/M2/M3/M4" means
Apple Silicon; "Intel" means Intel.

## Email text you can paste

> Here's the calendar converter: **[link]**
>
> Download it, then open it. Your computer will warn you that it's from an unknown
> developer — that's just because I wrote it myself rather than buying a certificate
> from Microsoft/Apple. It's safe.
>
> **On Windows:** double-click the file. If you see "Windows protected your PC", click
> **More info**, then **Run anyway**.
>
> **On a Mac:** double-click the .zip to unpack it. Then **right-click** the cal2xl app
> and choose **Open**, and **Open** again in the box that appears. You only have to do
> the right-click once — after that it opens normally.
>
> **On Linux:** double-click the .tar.gz to open it in Archive Manager and drag `cal2xl`
> out to your Desktop. Then right-click it and choose **Run as a Program**.
>
> Once it's open: click **Open .ics…**, pick your calendar file, check the table looks
> right (you can edit any cell), then click **Save CSV…**. Open the result in Excel.

## Why the warnings happen

The executables are unsigned. Removing the warnings means paying for certificates —
about $200–400/yr for Windows code signing, $99/yr for an Apple Developer ID plus
notarization. For fewer than ten people you can talk to, the one-time "Run anyway" and
"right-click → Open" are not worth that.

Antivirus software occasionally flags PyInstaller executables as suspicious. It's a
false positive from the self-extracting stub, and it is also only fixable with a
signing certificate.
