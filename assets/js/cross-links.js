/**
 * cross-links.js — Bidirectional cross-linking between
 * Radiofarmaco dossier pages and Guideline detail pages.
 *
 * On a radiofarmaco page: renders a "Guidelines relacionados" section.
 * On guideline-detail.html: exports data for the page to consume.
 */
(function () {
  'use strict';

  /* ── Radiofarmaco metadata ── */
  var RF = {
    'lu-psma.html':      { name: '177Lu-PSMA-617',     mass: '177', elem: 'Lu', color: '#FF8400', desc: 'Radioligand therapy para mCRPC PSMA-positivo' },
    'lu-dotatate.html':  { name: '177Lu-DOTATATE',      mass: '177', elem: 'Lu', color: '#10B981', desc: 'PRRT para tumores neuroendócrinos' },
    'ra-223.html':       { name: '223Ra-Cloreto',       mass: '223', elem: 'Ra', color: '#C084FC', desc: 'Alfa-emissor para metástases ósseas' },
    'y90.html':          { name: '90Y-Microesferas',    mass: '90',  elem: 'Y',  color: '#F59E0B', desc: 'Radioembolização hepática (TARE)' },
    'mibg.html':         { name: '131I-MIBG',           mass: '131', elem: 'I',  color: '#F472B6', desc: 'Terapia para neuroblastoma e feocromocitoma' },
    'iodo-131.html':     { name: '131I-Iodeto',         mass: '131', elem: 'I',  color: '#06B6D4', desc: 'Radioiodoterapia para doenças tireoidianas' },
    'novos-alfa.html':   { name: 'Novos α-emissores', mass: 'α', elem: '',  color: '#A855F7', desc: '225Ac, 212Pb e 161Tb em investigação' }
  };

  /* ── Guideline metadata (lightweight — just what's needed for cards) ── */
  var GL = {
    'prrt-eanm-iaea-snmmi-2026':       { t: 'EANM/IAEA/SNMMI Practical Guidance — PRRT',                y: '2026', s: 'EANM · IAEA · SNMMI', cat: 'PRRT',       cc: '#10B981' },
    'prrt-iaea-eanm-snmmi-2013':       { t: 'IAEA/EANM/SNMMI Practical Guidance — PRRT',                y: '2013', s: 'IAEA · EANM · SNMMI', cat: 'PRRT',       cc: '#10B981' },
    'prrt-nanets-snmmi-dotatate':      { t: 'NANETS/SNMMI Procedure Guidelines — 177Lu-DOTATATE',       y: '2022', s: 'NANETS · SNMMI',           cat: 'PRRT',       cc: '#10B981' },
    'prrt-sstr-pet-imaging-2023':      { t: 'SNMMI/EANM SSTR PET Imaging — Neuroendocrine Tumors',      y: '2023', s: 'SNMMI · EANM',             cat: 'PRRT',       cc: '#10B981' },
    'psma-rlt-eanm-snmmi-2023':        { t: 'EANM/SNMMI Procedure Guideline — 177Lu-PSMA-RLT',          y: '2023', s: 'EANM · SNMMI',             cat: 'PSMA',       cc: '#FF8400' },
    'psma-pet-imaging-v2-2023':        { t: 'EANM/SNMMI PSMA PET/CT Guideline v2.0',                    y: '2023', s: 'EANM · SNMMI',             cat: 'PSMA',       cc: '#FF8400' },
    'psma-eanm-2019':                  { t: 'EANM Procedure Guidelines — 177Lu-PSMA Ligands',           y: '2019', s: 'EANM',                           cat: 'PSMA',       cc: '#FF8400' },
    'tare-eanm-procedure-2022':        { t: 'EANM Procedure Guideline — TARE',                          y: '2022', s: 'EANM',                           cat: 'TARE',       cc: '#F59E0B' },
    'tare-dosimetry-sop-2021':         { t: 'EANM Dosimetry SOP — MAA/90Y TARE',                        y: '2021', s: 'EANM',                           cat: 'TARE',       cc: '#F59E0B' },
    'tare-glass-microspheres-2025':    { t: '90Y Glass Microsphere Radioembolization',                   y: '2025', s: 'Multisocietária',                cat: 'TARE',       cc: '#F59E0B' },
    'rait-snmmi-eanm-dtc-2022':        { t: 'SNMMI/EANM DTC Evaluation and Therapy',                    y: '2022', s: 'SNMMI · EANM',             cat: 'Tireoide',   cc: '#06B6D4' },
    'rait-eanm-benign-2023':           { t: 'EANM Radioiodine Therapy — Benign Thyroid',                 y: '2023', s: 'EANM',                           cat: 'Tireoide',   cc: '#06B6D4' },
    'rait-ata-dtc-2025':               { t: 'ATA Management Guidelines — DTC',                           y: '2025', s: 'ATA',                            cat: 'Tireoide',   cc: '#06B6D4' },
    'bone-snmmi-eanm-palliative-2023': { t: 'SNMMI/EANM Palliative Nuclear Medicine — Bone',             y: '2023', s: 'SNMMI · EANM',             cat: 'M. Ósseas', cc: '#C084FC' },
    'bone-eanm-beta-2018':             { t: 'EANM Beta-Emitters — Bone Metastases',                      y: '2018', s: 'EANM',                           cat: 'M. Ósseas', cc: '#C084FC' },
    'bone-acr-ra223-2020':             { t: 'ACR/SNMMI Practice Parameter — Ra-223',                     y: '2020', s: 'ACR · SNMMI',               cat: 'M. Ósseas', cc: '#C084FC' },
    'mibg-eanm-procedure-2008':        { t: 'EANM Procedure Guideline — 131I-MIBG Therapy',              y: '2008', s: 'EANM',                           cat: 'MIBG',       cc: '#F472B6' },
    'mibg-dosimetry-sop-2020':         { t: 'EANM Dosimetry SOP — 131I-MIBG',                            y: '2020', s: 'EANM',                           cat: 'MIBG',       cc: '#F472B6' },
    'rso-eanm-2022':                   { t: 'EANM Guideline — Radiosynoviorthesis',                      y: '2022', s: 'EANM',                           cat: 'RSO',        cc: '#F59E0B' },
    'dosim-eanm-lu177-2022':           { t: 'EANM Dosimetry — 177Lu-DOTATATE and PSMA',                  y: '2022', s: 'EANM',                           cat: 'Dosimetria', cc: '#60A5FA' },
    'dosim-eanm-targeted-2026':        { t: 'EANM Dosimetry — Targeted Radionuclide Therapy',            y: '2026', s: 'EANM',                           cat: 'Dosimetria', cc: '#60A5FA' },
    'dosim-eanm-reporting':            { t: 'EANM Dosimetry Reporting — Good Practice',                  y: '',     s: 'EANM',                           cat: 'Dosimetria', cc: '#60A5FA' },
    'dosim-eanm-bone-marrow':          { t: 'EANM Bone Marrow and Whole-Body Dosimetry',                 y: '',     s: 'EANM',                           cat: 'Dosimetria', cc: '#60A5FA' },
    'posttherapy-snmmi-acnm-lu177-2025': { t: 'SNMMI/ACNM Post-Treatment Imaging — 177Lu',              y: '2025', s: 'SNMMI · ACNM',             cat: 'Imagem',     cc: '#0EA5B7' },
    'service-eanm-snmmi-iaea-2022':    { t: 'How to Set Up a Theranostics Centre',                       y: '2022', s: 'EANM · SNMMI · IAEA', cat: 'Serviço', cc: '#8E949C' },
    'service-iaea-release':            { t: 'IAEA Release of Patients After Radionuclide Therapy',        y: '',     s: 'IAEA',                           cat: 'Serviço', cc: '#8E949C' }
  };

  /* ── Forward mapping: radiofarmaco page → guideline IDs ── */
  var RF_TO_GL = {
    'lu-psma.html': [
      'psma-rlt-eanm-snmmi-2023', 'psma-pet-imaging-v2-2023', 'psma-eanm-2019',
      'dosim-eanm-lu177-2022', 'dosim-eanm-targeted-2026',
      'dosim-eanm-bone-marrow', 'posttherapy-snmmi-acnm-lu177-2025'
    ],
    'lu-dotatate.html': [
      'prrt-eanm-iaea-snmmi-2026', 'prrt-iaea-eanm-snmmi-2013',
      'prrt-nanets-snmmi-dotatate', 'prrt-sstr-pet-imaging-2023',
      'dosim-eanm-lu177-2022', 'dosim-eanm-targeted-2026',
      'posttherapy-snmmi-acnm-lu177-2025'
    ],
    'ra-223.html': [
      'bone-acr-ra223-2020', 'bone-snmmi-eanm-palliative-2023',
      'bone-eanm-beta-2018'
    ],
    'y90.html': [
      'tare-eanm-procedure-2022', 'tare-dosimetry-sop-2021',
      'tare-glass-microspheres-2025', 'rso-eanm-2022',
      'dosim-eanm-targeted-2026'
    ],
    'mibg.html': [
      'mibg-eanm-procedure-2008', 'mibg-dosimetry-sop-2020',
      'dosim-eanm-targeted-2026', 'dosim-eanm-bone-marrow'
    ],
    'iodo-131.html': [
      'rait-snmmi-eanm-dtc-2022', 'rait-eanm-benign-2023', 'rait-ata-dtc-2025',
      'dosim-eanm-targeted-2026'
    ],
    'novos-alfa.html': [
      'dosim-eanm-targeted-2026', 'psma-rlt-eanm-snmmi-2023',
      'prrt-eanm-iaea-snmmi-2026', 'bone-acr-ra223-2020'
    ]
  };

  /* ── Reverse mapping: guideline ID → radiofarmaco pages ── */
  var GL_TO_RF = {};
  Object.keys(RF_TO_GL).forEach(function (page) {
    RF_TO_GL[page].forEach(function (gId) {
      if (!GL_TO_RF[gId]) GL_TO_RF[gId] = [];
      if (GL_TO_RF[gId].indexOf(page) === -1) GL_TO_RF[gId].push(page);
    });
  });

  /* ── Expose for guideline-detail.html to consume ── */
  window.CROSS_LINKS = { RF: RF, GL: GL, GL_TO_RF: GL_TO_RF, RF_TO_GL: RF_TO_GL };

  /* ── Inject CSS (only once) ── */
  var style = document.createElement('style');
  style.textContent =
    '.cl-section{margin-top:2.5rem;margin-bottom:2.5rem;padding-top:2rem;border-top:1px solid rgba(255,255,255,0.06)}' +
    '.cl-section h3{font-family:Outfit,sans-serif;font-size:1.15rem;font-weight:600;color:var(--off-white,#F5F6F7);margin-bottom:1.2rem;display:flex;align-items:center;gap:.5rem}' +
    '.cl-section h3 svg{opacity:.6}' +
    '.cl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.75rem}' +
    '.cl-card{display:flex;align-items:center;gap:.85rem;padding:.85rem 1rem;border-radius:10px;' +
      'background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.10);text-decoration:none;' +
      'transition:all .25s ease;position:relative;overflow:hidden}' +
    '.cl-card:hover{background:rgba(255,255,255,0.08);border-color:rgba(255,255,255,0.18);transform:translateY(-1px)}' +
    '.cl-card::before{content:"";position:absolute;top:0;left:0;width:3px;height:100%;border-radius:3px 0 0 3px}' +
    '.cl-iso{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;' +
      'flex-shrink:0;font-family:"JetBrains Mono",monospace;font-size:.7rem;font-weight:700;line-height:1;' +
      'flex-direction:column;gap:0}' +
    '.cl-iso .m{font-size:.55rem;opacity:.8}' +
    '.cl-iso .e{font-size:.85rem}' +
    '.cl-info{flex:1;min-width:0}' +
    '.cl-name{font-family:Outfit,sans-serif;font-size:.88rem;font-weight:600;color:var(--off-white,#F5F6F7);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.cl-desc{font-size:.75rem;color:var(--stone,#8E949C);margin-top:2px;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}' +
    '.cl-cat{font-family:"JetBrains Mono",monospace;font-size:.6rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em;' +
      'padding:2px 7px;border-radius:4px;white-space:nowrap;flex-shrink:0}' +
    '.cl-arrow{color:var(--stone,#8E949C);flex-shrink:0;opacity:.4;transition:all .25s ease}' +
    '.cl-card:hover .cl-arrow{opacity:1;transform:translateX(2px)}' +
    '@media(max-width:600px){.cl-grid{grid-template-columns:1fr}}';
  document.head.appendChild(style);

  /* ── Detect current page ── */
  var path = window.location.pathname;
  var filename = path.substring(path.lastIndexOf('/') + 1) || 'index.html';

  /* ── Render on radiofarmaco pages ── */
  if (RF_TO_GL[filename]) {
    document.addEventListener('DOMContentLoaded', function () {
      var guidelines = RF_TO_GL[filename];
      if (!guidelines || !guidelines.length) return;

      var html = '<div class="cl-section">' +
        '<h3><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>' +
        ' Guidelines relacionados</h3>' +
        '<div class="cl-grid">';

      guidelines.forEach(function (gId) {
        var g = GL[gId];
        if (!g) return;
        html += '<a href="guideline-detail.html#' + gId + '" class="cl-card" style="--cl-c:' + g.cc + '">' +
          '<div style="position:absolute;top:0;left:0;width:3px;height:100%;background:' + g.cc + ';border-radius:3px 0 0 3px"></div>' +
          '<div class="cl-cat" style="background:' + g.cc + '18;color:' + g.cc + '">' + g.cat + '</div>' +
          '<div class="cl-info">' +
            '<div class="cl-name">' + g.t + '</div>' +
            '<div class="cl-desc">' + g.s + (g.y ? ' · ' + g.y : '') + '</div>' +
          '</div>' +
          '<svg class="cl-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>' +
        '</a>';
      });

      html += '</div></div>';

      /* Insert before #proximos */
      var proximos = document.getElementById('proximos');
      if (proximos) {
        var wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        proximos.parentNode.insertBefore(wrapper.firstElementChild, proximos);
      }
    });
  }
})();
