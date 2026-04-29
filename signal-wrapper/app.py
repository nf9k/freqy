#!/usr/bin/env python3
"""
signal-wrapper — thin HTTP API around Signal Server (W3AXL/Signal-Server)

POST /coverage  { lat, lon, txh, freq, erp, name }  → KMZ binary (3 layered plots)
GET  /health                                         → {"status": "ok"}

Three plots per run (matching NF9K runplot.sh methodology):
  Service      — blue,    rel=50%, rt=37 dBuV/m (VHF) / 39 (UHF)
  Interference — green,   rel=10%, rt=19 (VHF) / 21 (UHF)
  Adjacent     — magenta, rel=10%, rt=43 (VHF) / 41 (UHF)
"""
import io
import os
import re
import subprocess
import tempfile
import zipfile

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

SDF_DIR   = os.getenv('SDF_DIR',  '/opt/sdf-us')
SIG_BIN   = os.getenv('SIG_BIN',  'signalserver')
COLOR_DIR = os.getenv('COLOR_DIR', '/opt/Signal-Server/color')
RADIUS    = float(os.getenv('RADIUS_MILES', '250'))
RES       = int(os.getenv('RESOLUTION', '600'))
PM        = int(os.getenv('PROP_MODEL', '1'))   # 1=ITM
RXH       = float(os.getenv('RX_HEIGHT', '6'))  # feet AGL
PORT      = int(os.getenv('PORT', '5001'))

# Receive thresholds in dBuV/m — from NF9K runplot.sh
THRESHOLDS = {
    'vhf': {'service': 37, 'interference': 19, 'adjacent': 43},
    'uhf': {'service': 39, 'interference': 21, 'adjacent': 41},
}

PLOTS = [
    {'key': 'service',      'color': 'blue.scf',    'rel': 50, 'label': 'Service'},
    {'key': 'interference', 'color': 'green.scf',   'rel': 10, 'label': 'Interference'},
    {'key': 'adjacent',     'color': 'magenta.scf', 'rel': 10, 'label': 'Adjacent'},
]


def _band_class(freq_mhz):
    return 'vhf' if freq_mhz <= 300 else 'uhf'


def _run_signalserver(lat, lon, txh, freq, erp, rt, rel, color_file, outbase):
    cmd = [
        SIG_BIN,
        '-sdf', SDF_DIR,
        '-lat', str(lat),
        '-lon', str(lon),
        '-txh', str(txh),   # feet AGL
        '-f',   str(freq),  # MHz
        '-erp', str(erp),   # watts ERP
        '-R',   str(RADIUS),
        '-res', str(RES),
        '-pm',  str(PM),
        '-rxh', str(RXH),
        '-te',  '3',        # farmland terrain
        '-cl',  '5',        # continental temperate
        '-pe',  '2',        # suburban mode
        '-rt',  str(rt),    # dBuV/m threshold
        '-rel', str(rel),   # reliability %
        '-color', color_file,
        '-dbg',
        '-o', outbase,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    return result.stdout + result.stderr, result.returncode


def _parse_bounds(output):
    m = re.search(
        r'boundaries:\s*(-?[\d.]+)\s*\|\s*(-?[\d.]+)\s*\|\s*(-?[\d.]+)\s*\|\s*(-?[\d.]+)',
        output,
    )
    if not m:
        return None
    return {
        'north': float(m.group(1)),
        'east':  float(m.group(2)),
        'south': float(m.group(3)),
        'west':  float(m.group(4)),
    }


def _convert_ppm(ppm_path, png_path):
    subprocess.run(
        ['convert', ppm_path, '-transparent', 'white', png_path],
        check=True, timeout=60,
    )


def _build_kmz(overlays, name):
    """
    overlays: list of {'label': str, 'png_path': str, 'bounds': dict}
    Returns KMZ bytes with all overlays layered in one KML Document.
    """
    overlay_kml = ''
    for o in overlays:
        b = o['bounds']
        overlay_kml += (
            f'  <GroundOverlay>\n'
            f'    <name>{o["label"]}</name>\n'
            f'    <Icon><href>{o["label"].lower()}.png</href></Icon>\n'
            f'    <LatLonBox>\n'
            f'      <north>{b["north"]}</north>\n'
            f'      <south>{b["south"]}</south>\n'
            f'      <east>{b["east"]}</east>\n'
            f'      <west>{b["west"]}</west>\n'
            f'    </LatLonBox>\n'
            f'  </GroundOverlay>\n'
        )

    kml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        '<Document>\n'
        f'  <name>{name}</name>\n'
        + overlay_kml +
        '</Document>\n'
        '</kml>\n'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for o in overlays:
            z.write(o['png_path'], f'{o["label"].lower()}.png')
        z.writestr('doc.kml', kml)
    return buf.getvalue()


@app.route('/coverage', methods=['POST'])
def coverage():
    data = request.get_json(silent=True) or {}
    try:
        lat  = float(data['lat'])
        lon  = float(data['lon'])
        txh  = float(data.get('txh', 30))
        freq = float(data['freq'])
        erp  = float(data.get('erp', 10))
        name = str(data.get('name', 'Coverage'))
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({'error': f'Bad request: {e}'}), 400

    band  = _band_class(freq)
    thres = THRESHOLDS[band]

    with tempfile.TemporaryDirectory() as tmpdir:
        overlays = []

        for plot in PLOTS:
            rt         = thres[plot['key']]
            color_file = os.path.join(COLOR_DIR, plot['color'])
            outbase    = os.path.join(tmpdir, plot['key'])
            ppm        = outbase + '.ppm'
            png        = os.path.join(tmpdir, f'{plot["label"].lower()}.png')

            output, rc = _run_signalserver(lat, lon, txh, freq, erp,
                                           rt, plot['rel'], color_file, outbase)
            if rc != 0:
                return jsonify({
                    'error': f'signalserver failed on {plot["label"]} plot (rc={rc})',
                    'detail': output[-1000:],
                }), 500

            bounds = _parse_bounds(output)
            if not bounds:
                return jsonify({
                    'error': f'Bounding box not found for {plot["label"]} plot',
                    'detail': output[-1000:],
                }), 500

            try:
                _convert_ppm(ppm, png)
            except subprocess.CalledProcessError as e:
                return jsonify({'error': f'Image convert failed: {e}'}), 500

            overlays.append({'label': plot['label'], 'png_path': png, 'bounds': bounds})

        kmz_bytes = _build_kmz(overlays, name)

    return send_file(
        io.BytesIO(kmz_bytes),
        mimetype='application/vnd.google-earth.kmz',
        as_attachment=True,
        download_name='coverage.kmz',
    )


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
