/* ============================================================================
 * ferramentas/dose.js — Calculadora de dose diagnóstica (EANM 2016 · North American Consensus 2024).
 *
 * Extraído LITERALMENTE de ferramentas.html (26/set/2026), sem nenhuma linha
 * reescrita. A indentação herdada do HTML foi mantida de propósito: os corpos
 * de modal são template strings, e preservá-los byte a byte é o que permite
 * provar a equivalência contra a versão inline (ver o harness de snapshot).
 *
 * Carregado como script CLÁSSICO e SÍNCRONO, na mesma posição em que o bloco
 * inline estava — mesma ordem de execução, mesmo escopo global compartilhado
 * (`const` de topo e `function` continuam visíveis aos handlers inline).
 * Expõe window.calcDose. No app iOS a seção #dose-calc é removida pelo native-guards.js (Guideline 1.4.1).
 * ==========================================================================*/

// =====================================================================
// Radiopharmaceutical Dose Calculator
// EANM Dosage Card 2016  +  North American Consensus 2024
// =====================================================================

(function(){
  "use strict";

  // -- EANM weight-to-multiple lookup table (class A, B, C) --
  var eanmTable = [
    {w:3,  a:1,    b:1,    c:1},
    {w:4,  a:1.12, b:1.14, c:1.33},
    {w:6,  a:1.47, b:1.71, c:2.00},
    {w:8,  a:1.71, b:2.14, c:3.00},
    {w:10, a:1.94, b:2.71, c:3.67},
    {w:12, a:2.18, b:3.14, c:4.67},
    {w:14, a:2.35, b:3.57, c:5.67},
    {w:16, a:2.53, b:4.00, c:6.33},
    {w:18, a:2.71, b:4.43, c:7.33},
    {w:20, a:2.88, b:4.86, c:8.33},
    {w:22, a:3.06, b:5.29, c:9.33},
    {w:24, a:3.18, b:5.71, c:10.00},
    {w:26, a:3.35, b:6.14, c:11.00},
    {w:28, a:3.47, b:6.43, c:12.00},
    {w:30, a:3.65, b:6.86, c:13.00},
    {w:32, a:3.77, b:7.29, c:14.00},
    {w:34, a:3.88, b:7.72, c:15.00},
    {w:36, a:4.00, b:8.00, c:16.00},
    {w:38, a:4.18, b:8.43, c:17.00},
    {w:40, a:4.29, b:8.86, c:18.00},
    {w:42, a:4.41, b:9.14, c:19.00},
    {w:44, a:4.53, b:9.57, c:20.00},
    {w:46, a:4.65, b:10.00, c:21.00},
    {w:48, a:4.77, b:10.29, c:22.00},
    {w:50, a:4.88, b:10.71, c:23.00},
    {w:52, a:5.00, b:11.00, c:24.00},
    {w:56, a:5.24, b:12.00, c:26.67},
    {w:60, a:5.47, b:12.71, c:28.67},
    {w:64, a:5.65, b:13.43, c:31.00},
    {w:68, a:5.77, b:14.00, c:32.33}
  ];

  // -- EANM radiopharmaceutical data --
  // cls: "A","B","C"  base: baseline MBq  min: minimum MBq
  var eanmData = {
    fdg_body:             {cls:"B", base:25.9,  min:26},
    fdg_brain:            {cls:"B", base:14.0,  min:14},
    naf:                  {cls:"B", base:10.5,  min:14},
    fdopa:                {cls:"B", base:14.0,  min:14},
    ga68_peptides:        {cls:"B", base:12.8,  min:14},
    nh3:                  {cls:"B", base:10.4,  min:14},
    rb82:                 {cls:"B", base:7.4,   min:14},
    mdp:                  {cls:"B", base:35.0,  min:40},
    dmsa:                 {cls:"B", base:6.8,   min:18.5},
    mag3:                 {cls:"A", base:11.9,  min:15},
    mag3_flow:            {cls:"A", base:11.9,  min:15},
    dtpa_abnormal:        {cls:"B", base:14.0,  min:20},
    dtpa_normal:          {cls:"A", base:34.0,  min:20},
    hippuran_abnormal:    {cls:"B", base:5.3,   min:10},
    hippuran_normal:      {cls:"A", base:12.8,  min:10},
    mibi_1day_rest:       {cls:"B", base:28.0,  min:80},
    mibi_1day_stress:     {cls:"B", base:84.0,  min:80},
    mibi_2day_rest_min:   {cls:"B", base:42.0,  min:80},
    mibi_2day_rest_max:   {cls:"B", base:63.0,  min:80},
    mibi_2day_stress_min: {cls:"B", base:42.0,  min:80},
    mibi_2day_stress_max: {cls:"B", base:63.0,  min:80},
    mibi_1scan:           {cls:"B", base:63.0,  min:80},
    rbc_pool:             {cls:"B", base:56.0,  min:80},
    albumin_cardiac:      {cls:"B", base:56.0,  min:80},
    pertec_firstpass:     {cls:"B", base:35.0,  min:80},
    i123_thyroid:         {cls:"C", base:0.6,   min:3},
    i123_cancer:          {cls:"B", base:3.7,   min:10},
    pertec_thyroid:       {cls:"B", base:5.6,   min:10},
    hmpao:                {cls:"B", base:51.8,  min:100},
    i123_amp:             {cls:"B", base:13.0,  min:18},
    maa:                  {cls:"B", base:5.6,   min:10},
    technegas:            {cls:"B", base:49.0,  min:100},
    ida:                  {cls:"B", base:10.5,  min:20},
    colloid_liver:        {cls:"B", base:5.6,   min:15},
    colloid_marrow:       {cls:"B", base:21.0,  min:20},
    colloid_ge:           {cls:"B", base:2.8,   min:10},
    pertec_meckel:        {cls:"B", base:10.5,  min:20},
    mibi_onco:            {cls:"B", base:63.0,  min:80},
    mibg_diag:            {cls:"B", base:28.0,  min:37},
    mibg_131:             {cls:"B", base:5.6,   min:35},
    wbc:                  {cls:"B", base:35.0,  min:40},
    ga67:                 {cls:"B", base:5.6,   min:10},
    spleen_rbc:           {cls:"B", base:2.8,   min:20},
    cystography:          {cls:"B", base:1.4,   min:20}
  };

  // -- North American Consensus 2024 data --
  // lo/hi: MBq per kg range (null = no weight-based dose)
  // mn/mx: min/max MBq (null = no limit)
  // note: extra info
  var naData = {
    mibg_diag:         {lo:5.2,   hi:5.2,   mn:37,    mx:370,  note:""},
    mdp:               {lo:9.3,   hi:9.3,   mn:37,    mx:740,  note:""},
    fdg_body:          {lo:2.96,  hi:5.2,   mn:26,    mx:370,  note:"Dose menor para equipamentos digitais"},
    fdg_brain:         {lo:1.85,  hi:3.7,   mn:14,    mx:148,  note:""},
    fdopa:             {lo:2.96,  hi:5.92,  mn:29.6,  mx:222,  note:""},
    dmsa:              {lo:1.85,  hi:1.85,  mn:18.5,  mx:100,  note:""},
    mag3:              {lo:3.7,   hi:3.7,   mn:37,    mx:148,  note:""},
    mag3_flow:         {lo:5.55,  hi:5.55,  mn:37,    mx:148,  note:""},
    ida:               {lo:1.85,  hi:1.85,  mn:18.5,  mx:null, note:""},
    maa_vent:          {lo:2.59,  hi:2.59,  mn:14.8,  mx:null, note:""},
    maa_novent:        {lo:1.11,  hi:1.11,  mn:14.8,  mx:null, note:""},
    pertec_meckel:     {lo:1.85,  hi:1.85,  mn:9.25,  mx:296,  note:""},
    naf:               {lo:1.85,  hi:1.85,  mn:18.5,  mx:148,  note:""},
    cystography:       {lo:null,  hi:null,  mn:null,   mx:37,   note:"Sem dose por peso; até 37 MBq por ciclo"},
    colloid_ge_liquid: {lo:null,  hi:null,  mn:18.5,  mx:37,   note:"Sem dose por peso"},
    colloid_ge_solid:  {lo:null,  hi:null,  mn:9.25,  mx:18.5, note:"Sem dose por peso"},
    hmpao:             {lo:11.1,  hi:11.1,  mn:185,   mx:740,  note:""},
    mibi_1scan:        {lo:5.55,  hi:5.55,  mn:185,   mx:370,  note:""},
    mibi_2nd:          {lo:16.7,  hi:16.7,  mn:185,   mx:1110, note:""},
    nh3:               {lo:10.4,  hi:10.4,  mn:74,    mx:null, note:""},
    rb82:              {lo:7.4,   hi:7.4,   mn:370,   mx:null, note:""},
    i123_thyroid:      {lo:0.28,  hi:0.28,  mn:1,     mx:11,   note:""},
    i123_cancer:       {lo:3.7,   hi:3.7,   mn:74,    mx:148,  note:""},
    pertec_thyroid:    {lo:1.1,   hi:1.1,   mn:7,     mx:93,   note:""},
    rbc_pool:          {lo:11.8,  hi:11.8,  mn:74,    mx:740,  note:""},
    wbc:               {lo:7.4,   hi:7.4,   mn:74,    mx:555,  note:""},
    ga68_dotatate:     {lo:2.0,   hi:2.0,   mn:14,    mx:200,  note:""},
    ga68_dotatoc:      {lo:1.59,  hi:1.59,  mn:11.1,  mx:111,  note:""}
  };

  // Map select values to EANM keys when IDs differ
  var eanmAlias = {
    maa_vent: "maa",
    maa_novent: "maa",
    colloid_ge_liquid: "colloid_ge",
    colloid_ge_solid: "colloid_ge",
    ga68_dotatate: "ga68_peptides",
    ga68_dotatoc: "ga68_peptides"
  };

  // Map some select values to NA equivalents when IDs differ
  var naAlias = {
    maa: "maa_vent",
    colloid_ge: "colloid_ge_solid",
    ga68_peptides: "ga68_dotatate"
  };

  // -- Interpolate EANM weight multiple --
  function getMultiple(weight, cls) {
    var key = cls.toLowerCase();
    // Clamp to table range
    if (weight <= 3) return eanmTable[0][key];
    if (weight >= 68) return eanmTable[eanmTable.length - 1][key];
    // Find surrounding entries
    for (var i = 0; i < eanmTable.length - 1; i++) {
      var lo = eanmTable[i];
      var hi = eanmTable[i + 1];
      if (weight >= lo.w && weight <= hi.w) {
        if (lo.w === hi.w) return lo[key];
        var frac = (weight - lo.w) / (hi.w - lo.w);
        return lo[key] + frac * (hi[key] - lo[key]);
      }
    }
    return eanmTable[eanmTable.length - 1][key];
  }

  function fmt(v, d) {
    if (v === null || v === undefined || isNaN(v)) return "--";
    return v.toFixed(d === undefined ? 1 : d);
  }

  function mci(mbq) { return mbq / 37; }
  function dual(mbq, dMci) {
    var d = dMci === undefined ? 2 : dMci;
    return fmt(mci(mbq), d) + " mCi (" + fmt(mbq) + " MBq)";
  }

  // -- Main calculation --
  window.calcDose = function() {
    var weight = parseFloat(document.getElementById("dose-weight").value) || 70;
    var sel = document.getElementById("dose-radio").value;

    // EANM calculation
    var eD = document.getElementById("eanm-dose");
    var eDm = document.getElementById("eanm-dose-mci");
    var eMin = document.getElementById("eanm-min");
    var eDet = document.getElementById("eanm-detail");

    var eanmKey = eanmAlias[sel] || sel;
    var eRec = eanmData[eanmKey];
    if (eRec) {
      var mult = getMultiple(weight, eRec.cls);
      var eanmMBq = eRec.base * mult;
      var appliedMin = false;
      if (eanmMBq < eRec.min) {
        eanmMBq = eRec.min;
        appliedMin = true;
      }
      var eanmMCi = eanmMBq / 37;
      eDm.textContent = fmt(eanmMCi, 2);
      eD.textContent = fmt(eanmMBq);
      eMin.textContent = appliedMin
        ? "Dose mínima aplicada: " + dual(eRec.min)
        : "Mínimo recomendado: " + dual(eRec.min);
      eMin.style.color = appliedMin ? "#FBBF24" : "";
      var rawMBq = eRec.base * mult;
      eDet.textContent = "Classe " + eRec.cls + " · Baseline "
        + fmt(mci(eRec.base), 2) + " mCi (" + eRec.base + " MBq)"
        + " × múltiplo " + fmt(mult, 2) + " = " + dual(rawMBq);
    } else {
      eDm.textContent = "N/A";
      eD.textContent = "--";
      eMin.textContent = "";
      eDet.textContent = "Radiofármaco não listado no EANM Dosage Card 2016";
    }

    // NA Consensus calculation
    var nD = document.getElementById("na-dose");
    var nDm = document.getElementById("na-dose-mci");
    var nRng = document.getElementById("na-range");
    var nDet = document.getElementById("na-detail");

    var naKey = naAlias[sel] || sel;
    var nRec = naData[naKey];
    if (nRec) {
      if (nRec.lo !== null && nRec.hi !== null) {
        var midRate = (nRec.lo + nRec.hi) / 2;
        var naMBq = midRate * weight;
        if (nRec.mn !== null && naMBq < nRec.mn) naMBq = nRec.mn;
        if (nRec.mx !== null && weight <= 70 && naMBq > nRec.mx) naMBq = nRec.mx;
        var naMCi = naMBq / 37;
        nDm.textContent = fmt(naMCi, 2);
        nD.textContent = fmt(naMBq);

        var rangeStr = "";
        if (nRec.lo === nRec.hi) {
          rangeStr = fmt(mci(nRec.lo), 3) + " mCi/kg (" + fmt(nRec.lo, 2) + " MBq/kg)";
        } else {
          rangeStr = fmt(mci(nRec.lo), 3) + " – " + fmt(mci(nRec.hi), 3) + " mCi/kg ("
            + fmt(nRec.lo, 2) + " – " + fmt(nRec.hi, 2) + " MBq/kg, média usada)";
        }
        if (nRec.mn !== null || nRec.mx !== null) {
          rangeStr += " · Limites: "
            + (nRec.mn !== null ? dual(nRec.mn) : "--") + " – "
            + (nRec.mx !== null ? dual(nRec.mx) : "∞");
        }
        nRng.textContent = rangeStr;
        var rawNa = midRate * weight;
        nDet.textContent = fmt(mci(midRate), 3) + " mCi/kg × " + fmt(weight, 0)
          + " kg = " + dual(rawNa) + (nRec.note ? " · " + nRec.note : "");
      } else {
        var fixedMBq = null;
        if (nRec.mn !== null && nRec.mx !== null) {
          fixedMBq = (nRec.mn + nRec.mx) / 2;
        } else if (nRec.mx !== null) {
          fixedMBq = nRec.mx;
        } else if (nRec.mn !== null) {
          fixedMBq = nRec.mn;
        }
        if (fixedMBq !== null) {
          nDm.textContent = fmt(fixedMBq / 37, 2);
          nD.textContent = fmt(fixedMBq);
        } else {
          nDm.textContent = "N/A";
          nD.textContent = "--";
        }
        nRng.textContent = nRec.note || "Dose fixa (sem cálculo por peso)";
        nDet.textContent = "Faixa: "
          + (nRec.mn !== null ? dual(nRec.mn) : "--") + " – "
          + (nRec.mx !== null ? dual(nRec.mx) : "∞");
      }
    } else {
      nDm.textContent = "N/A";
      nD.textContent = "--";
      nRng.textContent = "";
      nDet.textContent = "Radiofármaco não listado no NA Consensus 2024";
    }
  };

  // Run on load
  calcDose();
})();
