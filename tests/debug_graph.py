"""Systematic graph debug — checks console errors, DOM state, and SVG dimensions."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

URL = "https://cornell.learnleadai.com"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    errors = []
    page.on("console", lambda m: errors.append(f"[{m.type}] {m.text}") if m.type in ("error","warning") else None)
    page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))

    print("Loading page...")
    page.goto(URL, wait_until="load", timeout=60_000)
    page.wait_for_timeout(8000)  # wait for graph.json fetch + D3 init

    # ── DOM checks ──
    info = page.evaluate("""() => {
        const ga   = document.getElementById('graph-area');
        const gp   = document.getElementById('graph-panel');
        const svg  = document.getElementById('graph-canvas');
        const gpR  = gp  ? gp.getBoundingClientRect()  : null;
        const gaR  = ga  ? ga.getBoundingClientRect()  : null;
        const svgR = svg ? svg.getBoundingClientRect() : null;
        return {
            graphArea:  gaR  ? {w: gaR.width,  h: gaR.height,  top: gaR.top,  left: gaR.left}  : null,
            graphPanel: gpR  ? {w: gpR.width,  h: gpR.height,  top: gpR.top,  left: gpR.left}  : null,
            svgEl:      svgR ? {w: svgR.width, h: svgR.height, top: svgR.top, left: svgR.left} : null,
            svgAttrW:   svg  ? svg.getAttribute('width')  : null,
            svgAttrH:   svg  ? svg.getAttribute('height') : null,
            svgChildren: svg ? svg.children.length : 0,
            graphPanelDisplay: gp ? getComputedStyle(gp).display : null,
            graphAreaDisplay:  ga ? getComputedStyle(ga).display  : null,
            graphPanelVisible: gp ? gp.offsetWidth + 'x' + gp.offsetHeight : null,
            layoutEl: document.querySelector('.layout') ? {
                w: document.querySelector('.layout').clientWidth,
                h: document.querySelector('.layout').clientHeight,
            } : null,
            sidebarW: document.querySelector('.sidebar') ? document.querySelector('.sidebar').clientWidth : null,
            graphStatus: document.getElementById('graph-status')?.textContent,
            nodeCount: document.querySelectorAll('#graph-canvas circle').length,
        };
    }""")

    print("\n=== DOM STATE ===")
    for k, v in info.items():
        print(f"  {k}: {v}")

    print("\n=== CONSOLE ERRORS ===")
    if errors:
        for e in errors:
            print(f"  {e}")
    else:
        print("  (none)")

    page.screenshot(path="tests/screenshots/debug_graph_desktop.png", full_page=False)
    print("\nScreenshot: tests/screenshots/debug_graph_desktop.png")

    # ── Mobile check ──
    page2 = browser.new_page(viewport={"width": 390, "height": 844})
    mob_errors = []
    page2.on("console", lambda m: mob_errors.append(f"[{m.type}] {m.text}") if m.type in ("error","warning") else None)
    page2.goto(URL, wait_until="load", timeout=60_000)
    page2.wait_for_timeout(8000)  # wait for graph.json fetch + D3 init
    # Tap graph tab
    page2.evaluate("switchTab('graph')")
    page2.wait_for_timeout(2000)  # wait for resize + paint

    mob_info = page2.evaluate("""() => {
        const gp  = document.getElementById('graph-panel');
        const svg = document.getElementById('graph-canvas');
        const gpR = gp?.getBoundingClientRect();
        return {
            graphPanelDisplay: gp ? getComputedStyle(gp).display : null,
            graphPanelRect: gpR ? {w: gpR.width, h: gpR.height} : null,
            svgAttrW: svg?.getAttribute('width'),
            svgAttrH: svg?.getAttribute('height'),
            svgChildren: svg ? svg.children.length : 0,
            nodeCount: document.querySelectorAll('#graph-canvas circle').length,
            graphAreaClasses: document.getElementById('graph-area')?.className,
        };
    }""")
    print("\n=== MOBILE DOM STATE (after switching to graph tab) ===")
    for k, v in mob_info.items():
        print(f"  {k}: {v}")
    if mob_errors:
        print("  Mobile errors:", mob_errors)

    page2.screenshot(path="tests/screenshots/debug_graph_mobile.png")
    print("  Mobile screenshot: tests/screenshots/debug_graph_mobile.png")

    browser.close()
