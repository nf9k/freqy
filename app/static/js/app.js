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
