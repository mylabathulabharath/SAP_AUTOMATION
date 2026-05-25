import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CDP_URL = os.environ.get("CDP_URL", "http://127.0.0.1:2222")
TARGET_URL = os.environ.get("TARGET_URL", "https://fiori.sap.brightspeed.com/logon#Shell-home")
PO_NUMBER = os.environ.get("PO_NUMBER", "4700001533")
MATERIAL_NUMBER = os.environ.get("MATERIAL_NUMBER", "1481799")
ARTIFACT_DIR = Path(os.environ.get("ARTIFACT_DIR", "."))

DISPLAY_PO_TILE_SELECTORS = [
    "text=Display Purchase Order",
    "xpath=//*[contains(normalize-space(.), 'Display Purchase Order') and (self::a or self::div or self::span)]",
    "css=a[aria-label*='Display Purchase Order']",
    "css=[title*='Display Purchase Order']",
    "css=[aria-label*='Display Purchase Order']",
]

MENU_BUTTON_SELECTORS = [
    "#cua2sapmenu_btn",
    "css=[id='cua2sapmenu_btn']",
    "css=[id*='sapmenu'][role='button']",
    "css=[id*='sapmenu']",
    "css=[aria-label='Menu']",
    "css=[aria-label*='Menu']",
    "css=[title='Menu']",
    "css=[title*='Menu']",
    "text=Menu",
]

PURCHASE_ORDER_PARENT_SELECTORS = [
    "xpath=//*[normalize-space(.)='Purchase Order']",
    "xpath=//*[contains(normalize-space(.), 'Purchase Order') and not(contains(normalize-space(.), 'Other Purchase Order'))]",
    "css=[title='Purchase Order']",
    "css=[aria-label='Purchase Order']",
    "text=Purchase Order",
]

OTHER_PURCHASE_ORDER_SELECTORS = [
    "xpath=//*[normalize-space(.)='Other Purchase Order']",
    "xpath=//*[contains(normalize-space(.), 'Other Purchase Order')]",
    "css=[title*='Other Purchase Order']",
    "css=[aria-label*='Other Purchase Order']",
    "text=Other Purchase Order",
]

PO_INPUT_SELECTORS = [
    "css=[role='dialog'] input:not([type='hidden'])",
    "css=[role='dialog'] [role='textbox']",
    "css=input[aria-label*='Purchase Order']:not([type='hidden'])",
    "css=input[title*='Purchase Order']:not([type='hidden'])",
    "css=input[type='text']",
    "css=input:not([type='hidden'])",
    "css=[role='textbox']",
]


def log(level, message):
    print(f"[{level}] {message}", flush=True)


def settle(page, milliseconds=500):
    page.wait_for_timeout(milliseconds)
    try:
        page.wait_for_load_state("domcontentloaded", timeout=2000)
    except Exception:
        pass


def browser_roots(page):
    """Return the page and all frames so SAP/Fiori iframe content is searchable."""
    roots = [("page", page)]
    for index, frame in enumerate(page.frames):
        if frame == page.main_frame:
            continue
        roots.append((f"frame[{index}]:{frame.url[:80]}", frame))
    return roots


def visible_locators(page, selector, max_matches=8):
    matches = []
    for root_name, root in browser_roots(page):
        try:
            locator = root.locator(selector)
            count = min(locator.count(), max_matches)
        except Exception:
            continue

        for i in range(count):
            loc = locator.nth(i)
            try:
                if loc.is_visible(timeout=500):
                    matches.append((root_name, loc))
            except Exception:
                continue
    return matches


def click_locator(locator):
    errors = []
    for action_name, action in [
        ("normal click", lambda: locator.click(timeout=2500)),
        ("forced click", lambda: locator.click(timeout=2500, force=True)),
        (
            "mouse event dispatch",
            lambda: (
                locator.dispatch_event("mousedown", timeout=1500),
                locator.dispatch_event("mouseup", timeout=1500),
                locator.dispatch_event("click", timeout=1500),
            ),
        ),
        ("DOM click", lambda: locator.evaluate("el => el.click()", timeout=1500)),
    ]:
        try:
            try:
                locator.scroll_into_view_if_needed(timeout=1000)
            except Exception:
                pass
            action()
            return action_name
        except Exception as exc:
            errors.append(f"{action_name}: {exc}")
    raise RuntimeError("; ".join(errors[-2:]))


