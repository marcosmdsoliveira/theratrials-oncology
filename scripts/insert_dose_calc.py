#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
insert_dose_calc.py
Inserts the Radiopharmaceutical Dose Calculator section into ferramentas.html.
"""

import pathlib, sys

HTML_PATH = pathlib.Path(r"C:\Users\marco\Desktop\TheraTrials Oncology\site\ferramentas.html")

# The sentinel that marks the end of the clinica section + parent container close
SENTINEL = "    </section>\n\n  </div>\n</section>"

# ── NEW SECTION ──────────────────────────────────────────────────────────────
NEW_SECTION = r'''    <section class="tool" id="dose-calc" style="--tool-accent: #10B981">
      <div class="tool-head">
        <div class="tool-num" style="background: rgba(16, 185, 129, 0.15); color: #10B981">10</div>
        <h2>Calculadora de dose &middot; Radiof&aacute;rmacos diagn&oacute;sticos</h2>
      </div>
      <p style="color: var(--stone); margin: 0 0 1.5rem; max-width: 720px; line-height: 1.55">
        C&aacute;lculo de atividade administrada para medicina nuclear diagn&oacute;stica, comparando <strong>EANM Dosage Card 2016</strong> (sistema de classes pedi&aacute;tricas) e <strong>North American Consensus 2024</strong> (dose por peso com limites).
      </p>

      <!-- Inputs -->
      <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:1.5rem; align-items:flex-end">
        <div style="flex:0 0 140px">
          <label for="dose-weight" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Peso (kg)</label>
          <input type="number" id="dose-weight" value="70" min="3" max="200" step="1"
                 style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-mono); font-size:0.95rem"
                 oninput="calcDose()">
        </div>
        <div style="flex:1 1 340px">
          <label for="dose-radio" style="display:block; font-size:0.78rem; color:var(--stone); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.35rem">Radiof&aacute;rmaco</label>
          <select id="dose-radio"
                  style="width:100%; padding:0.55rem 0.7rem; background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:8px; color:var(--off-white); font-family:var(--font-body); font-size:0.9rem"
                  onchange="calcDose()">
            <optgroup label="PET">
              <option value="fdg_body" selected>&#185;&#8312;F-FDG (corpo/torso)</option>
              <option value="fdg_brain">&#185;&#8312;F-FDG (c&eacute;rebro)</option>
              <option value="naf">&#185;&#8312;F-Fluoreto de s&oacute;dio</option>
              <option value="fdopa">&#185;&#8312;F-FDOPA</option>
              <option value="ga68_dotatate">&#8310;&#8312;Ga-DOTATATE</option>
              <option value="ga68_dotatoc">&#8310;&#8312;Ga-DOTATOC</option>
              <option value="ga68_peptides">&#8310;&#8312;Ga-pept&iacute;deos (DOTATATE/TOC)</option>
              <option value="nh3">&#185;&#179;N-am&ocirc;nia (card&iacute;aco)</option>
              <option value="rb82">&#8312;&#178;Rb (card&iacute;aco)</option>
            </optgroup>
            <optgroup label="&Oacute;sseo">
              <option value="mdp">&#8313;&#8313;&#7489;Tc-MDP (&oacute;ssea)</option>
            </optgroup>
            <optgroup label="Renal">
              <option value="dmsa">&#8313;&#8313;&#7489;Tc-DMSA (cortical renal)</option>
              <option value="mag3">&#8313;&#8313;&#7489;Tc-MAG3 (renograma)</option>
              <option value="mag3_flow">&#8313;&#8313;&#7489;Tc-MAG3 (c/ fluxo)</option>
              <option value="dtpa_abnormal">&#8313;&#8313;&#7489;Tc-DTPA (fun&ccedil;&atilde;o anormal)</option>
              <option value="dtpa_normal">&#8313;&#8313;&#7489;Tc-DTPA (fun&ccedil;&atilde;o normal)</option>
              <option value="hippuran_abnormal">&#185;&#178;&#179;I-Hippuran (fun&ccedil;&atilde;o anormal)</option>
              <option value="hippuran_normal">&#185;&#178;&#179;I-Hippuran (fun&ccedil;&atilde;o normal)</option>
            </optgroup>
            <optgroup label="Card&iacute;aco">
              <option value="mibi_1day_rest">&#8313;&#8313;&#7489;Tc-MIBI (1-dia: repouso)</option>
              <option value="mibi_1day_stress">&#8313;&#8313;&#7489;Tc-MIBI (1-dia: estresse)</option>
              <option value="mibi_2day_rest_min">&#8313;&#8313;&#7489;Tc-MIBI (2-dias: rep. m&iacute;n)</option>
              <option value="mibi_2day_rest_max">&#8313;&#8313;&#7489;Tc-MIBI (2-dias: rep. m&aacute;x)</option>
              <option value="mibi_2day_stress_min">&#8313;&#8313;&#7489;Tc-MIBI (2-dias: estr. m&iacute;n)</option>
              <option value="mibi_2day_stress_max">&#8313;&#8313;&#7489;Tc-MIBI (2-dias: estr. m&aacute;x)</option>
              <option value="mibi_1scan">&#8313;&#8313;&#7489;Tc-MIBI (scan &uacute;nico)</option>
              <option value="rbc_pool">&#8313;&#8313;&#7489;Tc-hem&aacute;cias (blood pool)</option>
              <option value="albumin_cardiac">&#8313;&#8313;&#7489;Tc-albumina (card&iacute;aco)</option>
              <option value="pertec_firstpass">&#8313;&#8313;&#7489;Tc-pertecnetato (first pass)</option>
            </optgroup>
            <optgroup label="Tire&oacute;ide">
              <option value="i123_thyroid">&#185;&#178;&#179;I (tire&oacute;ide &ndash; capta&ccedil;&atilde;o)</option>
              <option value="i123_cancer">&#185;&#178;&#179;I (tire&oacute;ide &ndash; ca. diferenciado)</option>
              <option value="pertec_thyroid">&#8313;&#8313;&#7489;Tc-pertecnetato (tire&oacute;ide)</option>
            </optgroup>
            <optgroup label="C&eacute;rebro">
              <option value="hmpao">&#8313;&#8313;&#7489;Tc-HMPAO/ECD (perfus&atilde;o cerebral)</option>
              <option value="i123_amp">&#185;&#178;&#179;I-anfetamina (c&eacute;rebro)</option>
            </optgroup>
            <optgroup label="Pulm&atilde;o">
              <option value="maa_vent">&#8313;&#8313;&#7489;Tc-MAA (c/ ventila&ccedil;&atilde;o)</option>
              <option value="maa_novent">&#8313;&#8313;&#7489;Tc-MAA (s/ ventila&ccedil;&atilde;o)</option>
              <option value="technegas">&#8313;&#8313;&#7489;Tc-Technegas (ventila&ccedil;&atilde;o)</option>
            </optgroup>
            <optgroup label="Abdome">
              <option value="ida">&#8313;&#8313;&#7489;Tc-IDA (biliar/HIDA)</option>
              <option value="colloid_liver">&#8313;&#8313;&#7489;Tc-coloide (f&iacute;gado/ba&ccedil;o)</option>
              <option value="colloid_marrow">&#8313;&#8313;&#7489;Tc-coloide (medula)</option>
              <option value="colloid_ge_liquid">&#8313;&#8313;&#7489;Tc-coloide (esv. l&iacute;quido)</option>
              <option value="colloid_ge_solid">&#8313;&#8313;&#7489;Tc-coloide (esv. s&oacute;lido)</option>
              <option value="pertec_meckel">&#8313;&#8313;&#7489;Tc-pertecnetato (Meckel)</option>
            </optgroup>
            <optgroup label="Outros">
              <option value="mibg_diag">&#185;&#178;&#179;I-MIBG (diagn&oacute;stico)</option>
              <option value="mibg_131">&#185;&#179;&#185;I-MIBG (diagn&oacute;stico)</option>
              <option value="mibi_onco">&#8313;&#8313;&#7489;Tc-MIBI (oncol&oacute;gico)</option>
              <option value="wbc">&#8313;&#8313;&#7489;Tc-HMPAO WBC (infec&ccedil;&atilde;o)</option>
              <option value="ga67">&#8310;&#8311;Ga-citrato</option>
              <option value="spleen_rbc">&#8313;&#8313;&#7489;Tc-hem&aacute;cias desnaturadas (ba&ccedil;o)</option>
              <option value="cystography">&#8313;&#8313;&#7489;Tc-cistografia</option>
            </optgroup>
          </select>
        </div>
      </div>

      <!-- Result cards -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:1rem; margin-bottom:1.5rem">
        <!-- EANM card -->
        <div style="background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:var(--radius-md); padding:1.25rem 1.4rem">
          <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.9rem">
            <div style="width:8px;height:8px;border-radius:50%;background:#10B981"></div>
            <span style="font-family:var(--font-display); font-size:0.82rem; font-weight:600; color:#10B981; text-transform:uppercase; letter-spacing:0.04em">EANM Dosage Card 2016</span>
          </div>
          <div style="display:flex; align-items:baseline; gap:0.6rem; margin-bottom:0.25rem">
            <span id="eanm-dose" style="font-family:var(--font-mono); font-size:1.7rem; font-weight:700; color:var(--off-white)">--</span>
            <span style="font-size:0.85rem; color:var(--stone)">MBq</span>
            <span style="color:var(--border-soft)">|</span>
            <span id="eanm-dose-mci" style="font-family:var(--font-mono); font-size:1.1rem; color:var(--stone)">--</span>
            <span style="font-size:0.8rem; color:var(--stone)">mCi</span>
          </div>
          <div id="eanm-min" style="font-size:0.78rem; color:var(--stone); margin-bottom:0.5rem"></div>
          <div id="eanm-detail" style="font-size:0.78rem; color:var(--stone); line-height:1.5; border-top:1px solid var(--border-soft); padding-top:0.5rem"></div>
        </div>

        <!-- NA Consensus card -->
        <div style="background:var(--graphite-2); border:1px solid var(--border-soft); border-radius:var(--radius-md); padding:1.25rem 1.4rem">
          <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.9rem">
            <div style="width:8px;height:8px;border-radius:50%;background:#38BDF8"></div>
            <span style="font-family:var(--font-display); font-size:0.82rem; font-weight:600; color:#38BDF8; text-transform:uppercase; letter-spacing:0.04em">North American Consensus 2024</span>
          </div>
          <div style="display:flex; align-items:baseline; gap:0.6rem; margin-bottom:0.25rem">
            <span id="na-dose" style="font-family:var(--font-mono); font-size:1.7rem; font-weight:700; color:var(--off-white)">--</span>
            <span style="font-size:0.85rem; color:var(--stone)">MBq</span>
            <span style="color:var(--border-soft)">|</span>
            <span id="na-dose-mci" style="font-family:var(--font-mono); font-size:1.1rem; color:var(--stone)">--</span>
            <span style="font-size:0.8rem; color:var(--stone)">mCi</span>
          </div>
          <div id="na-range" style="font-size:0.78rem; color:var(--stone); margin-bottom:0.5rem"></div>
          <div id="na-detail" style="font-size:0.78rem; color:var(--stone); line-height:1.5; border-top:1px solid var(--border-soft); padding-top:0.5rem"></div>
        </div>
      </div>

      <!-- Disclaimer -->
      <div style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.18); border-radius:var(--radius-md); padding:0.9rem 1.1rem; font-size:0.78rem; color:var(--stone); line-height:1.55">
        <strong style="color:#10B981">&#9888; Aviso:</strong> Esta calculadora &eacute; uma ferramenta auxiliar de refer&ecirc;ncia. As doses devem ser validadas pelo m&eacute;dico nuclear respons&aacute;vel conforme protocolos institucionais, equipamento dispon&iacute;vel e condi&ccedil;&otilde;es cl&iacute;nicas do paciente. N&atilde;o substitui julgamento cl&iacute;nico.
      </div>

<script>
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

  // -- Main calculation --
  window.calcDose = function() {
    var weight = parseFloat(document.getElementById("dose-weight").value) || 70;
    var sel = document.getElementById("dose-radio").value;

    // EANM calculation
    var eD = document.getElementById("eanm-dose");
    var eDm = document.getElementById("eanm-dose-mci");
    var eMin = document.getElementById("eanm-min");
    var eDet = document.getElementById("eanm-detail");

    var eRec = eanmData[sel];
    if (eRec) {
      var mult = getMultiple(weight, eRec.cls);
      var eanmMBq = eRec.base * mult;
      var appliedMin = false;
      if (eanmMBq < eRec.min) {
        eanmMBq = eRec.min;
        appliedMin = true;
      }
      var eanmMCi = eanmMBq / 37;
      eD.textContent = fmt(eanmMBq);
      eDm.textContent = fmt(eanmMCi, 2);
      eMin.textContent = appliedMin
        ? "Dose mínima aplicada (" + eRec.min + " MBq)"
        : "Mínimo recomendado: " + eRec.min + " MBq";
      eMin.style.color = appliedMin ? "#FBBF24" : "";
      eDet.textContent = "Classe " + eRec.cls + " · Baseline " + eRec.base
        + " MBq × múltiplo " + fmt(mult, 2) + " = " + fmt(eRec.base * mult) + " MBq";
    } else {
      eD.textContent = "N/A";
      eDm.textContent = "--";
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
        // Clamp to min
        if (nRec.mn !== null && naMBq < nRec.mn) naMBq = nRec.mn;
        // Clamp to max only for patients <= 70 kg
        if (nRec.mx !== null && weight <= 70 && naMBq > nRec.mx) naMBq = nRec.mx;
        var naMCi = naMBq / 37;
        nD.textContent = fmt(naMBq);
        nDm.textContent = fmt(naMCi, 2);

        var rangeStr = "";
        if (nRec.lo === nRec.hi) {
          rangeStr = fmt(nRec.lo, 2) + " MBq/kg";
        } else {
          rangeStr = fmt(nRec.lo, 2) + " – " + fmt(nRec.hi, 2) + " MBq/kg (média usada)";
        }
        if (nRec.mn !== null || nRec.mx !== null) {
          rangeStr += " · Limites: "
            + (nRec.mn !== null ? fmt(nRec.mn) : "--") + " – "
            + (nRec.mx !== null ? fmt(nRec.mx) : "∞") + " MBq";
        }
        nRng.textContent = rangeStr;
        nDet.textContent = fmt(midRate, 2) + " MBq/kg × " + fmt(weight, 0)
          + " kg = " + fmt(midRate * weight) + " MBq" + (nRec.note ? " · " + nRec.note : "");
      } else {
        // Fixed-dose (no weight-based)
        var fixedMBq = null;
        if (nRec.mn !== null && nRec.mx !== null) {
          fixedMBq = (nRec.mn + nRec.mx) / 2;
        } else if (nRec.mx !== null) {
          fixedMBq = nRec.mx;
        } else if (nRec.mn !== null) {
          fixedMBq = nRec.mn;
        }
        if (fixedMBq !== null) {
          nD.textContent = fmt(fixedMBq);
          nDm.textContent = fmt(fixedMBq / 37, 2);
        } else {
          nD.textContent = "N/A";
          nDm.textContent = "--";
        }
        nRng.textContent = nRec.note || "Dose fixa (sem cálculo por peso)";
        nDet.textContent = "Faixa: "
          + (nRec.mn !== null ? fmt(nRec.mn) : "--") + " – "
          + (nRec.mx !== null ? fmt(nRec.mx) : "∞") + " MBq";
      }
    } else {
      nD.textContent = "N/A";
      nDm.textContent = "--";
      nRng.textContent = "";
      nDet.textContent = "Radiofármaco não listado no NA Consensus 2024";
    }
  };

  // Run on load
  calcDose();
})();
</script>
    </section>'''

# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if not HTML_PATH.exists():
        print(f"ERROR: File not found: {HTML_PATH}")
        sys.exit(1)

    content = HTML_PATH.read_text(encoding="utf-8")
    line_count_before = content.count("\n") + 1
    print(f"Lines before: {line_count_before}")

    # Find the sentinel
    idx = content.find(SENTINEL)
    if idx == -1:
        print("ERROR: Could not find sentinel string in file.")
        print("Looking for:")
        print(repr(SENTINEL))
        sys.exit(1)

    print(f"Sentinel found at character offset {idx}")

    # Split: keep the "    </section>\n\n" (clinica close), then insert new section,
    # then close with "  </div>\n</section>"
    clinica_close = "    </section>\n\n"
    parent_close  = "  </div>\n</section>"

    # Replace sentinel with: clinica_close + NEW_SECTION + "\n\n" + parent_close
    new_content = content[:idx] + clinica_close + NEW_SECTION + "\n\n" + parent_close + content[idx + len(SENTINEL):]

    HTML_PATH.write_text(new_content, encoding="utf-8")

    line_count_after = new_content.count("\n") + 1
    print(f"Lines after:  {line_count_after}")
    print(f"Lines added:  {line_count_after - line_count_before}")
    print("Done. Dose calculator section inserted successfully.")


if __name__ == "__main__":
    main()
