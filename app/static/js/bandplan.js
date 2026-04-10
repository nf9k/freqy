/**
 * Band plan SVG spectrum renderer.
 * renderBandPlan(container, data) — data from /directory/api/band-plan/<band>
 */
function renderBandPlan(container, data) {
  var range = data.range;
  var channels = data.channels;
  var lo = range[0], hi = range[1];
  var span = hi - lo;

  var width = container.clientWidth || 800;
  var height = 220;
  var padLeft = 50, padRight = 20, padTop = 20, padBot = 40;
  var plotW = width - padLeft - padRight;
  var plotH = height - padTop - padBot;

  var ns = 'http://www.w3.org/2000/svg';
  var svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);
  svg.style.display = 'block';

  function freqToX(f) {
    return padLeft + ((f - lo) / span) * plotW;
  }

  // Status color map
  function statusColor(status) {
    if (status === 'Final') return 'var(--bs-success)';
    if (status === 'Construction Permit') return 'var(--bs-warning)';
    return 'var(--bs-info)';
  }

  // Background
  var bg = document.createElementNS(ns, 'rect');
  bg.setAttribute('x', padLeft);
  bg.setAttribute('y', padTop);
  bg.setAttribute('width', plotW);
  bg.setAttribute('height', plotH);
  bg.setAttribute('fill', 'var(--bs-body-bg)');
  bg.setAttribute('stroke', 'var(--bs-border-color)');
  svg.appendChild(bg);

  // Frequency axis labels
  var step = span <= 1 ? 0.1 : span <= 5 ? 0.5 : span <= 10 ? 1 : span <= 50 ? 5 : 10;
  var f = Math.ceil(lo / step) * step;
  while (f <= hi) {
    var x = freqToX(f);
    // Tick
    var tick = document.createElementNS(ns, 'line');
    tick.setAttribute('x1', x); tick.setAttribute('y1', padTop + plotH);
    tick.setAttribute('x2', x); tick.setAttribute('y2', padTop + plotH + 5);
    tick.setAttribute('stroke', 'var(--bs-secondary)');
    svg.appendChild(tick);
    // Grid line
    var grid = document.createElementNS(ns, 'line');
    grid.setAttribute('x1', x); grid.setAttribute('y1', padTop);
    grid.setAttribute('x2', x); grid.setAttribute('y2', padTop + plotH);
    grid.setAttribute('stroke', 'var(--bs-border-color)');
    grid.setAttribute('stroke-dasharray', '2,4');
    grid.setAttribute('opacity', '0.5');
    svg.appendChild(grid);
    // Label
    var lbl = document.createElementNS(ns, 'text');
    lbl.setAttribute('x', x);
    lbl.setAttribute('y', padTop + plotH + 20);
    lbl.setAttribute('text-anchor', 'middle');
    lbl.setAttribute('font-size', '11');
    lbl.setAttribute('fill', 'var(--bs-secondary)');
    lbl.textContent = f.toFixed(step < 1 ? 1 : 0);
    svg.appendChild(lbl);
    f += step;
  }

  // MHz label
  var mhzLabel = document.createElementNS(ns, 'text');
  mhzLabel.setAttribute('x', width - padRight);
  mhzLabel.setAttribute('y', padTop + plotH + 35);
  mhzLabel.setAttribute('text-anchor', 'end');
  mhzLabel.setAttribute('font-size', '10');
  mhzLabel.setAttribute('fill', 'var(--bs-secondary)');
  mhzLabel.textContent = 'MHz';
  svg.appendChild(mhzLabel);

  // Channel bars
  var barWidth = Math.max(3, plotW / (span / 0.015));
  if (barWidth > 12) barWidth = 12;

  channels.forEach(function(ch) {
    var x = freqToX(ch.freq) - barWidth / 2;
    var bar = document.createElementNS(ns, 'rect');
    bar.setAttribute('x', x);
    bar.setAttribute('y', padTop + 2);
    bar.setAttribute('width', barWidth);
    bar.setAttribute('height', plotH - 4);
    bar.setAttribute('fill', statusColor(ch.status));
    bar.setAttribute('opacity', '0.85');
    bar.setAttribute('rx', '1');
    bar.style.cursor = 'pointer';

    // Tooltip
    var title = document.createElementNS(ns, 'title');
    title.textContent = ch.freq.toFixed(4) + ' MHz — ' +
      (ch.system_id || ch.callsign) + '\n' +
      ch.subdsc + '\n' +
      ch.city + (ch.state ? ', ' + ch.state : '') + '\n' +
      ch.status + ' · ' + ch.app_type +
      (ch.tx_pl ? ' · PL ' + ch.tx_pl : '') +
      (ch.dmr_cc !== null && ch.dmr_cc !== undefined ? ' · CC' + ch.dmr_cc : '');
    bar.appendChild(title);

    // Click to navigate
    bar.addEventListener('click', function() {
      window.location = '/directory/' + ch.subdir;
    });

    svg.appendChild(bar);
  });

  container.appendChild(svg);

  // Responsive resize
  var resizeTimer;
  window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
      container.innerHTML = '';
      renderBandPlan(container, data);
    }, 250);
  });
}
