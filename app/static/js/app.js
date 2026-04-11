// CSRF token helper — include in all fetch() POST/PUT/DELETE calls
function csrfHeaders(extra) {
    const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
    return Object.assign({'X-CSRFToken': token}, extra || {});
}

// Initialize Flatpickr on all .datepicker fields
document.addEventListener('DOMContentLoaded', () => {
    flatpickr('.datepicker', {
        dateFormat: 'm/d/Y',
        allowInput: true,
        disableMobile: false,
    });
});

// Auto-dismiss flash alerts after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert-dismissible').forEach(el => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            bsAlert.close();
        }, 5000);
    });
});

/**
 * Initialize "RX same as TX" checkbox.
 * Hides #rx-section when checked and clears its inputs;
 * shows it when unchecked. Auto-detects initial state from existing values.
 */
function initRxSameAsTx() {
    const cb      = document.getElementById('rx_same_as_tx');
    const section = document.getElementById('rx-section');
    if (!cb || !section) return;
    const inputs = section.querySelectorAll('input');

    const hasData = Array.from(inputs).some(el => el.value.trim() !== '');
    cb.checked = !hasData;
    section.classList.toggle('d-none', !hasData);

    cb.addEventListener('change', function () {
        if (this.checked) {
            section.classList.add('d-none');
            inputs.forEach(el => { el.value = ''; });
        } else {
            section.classList.remove('d-none');
        }
    });
}

/**
 * Attach zip-code city/state autofill to the given field IDs.
 * Only fills city/state if city is currently empty (won't override FCC lookup).
 * If multiple city/state results exist, renders clickable suggestions.
 *
 * @param {string} zipId   - id of the zip input
 * @param {string} cityId  - id of the city input
 * @param {string} stateId - id of the state input
 * @param {string} hintId  - id of an element to render suggestions into
 */
function attachZipLookup(zipId, cityId, stateId, hintId) {
    const zipEl   = document.getElementById(zipId);
    const cityEl  = document.getElementById(cityId);
    const stateEl = document.getElementById(stateId);
    const hintEl  = document.getElementById(hintId);
    if (!zipEl || !cityEl || !stateEl) return;

    zipEl.addEventListener('blur', function () {
        const zip = this.value.trim();
        if (zip.length < 5) { if (hintEl) hintEl.innerHTML = ''; return; }

        fetch('/zip-lookup/' + encodeURIComponent(zip))
            .then(r => r.json())
            .then(results => {
                if (!hintEl) return;
                if (!results || results.length === 0) {
                    hintEl.innerHTML = '';
                    return;
                }
                function makeBadge(r) {
                    const a = document.createElement('a');
                    a.href = '#';
                    a.className = 'badge text-bg-secondary text-decoration-none me-1';
                    a.textContent = r.city + ', ' + r.state;
                    a.addEventListener('click', function(e) {
                        e.preventDefault();
                        cityEl.value  = r.city;
                        stateEl.value = r.state;
                        hintEl.textContent = '';
                    });
                    return a;
                }

                if (cityEl.value.trim() === '') {
                    cityEl.value  = results[0].city;
                    stateEl.value = results[0].state;
                    hintEl.textContent = '';
                    if (results.length > 1) {
                        hintEl.textContent = '';
                        hintEl.append('Other matches: ');
                        results.slice(1).forEach(function(r) { hintEl.append(makeBadge(r)); });
                    }
                } else {
                    hintEl.textContent = '';
                    hintEl.append('Suggestions: ');
                    results.forEach(function(r) { hintEl.append(makeBadge(r)); });
                }
            })
            .catch(() => { if (hintEl) hintEl.innerHTML = ''; });
    });
}

/**
 * Add Decimal/DMS toggle to a lat/lng input pair.
 * Call: attachDmsToggle('loc_lat', 'loc_lng')
 * Inserts a toggle button and DMS input group after the decimal fields.
 */
