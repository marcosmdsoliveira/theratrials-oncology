/* ============================================================================
 * ferramentas/decaimento.js — Calculadora de decaimento PET/CT (agenda de doses por meia-vida).
 *
 * Extraído LITERALMENTE de ferramentas.html (26/set/2026), sem nenhuma linha
 * reescrita. A indentação herdada do HTML foi mantida de propósito: os corpos
 * de modal são template strings, e preservá-los byte a byte é o que permite
 * provar a equivalência contra a versão inline (ver o harness de snapshot).
 *
 * Carregado como script CLÁSSICO e SÍNCRONO, na mesma posição em que o bloco
 * inline estava — mesma ordem de execução, mesmo escopo global compartilhado
 * (`const` de topo e `function` continuam visíveis aos handlers inline).
 * Expõe window._dcCalc. No app iOS a seção #decay-calc é removida pelo native-guards.js (Guideline 1.4.1).
 * ==========================================================================*/

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
    var residual = 0;

    if(isNaN(t0min)) t0min = 480; // default 08:00

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

      elAvail.textContent = availActivity.toFixed(2);
      elAvailMbq.textContent = (availActivity * 37).toFixed(1);
      elDose.textContent = dose.toFixed(2);
      elVolUsed.textContent = volumeUsed.toFixed(2);
      elRem.textContent = remaining.toFixed(2);

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
    elSumConsumed.textContent = "Consumo total: " + totalConsumed.toFixed(2) + " mCi (" + (totalConsumed * 37).toFixed(1) + " MBq) · Peso total: " + totalWeight.toFixed(0) + " kg";
    elSumRemaining.textContent = "Remanescente final: " + lastRemaining.toFixed(2) + " mCi (" + (lastRemaining * 37).toFixed(1) + " MBq)";
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
