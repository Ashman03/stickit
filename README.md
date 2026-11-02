# Stickit

Erin's sticker-style day planner, hosted at **https://ashman03.github.io/stickit/** and installed on her iPhone as a home-screen web app.

- `index.html` is the whole app. Stickers are saved only on the phone (browser storage key `stickit-data-v1`, so don't rename it). Use Export and Import backup to move or protect them.
- `manifest.webmanifest`, `icons/` and the home-screen tags in `index.html` make it open full-screen with its own icon.
- `sw.js` makes it work offline. The page is always fetched fresh when online, so updates arrive on the next open. Bump `VERSION` in `sw.js` only if the icons or manifest change.
- `tests/run_tests.py` runs the checks (needs Python Playwright): `python3 tests/run_tests.py`

## Updating

Replace `index.html`, run the checks, commit to `main`, and Pages republishes within a few minutes.

## Versions

- **1.2.1**: review fixes (see REVIEWS-1.2.1.md)
- **1.2**: Erin's update from the first review, plus Plan my day
- **1.0**: first version on GitHub Pages, with home-screen and offline support
