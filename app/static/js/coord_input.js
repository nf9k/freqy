/**
 * Initialize coordinate input widget (Decimal / DMS / Map).
 * Call initCoordInput(prefix, mapId) for each coord input on the page.
 *
 * @param {string} prefix — matches the prefix used in coord_input.html include
 * @param {string} mapId  — the map div ID
 */
function initCoordInput(prefix, mapId) {
  var hiddenLat = document.getElementById(prefix + '_hidden_lat');
  var hiddenLon = document.getElementById(prefix + '_hidden_lon');
  var panels = ['decimal', 'dms', 'map'];
  var mapInit = false, map = null, marker = null;

  function showPanel(mode) {
    panels.forEach(function(p) {
      var el = document.getElementById(prefix + '_panel_' + p);
      if (el) el.classList.toggle('d-none', p !== mode);
    });
    if (mode === 'map' && !mapInit) initMap();
  }

  // Mode radio buttons
  document.querySelectorAll('input[name="' + prefix + '_coord_mode"]').forEach(function(el) {
    el.addEventListener('change', function() { showPanel(el.value); });
  });

  // Sync decimal → hidden on any input change
  var latDec = document.getElementById(prefix + '_lat_dec');
  var lonDec = document.getElementById(prefix + '_lon_dec');
  if (latDec) latDec.addEventListener('input', function() { hiddenLat.value = latDec.value; });
  if (lonDec) lonDec.addEventListener('input', function() { hiddenLon.value = lonDec.value; });

  // Sync DMS → hidden on any input change
  function syncDms() {
    var d, m, s, dir;
    d = parseFloat(document.querySelector('[name="' + prefix + '_lat_d"]')?.value || 0);
    m = parseFloat(document.querySelector('[name="' + prefix + '_lat_m"]')?.value || 0);
    s = parseFloat(document.querySelector('[name="' + prefix + '_lat_s"]')?.value || 0);
    dir = document.querySelector('[name="' + prefix + '_lat_dir"]')?.value || 'N';
    var lat = Math.abs(d) + m / 60 + s / 3600;
    if (dir === 'S') lat = -lat;

    d = parseFloat(document.querySelector('[name="' + prefix + '_lon_d"]')?.value || 0);
    m = parseFloat(document.querySelector('[name="' + prefix + '_lon_m"]')?.value || 0);
    s = parseFloat(document.querySelector('[name="' + prefix + '_lon_s"]')?.value || 0);
    dir = document.querySelector('[name="' + prefix + '_lon_dir"]')?.value || 'W';
    var lon = Math.abs(d) + m / 60 + s / 3600;
    if (dir === 'W') lon = -lon;

    if (!isNaN(lat)) hiddenLat.value = lat.toFixed(6);
    if (!isNaN(lon)) hiddenLon.value = lon.toFixed(6);
  }

  document.querySelectorAll('[name^="' + prefix + '_lat_"], [name^="' + prefix + '_lon_"]').forEach(function(el) {
    el.addEventListener('input', syncDms);
    el.addEventListener('change', syncDms);
  });

  // Map picker
  function initMap() {
    mapInit = true;
    var initLat = parseFloat(hiddenLat.value) || 39.77;
    var initLon = parseFloat(hiddenLon.value) || -86.16;
    var zoom = hiddenLat.value ? 10 : 7;

    map = L.map(mapId).setView([initLat, initLon], zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18, attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    function setCoords(lat, lng) {
      document.getElementById(prefix + '_map_lat').value = lat.toFixed(6);
      document.getElementById(prefix + '_map_lon').value = lng.toFixed(6);
      hiddenLat.value = lat.toFixed(6);
      hiddenLon.value = lng.toFixed(6);
      if (marker) {
        marker.setLatLng([lat, lng]);
      } else {
        marker = L.marker([lat, lng], {draggable: true}).addTo(map);
        marker.on('dragend', function() {
          var p = marker.getLatLng();
          setCoords(p.lat, p.lng);
        });
      }
    }

    map.on('click', function(e) { setCoords(e.latlng.lat, e.latlng.lng); });

    if (hiddenLat.value && hiddenLon.value) {
      setCoords(parseFloat(hiddenLat.value), parseFloat(hiddenLon.value));
    }
  }

  // Show initial panel
  var checked = document.querySelector('input[name="' + prefix + '_coord_mode"]:checked');
  if (checked) showPanel(checked.value);
}
