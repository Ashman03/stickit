"""Stickit checks. Run from the repo root:  python3 tests/run_tests.py [--shots DIR]

Needs Python Playwright with Chromium. Serves the app locally, fakes the clock,
and checks the date logic, the main flows, layout, contrast and tap sizes.
"""
import datetime as dt, functools, http.server, json, os, sys, tempfile, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
STORE_KEY = "stickit-data-v1"
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


def item(id, title, cat, date, time=None, end=None, repeat=None, due=False, subject=None, done=()):
    return {"id": id, "title": title, "cat": cat, "date": date, "time": time, "end": end, "repeat": repeat,
            "due": due, "subject": subject, "doneDates": list(done), "created": "2026-01-01T00:00:00Z"}


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


SAMPLE_DAY = dt.datetime(2026, 11, 2, 10, 0)  # a Monday


def sample_store():
    d = lambda n: (SAMPLE_DAY.date() + dt.timedelta(days=n)).isoformat()
    items = [
        item("a1", "Water the plants", "garden", d(0), repeat={"freq": "daily"}, done=[d(0)]),
        item("a2", "Gym", "exercise", d(0), "06:30", "07:30", {"freq": "weekly", "days": [1, 3, 5]}),
        item("a3", "Work", "work", d(0), "08:30", "17:00", {"freq": "weekly", "days": [1, 2, 3, 4, 5]}),
        item("a4", "Essay draft", "uni", d(2), due=True, subject="s1"),
        item("a5", "Book vet appointment", "home", d(-2)),
        item("a6", "Lecture", "uni", d(-7), "18:00", "20:00", {"freq": "weekly", "days": [2]}, subject="s1"),
        item("a7", "Fold washing", "home", d(0)),
    ]
    subs = [{"id": "s1", "code": "ABC101", "name": "Introduction to Statistics", "color": "lilac", "created": None}]
    return {"format": 1, "items": items, "subjects": subs, "lastExport": None}


class App:
    def __init__(self, browser, base):
        self.browser, self.base = browser, base

    def open(self, when, store=None, scheme="light", width=390, hash=""):
        ctx = self.browser.new_context(viewport={"width": width, "height": 844}, color_scheme=scheme,
                                       accept_downloads=True, locale="en-AU")
        ctx.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        ctx.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        pg = ctx.new_page()
        pg.errors = []
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and "ERR_FAILED" not in m.text and pg.errors.append(m.text))
        pg.clock.install(time=when)
        pg.goto(self.base + "index.html")
        if store is not None:
            pg.evaluate("([k, v]) => localStorage.setItem(k, v)", [STORE_KEY, json.dumps(store)])
        pg.goto(self.base + "index.html" + hash)
        pg.reload()
        pg.wait_for_selector("#sheet")
        return pg

    @staticmethod
    def close(pg):
        pg.context.close()


def overlap(a, b):
    return not (a["right"] <= b["left"] or b["right"] <= a["left"] or a["bottom"] <= b["top"] or b["bottom"] <= a["top"])


