import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP_URL = os.environ.get("CDP_URL", "http://127.0.0.1:2222")
TARGET_URL = os.environ.get("TARGET_URL", "https://fiori.sap.brightspeed.com/logon#Shell-home")
PO_NUMBER = os.environ.get("PO_NUMBER", "4700001533")
MATERIAL_NUMBER = os.environ.get("MATERIAL_NUMBER", "1480461")
TARGET_ITEM_NUMBER = os.environ.get("TARGET_ITEM_NUMBER", "30")
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
    "xpath=//*[contains(@id, 'sapmenu') or contains(@title, 'Menu') or contains(@aria-label, 'Menu')]",
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

PURCHASE_ORDER_HISTORY_SELECTORS = [
    "css=[role='tab']:has-text('Purchase Order History')",
    "css=[action='TAB_ACCESS']:has-text('Purchase Order History')",
    "xpath=//*[@role='tab' and contains(normalize-space(.), 'Purchase Order History')]",
    "xpath=//*[contains(normalize-space(.), 'Purchase Order History') and (@action='TAB_ACCESS' or @role='tab')]",
    "xpath=//*[normalize-space(.)='Purchase Order History']/ancestor::*[@action='TAB_ACCESS'][1]",
    "xpath=//*[normalize-space(.)='Purchase Order History']/ancestor::*[@role='tab'][1]",
    "text=Purchase Order History",
]


def normalize_item_number(item_number):
    return str(item_number).strip().lstrip("0") or "0"


def target_item_fragments(item_number):
    item = normalize_item_number(item_number)
    return [f"[ {item} ]", f"[{item}]", f"[  {item}  ]"]


def material_selectors(material_number, item_number=TARGET_ITEM_NUMBER):
    """Return exact SAP listbox option selectors for the target line item/material.

    Important: these selectors intentionally target only listbox/options.
    The previous broad selector could click hidden text or the wrong visible node,
    which made the log say 1480461 was clicked while the selected Item field
    stayed on line 10 / 1481799.
    """
    item = normalize_item_number(item_number)
    return [
        f"css=.lsListbox__values .lsListbox__value[data-itemvalue2*='[ {item} ]'][data-itemvalue2*='{material_number}']",
        f"css=[role='option'][data-itemvalue2*='[ {item} ]'][data-itemvalue2*='{material_number}']",
        f"xpath=//*[@role='option' and contains(@data-itemvalue2, '[ {item} ]') and contains(@data-itemvalue2, '{material_number}')]",
        f"xpath=//*[contains(@class, 'lsListbox__value') and contains(@data-itemvalue2, '[ {item} ]') and contains(@data-itemvalue2, '{material_number}')]",
        f"xpath=//*[@role='option' and contains(normalize-space(.), '[ {item} ]') and contains(normalize-space(.), '{material_number}')]",
        f"xpath=//*[contains(@class, 'lsListbox__value') and contains(normalize-space(.), '[ {item} ]') and contains(normalize-space(.), '{material_number}')]",
        f"xpath=//*[@role='option' and contains(normalize-space(.), '[{item}]') and contains(normalize-space(.), '{material_number}')]",
        f"xpath=//*[contains(@class, 'lsListbox__value') and contains(normalize-space(.), '[{item}]') and contains(normalize-space(.), '{material_number}')]",
    ]


def current_item_field_selectors():
    """Selectors that try to focus/open the visible Item combo field, not the listbox row."""
    return [
        "xpath=//*[normalize-space(.)='Item:']/following::*[@role='combobox' or contains(@class,'lsField') or contains(@class,'lsComboBox') or contains(normalize-space(.), '[')][1]",
        "xpath=//*[contains(normalize-space(.), 'Item:')]/following::*[@role='combobox' or contains(@class,'lsField') or contains(@class,'lsComboBox') or contains(normalize-space(.), '[')][1]",
        "css=[role='combobox']",
        "css=[aria-haspopup='listbox']",
        "css=[role='button'][aria-haspopup='listbox']",
        "css=.lsComboBox",
        "css=[class*='lsField'][title*='Item']",
        "css=[class*='lsField'][aria-label*='Item']",
    ]


