# NetScope

**Modern Linux Internet Usage Monitor**

A professional desktop application for monitoring network usage on Linux. Built with Python, PyWebView, and plain HTML/CSS/JavaScript. Uses **vnStat** for historical statistics and `/sys/class/net` counters for real-time bandwidth.

## Features

- **Dashboard** – Today / yesterday / month / all-time totals, live speeds, quota progress, daily chart
- **Live Monitor** – Real-time download & upload graphs, peak speeds, session totals
- **Usage History** – Hourly, daily, monthly, yearly views with interactive charts
- **Insights** – Automatic observations from your usage patterns
- **Interfaces** – Detect and select ethernet, Wi-Fi, VPN, and virtual interfaces
- **Data Limits** – Configurable monthly allowance, billing cycle, warning thresholds
- **Desktop Notifications** – Alerts when approaching or exceeding your data limit
- **Reports** – Export daily / monthly / yearly data as CSV or JSON
- **Dark & Light themes**

## Requirements

- Linux (tested on Fedora, Ubuntu, Debian)
- Python >= 3.11
- vnStat installed and running
- GTK / WebKit dependencies for PyWebView
- Optional: libnotify / notify-send for desktop notifications

## Quick Start

```bash
# 1. Install system dependencies (Fedora example)
sudo dnf install vnstat python3-pip python3-gobject webkit2gtk4.1

# Ubuntu/Debian
# sudo apt install vnstat python3-pip python3-gi gir1.2-webkit2-4.1 libnotify-bin

# 2. Start & enable vnStat
sudo systemctl enable --now vnstat

# Add your interface (replace wlan0 / eth0 with your interface)
sudo vnstat --add -i wlan0

# 3. Install Python dependencies
cd netscope
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Run
python main.py
# or with debug tools:
python main.py --debug
```

## Project Structure

```
netscope/
├── main.py                 # Entry point
├── requirements.txt
├── README.md
├── backend/
│   ├── app.py              # PyWebView API bridge
│   ├── vnstat.py           # vnStat CLI integration
│   ├── network_monitor.py  # Real-time /sys counters
│   ├── interface_manager.py
│   ├── analytics.py
│   ├── quota_manager.py
│   ├── notification_manager.py
│   ├── export_manager.py
│   ├── settings_manager.py
│   └── database.py         # SQLite settings/quota
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
└── docs/
    └── installation.md
```

## Configuration

Application settings and quota are stored in:

```
~/.config/netscope/netscope.db
```

vnStat's own database is never modified or reset by NetScope.

## Integrating with Bandora

If you already use the Bandora project:

1. You can run NetScope as a **standalone** application (recommended).
2. Or copy the `backend/` and `frontend/` folders into a new package layout similar to Bandora's `src/` structure and adjust the entry point.

See `docs/installation.md` for detailed integration and troubleshooting steps.

## License

MIT