def run(app):
    # 1. Sun and moon follow the arc and never touch the date block.
    for width in (360, 390, 412):
        for hh, mm in [(6, 0), (7, 30), (9, 0), (12, 0), (15, 0), (17, 50), (18, 0), (21, 0), (0, 0), (3, 0), (5, 50)]:
            pg = app.open(dt.datetime(2026, 11, 2, hh, mm), {"format": 1, "items": [], "subjects": []}, width=width)
            r = pg.evaluate("""() => {
              const box = e => { const b = e.getBoundingClientRect(); return {left:b.left,right:b.right,top:b.top,bottom:b.bottom}; };
              return {sky: box(document.getElementById('sky-body')),
                      parts: [...document.querySelectorAll('#weekday, #daynav .dt, #daynav button')].map(box)}; }""")
            hit = any(overlap(r["sky"], p) for p in r["parts"])
            check(f"sky clear of date at {hh:02}:{mm:02}, {width}px", not hit)
            App.close(pg)
    pg = app.open(dt.datetime(2026, 11, 2, 12, 0), {"format": 1, "items": [], "subjects": []})
    noon = pg.evaluate("() => { const c = document.querySelector('#sky-body circle'); return c ? +c.getAttribute('cx') : null; }")
    check("sun is at the top of the arc at noon", noon is not None and abs(noon - 195) < 1, f"cx={noon}")
    App.close(pg)

    # 2. Monthly repeat on the 31st lands on the last day of shorter months.
    st = {"format": 1, "items": [item("m1", "Pay rent", "home", "2026-10-31", repeat={"freq": "monthly"})], "subjects": []}
    for day, expect in [(dt.datetime(2026, 11, 30, 9), True), (dt.datetime(2026, 11, 29, 9), False),
                        (dt.datetime(2027, 2, 28, 9), True), (dt.datetime(2026, 12, 31, 9), True),
                        (dt.datetime(2026, 12, 30, 9), False)]:
        pg = app.open(day, st)
        shown = "Pay rent" in pg.inner_text("#sheet")
        check(f"monthly 31st shown on {day.date()}: {expect}", shown == expect)
        App.close(pg)

    # 3. Carried-over stickers say which day they're from.
    pg = app.open(SAMPLE_DAY, sample_store())
    meta = pg.locator(".sticker", has_text="Book vet appointment").locator(".meta").inner_text()
    check("carried-over sticker says 'From Saturday'", meta.startswith("From Saturday"), meta)
    # 8. Done stickers sink, and focus returns to the tick.
    titles = pg.locator(".list").first.locator(".title").all_inner_texts()
    check("done sticker sits at the bottom of the day", titles and titles[-1] == "Water the plants", " / ".join(titles))
    pg.locator('.tick[data-tick="a7"]').click()
    titles = pg.locator(".list").first.locator(".title").all_inner_texts()
    focused = pg.evaluate("() => document.activeElement && document.activeElement.getAttribute('data-tick')")
    check("ticked sticker moves to the bottom", titles[-1] in ("Fold washing", "Water the plants") and titles.index("Fold washing") > titles.index("Gym"), " / ".join(titles))
    check("focus returns to the same tick button", focused == "a7", str(focused))
    check("no script errors on Today", not pg.errors, "; ".join(pg.errors))
    App.close(pg)

    # 4. Coming back from the background on a new day refreshes straight away.
    pg = app.open(dt.datetime(2026, 11, 2, 23, 59), {"format": 1, "items": [], "subjects": []})
    before = pg.inner_text("#weekday")
    pg.clock.set_fixed_time(dt.datetime(2026, 11, 3, 0, 1))
    pg.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")
    after = pg.inner_text("#weekday")
    check("new day shows as soon as the app is reopened", before == "Monday" and after == "Tuesday", f"{before} -> {after}")
    App.close(pg)

    # 5 and 6. Form validation.
    pg = app.open(SAMPLE_DAY, {"format": 1, "items": [], "subjects": []})
    pg.click("#add-btn"); pg.fill("#f-title", "Test"); pg.fill("#f-time", "10:00"); pg.fill("#f-end", "09:00")
    pg.click("#save-btn")
    check("end time before start is refused", pg.is_visible("#f-end-err") and pg.is_visible("#overlay"))
    pg.fill("#f-end", "11:00"); pg.select_option("#f-repeat", "daily"); pg.fill("#f-until", "2026-11-01")
    pg.click("#save-btn")
    check("'stop repeating' before start is refused", pg.is_visible("#f-until-err") and pg.is_visible("#overlay"))
    pg.fill("#f-until", "2026-11-09"); pg.click("#save-btn")
    check("valid sticker saves", pg.is_hidden("#overlay") and "Test" in pg.inner_text("#sheet"))
    App.close(pg)

    # 7. A bad entry in storage doesn't break the app.
    bad = {"format": 1, "items": [{"id": "x", "title": "No date"}, item("g1", "Good one", "home", "2026-11-02"), "junk"],
           "subjects": [{"code": ""}, {"id": "s1", "code": "ABC101", "color": "nope"}]}
    pg = app.open(SAMPLE_DAY, bad)
    check("bad stored entries are skipped, good ones load", "Good one" in pg.inner_text("#sheet") and not pg.errors, "; ".join(pg.errors))
    App.close(pg)

    # 9. Plan my day fits untimed stickers into free time, after now, between 7am and 9pm.
    pg = app.open(SAMPLE_DAY, sample_store())
    pg.click("[data-plan-day]")
    st2 = json.loads(pg.evaluate("k => localStorage.getItem(k)", STORE_KEY))
    plan = st2.get("plans", {}).get("2026-11-02", {})
    busy = [(8 * 60 + 30, 17 * 60), (6 * 60 + 30, 7 * 60 + 30)]
    toM = lambda t: int(t[:2]) * 60 + int(t[3:])
    slots = [(toM(p["time"]), toM(p["end"])) for p in plan.values()]
    ok = bool(slots) and all(10 * 60 <= s and e <= 21 * 60 and not any(s < be and bs < e for bs, be in busy) for s, e in slots)
    ok = ok and all(not (a[0] < b[1] and b[0] < a[1]) for i, a in enumerate(slots) for b in slots[i + 1:])
    check("plan my day: slots after now, within 7am-9pm, no clashes", ok, json.dumps(plan))
    check("plan shows 'Planned' on the sticker", "Planned" in pg.inner_text("#sheet"))
    pg.click("[data-clear-plan]")
    check("clear plan removes it", "Planned" not in pg.inner_text("#sheet"))
    App.close(pg)

    # 10. Backup round trip.
    pg = app.open(SAMPLE_DAY, sample_store())
    with pg.expect_download() as dl:
        pg.click("[data-export]")
    path = os.path.join(tempfile.mkdtemp(), "backup.json"); dl.value.save_as(path)
    pg.evaluate("k => localStorage.removeItem(k)", STORE_KEY); pg.reload()
    pg.set_input_files("#import-file", path); pg.click("[data-import-confirm]")
    st3 = json.loads(pg.evaluate("k => localStorage.getItem(k)", STORE_KEY))
    check("export then import restores everything", len(st3["items"]) == 7 and len(st3["subjects"]) == 1)
    App.close(pg)

    # 11 and 12. Week view.
    pg = app.open(SAMPLE_DAY, sample_store(), hash="#week")
    check("backup buttons only on Today", pg.locator("[data-export]").count() == 0)
    check("week view shows work as compact lines", pg.locator(".blockline-btn", has_text="Work").count() == 5)
    check("week heading says 'Next 7 days'", pg.inner_text("#weekday") == "Next 7 days")
    check("week view blocks show their category icon (not a tick-box look)", pg.locator(".blockline-btn .mini-dot svg").count() == 5)
    App.close(pg)

    # Small fixes from the v1.2.1 review.
    pg = app.open(SAMPLE_DAY, {"format": 1, "items": [item("z", "Other day", "home", "2026-11-05")], "subjects": []})
    pg.click("#prev-day")
    check("empty past day reads 'yesterday' in lower case", "Nothing on for yesterday yet." in pg.inner_text("#sheet"))
    App.close(pg)
    pg = app.open(SAMPLE_DAY, sample_store())
    label = pg.locator('.body[data-edit="a2"]').get_attribute("aria-label")
    check("screen reader label includes the time", label.startswith("Edit Gym, 6:30"), label)
    pg.click("#add-btn")
    inert = pg.evaluate("() => document.querySelector('.app').inert && document.querySelector('.tabs').inert")
    pg.click("#cancel-btn")
    back = pg.evaluate("() => !document.querySelector('.app').inert && !document.querySelector('.tabs').inert")
    check("page behind an open sheet is blocked, then released", inert and back)
    App.close(pg)

    # Layout, contrast, tap sizes and screenshots on every screen.
    screens = [("today", "", None), ("week", "#week", None), ("uni", "#uni", None),
               ("subject", "#uni", "[data-open-subject]"), ("form", "", "#add-btn"),
               ("subject-form", "#uni", "[data-add-subject]"), ("past-day", "", "#prev-day")]
    worst, fails, small = 99, [], set()
    for scheme in ("light", "dark"):
        for width in (320, 360, 390, 412):
            for name, hash, click in screens:
                pg = app.open(dt.datetime(2026, 11, 2, 20, 30), sample_store(), scheme=scheme, width=width, hash=hash)
                if click: pg.click(click); pg.wait_for_timeout(100)
                over = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                if over > 0: fails.append(f"sideways scroll {over}px on {name} {width}px {scheme}")
                c = pg.evaluate(CONTRAST_JS)
                for x in c:
                    worst = min(worst, x["ratio"])
                    if x["ratio"] < x["need"]: fails.append(f'{scheme} {name}: "{x["text"]}" {x["ratio"]}:1')
                if width == 390:
                    for t in pg.evaluate(TARGETS_JS):
                        if t["h"] < 44 or t["w"] < 44: small.add(f'{name}: {t["label"]} {t["w"]}x{t["h"]}')
                    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f"{scheme}-{name}.png"))
                if pg.errors: fails.append(f"script error on {name}: {pg.errors}")
                App.close(pg)
    check("no sideways scrolling, every text passes contrast, no errors", not fails, "; ".join(sorted(set(fails))[:12]))
    print(f"lowest text contrast found: {worst}:1")
    check("every tap target at least 44x44", not small, "; ".join(sorted(small)))


