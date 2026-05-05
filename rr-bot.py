#!/usr/bin/env python3
"""
RR-BOT — Rival Regions Perk Auto-Upgrader (Python)
====================================================
البيرك: Education  |  العملة: Gold

SETUP:
  1. pip install cloudscraper
  2. افتح متصفحك وسجل دخول على rivalregions.com
  3. F12 → Application → Cookies → rivalregions.com
     انسخ قيمة كل كوكي والصقها في قسم COOKIES أدناه
  4. شغل السكربت:  python rr_bot.py
"""

import re
import time
import datetime
import cloudscraper

# ─── الإعدادات ────────────────────────────────────────────────────────────────

PERK     = 2    # 1=Strength  2=Education  3=Endurance
CURRENCY = 2    # 1=Money     2=Gold

# الكوكيز من متصفحك — F12 → Application → Cookies → rivalregions.com
COOKIES = {
    # انسخ الكوكيز من المتصفح وضعها هنا، مثال:
    # "PHPSESSID": "abc123xyz...",
    # "rr_f":      "...",
}

# اختياري: URL داشبورد Replit لإرسال النتائج هناك
REPORT_URL = "https://412a0da2-35d7-4444-a33e-8ea67a6b47db-00-91m35if4vlsb.riker.replit.dev/api/bot/report"

COOLDOWN_RETRY_MIN = 30   # دقائق الانتظار عند اكتشاف الكولداون

# ─── كود البوت (لا تعدل هنا) ─────────────────────────────────────────────────

PERK_NAMES     = {1: "Strength", 2: "Education", 3: "Endurance"}
CURRENCY_NAMES = {1: "Money", 2: "Gold"}
BASE_URL       = "https://rivalregions.com"

# cloudscraper يتجاوز حماية Cloudflare تلقائياً
session = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)
session.headers.update({"Referer": BASE_URL + "/"})

last_success_time    = None
learned_interval_sec = None


def log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[RR-BOT] [{ts}] {msg}", flush=True)


def get_csrf_token() -> str | None:
    """يفتح الصفحة الرئيسية ويسحب c_html (CSRF token)."""
    try:
        r = session.get(BASE_URL + "/", timeout=15)
        # البحث في الـ HTML عن متغير c_html
        for pattern in [
            r'c_html\s*=\s*["\'\']([^"\'\'>\s]+)["\'\']',
            r'var\s+c_html\s*=\s*["\'\']?([\w\-]+)',
        ]:
            m = re.search(pattern, r.text)
            if m:
                return m.group(1)
        log("⚠️  ما قدر يلاقي c_html في الصفحة — تأكد من الكوكيز")
    except Exception as e:
        log(f"❌ خطأ في جلب الصفحة: {e}")
    return None


def report_to_dashboard(msg: str, ok: bool, next_sec: float | None = None) -> None:
    """يرسل النتيجة للداشبورد (اختياري)."""
    if not REPORT_URL:
        return
    try:
        body: dict = {"success": ok, "message": f"[Python] {msg}"}
        if next_sec:
            body["nextUpgradeMs"] = int(next_sec * 1000)
        session.post(REPORT_URL, json=body, timeout=8)
    except Exception:
        pass


def do_upgrade() -> tuple[bool | None, float]:
    """
    يحاول ترقية البيرك.
    يرجع (نجح؟, ثواني_للمحاولة_القادمة)
    """
    global last_success_time, learned_interval_sec

    token = get_csrf_token()
    if not token:
        return None, COOLDOWN_RETRY_MIN * 60

    try:
        r = session.post(
            f"{BASE_URL}/perks/up/{PERK}/{CURRENCY}",
            data={"c": token},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=15,
        )
        text = r.text.strip()
        upgraded = "new_g" in text or "ajax_action" in text

        if upgraded:
            now = time.time()
            if last_success_time is not None:
                learned_interval_sec = now - last_success_time
                h = learned_interval_sec / 3600
                log(f"📊 تعلّم الكولداون: ~{h:.1f} ساعة — سيُستخدم للجدولة القادمة")
            last_success_time = now

            next_sec = (learned_interval_sec - 60) if learned_interval_sec else COOLDOWN_RETRY_MIN * 60
            msg = f"✅ تمت الترقية: {PERK_NAMES[PERK]} بـ {CURRENCY_NAMES[CURRENCY]}"
            log(msg)
            report_to_dashboard(msg, True, next_sec)
            return True, next_sec

        else:
            msg = f"⏳ البيرك على كولداون — يحاول بعد {COOLDOWN_RETRY_MIN} دقيقة"
            log(msg)
            report_to_dashboard(msg, False, COOLDOWN_RETRY_MIN * 60)
            return False, COOLDOWN_RETRY_MIN * 60

    except Exception as e:
        msg = f"❌ خطأ: {e}"
        log(msg)
        report_to_dashboard(msg, False, COOLDOWN_RETRY_MIN * 60)
        return None, COOLDOWN_RETRY_MIN * 60


def main() -> None:
    perk_str     = PERK_NAMES.get(PERK, str(PERK))
    currency_str = CURRENCY_NAMES.get(CURRENCY, str(CURRENCY))

    print("=" * 55)
    print(f"  RR-BOT — {perk_str} / {currency_str}")
    print("=" * 55)
    log(f"البوت شتغل ✅  |  كولداون-ريتراي: {COOLDOWN_RETRY_MIN} دقيقة")
    log("اضغط Ctrl+C للإيقاف")
    print()

    while True:
        _, wait_sec = do_upgrade()
        next_time = datetime.datetime.now() + datetime.timedelta(seconds=wait_sec)
        log(f"⏰ المحاولة القادمة: {next_time.strftime('%H:%M:%S')}  ({int(wait_sec / 60)} دقيقة)")
        print()
        time.sleep(wait_sec)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 البوت وقف.")
