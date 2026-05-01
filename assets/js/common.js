/* ============================================================
   TheraTrials Oncology — JavaScript comum
   Helpers, navegação e utilitários compartilhados
   ============================================================ */

(function() {
  'use strict';

  // Toggle do menu mobile
  document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    const nav = document.querySelector('.nav');
    if (navToggle && nav) {
      navToggle.addEventListener('click', () => nav.classList.toggle('open'));
    }

    // Marcar link ativo no menu
    const path = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav a').forEach(a => {
      const href = a.getAttribute('href') || '';
      if (href === path || (path === '' && href === 'index.html')) {
        a.classList.add('active');
      }
    });

    // Inicializa Lucide icons se disponível
    if (window.lucide) lucide.createIcons();
  });

  // ---------- Helpers de dados ----------
  window.TheraTrials = window.TheraTrials || {};

  TheraTrials.studyTitle = function(estudo) {
    if (!estudo) return '';
    return estudo.split('\n')[0].split('(')[0].trim();
  };

  TheraTrials.cleanText = function(t) {
    if (!t) return '';
    return String(t).replace(/\n+/g, ' · ');
  };

  TheraTrials.extractN = function(n) {
    if (!n) return '—';
    const m = String(n).match(/(\d{1,3}(?:\.\d{3})*|\d{2,4})/);
    return m ? `n=${m[0]}` : '—';
  };

  TheraTrials.extractYear = function(estudo) {
    if (!estudo) return 0;
    const m = String(estudo).match(/\((?:[^()]*?)(\d{4})/);
    return m ? parseInt(m[1]) : 0;
  };

  TheraTrials.phaseClass = function(fase) {
    const f = String(fase || '').toLowerCase();
    if (f.includes('fase 3') || f.includes('plataforma')) return 'phase-3';
    if (f.includes('fase 2')) return 'phase-2';
    if (f.includes('fase 1')) return 'phase-1';
    return 'phase-other';
  };

  TheraTrials.phaseShort = function(fase) {
    const f = String(fase || '').toLowerCase();
    if (f.includes('fase 3') && f.includes('plataforma')) return 'Fase 3 Plat.';
    if (f.includes('fase 3')) return 'Fase 3';
    if (f.includes('1/2')) return 'Fase 1/2';
    if (f.includes('fase 2')) return 'Fase 2';
    if (f.includes('fase 1')) return 'Fase 1';
    if (f.includes('coorte')) return 'Coorte';
    if (f.includes('retrospect')) return 'Retro';
    return fase || '—';
  };

  TheraTrials.isOngoing = function(s) {
    return s.status === 'Em andamento';
  };

  // ============================================================
  // FILTROS HIERÁRQUICOS — usados pelo database.html
  // ============================================================

  // Tipos tumorais (multi-select)
  TheraTrials.tumorTypes = [
    { id: 'prostata', name: 'Próstata', short: 'Próstata',
      match: (s) => ['lupsma_prostata', 'ra223_prostata', 'novos_psma', 'prostata_contexto'].includes(s.category_id) },
    { id: 'pulmao', name: 'Pulmão (NSCLC + SCLC)', short: 'Pulmão',
      match: (s) => ['nsclc_imuno', 'nsclc_alvo', 'nsclc_periop', 'sclc', 'lung_radio_dev'].includes(s.category_id) },
    { id: 'mama', name: 'Mama (HER2+, HR+, TNBC)', short: 'Mama',
      match: (s) => ['breast_her2', 'breast_hrpos', 'breast_tnbc_brca', 'breast_radio_dev'].includes(s.category_id) },
    { id: 'net', name: 'Tumores neuroendócrinos', short: 'NET',
      match: (s) => s.category_id === 'lu_dotatate_net' && !/(pheo|paragangli|neuroblastoma|ppgl)/i.test((s.indicacao || '') + ' ' + (s.estudo || '')) },
    { id: 'pheo_pgl', name: 'PPGL', short: 'PPGL',
      match: (s) => /(pheo|paragangli|ppgl|feocromo)/i.test((s.indicacao || '') + ' ' + (s.estudo || '')) },
    { id: 'neuroblastoma', name: 'Neuroblastoma', short: 'NB',
      match: (s) => /neuroblastoma/i.test((s.indicacao || '') + ' ' + (s.estudo || '')) },
    { id: 'hcc', name: 'Hepatocelular (HCC)', short: 'HCC',
      match: (s) => /(hcc|hepatocelular)/i.test(s.indicacao || '') },
    { id: 'mcrc', name: 'Colorretal (mCRC)', short: 'mCRC',
      match: (s) => /(mcrc|colorretal)/i.test(s.indicacao || '') },
    { id: 'ccrcc', name: 'Renal (ccRCC)', short: 'ccRCC',
      match: (s) => s.category_id === 'lupsma_ccrcc' },
  ];

  TheraTrials.tumorTypesUpcoming = [
    { id: 'melanoma', name: 'Melanoma' },
    { id: 'cabeca_pescoco', name: 'Cabeça e pescoço' },
    { id: 'tgi', name: 'Trato gastrointestinal' },
  ];

  // Modalidades terapêuticas (multi-select com subníveis)
  TheraTrials.modalities = [
    { id: 'teranostico', name: 'Teranóstico', short: 'Teranóstico',
      match: (s) => ['lupsma_prostata', 'ra223_prostata', 'lu_dotatate_net', 'lupsma_ccrcc', 'y90_tare', 'novos_psma', 'mibg_pediatria_pheo', 'lung_radio_dev', 'breast_radio_dev'].includes(s.category_id),
      subs: [
        { id: 'lupsma_prostata', name: '177Lu-PSMA · Próstata', short: 'Lu-PSMA' },
        { id: 'ra223_prostata', name: '223Ra · Próstata', short: 'Ra-223' },
        { id: 'lu_dotatate_net', name: '177Lu-DOTATATE · NET', short: 'Lu-DOTATATE' },
        { id: 'lupsma_ccrcc', name: '177Lu-PSMA · ccRCC', short: 'Lu-PSMA-RCC' },
        { id: 'y90_tare', name: 'Radioembolização 90Y', short: 'Y-90' },
        { id: 'novos_psma', name: 'Novos PSMA (α / 161Tb / RIT)', short: 'α-PSMA' },
        { id: 'mibg_pediatria_pheo', name: '131I-MIBG · PPGL · NB', short: 'MIBG/PPGL' },
        { id: 'lung_radio_dev', name: 'Pulmão · radio-exp (DLL3, FAPI)', short: 'Lung-radio' },
        { id: 'breast_radio_dev', name: 'Mama · 89Zr-trastu, FES, FAPI', short: 'Mama-radio' },
      ]},
    { id: 'imunoterapia', name: 'Imunoterapia (ICIs · vacinas · BiTE)', short: 'Imuno',
      match: (s) => {
        const r = (s.radiofarmaco || '').toLowerCase();
        if (/(sipuleucel|vacina)/i.test(r)) return true;
        if (['nsclc_imuno', 'sclc'].includes(s.category_id)) return true;
        if (s.category_id === 'nsclc_periop' && !/osi|alect/i.test(r)) return true;
        if (s.category_id === 'breast_tnbc_brca' && /pembro|nivo|atezo|durva/i.test(r)) return true;
        return false;
      },
      subs: [
        { id: 'nsclc_imuno', name: 'NSCLC · ICI 1L', short: 'NSCLC IO' },
        { id: 'nsclc_periop', name: 'NSCLC · perioperatório IO', short: 'NSCLC periop IO' },
        { id: 'sclc', name: 'SCLC · imuno + QT, BiTE', short: 'SCLC' },
        { id: 'breast_tnbc_brca', name: 'Mama · TNBC neoadj/1L (KEYNOTE-522/-355)', short: 'Mama TNBC IO' },
        { id: 'prostata_contexto', name: 'Próstata · vacinas (Sipuleucel-T)', short: 'Próstata' },
      ]},
    { id: 'terapia_alvo', name: 'Terapia-alvo (TKIs · ARPi · CDK4/6 · PI3K)', short: 'Alvo',
      match: (s) => {
        const r = (s.radiofarmaco || '').toLowerCase();
        const isProstateARPi = s.category_id === 'prostata_contexto' && /(abiraterona|enzalutamida|apalutamida|darolutamida)/i.test(r) && !/(olaparib|rucaparib|niraparib|talazoparib)/i.test(r);
        const isLungAlvo = s.category_id === 'nsclc_alvo';
        const isLungAdjAlvo = s.category_id === 'nsclc_periop' && /osi|alect/i.test(r);
        const isBreastAlvo = s.category_id === 'breast_hrpos' || (s.category_id === 'breast_her2' && /(tucatinib|neratinib|lapatinib)/i.test(r));
        return isProstateARPi || isLungAlvo || isLungAdjAlvo || isBreastAlvo;
      },
      subs: [
        { id: 'arpi', name: 'ARPi · próstata', short: 'ARPi' },
        { id: 'egfr', name: 'NSCLC · EGFR (FLAURA, MARIPOSA, ADAURA)', short: 'EGFR' },
        { id: 'alk', name: 'NSCLC · ALK (ALEX, CROWN, ALINA)', short: 'ALK' },
        { id: 'kras', name: 'NSCLC · KRAS G12C (CodeBreaK)', short: 'KRAS' },
        { id: 'ret_met_her2_ros1', name: 'NSCLC · RET / MET / HER2 / ROS1-NTRK', short: 'Outros drivers' },
        { id: 'cdk46', name: 'Mama · CDK4/6i (palbo, ribo, abema)', short: 'CDK4/6' },
        { id: 'pi3k_akt', name: 'Mama · PI3K/AKT (alpelisib, inavolisib, capivasertib)', short: 'PI3K/AKT' },
        { id: 'serd_her2tki', name: 'Mama · SERDs orais e HER2-TKI (elacestrant, tucatinib)', short: 'SERD/HER2-TKI' },
      ]},
    { id: 'adc', name: 'ADC · conjugados anticorpo-droga', short: 'ADC',
      match: (s) => /(trastuzumab emtansine|t-dm1|trastuzumab deruxtecan|t-dxd|sacituzumab|datopotamab)/i.test(s.radiofarmaco || ''),
      subs: [
        { id: 'tdm1', name: 'T-DM1 (HER2+)', short: 'T-DM1' },
        { id: 'tdxd', name: 'T-DXd (HER2+ e HER2-low)', short: 'T-DXd' },
        { id: 'sacituzumab', name: 'Sacituzumab govitecan (TNBC, Trop-2)', short: 'Sacituzumab' },
      ]},
    { id: 'parp', name: 'PARP inibidores', short: 'PARP',
      match: (s) => /(olaparib|rucaparib|niraparib|talazoparib)/i.test(s.radiofarmaco || ''),
      subs: [
        { id: 'parp_prostata', name: 'Próstata HRR+ (PROfound, TRITON, PROpel, MAGNITUDE, TALAPRO)', short: 'Próstata' },
        { id: 'parp_mama', name: 'Mama BRCA+ (OlympiAD, EMBRACA, OlympiA)', short: 'Mama BRCA+' },
      ]},
    { id: 'qt', name: 'Quimioterapia citotóxica', short: 'QT',
      match: (s) => {
        const r = (s.radiofarmaco || '').toLowerCase();
        return /(docetaxel|cabazitaxel)/i.test(r) && !/(psma|lu-?psma|ra-?223|177lu)/.test(r);
      }},
  ];

  TheraTrials.modalitiesUpcoming = [
    { id: 'cart', name: 'CAR-T' },
    { id: 'anti_angio', name: 'Anti-angiogênico' },
    { id: 'biteother', name: 'BiTE/anticorpos bispecíficos (não DLL3)' },
  ];

  // Linhas de tratamento
  TheraTrials.treatmentLines = [
    { id: '1L', name: '1ª linha',
      match: (s) => {
        const t = ((s.indicacao || '') + ' ' + (s.estudo || '') + ' ' + (s.fase || '')).toLowerCase();
        return /\b(1ª linha|1l|first-line|pré-qt|mhspc|recém-diagnost|de novo)\b/i.test(t);
      }},
    { id: '2L', name: '2ª linha',
      match: (s) => {
        const t = ((s.indicacao || '') + ' ' + (s.estudo || '')).toLowerCase();
        return /(pós-1|pos-1|pós-arpi|pós-doce|pós-docetaxel|2ª linha|2l|second-line|after.*progression)/i.test(t);
      }},
    { id: '3L', name: '3ª linha+',
      match: (s) => {
        const t = ((s.indicacao || '') + ' ' + (s.estudo || '')).toLowerCase();
        return /(pós-≥2|pós-2|pós-doce.*pós-arpi|3ª linha|3l|multi.*linha|fortemente pré-trat|heavily pretreat)/i.test(t);
      }},
    { id: 'adjuvante', name: 'Adjuvante',
      match: (s) => /(adjuvante|adjuvant)/i.test((s.indicacao || '') + ' ' + (s.estudo || '')) || (s.category_id === 'nsclc_periop') },
    { id: 'neoadjuvante', name: 'Neoadjuvante',
      match: (s) => /(neoadjuvante|neoadjuvant|pré-rpt|pre-rpt|pré-prostatec|pre-prostatec|neoadj|perioperat)/i.test((s.indicacao || '') + ' ' + (s.estudo || '') + ' ' + (s.desenho || '')) },
    { id: 'localizado', name: 'Localizado',
      match: (s) => /(localizado|hrlpc|localized)/i.test((s.indicacao || '') + ' ' + (s.estudo || '')) },
  ];


  // Mapeamentos por modalidade terapêutica (para a página Modalidades)
  TheraTrials.modalityMap = {
    teranostico: {
      name: 'Teranóstico',
      tagline: 'Imagem molecular + radiofármaco terapêutico no mesmo alvo',
      icon: 'atom',
      color: '#FF8400',
      categorias: ['lupsma_prostata', 'ra223_prostata', 'lu_dotatate_net', 'lupsma_ccrcc', 'y90_tare', 'novos_psma', 'mibg_pediatria_pheo']
    },
    terapia_alvo: {
      name: 'Terapias-alvo molecular',
      tagline: 'Inibidores específicos guiados por biomarcador (HRR, BRCA, ARPi)',
      icon: 'target',
      color: '#0EA5B7',
      keywords: ['olaparib', 'rucaparib', 'niraparib', 'talazoparib', 'abiraterona', 'enzalutamida', 'apalutamida', 'darolutamida']
    },
    quimio: {
      name: 'Quimioterapia citotóxica',
      tagline: 'Esquemas com taxanos em mHSPC e mCRPC',
      icon: 'flask-conical',
      color: '#FBBF24',
      keywords: ['docetaxel', 'cabazitaxel']
    },
    imunoterapia: {
      name: 'Imunoterapia',
      tagline: 'Vacinas autólogas (escopo atual em próstata)',
      icon: 'shield-plus',
      color: '#34D399',
      keywords: ['sipuleucel-t', 'vacina']
    }
  };

  // Mapa de tumores → categorias e palavras-chave
  TheraTrials.tumorMap = {
    prostata: {
      name: 'Câncer de próstata',
      tagline: 'mHSPC, mCRPC, nmCRPC, oligometastático',
      icon: 'circle-dot',
      color: '#FF8400',
      categorias: ['lupsma_prostata', 'ra223_prostata', 'novos_psma', 'prostata_contexto']
    },
    net: {
      name: 'Tumores neuroendócrinos',
      tagline: 'GEP-NET, midgut, pancreático, pulmonar',
      icon: 'activity',
      color: '#0EA5B7',
      categorias: ['lu_dotatate_net'],
      filter: function(s) { return !((s.indicacao||'').toLowerCase().includes('pheo') || (s.indicacao||'').toLowerCase().includes('paragangli') || (s.indicacao||'').toLowerCase().includes('neuroblastoma')); }
    },
    pheo_pgl: {
      name: 'Feocromocitoma e paraganglioma',
      tagline: 'PPGL maligno · 131I-MIBG e 177Lu-DOTATATE',
      icon: 'heart-pulse',
      color: '#F472B6',
      categorias: ['mibg_pediatria_pheo', 'lu_dotatate_net'],
      filter: function(s) { const i = (s.indicacao||'').toLowerCase(); return i.includes('pheo') || i.includes('paragangli') || i.includes('ppgl'); }
    },
    neuroblastoma: {
      name: 'Neuroblastoma (pediatria)',
      tagline: 'Alto risco refratário/recidivado · 131I-MIBG e PRRT pediátrica',
      icon: 'baby',
      color: '#C084FC',
      categorias: ['mibg_pediatria_pheo', 'lu_dotatate_net'],
      filter: function(s) { const i = (s.indicacao||'').toLowerCase(); return i.includes('neuroblastoma') || (i.includes('pediátric') && !i.includes('pheo')); }
    },
    hcc: {
      name: 'Carcinoma hepatocelular',
      tagline: 'BCLC A/B/C · radioembolização 90Y',
      icon: 'droplet',
      color: '#FBBF24',
      categorias: ['y90_tare'],
      filter: function(s) { const i = (s.indicacao||'').toLowerCase(); return i.includes('hcc') || i.includes('hepatocelular'); }
    },
    mcrc: {
      name: 'Câncer colorretal metastático',
      tagline: 'Mets hepáticas dominantes · TARE com Y-90',
      icon: 'activity-square',
      color: '#F87171',
      categorias: ['y90_tare'],
      filter: function(s) { const i = (s.indicacao||'').toLowerCase(); return i.includes('mcrc') || i.includes('colorretal'); }
    },
    ccrcc: {
      name: 'Carcinoma renal de células claras',
      tagline: '2ª/3ª linha pós-TKI/ICI · 177Lu-PSMA',
      icon: 'kidney',
      color: '#38BDF8',
      categorias: ['lupsma_ccrcc']
    },
    pulmao: {
      name: 'Câncer de pulmão',
      tagline: 'NSCLC drivers (EGFR/ALK/KRAS/etc), IO 1L, perioperatório, SCLC, radiofármacos exp',
      icon: 'wind',
      color: '#22d3ee',
      categorias: ['nsclc_imuno', 'nsclc_alvo', 'nsclc_periop', 'sclc', 'lung_radio_dev']
    },
    mama: {
      name: 'Câncer de mama',
      tagline: 'HER2+ (T-DXd, T-DM1), HR+/HER2- (CDK4/6, PI3K, AKT, SERD), TNBC (pembro, sacituzumab), BRCA-mut (PARPi), imagem molecular',
      icon: 'flower-2',
      color: '#ec4899',
      categorias: ['breast_her2', 'breast_hrpos', 'breast_tnbc_brca', 'breast_radio_dev']
    }
  };

})();