def click_any(page, selectors, label, timeout_ms=12000, optional=False):
    deadline = time.monotonic() + timeout_ms / 1000
    last_error = None

    while time.monotonic() < deadline:
        for selector in selectors:
            matches = visible_locators(page, selector)
            for root_name, locator in matches:
                try:
                    method = click_locator(locator)
                    log("INFO", f"Clicked {label} with {method}; selector={selector}; root={root_name}")
                    settle(page)
                    return {"selector": selector, "root": root_name, "method": method}
                except Exception as exc:
                    last_error = exc
                    continue
        page.wait_for_timeout(300)

    if optional:
        log("WARN", f"Could not click {label}; continuing. Last error: {last_error}")
        return None
    raise RuntimeError(f"Could not click {label}. Last error: {last_error}")


def hover_or_click_any(page, selectors, label, timeout_ms=10000):
    deadline = time.monotonic() + timeout_ms / 1000
    last_error = None

    while time.monotonic() < deadline:
        for selector in selectors:
            matches = visible_locators(page, selector)
            for root_name, locator in matches:
                try:
                    try:
                        locator.scroll_into_view_if_needed(timeout=1000)
                    except Exception:
                        pass
                    try:
                        locator.hover(timeout=2500)
                        method = "hover"
                    except Exception:
                        method = click_locator(locator)
                    log("INFO", f"Activated {label} with {method}; selector={selector}; root={root_name}")
                    settle(page)
                    return {"selector": selector, "root": root_name, "method": method}
                except Exception as exc:
                    last_error = exc
                    continue
        page.wait_for_timeout(300)

    raise RuntimeError(f"Could not activate {label}. Last error: {last_error}")


def try_menu_path(page):
    used = {"menu": None, "purchase_order": None, "other_purchase_order": None}

    used["menu"] = click_any(page, MENU_BUTTON_SELECTORS, "menu bar button", timeout_ms=12000)

    try:
        # First try hover, since this is a submenu parent in SAP GUI for HTML.
        used["purchase_order"] = hover_or_click_any(
            page,
            PURCHASE_ORDER_PARENT_SELECTORS,
            "Purchase Order parent menu item",
            timeout_ms=8000,
        )
    except Exception as exc:
        log("WARN", f"Purchase Order parent was not activated cleanly: {exc}")

    used["other_purchase_order"] = click_any(
        page,
        OTHER_PURCHASE_ORDER_SELECTORS,
        "Other Purchase Order submenu item",
        timeout_ms=12000,
    )
    return used


def press_shift_f5(page):
    log("WARN", "Menu path did not complete. Trying Shift+F5 fallback.")
    page.bring_to_front()
    try:
        page.keyboard.press("Shift+F5")
    except Exception:
        page.keyboard.down("Shift")
        page.keyboard.press("F5")
        page.keyboard.up("Shift")
    settle(page, milliseconds=1200)
    return {"fallback": "keyboard:Shift+F5"}


