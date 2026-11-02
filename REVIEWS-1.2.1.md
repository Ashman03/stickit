# Stickit 1.2.1 – review notes

Version 1.2 is Erin's update, made from Ashley's review list. It also adds a new **Plan my day** button that fits stickers without a set time into the free gaps in the day. Version 1.2.1 is that update plus a few small fixes found while reviewing it. Everything was tested in a phone-sized browser in light and dark mode at 320, 360, 390 and 412 pixels wide (the width range of current iPhones), with the clock set to different times and dates. All 62 automatic checks pass. They live in `tests/run_tests.py` so they can be rerun on the next update.

## What changed

**From Erin's 1.2 (all 17 items on the list were done):**
- Sun and moon now travel the right path (sun 6am–6pm, moon 6pm–6am) and never cover the date.
- "Still to do from earlier" stickers say which day they're from.
- Monthly stickers on the 29th–31st now show on the last day of shorter months.
- The date updates straight away when the app is reopened.
- End times and "stop repeating" dates are checked.
- Stored data is cleaned on load, like imports.
- Shorter one-line details, "Next 7 days" heading, compact work blocks in the week, done stickers move to the bottom, backup buttons only on Today, a tidier add form and Australian date format.
- New: **Plan my day** and **Clear plan**.

**Added in 1.2.1:**
- Week view: work and event blocks show their category icon. Before, a hollow circle looked like a tick box that did nothing.
- Every button is now at least 44 × 44 points, the iPhone standard ("Plan my day", "Add a task", the day headings in the week view and the backup buttons were 39–40).
- "Back to today" and "All subjects" have a back arrow, so they read as "go back" rather than as a selected tab.
- An empty past day reads "Nothing on for yesterday yet" instead of "Yesterday".
- VoiceOver now reads a sticker's time and details, not just its name.
- While the add or edit sheet is open, VoiceOver and the keyboard can't wander onto the page behind it.

## Design critique (ease of use)

| Finding | Severity | What changed |
|---|---|---|
| Week view blocks had a hollow circle that looked like a tick box but couldn't be ticked | Medium | **Fixed**: shows the category icon instead |
| "Back to today" and "All subjects" looked the same as the selected tab | Low | **Fixed**: added a back arrow |
| "Nothing on for Yesterday yet" had a capital in the middle of a sentence | Low | **Fixed** |
| The header is now about 64 points taller, so roughly one less sticker fits on screen | Medium | **Kept on purpose**: the extra height is what keeps the sun clear of the date at every hour. Trimming it means a flatter arc or a smaller sun, which changes the look Erin chose. It can be trimmed by about 30 points if she'd rather have more room |
| Plan my day doesn't say how it works (7am–9pm, fixed lengths such as 30 minutes for home and 60 for uni), and a planned time can't be moved, only cleared | Medium | **For Erin to decide**: this changes how the feature behaves, so it wasn't changed here |
| All 17 requested items | — | **Checked**: each one confirmed; the date, layout and flow items have automatic tests |

## Accessibility review

| Finding | Severity | What changed |
|---|---|---|
| Five kinds of button were under 44 × 44 | Medium | **Fixed** |
| VoiceOver read "Edit Gym" without the time or details | Medium | **Fixed** |
| With a sheet open, VoiceOver could move to the page behind it | Medium | **Fixed** |
| Buttons are 44 × 44, not 48 × 48 | Low | **Kept on purpose**: 44 points is Apple's standard for iPhone apps; 48 is Android's |

**Text contrast** was checked on every piece of visible text, on every screen, in both modes. The minimum standard is 4.5:1 for normal text.
- Lowest anywhere: **4.95:1** (crossed-out done stickers in dark mode). Light mode lowest: 5.12:1.
- Everyday details text: 7.38:1 light and 6.38:1 dark. Main text and headings: 8:1 or better.

**Also checked and passing:** nothing scrolls sideways at any width; colour is never the only signal (done shows a star and crossed-out text, deadlines say "due", and errors are written out); every field has a label and errors say what to fix; Escape closes sheets; the star animation is switched off when the phone's reduce-motion setting is on; nothing flashes.

## Senior developer review

| Finding | Risk | What changed |
|---|---|---|
| Saved stickers, the storage name and old backups | High if broken | **Checked**: same storage name; an old backup imports into 1.2.1 and an export round-trips exactly |
| Bad or damaged entries in storage | Medium | **Checked**: they're skipped and the rest loads (tested) |
| Plan my day placing stickers on top of work or each other | Medium | **Checked**: plans only go after the current time, between 7am and 9pm, with no clashes (tested) |
| Plans aren't included in backups | Low | **Kept on purpose**: plans are only kept for 7 days, so they're temporary |
| Home-screen settings, icon and offline support | High if broken | **Checked**: all still in place |
| Security | — | **Checked**: everything typed is made safe before it's shown, there's no private data in the code, and the only outside request is for the two Google fonts |

## Graphic designer review

**Verdict: Polish.** What reads first is the day name, then the deadline banner, then the stickers. That's the right order.

**What's working:** one consistent sticker style (chunky outline, offset shadow, slight tilt) across every screen; a tight palette of pastels with one dark ink; two fonts used with discipline; dark mode matches light mode screen for screen; and the new compact week view is much calmer.

**Polish items:** the empty band of sky under the date (see the header row above), and the back-arrow fix (done).

## Not covered

- Tested in a phone-sized Chromium browser, not on a real iPhone in Safari.
- The two Google fonts were blocked in the test browser, so screenshots used the backup font.
- No live test with VoiceOver switched on.

**One thing to try on the phone:** open Stickit from the home-screen icon in the evening and check the moon sits clear of the date, then tick a sticker and make sure it drops to the bottom.
