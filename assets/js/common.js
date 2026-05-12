/* ============================================================
   TheraTrials Oncology — JavaScript comum
   Helpers, navegação e utilitários compartilhados
   ============================================================ */

(function() {
  'use strict';

  // Marcar link ativo no menu
  document.addEventListener('DOMContentLoaded', function() {
    // Toggle do menu mobile agora eh feito via onclick inline na tag <button>
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

  // Categorias cuja intervencao principal eh um radiofarmaco/teranostico.
  // Define os labels do modal: estudos radio mostram "Intervencao e radiofarmacia" /
  // "Criterios moleculares e imagem"; estudos nao-radio mostram versoes neutras.
  TheraTrials.RADIO_CATEGORIES = new Set([
    'lupsma_prostata', 'ra223_prostata', 'net_gep', 'lupsma_ccrcc',
    'hepatobiliar', 'novos_psma', 'ppgl', 'neuroblastoma',
    'lung_radio_dev', 'breast_radio_dev',
    'teranostico_emergente'
  ]);

  // Modalidades teranósticas/radiofármacos — usadas para detectar estudo "radio" via tags
  TheraTrials.RADIO_MODALITIES = new Set([
    'teranostico_psma', 'teranostico_prrt', 'teranostico_alfa',
    'tare_y90', 'mibg', 'iodo_131', 'teranostico_emergente'
  ]);

  TheraTrials.isRadioStudy = function(study) {
    if (!study) return false;
    // Prioridade: array modalities[] (taxonomia canônica)
    if (Array.isArray(study.modalities) && study.modalities.length) {
      return study.modalities.some(m => TheraTrials.RADIO_MODALITIES.has(m));
    }
    // Fallback: category_id legado
    return TheraTrials.RADIO_CATEGORIES.has(study.category_id);
  };

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

  // Helper: estudo cobre tumor X? Prioriza array tumors[] (taxonomia canônica),
  // cai no category_id legado se ausente.
  function hasTumor(s, ...ids) {
    if (Array.isArray(s.tumors) && s.tumors.length) {
      return s.tumors.some(t => ids.includes(t));
    }
    return false;
  }
  TheraTrials.hasTumor = hasTumor;

  // Tipos tumorais (multi-select) — prioriza s.tumors[]; fallback para category_id legado
  TheraTrials.tumorTypes = [
    { id: 'prostata', name: 'Próstata', short: 'Próstata',
      match: (s) => hasTumor(s, 'prostata') || ['lupsma_prostata', 'ra223_prostata', 'novos_psma', 'prostata_contexto'].includes(s.category_id) },
    { id: 'pulmao', name: 'Pulmão (NSCLC + SCLC)', short: 'Pulmão',
      match: (s) => hasTumor(s, 'nsclc_egfr', 'nsclc_alk', 'nsclc_kras', 'nsclc_outros_drivers', 'nsclc_imuno', 'nsclc_periop', 'sclc') || ['nsclc_imuno', 'nsclc_alvo', 'nsclc_periop', 'sclc', 'lung_radio_dev'].includes(s.category_id) },
    { id: 'mama', name: 'Mama (HER2+, HR+, TNBC)', short: 'Mama',
      match: (s) => hasTumor(s, 'mama_her2pos', 'mama_hrpos', 'mama_tnbc') || ['breast_her2', 'breast_hrpos', 'breast_tnbc_brca', 'breast_radio_dev'].includes(s.category_id) },
    { id: 'net', name: 'Tumores neuroendócrinos (GEP + brônquicos)', short: 'Neuroendócrinos',
      match: (s) => hasTumor(s, 'net_gep') || s.category_id === 'net_gep' },
    { id: 'pheo_pgl', name: 'Feocromocitoma e Paraganglioma (PPGL)', short: 'Feocromocitoma',
      match: (s) => hasTumor(s, 'ppgl') || s.category_id === 'ppgl' },
    { id: 'neuroblastoma', name: 'Neuroblastoma', short: 'Neuroblastoma',
      match: (s) => hasTumor(s, 'neuroblastoma') || s.category_id === 'neuroblastoma' },
    { id: 'hcc', name: 'Hepatocelular (CHC)', short: 'CHC',
      match: (s) => hasTumor(s, 'hcc') || /(hcc|hepatocelular)/i.test(s.indicacao || '') },
    { id: 'colangiocarcinoma', name: 'Colangiocarcinoma (intra/extra-hep + vesícula)', short: 'Colangio',
      match: (s) => hasTumor(s, 'colangiocarcinoma', 'vesicula') },
    { id: 'mcrc', name: 'Colorretal', short: 'Colorretal',
      match: (s) => hasTumor(s, 'colorretal') || /(mcrc|colorretal)/i.test(s.indicacao || '') },
    { id: 'ccrcc', name: 'Renal (ccRCC e não-clear)', short: 'Rim',
      match: (s) => hasTumor(s, 'ccrcc', 'rcc_naoclear') || ['lupsma_ccrcc', 'rcc_avancado', 'rcc_adjuvante_naocc'].includes(s.category_id) },
    { id: 'urotelial', name: 'Urotelial (bexiga · trato superior · NMIBC)', short: 'Bexiga',
      match: (s) => hasTumor(s, 'urotelial_avancado', 'urotelial_periop') || ['urotelial_avancado', 'urotelial_periop_nmibc'].includes(s.category_id) },
    { id: 'tireoide', name: 'Tireoide (CDT / MTC / ATC)', short: 'Tireoide',
      match: (s) => hasTumor(s, 'tireoide_cdt', 'tireoide_mtc', 'tireoide_atc') || s.category_id === 'tireoide_avancado' },
    { id: 'esofago_egj', name: 'Esôfago e EGJ (ESCC + EAC + gástrico)', short: 'Esôfago e estômago',
      match: (s) => hasTumor(s, 'esofago_escc', 'esofago_eac', 'gastrico') || s.category_id === 'esofago_egj' },
    { id: 'pancreas', name: 'Pâncreas (adenocarcinoma)', short: 'Pâncreas',
      match: (s) => hasTumor(s, 'pancreas_ductal') || s.category_id === 'pancreas' },
    { id: 'teranostico_emergente', name: 'Teranóstico emergente (CAIX, FAPI, α-PRRT)', short: 'Teranóstico emergente',
      match: (s) => s.category_id === 'teranostico_emergente' },
    { id: 'hnscc', name: 'Cabeça e Pescoço (HNSCC)', short: 'Cabeça e pescoço',
      match: (s) => hasTumor(s, 'hnscc') || s.category_id === 'hnscc' },
    { id: 'melanoma', name: 'Melanoma (cutâneo + uveal)', short: 'Melanoma',
      match: (s) => hasTumor(s, 'melanoma_cutaneo', 'melanoma_uveal') || ['melanoma_avancado', 'melanoma_adjuvante'].includes(s.category_id) },
    { id: 'mieloma', name: 'Mieloma múltiplo (NDMM + RRMM)', short: 'Mieloma',
      match: (s) => hasTumor(s, 'mieloma') || s.category_id === 'mieloma' },
    { id: 'linfoma', name: 'Linfoma B agressivo (DLBCL · Hodgkin · PTCL)', short: 'Linfoma',
      match: (s) => hasTumor(s, 'dlbcl', 'hodgkin', 'follicular') || s.category_id === 'linfoma_dlbcl' },
    { id: 'lma', name: 'Leucemia mieloide aguda (LMA)', short: 'Leucemia',
      match: (s) => hasTumor(s, 'lma', 'lla') || s.category_id === 'lma' },
    { id: 'ovario', name: 'Ovário (epitelial avançado/recidivado)', short: 'Ovário',
      match: (s) => hasTumor(s, 'ovario') || s.category_id === 'ovario' },
    { id: 'endometrio', name: 'Endométrio (avançado/recidivado)', short: 'Endométrio',
      match: (s) => hasTumor(s, 'endometrio') || s.category_id === 'endometrio' },
    { id: 'cervix', name: 'Cérvix (LACC + recurrente/metastático)', short: 'Colo do útero',
      match: (s) => hasTumor(s, 'cervix') || s.category_id === 'cervix' },
  ];

  TheraTrials.tumorTypesUpcoming = [
    { id: 'tgi', name: 'Trato gastrointestinal (cólon, reto, hepatobiliar)' },
    { id: 'ginecologico', name: 'Ginecológico (ovário, endométrio, cérvix)' },
    { id: 'hematologico', name: 'Hematológico (mieloma, linfoma, leucemias)' },
  ];

  // Modalidades terapêuticas (multi-select com subníveis)
  TheraTrials.modalities = [
    { id: 'teranostico', name: 'Teranóstico', short: 'Teranóstico',
      match: (s) => ['lupsma_prostata', 'ra223_prostata', 'net_gep', 'lupsma_ccrcc', 'hepatobiliar', 'novos_psma', 'ppgl', 'neuroblastoma', 'lung_radio_dev', 'breast_radio_dev', 'teranostico_emergente'].includes(s.category_id),
      subs: [
        { id: 'lupsma_prostata', name: '177Lu-PSMA · Próstata', short: 'Lu-PSMA' },
        { id: 'ra223_prostata', name: '223Ra · Próstata', short: 'Ra-223' },
        { id: 'net_gep', name: 'NETs · GEP e brônquicos (PRRT)', short: 'NETs' },
        { id: 'lupsma_ccrcc', name: '177Lu-PSMA · ccRCC', short: 'Lu-PSMA-RCC' },
        { id: 'hepatobiliar', name: 'Hepatobiliar (CHC, colangio · inclui TARE Y-90)', short: 'Hepatobiliar' },
        { id: 'novos_psma', name: 'Novos PSMA (α / 161Tb / RIT)', short: 'α-PSMA' },
        { id: 'ppgl', name: 'PPGL · 131I-MIBG e 177Lu-DOTATATE', short: 'PPGL' },
        { id: 'neuroblastoma', name: 'Neuroblastoma · pediátrico', short: 'NB' },
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
        // Uro-oncologia: regimes IO ou IO+TKI/QT/ADC nas 4 categorias novas
        const uroCats = ['rcc_avancado', 'rcc_adjuvante_naocc', 'urotelial_avancado', 'urotelial_periop_nmibc'];
        if (uroCats.includes(s.category_id) && /(pembro|nivo|atezo|durva|avelumab|tremelimumab|ipilimumab|n-803|nogapendekin|anktiva)/i.test(r)) return true;
        return false;
      },
      subs: [
        { id: 'nsclc_imuno', name: 'NSCLC · ICI 1L', short: 'NSCLC IO' },
        { id: 'nsclc_periop', name: 'NSCLC · perioperatório IO', short: 'NSCLC periop IO' },
        { id: 'sclc', name: 'SCLC · imuno + QT, BiTE', short: 'SCLC' },
        { id: 'breast_tnbc_brca', name: 'Mama · TNBC neoadj/1L (KEYNOTE-522/-355)', short: 'Mama TNBC IO' },
        { id: 'prostata_contexto', name: 'Próstata · vacinas (Sipuleucel-T)', short: 'Próstata' },
        { id: 'rcc_avancado', name: 'ccRCC · IO+TKI / IO+IO 1L (CM-214, KN-426, CM-9ER, CLEAR)', short: 'ccRCC IO' },
        { id: 'rcc_adjuvante_naocc', name: 'RCC · IO adjuvante (KN-564, CM-914, IMmotion010)', short: 'RCC adj IO' },
        { id: 'urotelial_avancado', name: 'Urotelial · IO+ADC/QT 1L e 2L+ (EV-302, CM-901, KN-045)', short: 'Uro IO' },
        { id: 'urotelial_periop_nmibc', name: 'Urotelial · IO periop e NMIBC (NIAGARA, CM-274, KN-057)', short: 'Uro periop IO' },
      ]},
    { id: 'terapia_alvo', name: 'Terapia-alvo (TKIs · ARPi · CDK4/6 · PI3K · VEGFR · FGFR · HIF-2α)', short: 'Alvo',
      match: (s) => {
        const r = (s.radiofarmaco || '').toLowerCase();
        const isProstateARPi = s.category_id === 'prostata_contexto' && /(abiraterona|enzalutamida|apalutamida|darolutamida)/i.test(r) && !/(olaparib|rucaparib|niraparib|talazoparib)/i.test(r);
        const isLungAlvo = s.category_id === 'nsclc_alvo';
        const isLungAdjAlvo = s.category_id === 'nsclc_periop' && /osi|alect/i.test(r);
        const isBreastAlvo = s.category_id === 'breast_hrpos' || (s.category_id === 'breast_her2' && /(tucatinib|neratinib|lapatinib)/i.test(r));
        // Uro-oncologia: TKIs VEGFR (sunitinibe/cabo/axi/pazo/lenva/tivo), FGFRi (erdafitinibe), HIF-2α (belzutifan), MET (savolitinibe/crizo)
        const uroCats = ['rcc_avancado', 'rcc_adjuvante_naocc', 'urotelial_avancado'];
        const isUroAlvo = uroCats.includes(s.category_id) && /(sunitinib|cabozantinib|axitinib|pazopanib|lenvatinib|tivozanib|sorafenib|everolimus|belzutifan|erdafitinib|savolitinib|crizotinib)/i.test(r);
        return isProstateARPi || isLungAlvo || isLungAdjAlvo || isBreastAlvo || isUroAlvo;
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
        { id: 'vegfr_tki_rcc', name: 'RCC · VEGFR-TKI (sunitinibe, cabo, axi, lenva, pazo, tivo)', short: 'VEGFR-TKI' },
        { id: 'hif2a', name: 'RCC · HIF-2α (belzutifan)', short: 'HIF-2α' },
        { id: 'fgfr_uro', name: 'Urotelial · FGFR (erdafitinibe)', short: 'FGFR' },
        { id: 'met_papRCC', name: 'papRCC · MET (savolitinibe, crizotinibe)', short: 'MET' },
      ]},
    { id: 'adc', name: 'ADC · conjugados anticorpo-droga', short: 'ADC',
      match: (s) => /(trastuzumab emtansine|t-dm1|trastuzumab deruxtecan|t-dxd|sacituzumab|datopotamab|enfortumab vedotin|enfortumabe vedotina)/i.test(s.radiofarmaco || ''),
      subs: [
        { id: 'tdm1', name: 'T-DM1 (HER2+)', short: 'T-DM1' },
        { id: 'tdxd', name: 'T-DXd (HER2+ e HER2-low · pan-tumor IHC 3+)', short: 'T-DXd' },
        { id: 'sacituzumab', name: 'Sacituzumab govitecan (TNBC, Trop-2)', short: 'Sacituzumab' },
        { id: 'ev_uro', name: 'Enfortumab vedotin (Nectin-4 · UC)', short: 'EV' },
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
      categorias: ['lupsma_prostata', 'ra223_prostata', 'net_gep', 'lupsma_ccrcc', 'hepatobiliar', 'novos_psma', 'ppgl', 'neuroblastoma']
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
      tagline: 'GEP-NET, midgut, pancreático, brônquico/pulmonar',
      icon: 'activity',
      color: '#10B981',
      categorias: ['net_gep']
    },
    pheo_pgl: {
      name: 'Feocromocitoma e paraganglioma',
      tagline: 'PPGL maligno · 131I-MIBG e 177Lu-DOTATATE',
      icon: 'heart-pulse',
      color: '#EC4899',
      categorias: ['ppgl']
    },
    neuroblastoma: {
      name: 'Neuroblastoma (pediatria)',
      tagline: 'Alto risco refratário/recidivado · 131I-MIBG e PRRT pediátrica',
      icon: 'baby',
      color: '#8B5CF6',
      categorias: ['neuroblastoma']
    },
    hcc: {
      name: 'Carcinoma hepatocelular (CHC)',
      tagline: 'BCLC A/B/C · IO+anti-VEGF, TKIs, IO duplo, radioembolização ⁹⁰Y',
      icon: 'droplet',
      color: '#FBBF24',
      categorias: ['hepatobiliar'],
      filter: function(s) { return (Array.isArray(s.tumors) && s.tumors.includes('hcc')) || /(hcc|hepatocelular)/i.test(s.indicacao||''); }
    },
    colangiocarcinoma: {
      name: 'Colangiocarcinoma e vesícula biliar',
      tagline: 'Intra-hep, extra-hep e vesícula · gem/cis ± durva, alvos moleculares (FGFR2, IDH1, HER2)',
      icon: 'droplet',
      color: '#F59E0B',
      categorias: ['hepatobiliar'],
      filter: function(s) { return Array.isArray(s.tumors) && (s.tumors.includes('colangiocarcinoma') || s.tumors.includes('vesicula')); }
    },
    mcrc: {
      name: 'Câncer colorretal',
      tagline: 'Sistêmico e direcionado a mets hepáticas (TARE ⁹⁰Y)',
      icon: 'activity-square',
      color: '#F87171',
      categorias: ['hepatobiliar'],
      filter: function(s) { return (Array.isArray(s.tumors) && s.tumors.includes('colorretal')) || /(mcrc|colorretal)/i.test(s.indicacao||''); }
    },
    ccrcc: {
      name: 'Carcinoma renal (ccRCC e não-clear)',
      tagline: '1L IO+TKI/IO+IO · adjuvante · 2L+ HIF-2α · não-clear · teranóstico Lu-PSMA exploratório',
      icon: 'kidney',
      color: '#38BDF8',
      categorias: ['lupsma_ccrcc', 'rcc_avancado', 'rcc_adjuvante_naocc']
    },
    urotelial: {
      name: 'Carcinoma urotelial',
      tagline: 'mUC 1L EV+pembro/IO-quimio · adjuvante · perioperatório (NIAGARA, VOLGA) · NMIBC BCG-unresponsive',
      icon: 'flask-conical',
      color: '#EAB308',
      categorias: ['urotelial_avancado', 'urotelial_periop_nmibc']
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