MATERIAL_DROPDOWN_OPENERS = [
    # Keep this list conservative. Broad selectors like [title*='Item'] can hit
    # unrelated SAP nodes and make Playwright think the dropdown was opened when
    # the list text only existed in hidden DOM.
    "xpath=//*[normalize-space(.)='Item:']/following::*[@role='combobox' or contains(@class,'lsField') or contains(@class,'lsComboBox') or contains(normalize-space(.), '[')][1]",
    "css=[role='combobox']",
    "css=[aria-haspopup='listbox']",
    "css=[role='button'][aria-haspopup='listbox']",
    "css=.lsComboBox",
    "css=[class*='lsField'][title*='Item']",
    "css=[class*='lsField'][aria-label*='Item']",
]

DIALOG_CONFIRM_SELECTORS = [
    "css=[role='button']:has-text('OK')",
    "css=[role='button']:has-text('Continue')",
    "css=[title='Continue']",
    "css=[title*='Continue']",
    "css=[aria-label='Continue']",
    "css=[aria-label*='Continue']",
    "css=[title='OK']",
    "css=[aria-label='OK']",
    "xpath=//*[(@role='button' or self::button or contains(@class, 'lsButton')) and (normalize-space(.)='OK' or contains(@title, 'Continue') or contains(@aria-label, 'Continue'))]",
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
    """Return page and all frames so SAP/Fiori iframe content is searchable."""
    roots = [("page", page)]
    for index, frame in enumerate(page.frames):
        if frame == page.main_frame:
            continue
        roots.append((f"frame[{index}]:{frame.url[:80]}", frame))
    return roots


def visible_locators(page, selector, max_matches=10):
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



def attached_locators(page, selector, max_matches=20):
    """Return attached locators across page/frames, without requiring visibility."""
    matches = []
    for root_name, root in browser_roots(page):
        try:
            locator = root.locator(selector)
            count = min(locator.count(), max_matches)
        except Exception:
            continue
        for i in range(count):
            matches.append((root_name, locator.nth(i)))
    return matches


def click_any_attached(page, selectors, label, timeout_ms=6000, optional=True):
    """Fallback click for SAP controls that are attached but do not report visible."""
    deadline = time.monotonic() + timeout_ms / 1000
    last_error = None

    while time.monotonic() < deadline:
        for selector in selectors:
            for root_name, locator in attached_locators(page, selector):
                try:
                    method = click_locator(locator, prefer_double_click=True)
                    log("INFO", f"Clicked attached {label} with {method}; selector={selector}; root={root_name}")
                    settle(page, milliseconds=1000)
                    return {"selector": selector, "root": root_name, "method": method, "visibility": "attached"}
                except Exception as exc:
                    last_error = exc
                    try:
                        locator.evaluate(
                            """el => {
                                el.scrollIntoView({block: 'center', inline: 'center'});
                                for (const type of ['mouseover', 'mousemove', 'mousedown', 'mouseup', 'click']) {
                                    el.dispatchEvent(new MouseEvent(type, {bubbles: true, cancelable: true, view: window}));
                                }
                                if (typeof el.click === 'function') el.click();
                            }""",
                            timeout=1500,
                        )
                        log("INFO", f"Clicked attached {label} with JS event dispatch; selector={selector}; root={root_name}")
                        settle(page, milliseconds=1000)
                        return {"selector": selector, "root": root_name, "method": "JS event dispatch", "visibility": "attached"}
                    except Exception as js_exc:
                        last_error = js_exc
                        continue
        page.wait_for_timeout(250)

    if optional:
        log("WARN", f"Could not click attached {label}. Last error: {last_error}")
        return None
    raise RuntimeError(f"Could not click attached {label}. Last error: {last_error}")


def report_text_locations(page, needle):
    """Log whether text exists anywhere in page/frame HTML, including hidden DOM."""
    found = []
    for root_name, root in browser_roots(page):
        try:
            html = root.content()
            if needle in html:
                found.append(root_name)
        except Exception:
            continue
    if found:
        log("INFO", f"Text '{needle}' exists in DOM at: {found}")
    else:
        log("WARN", f"Text '{needle}' was not found in current page/frame DOM.")
    return found


def js_click_exact_material_option(page, material_number, item_number):
    """Click only the exact visible SAP listbox option for [item] material."""
    item = normalize_item_number(item_number)
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


def selected_item_matches(page, material_number, item_number):
    """Verify the visible Item field changed to the requested line/material.

    Hidden SAP listbox rows are ignored. This prevents the false-success case
    where a hidden/dropdown row contains 1480461 but the field still shows item 10.
    """
    item = normalize_item_number(item_number)
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


def js_select_material_by_aria_controls(page, material_number, item_number):
    """Open the combobox (by clicking the visible input) and click the exact
    listbox row referenced by the input's `aria-controls` (or `aria-owns`).
    This targets the SAP HTML listbox id (e.g. DYN_6000-LISTSAPLMEGUI_ei).
    """
    item = normalize_item_number(item_number)
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

        // Find visible inputs that look like the SAP combobox field
        const inputs = [...document.querySelectorAll('input.lsField__input, input[aria-roledescription="Dropdown List Box"], [role="combobox"][aria-controls], [role="combobox"][aria-owns]')];
        for (const input of inputs) {
            if (!visible(input)) continue;
            // Try to open the popup if not already visible
            try { input.scrollIntoView({block: 'center', inline: 'center'}); } catch(e){}
            const rect = input.getBoundingClientRect();
            const clickOpts = {bubbles: true, cancelable: true, view: window, clientX: rect.left + Math.min(10, rect.width/2), clientY: rect.top + rect.height/2};
            for (const type of ['mouseover','mousemove','mousedown','mouseup','click']) input.dispatchEvent(new MouseEvent(type, clickOpts));
            if (typeof input.click === 'function') input.click();

            // Resolve aria-controls/owns value (may contain multiple ids)
            const aria = (input.getAttribute('aria-controls') || input.getAttribute('aria-owns') || '').trim();
            const ids = aria ? aria.split(/\s+/) : [];
            // Also try the nearest descendant listbox if aria not present
            const candidates = [];
            for (const id of ids) {
                try {
                    const el = document.getElementById(id);
                    if (el) candidates.push(el);
                } catch (e) {}
            }
            if (!candidates.length) {
                // try to find a nearby .lsListbox that looks like the dropdown
                const near = input.closest('div') || document.body;
                const found = near.querySelectorAll('.lsListbox, [role="listbox"]');
                for (const f of found) candidates.push(f);
            }

            for (const listbox of candidates) {
                if (!visible(listbox)) continue;
                const options = [...listbox.querySelectorAll('.lsListbox__value, [role="option"]')];
                for (const opt of options) {
                    if (!opt || !opt.isConnected) continue;
                    const hay = normalize([opt.textContent, opt.getAttribute('data-itemvalue2'), opt.getAttribute('title'), opt.getAttribute('aria-label')].filter(Boolean).join(' | '));
                    if (!hay.includes(material)) continue;
                    if (!fragments.some(f => hay.includes(f))) continue;
                    try { opt.scrollIntoView({block: 'center', inline: 'center'}); } catch(e){}
                    const r = opt.getBoundingClientRect();
                    const opts = {bubbles: true, cancelable: true, view: window, clientX: r.left + Math.min(10, r.width/2), clientY: r.top + r.height/2};
                    for (const type of ['mouseover','mousemove','mousedown','mouseup','click']) opt.dispatchEvent(new MouseEvent(type, opts));
                    if (typeof opt.click === 'function') opt.click();
                    return {id: opt.id||'', tag: opt.tagName, cls: String(opt.className||''), text: hay.slice(0,220), dataItemValue2: opt.getAttribute('data-itemvalue2')||''};
                }
            }
        }
        return null;
    }"""

    for root_name, root in browser_roots(page):
        try:
            result = root.evaluate(script, {"material": material_number, "item": item})
            if result:
                log("INFO", f"Clicked material via aria-controls helper; root={root_name}; element={result}")
                settle(page, milliseconds=1000)
                return {"root": root_name, "method": "JS aria-controls listbox", "element": result}
        except Exception:
            continue
    return None


def click_visible_item_field_by_js(page):
    """Click the visible Item combo field by geometry near the 'Item:' label."""
    script = r"""() => {
        const normalize = s => (s || '').replace(/\s+/g, ' ').trim();
        const visible = el => {
            if (!el || !el.isConnected) return false;
            const style = window.getComputedStyle(el);
            if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) === 0) return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && rect.bottom >= 0 && rect.right >= 0 && rect.top <= window.innerHeight && rect.left <= window.innerWidth;
        };
        const all = [...document.querySelectorAll('label, span, div, input, [role="combobox"], [class*="lsField"], [class*="lsComboBox"]')].filter(visible);
        const labels = all.filter(el => /^Item:?$/i.test(normalize(el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '')));
        const controls = all.filter(el => {
            if (el.closest('[role="listbox"]') || el.closest('.lsListbox') || el.getAttribute('role') === 'option') return false;
            const text = normalize([el.value, el.textContent, el.getAttribute('title'), el.getAttribute('aria-label')].filter(Boolean).join(' | '));
            const cls = String(el.className || '');
            return /\[\s*\d+\s*\]/.test(text) || el.getAttribute('role') === 'combobox' || (el.getAttribute('aria-haspopup') || '').includes('listbox') || cls.includes('lsComboBox') || cls.includes('lsField');
        }).map(el => {
            const r = el.getBoundingClientRect();
            return {el, r, text: normalize([el.value, el.textContent, el.getAttribute('title'), el.getAttribute('aria-label')].filter(Boolean).join(' | '))};
        }).filter(o => o.r.width >= 50 && o.r.height >= 8 && o.r.height <= 80);

        let best = null;
        if (labels.length) {
            for (const label of labels) {
                const lr = label.getBoundingClientRect();
                for (const c of controls) {
                    const sameRow = Math.abs((c.r.top + c.r.bottom) / 2 - (lr.top + lr.bottom) / 2);
                    const rightOf = c.r.left - lr.right;
                    if (rightOf < -10 || rightOf > 600 || sameRow > 40) continue;
                    const score = sameRow + Math.max(0, rightOf) / 20 + (c.text.includes('[') ? -10 : 0);
                    if (!best || score < best.score) best = {...c, score};
                }
            }
        }
        if (!best) {
            for (const c of controls) {
                if (!/\[\s*\d+\s*\]/.test(c.text)) continue;
                const score = c.r.top + (c.r.width > 100 ? -10 : 0);
                if (!best || score < best.score) best = {...c, score};
            }
        }
        if (!best) return null;
        const el = best.el;
        el.scrollIntoView({block: 'center', inline: 'center'});
        const rect = el.getBoundingClientRect();
        const x = rect.right - 8;
        const y = rect.top + rect.height / 2;
        const opts = {bubbles: true, cancelable: true, view: window, clientX: x, clientY: y};
        for (const type of ['mouseover', 'mousemove', 'mousedown', 'mouseup', 'click']) {
            el.dispatchEvent(new MouseEvent(type, opts));
        }
        if (typeof el.focus === 'function') el.focus();
        if (typeof el.click === 'function') el.click();
        return {
            id: el.id || '',
            tag: el.tagName,
            role: el.getAttribute('role') || '',
            cls: String(el.className || ''),
            text: best.text.slice(0, 220),
            x: Math.round(rect.left),
            y: Math.round(rect.top),
            w: Math.round(rect.width),
            h: Math.round(rect.height)
        };
    }"""
    for root_name, root in browser_roots(page):
        try:
            result = root.evaluate(script)
            if result:
                log("INFO", f"Clicked visible Item field by geometry; root={root_name}; element={result}")
                settle(page, milliseconds=800)
                return {"root": root_name, "method": "JS item-field geometry", "element": result}
        except Exception:
            continue
    return None

def try_confirm_dialog(page):
    """Press Enter/click OK if the SAP Other Purchase Order dialog is still open."""
    try:
        page.keyboard.press("Enter")
        settle(page, milliseconds=1200)
    except Exception:
        pass
    result = click_any(page, DIALOG_CONFIRM_SELECTORS, "dialog OK/Continue", timeout_ms=2500, optional=True)
    if result:
        settle(page, milliseconds=2500)
    return result


def visible_exact_material_option_exists(page, material_number, item_number):
    selectors = material_selectors(material_number, item_number)
    for selector in selectors:
        matches = visible_locators(page, selector, max_matches=20)
        if matches:
            return True
    return False


def try_click_material_visible_or_attached(page, material_number, item_number=TARGET_ITEM_NUMBER, timeout_ms=5000):
    selectors = material_selectors(material_number, item_number)

    # First use exact visible listbox options only.
    result = click_any(
        page,
        selectors,
        f"line item {normalize_item_number(item_number)} / material {material_number}",
        timeout_ms=timeout_ms,
        optional=True,
        prefer_double_click=False,
    )
    if result:
        return result

    # Then use exact JS scan, again restricted to visible role=option/listbox rows.
    result = js_click_exact_material_option(page, material_number, item_number)
    if result:
        return result

    # Do not use the previous broad hidden/attached fallback for material rows.
    # Hidden rows caused a false success while the visible Item field stayed wrong.
    return None


def try_open_material_dropdown(page, material_number, item_number=TARGET_ITEM_NUMBER):
    """Open SAP item/material dropdown/listbox, then let caller select the exact target row."""
    log("INFO", "Trying to open the visible Item dropdown before selecting the exact row.")

    # Click the visible Item combo field near the 'Item:' label first.
    geometry_result = click_visible_item_field_by_js(page)
    if geometry_result:
        for key in ["Alt+ArrowDown", "F4"]:
            try:
                log("INFO", f"Trying item-field keyboard opener after geometry click: {key}")
                page.keyboard.press(key)
                settle(page, milliseconds=1000)
                if visible_exact_material_option_exists(page, material_number, item_number):
                    return {"method": f"geometry+keyboard:{key}", "geometry": geometry_result}
            except Exception as exc:
                log("WARN", f"Keyboard opener {key} failed: {exc}")

    # Try conservative selectors that represent the item combo itself.
    deadline = time.monotonic() + 12
    tried = 0
    while time.monotonic() < deadline:
        for selector in MATERIAL_DROPDOWN_OPENERS:
            matches = visible_locators(page, selector, max_matches=15)
            for root_name, locator in matches:
                tried += 1
                try:
                    try:
                        locator.scroll_into_view_if_needed(timeout=1000)
                    except Exception:
                        pass
                    method = click_locator(locator)
                    log("INFO", f"Clicked possible Item dropdown opener with {method}; selector={selector}; root={root_name}")
                    settle(page, milliseconds=700)
                    try:
                        page.keyboard.press("Alt+ArrowDown")
                        settle(page, milliseconds=800)
                    except Exception:
                        pass
                    if visible_exact_material_option_exists(page, material_number, item_number):
                        return {"method": method, "selector": selector, "root": root_name}
                except Exception:
                    continue
        page.wait_for_timeout(250)

    log("WARN", f"No opener produced a visible exact option for item {normalize_item_number(item_number)} / material {material_number}; tried {tried} opener candidates.")
    return None

def click_locator(locator, prefer_double_click=False):
    errors = []
    actions = []
    if prefer_double_click:
        actions.append(("double click", lambda: locator.dblclick(timeout=2500)))
    actions.extend([
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
    ])

    for action_name, action in actions:
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


def click_any(page, selectors, label, timeout_ms=12000, optional=False, prefer_double_click=False):
    deadline = time.monotonic() + timeout_ms / 1000
    last_error = None

    while time.monotonic() < deadline:
        for selector in selectors:
            matches = visible_locators(page, selector)
            for root_name, locator in matches:
                try:
                    method = click_locator(locator, prefer_double_click=prefer_double_click)
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
    settle(page, milliseconds=1500)
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
                        pass

                    locator.click(timeout=2500, force=True)
                    try:
                        locator.fill(po_number, timeout=2500)
                    except Exception:
                        modifier = "Meta" if sys.platform == "darwin" else "Control"
                        locator.press(f"{modifier}+A", timeout=1500)
                        locator.type(po_number, timeout=2500)

                    try:
                        locator.press("Enter", timeout=1500)
                    except Exception:
                        page.keyboard.press("Enter")

                    log("SUCCESS", f"Entered PO number {po_number}; selector={selector}; root={root_name}")
                    settle(page, milliseconds=1200)
                    try_confirm_dialog(page)
                    settle(page, milliseconds=3000)
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
        settle(page, milliseconds=1200)
        try_confirm_dialog(page)
        settle(page, milliseconds=3500)
        return {"selector": "focused-control", "root": "page"}
    except Exception as exc:
        last_error = exc

    raise RuntimeError(f"Could not enter PO number. Last error: {last_error}")


def select_material_number(page, material_number, item_number=TARGET_ITEM_NUMBER):
    item = normalize_item_number(item_number)
    log("INFO", f"Selecting line item {item} / material number {material_number} from the Item dropdown.")

    try_confirm_dialog(page)
    save_debug_artifacts(page, "before_material_select")
    report_text_locations(page, material_number)

    precheck = selected_item_matches(page, material_number, item_number)
    if precheck:
        log("INFO", f"Target line item {item} / material {material_number} is already selected.")
        return {"method": "already selected", "verification": precheck}

    result = None
    for attempt in range(1, 4):
        log("INFO", f"Material selection attempt {attempt}/3 for line item {item} / material {material_number}.")

        # First try the aria-controls targeting helper that clicks the input's
        # referenced listbox (precise SAP listbox id like DYN_6000-LISTSAPLMEGUI_ei).
        try:
            aria_result = js_select_material_by_aria_controls(page, material_number, item_number)
            if aria_result:
                try:
                    page.keyboard.press("Enter")
                    settle(page, milliseconds=1200)
                except Exception:
                    pass
                verification = selected_item_matches(page, material_number, item_number)
                if verification:
                    log("SUCCESS", f"Verified selected line item {item} / material {material_number} via aria-controls.")
                    aria_result["verification"] = verification
                    return aria_result
                log("WARN", "aria-controls click did not verify; will continue with other fallbacks.")
                save_debug_artifacts(page, f"aria_click_verify_failed_attempt_{attempt}")
        except Exception as exc:
            log("WARN", f"aria-controls helper threw: {exc}")

        # If the exact option is already visible, click it. Otherwise open dropdown first.
        if not visible_exact_material_option_exists(page, material_number, item_number):
            opener_result = try_open_material_dropdown(page, material_number, item_number)
            if opener_result:
                log("INFO", f"Dropdown opener result: {opener_result}")

        result = try_click_material_visible_or_attached(page, material_number, item_number, timeout_ms=7000)
        if result:
            try:
                page.keyboard.press("Enter")
                settle(page, milliseconds=1200)
            except Exception:
                pass
            verification = selected_item_matches(page, material_number, item_number)
            if verification:
                log("SUCCESS", f"Verified selected line item {item} / material {material_number}.")
                result["verification"] = verification
                return result

            log("WARN", "Clicked the material option, but the visible Item field did not verify. Retrying.")
            save_debug_artifacts(page, f"material_verify_failed_attempt_{attempt}")

        # Close any stray dropdown and reset focus before the next attempt.
        try:
            page.keyboard.press("Escape")
            settle(page, milliseconds=600)
        except Exception:
            pass

    save_debug_artifacts(page, "material_select_failed")
    raise RuntimeError(
        f"Could not verify selected line item {item} / material {material_number}. "
        "The script will not continue to Purchase Order History because the screenshot would show the wrong Item field. "
        "Check material_verify_failed_attempt_* and material_select_failed*.png/html."
    )

def click_purchase_order_history(page):
    log("INFO", "Clicking Purchase Order History tab.")
    result = click_any(
        page,
        PURCHASE_ORDER_HISTORY_SELECTORS,
        "Purchase Order History tab",
        timeout_ms=20000,
    )
    settle(page, milliseconds=2000)
    log("SUCCESS", "Purchase Order History tab is selected.")
    return result


def save_debug_artifacts(page, prefix, include_frames=True):
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

    if include_frames:
        for index, frame in enumerate(page.frames):
            if frame == page.main_frame:
                continue
            try:
                safe_index = str(index).zfill(2)
                frame_path = ARTIFACT_DIR / f"{prefix}_frame_{safe_index}.html"
                frame_path.write_text(frame.content(), encoding="utf-8")
                log("INFO", f"Saved frame HTML dump: {frame_path}")
            except Exception as exc:
                log("WARN", f"Could not save frame[{index}] HTML dump: {exc}")


def get_active_page(browser):
    contexts = browser.contexts
    context = contexts[0] if contexts else browser.new_context()
    pages = context.pages
    page = pages[-1] if pages else context.new_page()
    page.bring_to_front()
    return context, page


def maybe_switch_to_new_page(context, previous_count, current_page):
    if len(context.pages) > previous_count:
        page = context.pages[-1]
        page.bring_to_front()
        log("INFO", "Detected a new tab/window; continuing there.")
        return page
    current_page.bring_to_front()
    return current_page


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
            page = maybe_switch_to_new_page(context, before_pages, page)
            settle(page, milliseconds=1500)
        else:
            log("INFO", "Display Purchase Order tile was not found; assuming the current SAP screen is already correct.")

        try:
            navigation_result = try_menu_path(page)
            log("SUCCESS", "Opened Other Purchase Order through the menu path.")
        except Exception as menu_exc:
            log("WARN", f"Menu path failed: {menu_exc}")
            navigation_result = press_shift_f5(page)

        po_result = fill_po_number(page, PO_NUMBER)
        save_debug_artifacts(page, "screenshot_after_po_entry")

        material_result = select_material_number(page, MATERIAL_NUMBER)
        history_result = click_purchase_order_history(page)
        save_debug_artifacts(page, "sc-1")

        log("INFO", f"Navigation result: {navigation_result}")
        log("INFO", f"PO input result: {po_result}")
        log("INFO", f"Material selection result: {material_result}")
        log("INFO", f"Purchase Order History result: {history_result}")
        log("SUCCESS", "Completed PO entry, material selection, Purchase Order History tab, and sc-1 screenshot.")

        # Do not close the CDP-connected browser; detaching leaves the desktop tab open.


if __name__ == "__main__":
    try:
        run_automation()
    except KeyboardInterrupt:
        log("ERROR", "Interrupted by user.")
        sys.exit(130)
    except Exception as exc:
        log("ERROR", f"Automation execution failed: {exc}")
        sys.exit(1)