def fill_po_number(page, po_number):
    last_error = None
    deadline = time.monotonic() + 12

    while time.monotonic() < deadline:
        for selector in PO_INPUT_SELECTORS:
            for root_name, locator in visible_locators(page, selector, max_matches=12):
                try:
                    try:
                        if not locator.is_enabled(timeout=500):
                            continue
                    except Exception:
                        pass
                    try:
                        if not locator.is_editable(timeout=500):
                            continue
                    except Exception:
                        # Some SAP GUI input controls do not report editable reliably.
                        pass

                    locator.click(timeout=2500, force=True)
                    try:
                        locator.fill(po_number, timeout=2500)
                    except Exception:
                        # Fallback for SAP fields that ignore fill().
                        modifier = "Meta" if sys.platform == "darwin" else "Control"
                        locator.press(f"{modifier}+A", timeout=1500)
                        locator.type(po_number, timeout=2500)

                    try:
                        locator.press("Enter", timeout=1500)
                    except Exception:
                        page.keyboard.press("Enter")

                    log("SUCCESS", f"Entered PO number {po_number}; selector={selector}; root={root_name}")
                    return {"selector": selector, "root": root_name}
                except Exception as exc:
                    last_error = exc
                    continue
        page.wait_for_timeout(300)

    # Last resort: type into the currently focused control if the dialog opened with focus already set.
    try:
        page.keyboard.type(po_number)
        page.keyboard.press("Enter")
        log("SUCCESS", f"Entered PO number {po_number} using focused-control fallback.")
        return {"selector": "focused-control", "root": "page"}
    except Exception as exc:
        last_error = exc

    raise RuntimeError(f"Could not enter PO number. Last error: {last_error}")


def save_debug_artifacts(page, prefix):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = ARTIFACT_DIR / f"{prefix}.png"
    html_path = ARTIFACT_DIR / f"{prefix}.html"
    try:
        page.screenshot(path=str(screenshot_path), full_page=False)
        log("INFO", f"Saved screenshot: {screenshot_path}")
    except Exception as exc:
        log("WARN", f"Could not save screenshot: {exc}")
    try:
        html_path.write_text(page.content(), encoding="utf-8")
        log("INFO", f"Saved HTML dump: {html_path}")
    except Exception as exc:
        log("WARN", f"Could not save HTML dump: {exc}")


def js_click_exact_material_option(page, material_number, item_number):
    """Click only the exact visible SAP listbox option for [item] material using JS."""
    item = str(item_number).strip().lstrip("0") or "0"
    script = r"""args => {
        const material = String(args.material);
        const item = String(args.item);
        const fragments = [`[ ${item} ]`, `[${item}]`, `[  ${item}  ]`];
        const normalize = s => (s || '').replace(/\s+/g, ' ').trim();
        const visible = el => {
            if (!el || !el.isConnected) return false;
            const style = window.getComputedStyle(el);
            if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) === 0) return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && rect.bottom >= 0 && rect.right >= 0 && rect.top <= window.innerHeight && rect.left <= window.innerWidth;
        };
        const candidates = [
            ...document.querySelectorAll('[role="option"]'),
            ...document.querySelectorAll('.lsListbox__value'),
            ...document.querySelectorAll('[data-itemvalue2]')
        ];
        const seen = new Set();
        for (const el of candidates) {
            if (seen.has(el)) continue;
            seen.add(el);
            if (!visible(el)) continue;
            const hay = normalize([
                el.textContent,
                el.getAttribute('data-itemvalue2'),
                el.getAttribute('title'),
                el.getAttribute('aria-label')
            ].filter(Boolean).join(' | '));
            if (!hay.includes(material)) continue;
            if (!fragments.some(f => hay.includes(f))) continue;
            el.scrollIntoView({block: 'center', inline: 'center'});
            const rect = el.getBoundingClientRect();
            const opts = {bubbles: true, cancelable: true, view: window, clientX: rect.left + Math.min(10, rect.width / 2), clientY: rect.top + rect.height / 2};
            for (const type of ['mouseover', 'mousemove', 'mousedown', 'mouseup', 'click']) {
                el.dispatchEvent(new MouseEvent(type, opts));
            }
            if (typeof el.click === 'function') el.click();
            return {
                id: el.id || '',
                tag: el.tagName,
                role: el.getAttribute('role') || '',
                cls: String(el.className || ''),
                text: normalize(el.textContent).slice(0, 220),
                dataItemValue2: el.getAttribute('data-itemvalue2') || ''
            };
        }
        return null;
    }"""

    for root_name, root in browser_roots(page):
        try:
            result = root.evaluate(script, {"material": material_number, "item": item})
            if result:
                log("INFO", f"Clicked exact visible material option using JS; root={root_name}; element={result}")
                settle(page, milliseconds=1200)
                return {"root": root_name, "method": "JS exact visible option", "element": result}
        except Exception:
            continue
    return None