function attachDmsToggle(latId, lngId) {
    var latEl = document.getElementById(latId);
    var lngEl = document.getElementById(lngId);
    if (!latEl || !lngEl) return;

    // Create toggle button
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-outline-secondary mt-1';
    btn.textContent = 'Switch to DMS';
    btn.dataset.mode = 'dec';

    // Create DMS container
    var dmsDiv = document.createElement('div');
    dmsDiv.className = 'd-none mt-2';
    dmsDiv.innerHTML =
        '<div class="row g-1 align-items-center mb-1">' +
        '<div class="col-auto"><small class="text-secondary">Lat:</small></div>' +
        '<div class="col-auto"><input type="number" class="form-control form-control-sm dms-lat-d" style="width:4rem" placeholder="°"></div>' +
        '<div class="col-auto"><input type="number" class="form-control form-control-sm dms-lat-m" style="width:4rem" placeholder="\'"></div>' +
        '<div class="col-auto"><input type="number" step="0.01" class="form-control form-control-sm dms-lat-s" style="width:5rem" placeholder="&quot;"></div>' +
        '<div class="col-auto"><select class="form-select form-select-sm dms-lat-dir" style="width:4rem"><option value="N">N</option><option value="S">S</option></select></div>' +
        '</div>' +
        '<div class="row g-1 align-items-center">' +
        '<div class="col-auto"><small class="text-secondary">Lon:</small></div>' +
        '<div class="col-auto"><input type="number" class="form-control form-control-sm dms-lon-d" style="width:4rem" placeholder="°"></div>' +
        '<div class="col-auto"><input type="number" class="form-control form-control-sm dms-lon-m" style="width:4rem" placeholder="\'"></div>' +
        '<div class="col-auto"><input type="number" step="0.01" class="form-control form-control-sm dms-lon-s" style="width:5rem" placeholder="&quot;"></div>' +
        '<div class="col-auto"><select class="form-select form-select-sm dms-lon-dir" style="width:4rem"><option value="W">W</option><option value="E">E</option></select></div>' +
        '</div>';

    // Insert after the lng field's parent
    var container = lngEl.closest('.col-md-3, .col-md-4, .col') || lngEl.parentNode;
    container.parentNode.insertBefore(dmsDiv, container.nextSibling);
    container.parentNode.insertBefore(btn, dmsDiv);

    function dmsToDecLat() {
        var d = parseFloat(dmsDiv.querySelector('.dms-lat-d').value || 0);
        var m = parseFloat(dmsDiv.querySelector('.dms-lat-m').value || 0);
        var s = parseFloat(dmsDiv.querySelector('.dms-lat-s').value || 0);
        var dir = dmsDiv.querySelector('.dms-lat-dir').value;
        var v = Math.abs(d) + m / 60 + s / 3600;
        return dir === 'S' ? -v : v;
    }
    function dmsToDecLon() {
        var d = parseFloat(dmsDiv.querySelector('.dms-lon-d').value || 0);
        var m = parseFloat(dmsDiv.querySelector('.dms-lon-m').value || 0);
        var s = parseFloat(dmsDiv.querySelector('.dms-lon-s').value || 0);
        var dir = dmsDiv.querySelector('.dms-lon-dir').value;
        var v = Math.abs(d) + m / 60 + s / 3600;
        return dir === 'W' ? -v : v;
    }
    function decToDms(dec) {
        var neg = dec < 0;
        dec = Math.abs(dec);
        var d = Math.floor(dec);
        var m = Math.floor((dec - d) * 60);
        var s = ((dec - d) * 60 - m) * 60;
        return {d: d, m: m, s: parseFloat(s.toFixed(2)), neg: neg};
    }

    function syncDmsToDec() {
        latEl.value = dmsToDecLat().toFixed(6);
        lngEl.value = dmsToDecLon().toFixed(6);
    }

    dmsDiv.querySelectorAll('input, select').forEach(function(el) {
        el.addEventListener('input', syncDmsToDec);
        el.addEventListener('change', syncDmsToDec);
    });

    btn.addEventListener('click', function() {
        if (btn.dataset.mode === 'dec') {
            btn.dataset.mode = 'dms';
            btn.textContent = 'Switch to Decimal';
            dmsDiv.classList.remove('d-none');
            latEl.closest('.col-md-3, .col-md-4, .col').classList.add('d-none');
            lngEl.closest('.col-md-3, .col-md-4, .col').classList.add('d-none');
            // Populate DMS from current decimal
            if (latEl.value) {
                var lt = decToDms(parseFloat(latEl.value));
                dmsDiv.querySelector('.dms-lat-d').value = lt.d;
                dmsDiv.querySelector('.dms-lat-m').value = lt.m;
                dmsDiv.querySelector('.dms-lat-s').value = lt.s;
                dmsDiv.querySelector('.dms-lat-dir').value = lt.neg ? 'S' : 'N';
            }
            if (lngEl.value) {
                var ln = decToDms(parseFloat(lngEl.value));
                dmsDiv.querySelector('.dms-lon-d').value = ln.d;
                dmsDiv.querySelector('.dms-lon-m').value = ln.m;
                dmsDiv.querySelector('.dms-lon-s').value = ln.s;
                dmsDiv.querySelector('.dms-lon-dir').value = ln.neg ? 'W' : 'E';
            }
        } else {
            btn.dataset.mode = 'dec';
            btn.textContent = 'Switch to DMS';
            dmsDiv.classList.add('d-none');
            latEl.closest('.col-md-3, .col-md-4, .col').classList.remove('d-none');
            lngEl.closest('.col-md-3, .col-md-4, .col').classList.remove('d-none');
        }
    });
}

/**
 * IRC Policy 8.2.7 — flag default/prohibited digital access codes.
 * Shows a yellow note below the field when a prohibited value is selected.
 * Auto-attaches to any form containing these fields.
 */
(function() {
    var rules = [
        { name: 'dmr_cc',    prohibited: ['1'],    label: 'DMR Color Code 1 is a default code' },
        { name: 'p25_nac',   prohibited: ['$293', '$F7E', '$F7F'], label: 'This P25 NAC is a default/all-access code' },
        { name: 'nxdn_ran',  prohibited: ['0'],    label: 'NXDN RAN 0 is a default code' },
        { name: 'fusion_dsq', prohibited: ['0'],   label: 'Fusion DSQ 0 is a default code' },
    ];
    var policyRef = 'Per IRC Policy 8.2.7, default codes shall not be assigned to new coordinations.';

    rules.forEach(function(rule) {
        var el = document.querySelector('[name="' + rule.name + '"]');
        if (!el) return;

        var note = document.createElement('div');
        note.className = 'form-text text-warning small d-none';
        note.textContent = rule.label + '. ' + policyRef;
        el.parentNode.appendChild(note);

        function check() {
            var val = el.value.trim();
            if (val && rule.prohibited.indexOf(val) !== -1) {
                note.classList.remove('d-none');
            } else {
                note.classList.add('d-none');
            }
        }
        el.addEventListener('change', check);
        el.addEventListener('input', check);
        check();
    });
})();
