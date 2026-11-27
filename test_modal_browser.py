#!/usr/bin/env python3
"""Prove the confirmation modal in a real browser.

Runs the page in Chromium, stubs the enquiry function with a page route,
and checks three things that only a browser can prove:

  1. when the server answers ok:true, the modal opens, the fields are
     cleared, and the page says so;
  2. when the server refuses, the modal does NOT open, the fields are NOT
     cleared, and the honest message is shown instead;
  3. the footer credit is there and points at https://aicoder.click.

Usage:  python3 test_modal_browser.py [--shots]
"""

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SHOTS = "--shots" in sys.argv
PORT = 8765

# The browser is installed for the root user; this sandbox runs with a
# different HOME, so the path is given explicitly.
CHROME = "/root/.cache/ms-playwright/chromium-1243/chrome-linux/chrome"
if not Path(CHROME).exists():
    CHROME = None


def fill(page):
    page.fill("#f-name", "Test Guest")
    page.fill("#f-email", "guest@example.com")
    page.fill("#f-dates", "12-19 December")
    page.fill("#f-msg", "Two anglers, one week.")


def main():
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    failures = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME)
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            def stub(status, body):
                def handler(route):
                    route.fulfill(
                        status=status,
                        content_type="application/json",
                        body=body,
                    )
                return handler

            # ---------- 1. the server confirms ----------
            page.route("**/.netlify/functions/enquiry",
                       stub(200, '{"ok":true,"transport":"smtp","storedInForms":true}'))
            page.goto(f"http://127.0.0.1:{PORT}/index.html")
            page.wait_for_selector("#enquiry-form")
            fill(page)
            page.click("#enquiry-form button[type=submit]")
            page.wait_for_selector("#enquiry-modal:not([hidden])", timeout=8000)
            if not failures:
                print("ok   the modal opens after the server confirmed")
            title = page.inner_text("#enquiry-modal-title")
            if title.strip() != "Your enquiry has been sent":
                failures.append(f"the modal title is {title!r}")
            else:
                print("ok   the modal says the enquiry has been sent")
            body = page.inner_text("#enquiry-modal-text")
            if "reply to you by email" not in body:
                failures.append(f"the modal text is {body!r}")
            else:
                print("ok   the modal says what happens next")
            for field in ("#f-name", "#f-email", "#f-dates", "#f-msg"):
                value = page.input_value(field)
                if value != "":
                    failures.append(f"{field} still holds {value!r}")
            if not failures:
                print("ok   the fields are cleared")
            if SHOTS:
                page.screenshot(path=str(ROOT / "modal-open.png"))
            page.keyboard.press("Escape")
            page.wait_for_selector("#enquiry-modal", state="hidden", timeout=4000)
            print("ok   Escape closes the modal")
            if not page.is_hidden("#enquiry-modal"):
                page.click("#enquiry-modal-close")
                page.wait_for_selector("#enquiry-modal", state="hidden", timeout=4000)
                print("ok   the Close button closes it too")

            # ---------- 2. the server refuses ----------
            page2 = browser.new_page(viewport={"width": 1280, "height": 900})
            page2.route("**/.netlify/functions/enquiry",
                        stub(500, '{"ok":false,"error":"the provider refused the send"}'))
            page2.goto(f"http://127.0.0.1:{PORT}/index.html")
            page2.wait_for_selector("#enquiry-form")
            fill(page2)
            page2.click("#enquiry-form button[type=submit]")
            page2.wait_for_timeout(1500)
            if page2.is_hidden("#enquiry-modal"):
                print("ok   the modal does NOT open when the send failed")
            else:
                failures.append("the modal opened although the send failed")
            if page2.input_value("#f-name") == "Test Guest":
                print("ok   the fields keep what the guest typed")
            else:
                failures.append("the fields were cleared although the send failed")
            if page2.is_visible("#enquiry-status-fallback"):
                print("ok   the honest message is shown instead")
            else:
                failures.append("the failure message is not shown")
            if SHOTS:
                page2.screenshot(path=str(ROOT / "modal-refused.png"))

            # ---------- 3. the credit ----------
            href = page2.get_attribute(".foot-credit a", "href")
            if href == "https://aicoder.click":
                print("ok   the credit links to https://aicoder.click")
            else:
                failures.append(f"the credit points at {href!r}")
            text = page2.inner_text(".foot-credit").strip()
            if text.replace("\n", " ") != "Created by aicoder.click":
                failures.append(f"the credit reads {text!r}")
            else:
                print("ok   the credit reads 'Created by aicoder.click'")

            # ---------- 4. the modal in another language ----------
            page2.goto(f"http://127.0.0.1:{PORT}/index.html?lang=de")
            page2.wait_for_selector("#enquiry-form")
            de = page2.inner_text("#enquiry-modal-title")
            if "gesendet" in de:
                print("ok   the modal is translated (German)")
            else:
                failures.append(f"the German modal title is {de!r}")

            browser.close()
    finally:
        server.terminate()

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nThe modal behaves as it should in a real browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
