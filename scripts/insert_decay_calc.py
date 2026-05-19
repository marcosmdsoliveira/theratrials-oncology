#!/usr/bin/env python3
"""
insert_decay_calc.py
Inserts tool #11 (Planejamento PET/CT - Decaimento radioativo) into ferramentas.html.
1. Adds a navigation card in the tools-hub grid after the last card (Oncologia clinica #10).
2. Adds the full section HTML (calculator + script) before the <!-- FOOTER --> sentinel.
"""

import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(BASE, "ferramentas.html")

# ---------- Navigation card ----------
NAV_CARD = """\
      <a href="#decay-calc" class="tool-link" style="--accent: #06B6D4">
        <div class="num">11</div>
        <i data-lucide="timer" class="icon"></i>
        <h3>Planejamento PET/CT</h3>
        <p>Decaimento radioativo &middot; Proje&ccedil;&atilde;o de agenda &middot; F-18 &middot; Ga-68 &middot; C-11</p>
      </a>"""

# ---------- Section HTML ----------
SECTION_HTML = r"""
    <!-- ============================================================ -->
    <!-- 11. PLANEJAMENTO PET/CT &middot; DECAIMENTO RADIOATIVO       -->
    <!-- ============================================================ -->
    <section class="tool" id="decay-calc" style="--tool-accent: #06B6D4">
      <div class="tool-head">
        <div class="tool-num" style="background: rgba(6, 182, 212, 0.15); color: #06B6D4">11</div>
        <h2>Planejamento PET/CT &middot; Decaimento radioativo</h2>
      </div>
      <p style="color: var(--stone); margin: 0 0 1.5rem; max-width: 720px; line-height: 1.55">
        Proje&ccedil;&atilde;o de atividade dispon&iacute;vel ao longo do dia para radiof&aacute;rmacos PET, considerando decaimento f&iacute;sico, doses individuais e res&iacute;duo em seringa. Baseado na f&oacute;rmula A(t) = A&#8320; &times; e<sup>&minus;ln2/t&frac12; &times; &Delta;t</sup>.
      </p>

      <!-- Inputs Row 1 -->
      <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:1rem; align-items:flex-end">
        <div style="flex:1 1 200px">
          <label for="dc-isotope" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Radiois&oacute;topo</label>
          <select id="dc-isotope"
                  style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-body); font-size:0.9rem"
                  onchange="window._dcCalc &amp;&amp; window._dcCalc.onIsotopeChange()">
            <option value="109.77">&#185;&#8312;F-FDG (t&frac12; = 109.77 min)</option>
            <option value="67.71_dotatate">&#8310;&#8312;Ga-DOTATATE (t&frac12; = 67.71 min)</option>
            <option value="67.71_psma">&#8310;&#8312;Ga-PSMA (t&frac12; = 67.71 min)</option>
            <option value="20.39">&#185;&#185;C (t&frac12; = 20.39 min)</option>
            <option value="9.97">&#185;&#179;N-am&ocirc;nia (t&frac12; = 9.97 min)</option>
            <option value="custom">Personalizado</option>
          </select>
        </div>
        <div style="flex:0 0 130px">
          <label for="dc-a0" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Atividade inicial (mCi)</label>
          <input type="number" id="dc-a0" value="21.6" min="0" step="0.1"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
        <div style="flex:0 0 110px">
          <label for="dc-vol" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Volume inicial (mL)</label>
          <input type="number" id="dc-vol" value="6" min="0" step="0.1"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
        <div style="flex:0 0 110px">
          <label for="dc-hl" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Meia-vida (min)</label>
          <input type="number" id="dc-hl" value="109.77" min="0.1" step="0.01"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
      </div>

      <!-- Inputs Row 2 -->
      <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:1.5rem; align-items:flex-end">
        <div style="flex:0 0 120px">
          <label for="dc-t0" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Hora da 1&ordf; inje&ccedil;&atilde;o</label>
          <input type="time" id="dc-t0" value="10:00"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
        <div style="flex:0 0 130px">
          <label for="dc-interval" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Intervalo (min)</label>
          <input type="number" id="dc-interval" value="25" min="1" step="1"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
        <div style="flex:0 0 130px">
          <label for="dc-uptake" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Capta&ccedil;&atilde;o (min)</label>
          <input type="number" id="dc-uptake" value="60" min="0" step="5"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
        <div style="flex:0 0 130px">
          <label for="dc-factor" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Fator dose (mCi/kg)</label>
          <input type="number" id="dc-factor" value="0.09" min="0.01" step="0.01"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
        <div style="flex:0 0 130px">
          <label for="dc-residual" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Res&iacute;duo seringa (mCi)</label>
          <input type="number" id="dc-residual" value="0.3" min="0" step="0.1"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">
        </div>
      </div>

      <!-- Patient Table -->
      <div style="overflow-x:auto; margin-bottom:1rem; border:1px solid var(--border-soft); border-radius:var(--radius-md)">
        <table id="dc-table" style="width:100%; border-collapse:collapse; font-size:0.82rem; min-width:900px">
          <thead>
            <tr style="background:var(--graphite-2); text-align:left">
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft); width:36px">#</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft); width:80px">Peso (kg)</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft)">Hora inje&ccedil;&atilde;o</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft)">Hora sa&iacute;da</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft)">Dispon&iacute;vel (mCi)</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft)">Dispon&iacute;vel (MBq)</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft)">Dose prescrita (mCi)</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft)">Volume (mL)</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft)">Remanescente (mCi)</th>
              <th style="padding:0.6rem 0.5rem; color:var(--stone); font-weight:600; border-bottom:1px solid var(--border-soft); width:50px">Status</th>
            </tr>
          </thead>
          <tbody id="dc-tbody"></tbody>
          <tfoot>
            <tr style="background:var(--graphite-2); font-weight:600">
              <td colspan="2" style="padding:0.6rem 0.5rem; color:var(--off-white); border-top:2px solid var(--border-soft)">Total</td>
              <td colspan="4" style="padding:0.6rem 0.5rem; color:var(--stone); border-top:2px solid var(--border-soft); font-family:var(--font-mono)" id="dc-summary-consumed"></td>
              <td colspan="2" style="padding:0.6rem 0.5rem; color:var(--stone); border-top:2px solid var(--border-soft); font-family:var(--font-mono)" id="dc-summary-remaining"></td>
              <td colspan="2" style="padding:0.6rem 0.5rem; border-top:2px solid var(--border-soft)"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <button type="button" onclick="window._dcCalc &amp;&amp; window._dcCalc.addPatient()"
              style="padding:0.5rem 1.2rem; background:rgba(6,182,212,0.12); border:1px solid rgba(6,182,212,0.3); border-radius:8px; color:#06B6D4; font-size:0.85rem; font-weight:600; cursor:pointer; margin-bottom:1.5rem; transition:all 0.2s"
              onmouseover="this.style.background='rgba(6,182,212,0.22)'" onmouseout="this.style.background='rgba(6,182,212,0.12)'">&#xFF0B; Adicionar paciente</button>

      <!-- Disclaimer -->
      <div style="background:rgba(6,182,212,0.06); border:1px solid rgba(6,182,212,0.18); border-radius:var(--radius-md); padding:0.9rem 1.1rem; font-size:0.78rem; color:var(--stone); line-height:1.55">
        <strong style="color:#06B6D4">&#9888; Aviso:</strong> Esta calculadora &eacute; uma ferramenta auxiliar de refer&ecirc;ncia para planejamento log&iacute;stico de PET/CT. Os c&aacute;lculos de decaimento radioativo devem ser validados pelo m&eacute;dico nuclear e f&iacute;sico m&eacute;dico respons&aacute;veis conforme protocolos institucionais, calibra&ccedil;&atilde;o do ativimetr&iacute;o e condi&ccedil;&otilde;es espec&iacute;ficas do dia. N&atilde;o substitui julgamento cl&iacute;nico nem valida&ccedil;&atilde;o f&iacute;sica.
      </div>

<script>
// =====================================================================
// PET/CT Day Planner — Radioactive Decay Calculator
// Tool #11 · TheraTrials Oncology
// =====================================================================
(function(){
  "use strict";

  var MAX_PATIENTS = 20;
  var LN2 = Math.LN2; // 0.6931471805599453

  // --- DOM references ---
  var elIsotope  = document.getElementById("dc-isotope");
  var elA0       = document.getElementById("dc-a0");
  var elVol      = document.getElementById("dc-vol");
  var elHL       = document.getElementById("dc-hl");
  var elT0       = document.getElementById("dc-t0");
  var elInterval = document.getElementById("dc-interval");
  var elUptake   = document.getElementById("dc-uptake");
  var elFactor   = document.getElementById("dc-factor");
  var elResidual = document.getElementById("dc-residual");
  var elTbody    = document.getElementById("dc-tbody");
  var elSumConsumed  = document.getElementById("dc-summary-consumed");
  var elSumRemaining = document.getElementById("dc-summary-remaining");

  var patientCount = 10;

  // --- Helpers ---
  function pad2(n){ return n < 10 ? "0" + n : "" + n; }

  function minutesToHHMM(totalMinutes){
    var h = Math.floor(totalMinutes / 60) % 24;
    var m = Math.floor(totalMinutes % 60);
    return pad2(h) + ":" + pad2(m);
  }

  function parseTime(val){
    if(!val) return NaN;
    var parts = val.split(":");
    return parseInt(parts[0],10) * 60 + parseInt(parts[1],10);
  }

  function decay(activity, halfLife, dt){
    return activity * Math.exp(-LN2 / halfLife * dt);
  }

  // --- Build patient rows ---
  function buildRows(){
    var html = "";
    for(var i = 0; i < patientCount; i++){
      var bg = (i % 2 === 0) ? "transparent" : "rgba(255,255,255,0.02)";
      html += '<tr style="background:' + bg + '" id="dc-row-' + i + '">';
      html += '<td style="padding:0.45rem 0.5rem; color:var(--stone); font-family:var(--font-mono); border-bottom:1px solid var(--border-soft)">' + (i + 1) + '</td>';
      html += '<td style="padding:0.45rem 0.3rem; border-bottom:1px solid var(--border-soft)">';
      html += '<input type="number" id="dc-w-' + i + '" placeholder="kg" min="1" max="300" step="1" ';
      html += 'style="width:70px; padding:0.35rem 0.5rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:6px; color:var(--off-white); font-family:var(--font-mono); font-size:0.82rem" ';
      html += 'oninput="window._dcCalc &amp;&amp; window._dcCalc.recalc()">';
      html += '</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); color:var(--off-white); border-bottom:1px solid var(--border-soft)" id="dc-tinj-' + i + '">--</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); color:var(--off-white); border-bottom:1px solid var(--border-soft)" id="dc-tout-' + i + '">--</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); color:var(--off-white); border-bottom:1px solid var(--border-soft)" id="dc-avail-' + i + '">--</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); color:var(--stone); border-bottom:1px solid var(--border-soft)" id="dc-avail-mbq-' + i + '">--</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); color:var(--off-white); border-bottom:1px solid var(--border-soft)" id="dc-dose-' + i + '">--</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); color:var(--stone); border-bottom:1px solid var(--border-soft)" id="dc-volused-' + i + '">--</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); color:var(--off-white); border-bottom:1px solid var(--border-soft)" id="dc-rem-' + i + '">--</td>';
      html += '<td style="padding:0.45rem 0.5rem; font-family:var(--font-mono); border-bottom:1px solid var(--border-soft); text-align:center; font-size:1rem" id="dc-status-' + i + '">--</td>';
      html += '</tr>';
    }
    elTbody.innerHTML = html;
  }

  // --- Main recalculation ---
  function recalc(){
    var a0       = parseFloat(elA0.value) || 0;
    var vol0     = parseFloat(elVol.value) || 0;
    var halfLife = parseFloat(elHL.value) || 109.77;
    var t0min    = parseTime(elT0.value);
    var interval = parseFloat(elInterval.value) || 25;
    var uptake   = parseFloat(elUptake.value) || 60;
    var factor   = parseFloat(elFactor.value) || 0.09;
    var residual = parseFloat(elResidual.value) || 0;

    if(isNaN(t0min)) t0min = 600; // default 10:00

    var availActivity = a0;
    var availVolume = vol0;
    var totalConsumed = 0;
    var totalWeight = 0;
    var lastRemaining = a0;

    for(var i = 0; i < patientCount; i++){
      var wEl = document.getElementById("dc-w-" + i);
      var weight = wEl ? (parseFloat(wEl.value) || 0) : 0;

      var injTime = t0min + i * interval;
      var exitTime = injTime + uptake;

      // decay from previous remaining
      if(i === 0){
        availActivity = a0;
        availVolume = vol0;
      } else {
        availActivity = decay(lastRemaining, halfLife, interval);
        // volume stays as what was left
      }

      var elTinj     = document.getElementById("dc-tinj-" + i);
      var elTout     = document.getElementById("dc-tout-" + i);
      var elAvail    = document.getElementById("dc-avail-" + i);
      var elAvailMbq = document.getElementById("dc-avail-mbq-" + i);
      var elDose     = document.getElementById("dc-dose-" + i);
      var elVolUsed  = document.getElementById("dc-volused-" + i);
      var elRem      = document.getElementById("dc-rem-" + i);
      var elStatus   = document.getElementById("dc-status-" + i);
      var elRow      = document.getElementById("dc-row-" + i);

      if(!elTinj) continue;

      elTinj.textContent = minutesToHHMM(injTime);
      elTout.textContent = minutesToHHMM(exitTime);

      if(weight <= 0){
        // skip patient
        elAvail.textContent = "--";
        elAvailMbq.textContent = "--";
        elDose.textContent = "--";
        elVolUsed.textContent = "--";
        elRem.textContent = "--";
        elStatus.textContent = "--";
        elStatus.style.color = "var(--stone)";
        if(elRow) elRow.style.background = (i % 2 === 0) ? "transparent" : "rgba(255,255,255,0.02)";
        // pass through: remaining stays the same but decays
        lastRemaining = availActivity;
        continue;
      }

      var dose = weight * factor;
      var volumeUsed = (availActivity > 0) ? (availVolume * dose / availActivity) : 0;
      var remaining = availActivity - dose - residual;
      var ok = (dose <= availActivity) && (remaining >= -0.05);

      elAvail.textContent = availActivity.toFixed(1);
      elAvailMbq.textContent = (availActivity * 37).toFixed(1);
      elDose.textContent = dose.toFixed(1);
      elVolUsed.textContent = volumeUsed.toFixed(2);
      elRem.textContent = remaining.toFixed(1);

      if(ok){
        elStatus.innerHTML = '<span style="color:#22C55E">&#10003;</span>';
      } else {
        elStatus.innerHTML = '<span style="color:#EF4444">&#10007;</span>';
      }

      // row highlighting
      if(!ok){
        if(elRow) elRow.style.background = "rgba(239,68,68,0.08)";
      } else if(remaining < dose * 0.2){
        // amber warning: less than 20% margin
        if(elRow) elRow.style.background = "rgba(255,132,0,0.06)";
      } else {
        if(elRow) elRow.style.background = (i % 2 === 0) ? "transparent" : "rgba(255,255,255,0.02)";
      }

      totalConsumed += dose + residual;
      totalWeight += weight;
      lastRemaining = remaining > 0 ? remaining : 0;
      availVolume = availVolume - volumeUsed;
      if(availVolume < 0) availVolume = 0;
    }

    // Summary
    elSumConsumed.textContent = "Consumo total: " + totalConsumed.toFixed(1) + " mCi (" + (totalConsumed * 37).toFixed(0) + " MBq) · Peso total: " + totalWeight.toFixed(0) + " kg";
    elSumRemaining.textContent = "Remanescente final: " + lastRemaining.toFixed(1) + " mCi (" + (lastRemaining * 37).toFixed(0) + " MBq)";
  }

  // --- Isotope change handler ---
  function onIsotopeChange(){
    var val = elIsotope.value;
    if(val === "custom"){
      elHL.value = "";
      elHL.focus();
    } else {
      // extract numeric half-life
      var hl = parseFloat(val);
      if(!isNaN(hl)){
        elHL.value = hl;
      }
    }
    recalc();
  }

  // --- Add patient ---
  function addPatient(){
    if(patientCount >= MAX_PATIENTS) return;
    patientCount++;
    buildRows();
    recalc();
  }

  // --- Init ---
  buildRows();
  recalc();

  // Expose for onclick handlers
  window._dcCalc = {
    recalc: recalc,
    onIsotopeChange: onIsotopeChange,
    addPatient: addPatient
  };
})();
</script>

    </section>
"""


def main():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # ---- 1. Insert navigation card ----
    # Find the last tool-link card (Oncologia clinica, href="#clinica")
    # and insert after its closing </a> tag
    clinica_pattern = r'(      <a href="#clinica" class="tool-link"[^>]*>.*?</a>)'
    match = re.search(clinica_pattern, html, re.DOTALL)
    if not match:
        raise RuntimeError("Could not find the #clinica tool-link card")

    insert_pos = match.end()
    html = html[:insert_pos] + "\n" + NAV_CARD + html[insert_pos:]
    print("[OK] Navigation card inserted after #clinica card.")

    # ---- 2. Insert section before <!-- FOOTER --> ----
    footer_sentinel = "<!-- FOOTER -->"
    footer_idx = html.find(footer_sentinel)
    if footer_idx < 0:
        raise RuntimeError("Could not find <!-- FOOTER --> sentinel")

    html = html[:footer_idx] + SECTION_HTML + "\n" + html[footer_idx:]
    print("[OK] Section #decay-calc inserted before FOOTER.")

    # ---- 3. Write back ----
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    total_lines = html.count("\n") + 1
    print(f"[OK] File written. Total lines: {total_lines}")


if __name__ == "__main__":
    main()
