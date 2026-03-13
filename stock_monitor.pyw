import threading
import time
import urllib.request
import json
import os
import sys
import winreg
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont
import pystray

# ─────────────────────────────────────────
#  Configuração
# ─────────────────────────────────────────
INTERVALO_MINUTOS = 5

# ficheiro JSON na mesma pasta do script
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_FILE = os.path.join(BASE_DIR, "stocks.json")

DEFAULT_STOCKS = [
    {"symbol": "^GSPC",   "name": "S&P 500"},
    {"symbol": "VWCE.AS", "name": "VWCE Amsterdão"},
]
# ─────────────────────────────────────────


# ── Config JSON ───────────────────────────

def load_stocks():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_STOCKS


def save_stocks(stocks):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)


# ── Yahoo Finance ─────────────────────────

def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        meta = data["chart"]["result"][0]["meta"]
        return meta["regularMarketPrice"], meta.get("previousClose")
    except:
        return None, None


# ── Ícone ─────────────────────────────────

def get_system_text_color():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
        winreg.CloseKey(key)
        return (0, 0, 0, 255) if value == 1 else (255, 255, 255, 255)
    except:
        return (255, 255, 255, 255)


def make_icon(text, change_pct=None):
    SIZE = 256
    FONT_SIZE = 180

    fnt = None
    for path in ["C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/tahomabd.ttf"]:
        try:
            fnt = ImageFont.truetype(path, FONT_SIZE)
            break
        except:
            pass
    if fnt is None:
        fnt = ImageFont.load_default()

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, SIZE, SIZE], fill=(0, 0, 0, 0))

    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (SIZE - tw) // 2 - bbox[0]
    y = (SIZE - th) // 2 - bbox[1]

    if change_pct is None:
        color = (180, 180, 180, 255)
    elif change_pct > 0:
        color = (0, 200, 80, 255)
    elif change_pct == 0:
        color = get_system_text_color()
    else:
        color = (220, 50, 50, 255)

    draw.text((x + 2, y + 2), text, font=fnt, fill=(0, 0, 0, 120))
    draw.text((x, y), text, font=fnt, fill=color)
    return img


def format_price(change_pct):
    if change_pct is None:
        return "…"
    return f"{abs(change_pct):.1f}"


# ── Janela de gestão ──────────────────────

class ManageWindow:
    def __init__(self, stocks, on_save):
        self.stocks = [dict(s) for s in stocks]  # cópia
        self.on_save = on_save
        self._build()

    def _build(self):
        self.win = tk.Tk()
        self.win.title("Gerir índices")
        self.win.configure(bg="#1e1e2e")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)

        # ── lista ──
        frame_list = tk.Frame(self.win, bg="#1e1e2e")
        frame_list.pack(padx=16, pady=(16, 8), fill="both")

        self.rows_frame = tk.Frame(frame_list, bg="#1e1e2e")
        self.rows_frame.pack(fill="both")
        self._render_rows()

        # ── adicionar novo ──
        frame_add = tk.Frame(self.win, bg="#313244")
        frame_add.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(frame_add, text="Símbolo", bg="#313244", fg="#a6adc8",
                 font=("Segoe UI", 9)).grid(row=0, column=0, padx=(10, 4), pady=8, sticky="w")
        self.entry_symbol = tk.Entry(frame_add, width=12, bg="#45475a", fg="#cdd6f4",
                                     insertbackground="white", relief="flat",
                                     font=("Segoe UI", 10))
        self.entry_symbol.grid(row=0, column=1, padx=4, pady=8)

        tk.Label(frame_add, text="Nome", bg="#313244", fg="#a6adc8",
                 font=("Segoe UI", 9)).grid(row=0, column=2, padx=(10, 4), pady=8, sticky="w")
        self.entry_name = tk.Entry(frame_add, width=18, bg="#45475a", fg="#cdd6f4",
                                   insertbackground="white", relief="flat",
                                   font=("Segoe UI", 10))
        self.entry_name.grid(row=0, column=3, padx=4, pady=8)

        tk.Button(frame_add, text="Adicionar", bg="#89b4fa", fg="#1e1e2e",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  command=self._add).grid(row=0, column=4, padx=(8, 10), pady=8)

        # ── guardar ──
        tk.Button(self.win, text="Guardar e reiniciar", bg="#a6e3a1", fg="#1e1e2e",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  command=self._save).pack(pady=(0, 16), ipadx=10, ipady=4)

    def _render_rows(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        if not self.stocks:
            tk.Label(self.rows_frame, text="Nenhum índice adicionado.",
                     bg="#1e1e2e", fg="#6c7086", font=("Segoe UI", 9)).pack(pady=8)
            return

        for i, s in enumerate(self.stocks):
            row = tk.Frame(self.rows_frame, bg="#181825")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=s["symbol"], bg="#181825", fg="#89b4fa",
                     font=("Segoe UI", 10, "bold"), width=10, anchor="w",
                     padx=10).pack(side="left")
            tk.Label(row, text=s["name"], bg="#181825", fg="#cdd6f4",
                     font=("Segoe UI", 10), anchor="w").pack(side="left", expand=True, fill="x")
            tk.Button(row, text="✕", bg="#f38ba8", fg="#1e1e2e",
                      font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                      command=lambda idx=i: self._remove(idx)).pack(side="right", padx=6, pady=4)

    def _add(self):
        symbol = self.entry_symbol.get().strip().upper()
        name = self.entry_name.get().strip()
        if not symbol or not name:
            messagebox.showwarning("Atenção", "Preenche o símbolo e o nome.", parent=self.win)
            return
        if any(s["symbol"] == symbol for s in self.stocks):
            messagebox.showwarning("Atenção", f"{symbol} já está na lista.", parent=self.win)
            return
        self.stocks.append({"symbol": symbol, "name": name})
        self.entry_symbol.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self._render_rows()

    def _remove(self, idx):
        del self.stocks[idx]
        self._render_rows()

    def _save(self):
        if not self.stocks:
            messagebox.showwarning("Atenção", "Adiciona pelo menos um índice.", parent=self.win)
            return
        save_stocks(self.stocks)
        self.on_save(self.stocks)
        self.win.destroy()

    def show(self):
        self.win.mainloop()


