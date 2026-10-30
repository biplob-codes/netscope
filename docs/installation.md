# NetScope – Installation & Integration Guide

## 1. System dependencies

### Fedora

```bash
sudo dnf install vnstat python3 python3-pip python3-gobject webkit2gtk4.1 libnotify
sudo systemctl enable --now vnstat
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install vnstat python3 python3-pip python3-gi gir1.2-webkit2-4.1 libnotify-bin
sudo systemctl enable --now vnstat
```

### Arch

```bash
sudo pacman -S vnstat python python-pip python-gobject webkit2gtk-4.1 libnotify
sudo systemctl enable --now vnstat
```

## 2. Configure vnStat

List interfaces:

```bash
ip link
# or
ls /sys/class/net
```

Add the interface you care about (example `wlan0`):

```bash
sudo vnstat --add -i wlan0
sudo systemctl restart vnstat
```

Wait a few minutes for the first data points, or force an update:

```bash
sudo vnstat -u -i wlan0
vnstat -i wlan0
```

## 3. Install & run NetScope

```bash
cd netscope
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Debug mode (opens WebKit inspector):

```bash
python main.py --debug
```

## 4. Integrating with the existing Bandora project

Bandora layout:

```
bandora/
├── frontend/
├── src/bandora/
│   ├── main.py
│   ├── vnstat.py
│   └── config.py
├── assets/
└── pyproject.toml
```

**Recommended approach – run NetScope side-by-side**

NetScope is a complete replacement with a richer feature set. Keep Bandora as-is and use NetScope as the new application.

**If you want to merge into the Bandora repository:**

1. Create directories:

   ```bash
   mkdir -p src/netscope
   mkdir -p frontend_netscope   # or replace frontend/
   ```

2. Copy backend modules:

   ```bash
   cp -r netscope/backend/* src/netscope/
   ```

3. Copy frontend:

   ```bash
   cp -r netscope/frontend/* frontend/   # overwrites Bandora UI
   ```

4. Replace `src/bandora/main.py` (or create a new entry point) with the contents of `netscope/main.py`, adjusting the import path:

   ```python
   from netscope.app import Api   # instead of from backend.app
   ```

5. Update `pyproject.toml` dependencies and script entry point.

6. Install:

   ```bash
   uv sync
   uv run netscope   # or whatever entry you defined
   ```

## 5. Common issues

| Problem | Solution |
|--------|----------|
| `vnStat is not installed` | Install the `vnstat` package and enable the service |
| `No interfaces found` | Run `sudo vnstat --add -i <iface>` then wait or force update |
| Blank window / WebKit errors | Install the correct `webkit2gtk` package for your distro |
| No desktop notifications | Install `libnotify` / `notify-bin` (`notify-send`) |
| Permission errors on `/sys` | Normally readable by any user; check SELinux/AppArmor if restricted |
| High CPU when idle | Increase refresh interval in Settings (2–5 s) |

## 6. Data locations

- NetScope config & quota: `~/.config/netscope/netscope.db`
- vnStat database: usually `/var/lib/vnstat/` (never modified by NetScope)
