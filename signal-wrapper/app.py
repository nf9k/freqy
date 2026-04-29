#!/usr/bin/env python3
"""
signal-wrapper — thin HTTP API around Signal Server (W3AXL/Signal-Server)

POST /coverage  { lat, lon, txh, freq, erp, name }  → KMZ binary
GET  /health                                         → {"status": "ok"}
"""
import io
import os
import re
import subprocess
import tempfile
import zipfile

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

SDF_DIR = os.getenv('SDF_DIR', '/mnt/data')
SIG_BIN = os.getenv('SIG_BIN', 'signalserver')
RADIUS  = float(os.getenv('RADIUS_MILES', '75'))
RES     = int(os.getenv('RESOLUTION', '600'))
PM      = int(os.getenv('PROP_MODEL', '1'))    # 1=ITM (best for VHF/UHF)
RXH     = float(os.getenv('RX_HEIGHT', '6'))   # feet AGL, typical mobile
PORT    = int(os.getenv('PORT', '5001'))


def _run_signalserver(lat, lon, txh, freq, erp, outbase):
    cmd = [
        SIG_BIN,
        '-sdf', SDF_DIR,
        '-lat', str(lat),
        '-lon', str(lon),
        '-txh', str(txh),    # feet AGL (no -m flag → imperial units)
        '-f',   str(freq),   # MHz
        '-erp', str(erp),    # watts ERP
        '-R',   str(RADIUS), # miles
        '-res', str(RES),
        '-pm',  str(PM),
        '-rxh', str(RXH),
        '-te',  '3',         # farmland terrain
        '-cl',  '5',         # continental temperate
        '-pe',  '2',         # suburban mode
        '-dbm',
        '-rt',  '-90',
        '-dbg',
        '-o', outbase,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=360)
    return result.stdout + result.stderr, result.returncode


def _parse_bounds(output):
    """Extract bounding box from 'Area boundaries:N | E | S | W' in signalserver stdout."""
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


def _build_kmz(outbase, bounds, name):
    """Convert ppm → png, build KML, return KMZ bytes."""
    ppm = outbase + '.ppm'
    png = outbase + '.png'

    subprocess.run(
        ['convert', ppm, '-transparent', 'white', png],
        check=True, timeout=60,
    )

    kml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        '<GroundOverlay>\n'
        f'  <name>{name}</name>\n'
        '  <Icon><href>overlay.png</href></Icon>\n'
        '  <LatLonBox>\n'
        f'    <north>{bounds["north"]}</north>\n'
        f'    <south>{bounds["south"]}</south>\n'
        f'    <east>{bounds["east"]}</east>\n'
        f'    <west>{bounds["west"]}</west>\n'
        '  </LatLonBox>\n'
        '</GroundOverlay>\n'
        '</kml>\n'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(png, 'overlay.png')
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

    with tempfile.TemporaryDirectory() as tmpdir:
        outbase = os.path.join(tmpdir, 'cover')   # ≥5 chars required by signalserver

        output, rc = _run_signalserver(lat, lon, txh, freq, erp, outbase)

        if rc != 0:
            return jsonify({
                'error': f'signalserver exited {rc}',
                'detail': output[-1000:],
            }), 500

        bounds = _parse_bounds(output)
        if not bounds:
            return jsonify({
                'error': 'Bounding box not found in signalserver output',
                'detail': output[-1000:],
            }), 500

        try:
            kmz_bytes = _build_kmz(outbase, bounds, name)
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'Image convert failed: {e}'}), 500

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
