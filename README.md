# Stock Tray Monitor

Simple Windows tray app that tracks stock/index prices (Yahoo Finance) and shows the daily % change in the tray icon.

## What it does

- Runs in the system tray.
- Monitors one or more symbols from `stocks.json`.
- Updates automatically every 5 minutes.
- Lets you manage symbols from **Gerir índices...**.

## Requirements

- Windows
- Python 3.10+ (with `pip`)

## Install

From the project folder:

```bat
install.bat
```

This installs:

- `pystray`
- `Pillow`

## Run (development)

```bat
pythonw stock_monitor.pyw
```

## Build executable

From the project folder:

```bat
build.bat
```

This will:

1. Install `pyinstaller`
2. Build a single-file executable with no console window

Output executable:

- `dist\stock_monitor.exe`

## Config file

Symbols are stored in:

- `stocks.json`

Example format:

```json
[
  { "symbol": "^GSPC", "name": "S&P 500" },
  { "symbol": "VWCE.AS", "name": "VWCE Amsterdão" }
]
```