def js_select_material_from_combobox(page, material_number, item_number):
    """Open the visible SAP combo input and click the matching list option."""
    script = r"""args => {
        const material = String(args.material);
        const item = String(args.item).trim().replace(/^0+/, '') || '0';
        const fragments = [`[ ${item} ]`, `[${item}]`, `[  ${item}  ]`];
        const normalize = s => (s || '').replace(/\s+/g, ' ').trim();

        const inputs = Array.from(document.querySelectorAll('input.lsField__input, input[aria-roledescription]'));
        const visible = el => {
            if (!el || !el.isConnected) return false;
            const style = window.getComputedStyle(el);
            if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) === 0) return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && rect.bottom >= 0 && rect.right >= 0 && rect.top <= window.innerHeight && rect.left <= window.innerWidth;
        };

        for (const input of inputs) {
            if (!visible(input)) continue;
            const hay = normalize(input.value || input.getAttribute('value') || input.getAttribute('title') || '');
            if (!hay.includes(material)) continue;

            try { input.scrollIntoView({block: 'center'}); } catch(e) {}
            try { input.click(); } catch(e) {}

            const controls = input.getAttribute('aria-controls');
            const searchContainers = [];
            if (controls) {
                const el = document.getElementById(controls);
                if (el) searchContainers.push(el);
            }
            searchContainers.push(...Array.from(document.querySelectorAll('[role="listbox"], .lsListbox, .sapMSelectList, .sapMSelectListUl')));

            for (const container of searchContainers) {
                if (!container) continue;
                const items = Array.from(container.querySelectorAll('li, div, [role="option"]'));
                for (const it of items) {
                    if (!visible(it)) continue;
                    const text = normalize(it.textContent || it.innerText || it.getAttribute('title') || '');
                    if (!text.includes(material)) continue;
                    if (!fragments.some(f => text.includes(f))) continue;
                    try { it.scrollIntoView({block: 'center'}); } catch(e) {}
                    try {
                        it.click();
                        return {inputId: input.id || '', containerId: container.id || '', itemText: text.slice(0, 220)};
                    } catch(e) {
                        try { const ev = new MouseEvent('click', {bubbles:true, cancelable:true}); it.dispatchEvent(ev); return {inputId: input.id||'', containerId: container.id||'', itemText: text.slice(0,220)}; } catch(e2) {}
                    }
                }
            }
        }
        return null;
    }"""

    for root_name, root in browser_roots(page):
        try:
            result = root.evaluate(script, {"material": material_number, "item": item_number})
            if result:
                log("INFO", f"Selected material via combobox helper; root={root_name}; result={result}")
                settle(page, milliseconds=800)
                return {"root": root_name, "result": result}
        except Exception:
            continue
    return None


def selected_item_matches(page, material_number, item_number):
    """Verify the visible Item field changed to the requested line/material."""
    item = str(item_number).strip().lstrip("0") or "0"
    script = r"""args => {
        const material = String(args.material);
        const item = String(args.item);
        const fragments = [`[ ${item} ]`, `[${item}]`, `[  ${item}  ]`];
        const normalize = s => (s || '').replace(/\s+/g, ' ').trim();
        const visible = el => {
            if (!el || !el.isConnected) return false;
            const style = window.getComputedStyle(el);
            if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) === 0) return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && rect.bottom >= 0 && rect.right >= 0 && rect.top <= window.innerHeight && rect.left <= window.innerWidth;
        };
        const nodes = [...document.querySelectorAll('input, [role="combobox"], [class*="lsField"], [class*="lsComboBox"], div, span')];
        for (const el of nodes) {
            if (!visible(el)) continue;
            if (el.closest('[role="listbox"]') || el.closest('.lsListbox') || el.getAttribute('role') === 'option') continue;
            const hay = normalize([
                el.value,
                el.textContent,
                el.getAttribute('title'),
                el.getAttribute('aria-label')
            ].filter(Boolean).join(' | '));
            if (!hay.includes(material)) continue;
            if (!fragments.some(f => hay.includes(f))) continue;
            const rect = el.getBoundingClientRect();
            return {
                id: el.id || '',
                tag: el.tagName,
                role: el.getAttribute('role') || '',
                cls: String(el.className || ''),
                text: hay.slice(0, 220),
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                w: Math.round(rect.width),
                h: Math.round(rect.height)
            };
        }
        return null;
    }"""

    for root_name, root in browser_roots(page):
        try:
            result = root.evaluate(script, {"material": material_number, "item": item})
            if result:
                log("INFO", f"Verified selected Item field is [{item}] {material_number}; root={root_name}; element={result}")
                return {"root": root_name, "element": result}
        except Exception:
            continue
    return None


