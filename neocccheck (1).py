#!/usr/bin/env python3
import os
import re
import sys
import requests
from getpass import getpass

have_pyfiglet = False
have_rich = False
have_colorama = False

try:
    from pyfiglet import Figlet
    have_pyfiglet = True
except Exception:
    have_pyfiglet = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    have_rich = True
except Exception:
    have_rich = False

try:
    import colorama
    colorama.init()
    have_colorama = True
except Exception:
    have_colorama = False

CARD_PATTERNS = {
    "Visa": re.compile(r"^4\d{12}(\d{3})?$"),
    "Mastercard": re.compile(r"^(5[1-5]\d{14}|2(2[2-9]\d{12}|[3-6]\d{13}|7[01]\d{12}|720\d{12}))$"),
    "American Express": re.compile(r"^3[47]\d{13}$"),
    "Discover": re.compile(r"^(6011\d{12}|65\d{14}|64[4-9]\d{13}|622(12[6-9]|1[3-9]\d|[2-8]\d{2}|9([01]\d|2[0-5]))\d{10})$"),
    "JCB": re.compile(r"^(2131|1800|35\d{3})\d{11}$"),
    "Diners Club": re.compile(r"^3(?:0[0-5]|[68]\d)\d{11}$"),
}

def sanitize_digits(s: str) -> str:
    return ''.join(ch for ch in s if ch.isdigit())

def detect_brand(card_number: str) -> str:
    num = sanitize_digits(card_number)
    for brand, pattern in CARD_PATTERNS.items():
        if pattern.match(num):
            return brand
    return "Bilinmiyor"

def luhn_check(card_number: str) -> bool:
    digits = [int(d) for d in sanitize_digits(card_number)]
    digits_rev = digits[::-1]
    total = 0
    for i, d in enumerate(digits_rev):
        if i % 2 == 1:
            doubled = d * 2
            if doubled > 9:
                doubled -= 9
            total += doubled
        else:
            total += d
    return total % 10 == 0

def mask_card(card_number: str, keep_last: int = 4) -> str:
    digits = sanitize_digits(card_number)
    if len(digits) <= keep_last:
        return "*" * len(digits)
    masked = "*" * (len(digits) - keep_last) + digits[-keep_last:]
    groups = [masked[max(i-4,0):i] for i in range(len(masked), 0, -4)]
    return ' '.join(reversed(groups))

def send_telegram_message(bot_token: str, chat_id: str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text})
    resp.raise_for_status()
    return resp.json()

def print_rgb_title(title: str, r: int = 0, g: int = 200, b: int = 255):
    esc = f"\033[38;2;{r};{g};{b}m"
    reset = "\033[0m"
    print(esc + title + reset)

def print_pyfiglet_title(text: str, font: str = "slant", r: int = 138, g: int = 43, b: int = 226):
    if not have_pyfiglet:
        print("[pyfiglet yüklü değil — 'pip install pyfiglet' ile kurabilirsiniz]")
        return
    f = Figlet(font=font)
    art = f.renderText(text)
    print(f"\033[38;2;{r};{g};{b}m{art}\033[0m")

def print_rich_panel(text: str, style_rgb: tuple = (0,255,128), border_style: str = "bright_blue"):
    if not have_rich:
        print("[rich yüklü değil — 'pip install rich' ile kurabilirsiniz]")
        return
    console = Console()
    r,g,b = style_rgb
    title_text = Text(text, style=f"bold rgb({r},{g},{b})")
    panel = Panel(title_text, border_style=border_style, expand=False)
    console.print(panel)

def main():
    title_line = "== NEO CC CHECKERRR =="
    print()
    print_rgb_title(title_line, r=0, g=200, b=255)
    if have_pyfiglet:
        print_pyfiglet_title("NEO CC", font="slant", r=138, g=43, b=226)
    else:
        print("[Not: pyfiglet yüklü değil; ascii-art atlanıyor. Kurmak için: pip install pyfiglet]")
    if have_rich:
        print_rich_panel("NEOO CC CHECKERR BRO", style_rgb=(0,255,128), border_style="bright_blue")
    else:
        print("[Not: rich yüklü değil; panel atlanıyor. Kurmak için: pip install rich]")
    print()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token:
        bot_token = getpass("Telegram bot token : ").strip()
    if not chat_id:
        chat_id = input("Telegram chat_id: ").strip()
    raw_card = getpass("Kart numarasını gir : ").strip()
    digits = sanitize_digits(raw_card)
    if len(digits) < 8:
        print("Girilen rakam sayısı çok kısa. En az 8 haneli bir test numarası girin.")
        return
    brand = detect_brand(digits)
    luhn_ok = luhn_check(digits)
    masked = mask_card(digits, keep_last=4)
    message = (
        f"🪬 CC İnfo\n\n"
        f"CC: {brand}\n"
        f"No: {masked}\n"
        f"CC Check: {'Geçerli' if luhn_ok else 'Geçersiz'}\n\n"
        f"⚜️ OWNER : NEO"
        KARTIN CHECKLENDİİ REİSİM
    )
    try:
        resp = send_telegram_message(bot_token, chat_id, message)
        print("Telegram'a başarıyla gönderildi. Mesaj ID:", resp.get("result", {}).get("message_id"))
    except requests.HTTPError as e:
        print("Telegram gönderiminde hata:", e)
        if e.response is not None:
            print("Sunucu yanıtı:", e.response.text)
    except Exception as e:
        print("Beklenmeyen hata:", e)

if __name__ == "__main__":
    missing = []
    if not have_pyfiglet:
        missing.append("pyfiglet")
    if not have_rich:
        missing.append("rich")
    if not have_colorama:
        missing.append("colorama (opsiyonel, Windows için önerilir)")
    if missing:
        print("Not: Aşağıdaki paketler kurulu değil veya import edilemedi:", ", ".join(missing))
        print("İsterseniz bunları kurmak için terminalde şu komutları çalıştırabilirsiniz:")
        print("  pip install pyfiglet rich colorama")
        print()
    main()
    
    #editlersen ananı allahını 