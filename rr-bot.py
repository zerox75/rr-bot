#!/usr/bin/env python3
"""
RR-BOT — Rival Regions Perk Auto-Upgrader (Playwright)
=======================================================
البيرك: Education  |  العملة: Gold

يستخدم متصفح Chrome حقيقي لتجاوز حماية Cloudflare.

SETUP (محلياً):
  pip install playwright && playwright install chromium

SETUP (على Railway):
  أضف ملف railway.toml — راجع الداشبورد للتعليمات
"""

import time
import datetime
from playwright.sync_api import sync_playwright

# ─── الإعدادات ────────────────────────────────────────────────────────────────

PERK     = 2    # 1=Strength  2=Education  3=Endurance
CURRENCY = 2    # 1=Money     2=Gold

# الكوكيز من متصفحك — F12 → Application → Cookies → rivalregions.com
COOKIES = [
    # {"name": "PHPSESSID", "value": "...", "domain": "rivalregions.com", "path": "/"},
    # {"name": "rr_f",      "value": "...", "domain": "rivalregions.com", "path": "/"},
]

# URL داشبورد Replit لإرسال النتائج
REPORT_URL = "https://412a0da2-35d7-4444-a33e-8ea67a6b47db-00-91m35if4vlsb.riker.replit.dev/api/bot/report"

COOLDOWN_RETRY_MIN = 30   # دقائق الانتظار عند اكتشاف الكولداون

# ─── كود البوت (لا تعدل هنا) ─────────────────────────────────────────────────

PERK_NAMES     = {1: "Strength", 2: "Education", 3: "Endurance"}
CURRENCY_NAMES = {1: "Money", 2: "Gold"}
BASE_URL       = "https://rivalregions.com"


def log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[RR-BOT] [{ts}] {msg}", flush=True)


def main() -> None:
    last_success_time    = None
    learned_interval_sec = None

    print("=" * 55)
    print(f"  RR-BOT — {PERK_NAMES.get(PERK)} / {CURRENCY_NAMES.get(CURRENCY)}")
    print("=" * 55)
    log("البوت شتغل ✅  — يفتح متصفح Chrome حقيقي")
    log("اضغط Ctrl+C للإيقاف")
    print()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--single-process",
            ],
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        if COOKIES:
            ctx.add_cookies(COOKIES)

        page = ctx.new_page()

        while True:
            try:
                log("جاري فتح الصفحة...")
                page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=30_000)

                # سحب CSRF token من المتصفح مباشرة
                c_html = page.evaluate("typeof c_html !== 'undefined' ? String(c_html) : null")

                if not c_html:
                    log("⚠️  ما لاقى c_html — تأكد من الكوكيز")
                    wait_sec = COOLDOWN_RETRY_MIN * 60
                else:
                    # الترقية عبر fetch داخل المتصفح الحقيقي
                    response_text = page.evaluate(f"""async () => {{
                        const r = await fetch('/perks/up/{PERK}/{CURRENCY}', {{
                            method: 'POST',
                            headers: {{
                                'X-Requested-With': 'XMLHttpRequest',
                                'Content-Type': 'application/x-www-form-urlencoded'
                            }},
                            body: 'c=' + c_html
                        }});
                        return await r.text();
                    }}""")

                    now      = time.time()
                    upgraded = "new_g" in response_text or "ajax_action" in response_text

                    if upgraded:
                        if last_success_time is not None:
                            learned_interval_sec = now - last_success_time
                            log(f"📊 تعلّم الكولداون: ~{learned_interval_sec/3600:.1f} ساعة")
                        last_success_time = now
                        wait_sec = (learned_interval_sec - 60) if learned_interval_sec else COOLDOWN_RETRY_MIN * 60
                        msg = f"✅ تمت الترقية: {PERK_NAMES[PERK]} بـ {CURRENCY_NAMES[CURRENCY]}"
                        log(msg)
                        # إرسال للداشبورد
                        if REPORT_URL:
                            try:
                                page.evaluate(f"""fetch('{REPORT_URL}', {{
                                    method: 'POST',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{
                                        success: true,
                                        message: '[Playwright] {msg}',
                                        nextUpgradeMs: {int(wait_sec * 1000)}
                                    }})
                                }})""")
                            except Exception:
                                pass
                    else:
                        wait_sec = COOLDOWN_RETRY_MIN * 60
                        msg = f"⏳ البيرك على كولداون — يحاول بعد {COOLDOWN_RETRY_MIN} دقيقة"
                        log(msg)
                        if REPORT_URL:
                            try:
                                page.evaluate(f"""fetch('{REPORT_URL}', {{
                                    method: 'POST',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{success: false, message: '[Playwright] {msg}'}})
                                }})""")
                            except Exception:
                                pass

            except KeyboardInterrupt:
                raise
            except Exception as e:
                log(f"❌ خطأ: {e}")
                wait_sec = 60

            next_time = datetime.datetime.now() + datetime.timedelta(seconds=wait_sec)
            log(f"⏰ المحاولة القادمة: {next_time.strftime('%H:%M:%S')}  ({int(wait_sec/60)} دقيقة)")
            print()
            time.sleep(wait_sec)

        browser.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 البوت وقف.")
