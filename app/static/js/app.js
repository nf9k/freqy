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
                if (cityEl.value.trim() === '') {
                    // Auto-fill with first result
                    cityEl.value  = results[0].city;
                    stateEl.value = results[0].state;
                    hintEl.innerHTML = '';
                    if (results.length > 1) {
                        // Show alternates as clickable badges
                        hintEl.innerHTML = 'Other matches: ' + results.slice(1).map(r =>
                            `<a href="#" class="badge text-bg-secondary text-decoration-none me-1 zip-alt"
                                data-city="${r.city}" data-state="${r.state}">${r.city}, ${r.state}</a>`
                        ).join('');
                        hintEl.querySelectorAll('.zip-alt').forEach(el => {
                            el.addEventListener('click', e => {
                                e.preventDefault();
                                cityEl.value  = el.dataset.city;
                                stateEl.value = el.dataset.state;
                                hintEl.innerHTML = '';
                            });
                        });
                    }
                } else {
                    // City already filled — show suggestions without overwriting
                    hintEl.innerHTML = 'Suggestions: ' + results.map(r =>
                        `<a href="#" class="badge text-bg-secondary text-decoration-none me-1 zip-alt"
                            data-city="${r.city}" data-state="${r.state}">${r.city}, ${r.state}</a>`
                    ).join('');
                    hintEl.querySelectorAll('.zip-alt').forEach(el => {
                        el.addEventListener('click', e => {
                            e.preventDefault();
                            cityEl.value  = el.dataset.city;
                            stateEl.value = el.dataset.state;
                            hintEl.innerHTML = '';
                        });
                    });
                }
            })
            .catch(() => { if (hintEl) hintEl.innerHTML = ''; });
    });
}