def select_material_number(page, material_number, item_number="10"):
    log("INFO", f"Selecting material {material_number} for item {item_number}")
    save_debug_artifacts(page, "before_material_select")

    # First, try the combobox-specific selector which targets the visible
    # `lsField__input` combo input and clicks the matching dropdown entry.
    try:
        log("INFO", "Trying combobox-specific JS selection")
        cmb = js_select_material_from_combobox(page, material_number, item_number)
        if cmb:
            log("INFO", f"Combobox helper returned: {cmb}")
            verify = selected_item_matches(page, material_number, item_number)
            if verify:
                log("SUCCESS", f"Material selection verified via combobox helper: {verify}")
                save_debug_artifacts(page, f"material_selected_{material_number}_{item_number}")
                return {"method": "combobox_js", "verify": verify}
            else:
                log("WARN", "Combobox helper clicked an option but visible Item field did not update; continuing")
    except Exception as exc:
        log("WARN", f"Combobox helper failed: {exc}")

    # Try JS exact visible option click first
    for attempt in range(1, 4):
        log("INFO", f"Attempt {attempt}: trying JS click of exact visible option")
        res = js_click_exact_material_option(page, material_number, item_number)
        if res:
            log("INFO", f"JS click returned: {res}")
            verify = selected_item_matches(page, material_number, item_number)
            if verify:
                log("SUCCESS", f"Material selection verified: {verify}")
                save_debug_artifacts(page, f"material_selected_{material_number}_{item_number}")
                return {"method": "js_click_exact", "verify": verify}
            else:
                log("WARN", "JS click did not update visible Item field; retrying")
        page.wait_for_timeout(800)

    # Fallback: try pressing ArrowDown or F4 to open dropdown then JS click
    try:
        log("INFO", "Fallback: try focusing visible item field and opening dropdown then selecting")
        # Try clicking visible item field by geometry via JS
        page.evaluate("() => { const ev = new Event('focus'); document.querySelector('input, [role=combobox], .lsComboBox')?.dispatchEvent(ev); }")
        page.keyboard.press('F4')
        page.wait_for_timeout(800)
        res = js_click_exact_material_option(page, material_number, item_number)
        if res:
            verify = selected_item_matches(page, material_number, item_number)
            if verify:
                save_debug_artifacts(page, f"material_selected_{material_number}_{item_number}")
                return {"method": "f4_then_js", "verify": verify}
    except Exception as exc:
        log("WARN", f"Fallback material selection failed: {exc}")

    # Coordinate-click fallback: if we can find the visible Item field/element
    # that should reflect the selected material, click its center by mapping
    # the element bounding box from the frame viewport to the main page.
    try:
        info = selected_item_matches(page, material_number, item_number)
        if info and "element" in info and all(k in info["element"] for k in ("x", "y", "w", "h")):
            root_name = info.get("root")
            elem = info["element"]
            # Find the matching root/frame object
            for rn, root in browser_roots(page):
                if rn != root_name:
                    continue
                try:
                    ex, ey = int(elem["x"]), int(elem["y"])
                    ew, eh = int(elem["w"]), int(elem["h"])
                except Exception:
                    break

                # If root is the top-level page, coordinates are already global
                if rn == "page":
                    gx = ex + ew // 2
                    gy = ey + eh // 2
                else:
                    try:
                        # root is a Frame object; get its frame element bounding box
                        frame_el = root.frame_element()
                        box = frame_el.bounding_box()
                        if not box:
                            continue
                        gx = box["x"] + ex + ew // 2
                        gy = box["y"] + ey + eh // 2
                    except Exception:
                        continue

                log("INFO", f"Attempting coordinate click at global ({gx},{gy}) for element {elem}")
                try:
                    page.mouse.click(gx, gy, timeout=2500)
                    settle(page, milliseconds=800)
                    verify = selected_item_matches(page, material_number, item_number)
                    if verify:
                        log("SUCCESS", f"Material selection verified after coordinate click: {verify}")
                        save_debug_artifacts(page, f"material_selected_{material_number}_{item_number}")
                        return {"method": "coordinate_click_fallback", "verify": verify}
                except Exception as exc:
                    log("WARN", f"Coordinate click attempt failed: {exc}")
                break
    except Exception as exc:
        log("WARN", f"Coordinate-click fallback encountered an error: {exc}")

    save_debug_artifacts(page, "material_select_failed")
    raise RuntimeError(f"Could not select material {material_number} for item {item_number}")


