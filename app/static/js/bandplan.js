/**
 * Band plan SVG spectrum renderer with zoom/pan.
 * renderBandPlan(container, data) — data from /directory/api/band-plan/<band>
 */
function renderBandPlan(container, data) {
  var fullLo = data.range[0], fullHi = data.range[1];
  var channels = data.channels;
  var viewLo = fullLo, viewHi = fullHi;

  function draw() {
    container.innerHTML = '';
    var span = viewHi - viewLo;
    var width = container.clientWidth || 800;
    var height = 240;
    var padLeft = 55, padRight = 20, padTop = 30, padBot = 40;
    var plotW = width - padLeft - padRight;
    var plotH = height - padTop - padBot;

    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.style.display = 'block';
    svg.style.cursor = 'grab';

    function freqToX(f) {
      return padLeft + ((f - viewLo) / span) * plotW;
    }

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

    // Frequency axis
    var step = span <= 0.5 ? 0.05 : span <= 1 ? 0.1 : span <= 3 ? 0.25 : span <= 5 ? 0.5 : span <= 10 ? 1 : span <= 50 ? 5 : 10;
    var f = Math.ceil(viewLo / step) * step;
    while (f <= viewHi) {
      var x = freqToX(f);
      var tick = document.createElementNS(ns, 'line');
      tick.setAttribute('x1', x); tick.setAttribute('y1', padTop + plotH);
      tick.setAttribute('x2', x); tick.setAttribute('y2', padTop + plotH + 5);
      tick.setAttribute('stroke', 'var(--bs-secondary)');
      svg.appendChild(tick);
      var grid = document.createElementNS(ns, 'line');
      grid.setAttribute('x1', x); grid.setAttribute('y1', padTop);
      grid.setAttribute('x2', x); grid.setAttribute('y2', padTop + plotH);
      grid.setAttribute('stroke', 'var(--bs-border-color)');
      grid.setAttribute('stroke-dasharray', '2,4');
      grid.setAttribute('opacity', '0.5');
      svg.appendChild(grid);
      var lbl = document.createElementNS(ns, 'text');
      lbl.setAttribute('x', x);
      lbl.setAttribute('y', padTop + plotH + 20);
      lbl.setAttribute('text-anchor', 'middle');
      lbl.setAttribute('font-size', '11');
      lbl.setAttribute('fill', 'var(--bs-secondary)');
      lbl.textContent = f.toFixed(step < 0.1 ? 3 : step < 1 ? 1 : 0);
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

    // Zoom hint
    var hint = document.createElementNS(ns, 'text');
    hint.setAttribute('x', padLeft + 5);
    hint.setAttribute('y', padTop - 8);
    hint.setAttribute('font-size', '10');
    hint.setAttribute('fill', 'var(--bs-secondary)');
    hint.textContent = 'Scroll to zoom \u00b7 Drag to pan';
    svg.appendChild(hint);

    // Channel bars
    var barWidth = Math.max(3, plotW / (span / 0.015));
    if (barWidth > 14) barWidth = 14;

    channels.forEach(function(ch) {
      if (ch.freq < viewLo || ch.freq > viewHi) return;
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

      var title = document.createElementNS(ns, 'title');
      title.textContent = ch.freq.toFixed(4) + ' MHz \u2014 ' +
        (ch.system_id || ch.callsign) + '\n' +
        ch.subdsc + '\n' +
        ch.city + (ch.state ? ', ' + ch.state : '') + '\n' +
        ch.status + ' \u00b7 ' + ch.app_type +
        (ch.tx_pl ? ' \u00b7 PL ' + ch.tx_pl : '') +
        (ch.dmr_cc !== null && ch.dmr_cc !== undefined ? ' \u00b7 CC' + ch.dmr_cc : '');
      bar.appendChild(title);

      bar.addEventListener('click', function(e) {
        e.stopPropagation();
        window.location = '/directory/' + ch.subdir;
      });
      svg.appendChild(bar);
    });

    container.appendChild(svg);

    // Zoom with scroll wheel
    svg.addEventListener('wheel', function(e) {
      e.preventDefault();
      var rect = svg.getBoundingClientRect();
      var mouseX = e.clientX - rect.left;
      var frac = (mouseX - padLeft) / plotW;
      frac = Math.max(0, Math.min(1, frac));
      var mouseFreq = viewLo + frac * span;

      var factor = e.deltaY > 0 ? 1.3 : 0.7;
      var newSpan = span * factor;
      var minSpan = (fullHi - fullLo) * 0.02;
      var maxSpan = fullHi - fullLo;
      newSpan = Math.max(minSpan, Math.min(maxSpan, newSpan));

      viewLo = mouseFreq - frac * newSpan;
      viewHi = mouseFreq + (1 - frac) * newSpan;
      if (viewLo < fullLo) { viewHi += fullLo - viewLo; viewLo = fullLo; }
      if (viewHi > fullHi) { viewLo -= viewHi - fullHi; viewHi = fullHi; }
      viewLo = Math.max(viewLo, fullLo);
      viewHi = Math.min(viewHi, fullHi);
      draw();
    });

    // Pan with drag
    var dragging = false, dragStartX = 0, dragStartLo = 0;
    svg.addEventListener('mousedown', function(e) {
      dragging = true;
      dragStartX = e.clientX;
      dragStartLo = viewLo;
      svg.style.cursor = 'grabbing';
    });
    window.addEventListener('mousemove', function(e) {
      if (!dragging) return;
      var dx = e.clientX - dragStartX;
      var freqShift = -(dx / plotW) * span;
      var newLo = dragStartLo + freqShift;
      var newHi = newLo + span;
      if (newLo >= fullLo && newHi <= fullHi) {
        viewLo = newLo;
        viewHi = newHi;
        draw();
      }
    });
    window.addEventListener('mouseup', function() {
      if (dragging) { dragging = false; draw(); }
    });
  }

  draw();

  var resizeTimer;
  window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(draw, 250);
  });
}