CONTRAST_JS = r"""() => {
  const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v /= 255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); };
    return .2126*f(m[0]) + .7152*f(m[1]) + .0722*f(m[2]); };
  const alpha = c => { const m = c.match(/[\d.]+/g); return m.length > 3 ? +m[3] : 1; };
  const bg = el => { for (let e = el; e; e = e.parentElement) { const s = getComputedStyle(e);
      if (e.classList && e.classList.contains('scene')) return s.backgroundColor;
      if (alpha(s.backgroundColor) > .5) return s.backgroundColor; } return 'rgb(255,255,255)'; };
  const out = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walk.nextNode()) { const n = walk.currentNode, el = n.parentElement;
    if (!n.textContent.trim() || !el) continue; const s = getComputedStyle(el), r = el.getBoundingClientRect();
    if (s.visibility === 'hidden' || r.width === 0 || el.closest('[hidden]') || el.closest('.vh')) continue;
    const a = lum(s.color), b = lum(bg(el)), ratio = Math.round(((Math.max(a,b)+.05)/(Math.min(a,b)+.05))*100)/100;
    const size = parseFloat(s.fontSize), bold = +s.fontWeight >= 700;
    out.push({text: n.textContent.trim().slice(0, 30), ratio, need: (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5}); }
  return out; }"""

TARGETS_JS = r"""() => [...document.querySelectorAll('button, input, select, label.chip, summary')].filter(e => {
    const r = e.getBoundingClientRect(); return r.width && r.height && !e.closest('[hidden]') && getComputedStyle(e).visibility !== 'hidden'
      && !(e.type === 'file') && !(e.tagName === 'INPUT' && e.closest('label')); })  /* a box inside its label: the whole label row is the tap area */
  .map(e => { const r = e.getBoundingClientRect(); let w = r.width, h = r.height;
    if (e.classList.contains('round')) { w += 14; h += 14; }  /* invisible ::after enlarges the tap area by 7px each side */
    return {label: (e.getAttribute('aria-label') || e.textContent || e.id || e.type).trim().slice(0, 24), w: Math.round(w), h: Math.round(h)}; })"""


if __name__ == "__main__":
    srv, base = serve()
    with sync_playwright() as p:
        b = p.chromium.launch()
        run(App(b, base))
        b.close()
    srv.shutdown()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)