def get_active_page(browser):
    contexts = browser.contexts
    context = contexts[0] if contexts else browser.new_context()
    pages = context.pages
    page = pages[-1] if pages else context.new_page()
    page.bring_to_front()
    return context, page


def run_automation():
    log("INFO", f"Connecting to Chrome over CDP at: {CDP_URL}")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context, page = get_active_page(browser)
        log("INFO", "Connected successfully.")

        log("INFO", f"Navigating to: {TARGET_URL}")
        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)

        print("\n" + "=" * 72)
        print("  PAUSE REQUIRED: complete login/MFA in the attached Chrome window.")
        print("  When the SAP screen is ready, return here and press ENTER.")
        print("=" * 72)
        input("Press [ENTER] to continue...")

        settle(page, milliseconds=1500)

        # If the launchpad tile is present, click it. If the user is already inside the app,
        # this step is skipped and the menu path is attempted directly.
        before_pages = len(context.pages)
        tile_result = click_any(
            page,
            DISPLAY_PO_TILE_SELECTORS,
            "Display Purchase Order tile",
            timeout_ms=12000,
            optional=True,
        )
        if tile_result:
            page.wait_for_timeout(2500)
            if len(context.pages) > before_pages:
                page = context.pages[-1]
                page.bring_to_front()
                log("INFO", "Detected a new tab/window after tile click; continuing there.")
            settle(page, milliseconds=1500)
        else:
            log("INFO", "Display Purchase Order tile was not found; assuming the current SAP screen is already correct.")

        used = None
        try:
            used = try_menu_path(page)
            log("SUCCESS", "Opened Other Purchase Order through the menu path.")
        except Exception as menu_exc:
            log("WARN", f"Menu path failed: {menu_exc}")
            used = press_shift_f5(page)

        fill_result = fill_po_number(page, PO_NUMBER)
        save_debug_artifacts(page, "screenshot_after_po_entry")

        # Attempt to select material number (if provided)
        try:
            if MATERIAL_NUMBER:
                mat_result = select_material_number(page, MATERIAL_NUMBER)
                log("INFO", f"Material selection result: {mat_result}")
        except Exception as mat_exc:
            log("WARN", f"Material selection failed: {mat_exc}")

        log("INFO", f"Navigation result: {used}")
        log("INFO", f"PO input result: {fill_result}")
        log("SUCCESS", "Menu navigation / fallback and PO entry completed.")

        # Do not close the CDP-connected browser; detaching leaves the desktop tab open.


if __name__ == "__main__":
    try:
        run_automation()
    except KeyboardInterrupt:
        log("ERROR", "Interrupted by user.")
        sys.exit(130)
    except Exception as exc:
        log("ERROR", f"Automation execution failed: {exc}")
        try:
            # No page object may exist here, so debug capture is handled inside the main flow.
            pass
        finally:
            sys.exit(1)
