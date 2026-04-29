# signal-wrapper — Remote Server Installation

Thin Flask HTTP wrapper around W3AXL/Signal-Server.
Accepts `POST /coverage` from freqy and returns a KMZ file.

## Prerequisites

Assumes a Debian/Ubuntu host with SRTM terrain tiles already in `/mnt/data`.

---

## 1. Build Signal Server

```bash
sudo apt-get install -y g++ cmake libbz2-dev imagemagick python3 python3-pip python3-venv git

git clone https://github.com/W3AXL/Signal-Server.git /opt/signal-server
cd /opt/signal-server
mkdir build && cd build
cmake ../src
make -j$(nproc)
sudo ln -s /opt/signal-server/build/signalserver /usr/local/bin/signalserver
```

Verify:
```bash
signalserver --help
```

---

## 2. Install the wrapper

```bash
cp -r signal-wrapper /opt/signal-wrapper
cd /opt/signal-wrapper

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Configure environment

Create `/opt/signal-wrapper/.env`:

```env
SDF_DIR=/mnt/data        # directory containing .sdf terrain tiles
SIG_BIN=signalserver     # full path if not on PATH
RADIUS_MILES=75          # coverage radius
RESOLUTION=600           # pixels per tile (300/600/1200/3600)
PROP_MODEL=1             # 1=ITM (recommended for VHF/UHF)
RX_HEIGHT=6              # receiver height AGL in feet
PORT=5001
```

---

## 4. Run as a systemd service

Create `/etc/systemd/system/signal-wrapper.service`:

```ini
[Unit]
Description=signal-wrapper (freqy coverage plot API)
After=network.target

[Service]
User=nobody
WorkingDirectory=/opt/signal-wrapper
EnvironmentFile=/opt/signal-wrapper/.env
ExecStart=/opt/signal-wrapper/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now signal-wrapper
sudo systemctl status signal-wrapper
```

---

## 5. Test

```bash
curl -s http://localhost:5001/health
# {"status": "ok"}

curl -s -X POST http://localhost:5001/coverage \
  -H 'Content-Type: application/json' \
  -d '{"lat":41.88,"lon":-87.63,"txh":100,"freq":146.94,"erp":50,"name":"Test"}' \
  -o test.kmz
file test.kmz
# test.kmz: Zip archive data ...
```

---

## 6. Configure freqy

In freqy's `.env`:

```env
SIGNAL_SERVER_URL=http://<signal-server-ip>:5001
KMZ_DIR=/data/kmz
```

`KMZ_DIR` is a Docker volume mount — no action needed unless changing the path.

---

## SRTM Terrain Tiles

Signal Server requires SRTM-derived `.sdf` tiles for the coverage area.
Tiles are available from the SPLAT! project or can be converted from `.hgt` files
using the `srtm2sdf` utility included in the Signal Server source.

US coverage typically requires tiles for the relevant 1°×1° blocks.
Place all `.sdf` (or `.sdf.bz2`) files in `SDF_DIR`.