# ── Ícone do tray ─────────────────────────

class StockIcon:
    def __init__(self, symbol, name, on_quit_all, on_manage):
        self.symbol = symbol
        self.name = name
        self.on_quit_all = on_quit_all
        self.on_manage = on_manage
        self.price = None
        self.previous_close = None
        self.change_pct = None
        self.icon = None
        self._create()

    def _create(self):
        img = make_icon("…")
        menu = pystray.Menu(
            pystray.MenuItem(self.name, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Atualizar agora", lambda i, it: self._fetch()),
            pystray.MenuItem("Gerir índices...", lambda i, it: self.on_manage()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", lambda i, it: self.on_quit_all()),
        )
        self.icon = pystray.Icon(
            f"stock_{self.symbol}",
            icon=img,
            title=f"{self.name}: a carregar...",
            menu=menu,
        )

    def _fetch(self):
        price, previous_close = get_price(self.symbol)
        self.price = price

        if previous_close is not None and self.previous_close is None:
            self.previous_close = previous_close

        if self.price is not None and self.previous_close not in (None, 0):
            self.change_pct = ((self.price - self.previous_close) / self.previous_close) * 100
        else:
            self.change_pct = None

        self._refresh()

    def _refresh(self):
        text = format_price(self.change_pct)
        self.icon.icon = make_icon(text, self.change_pct)
        if self.price is not None:
            self.icon.title = f"{self.name}:  {self.price:,.2f}"
        else:
            self.icon.title = f"{self.name}: erro ao carregar"

    def run(self):
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        try:
            self.icon.stop()
        except:
            pass


# ── Monitor principal ─────────────────────

class StockMonitor:
    def __init__(self):
        self.running = True
        self.icons = []
        self._load_icons(load_stocks())

    def _load_icons(self, stocks):
        for ic in self.icons:
            ic.stop()
        self.icons = [
            StockIcon(s["symbol"], s["name"], self.quit_all, self.open_manage)
            for s in stocks
        ]

    def open_manage(self):
        def on_save(new_stocks):
            self._load_icons(new_stocks)
            for ic in self.icons:
                ic.run()
            threading.Thread(target=self._fetch_all, daemon=True).start()

        threading.Thread(
            target=lambda: ManageWindow(load_stocks(), on_save).show(),
            daemon=True
        ).start()

    def quit_all(self):
        self.running = False
        for ic in self.icons:
            ic.stop()

    def _fetch_all(self):
        threads = [threading.Thread(target=ic._fetch, daemon=True) for ic in self.icons]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def run(self):
        for ic in self.icons:
            ic.run()

        while self.running:
            self._fetch_all()
            elapsed = 0
            while self.running and elapsed < INTERVALO_MINUTOS * 60:
                time.sleep(1)
                elapsed += 1


if __name__ == "__main__":
    StockMonitor().run()
