"""
Batch D — Dosimetria + Imagem pos-terapia + Estruturacao de servico
Appends 7 deeply expanded guideline objects and closes the JS array.
"""
import os

target = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\assets\js\guidelines-data.js"

content = r'''
  // ═══════════════════════════════════════════════
  //  8. Dosimetria para RLT
  // ═══════════════════════════════════════════════
  {
    id: "dosim-eanm-lu177-2022",
    title: "EANM dosimetry committee recommendations for dosimetry of 177Lu-labelled somatostatin receptor- and PSMA-targeting ligands",
    year: "2022",
    society: "EANM — Dosimetry Committee",
    type: "Recommendation",
    badges: ["dosimetry","essential"],
    category: "dosimetria",
    categoryName: "Dosimetria para RLT",
    categoryColor: "#60A5FA",
    scope: "Recomendacoes do Comite de Dosimetria da EANM para dosimetria clinica especifica de 177Lu-DOTATATE e 177Lu-PSMA-617, os dois radioligantes terapeuticos mais utilizados na pratica clinica global. O documento aborda a dosimetria personalizada como ferramenta essencial para otimizacao terapeutica, alinhando-se ao Artigo 56 da Diretiva Europeia 2013/59/Euratom, que exige planejamento individual de doses em terapia com radionuclideos. Com os avancos na quantificacao por SPECT/CT, a dosimetria deixou de ser meramente academica e tornou-se clinicamente viavel para integracao na rotina de centros de referencia. O guideline estabelece protocolos praticos para calcular doses absorvidas em orgaos de risco e tumores, transformando a RLT de uma abordagem empirica baseada em atividade fixa para um modelo personalizado orientado por dose. A imagem pos-terapia e a analise farmacocinetica individualizada formam a base desse paradigma dosimetrico. A padronizacao de metodos entre centros e fundamental para viabilizar estudos multicentricos de correlacao dose-resposta.",
    indications: [
      "Dosimetria de orgaos de risco (rins, medula ossea) em PRRT com 177Lu-DOTATATE para monitoramento de toxicidade cumulativa",
      "Dosimetria de glandulas salivares e rins em PSMA-RLT com 177Lu-PSMA-617 para prevencao de xerostomia e nefrotoxicidade",
      "Dosimetria tumoral para correlacao dose-resposta e predicao de desfecho terapeutico",
      "Personalizacao de atividade administrada em ciclos subsequentes com base na farmacocinetica individual",
      "Avaliacao dosimetrica simplificada (single-timepoint) quando protocolo completo nao e viavel",
      "Dosimetria completa (multi-timepoint) em centros de referencia para pesquisa e validacao de metodos",
      "Avaliacao de pacientes com fatores de risco para nefrotoxicidade (diabetes, hipertensao, rim unico, QT previa com nefrotoxicos)",
      "Dosimetria pre-terapeutica com atividade tracer para planejamento de atividade no primeiro ciclo",
      "Monitoramento dosimetrico em protocolos de retratamento (re-PRRT ou re-PSMA) para definir limite cumulativo seguro",
      "Documentacao dosimetrica obrigatoria conforme regulacao europeia para auditoria e compliance"
    ],
    keyPoints: [
      "Protocolo de aquisicao SPECT/CT: imagens em 24h e 96-120h pos-administracao como minimo (2 timepoints) — 3-4 timepoints (4h, 24h, 48-72h, 96-168h) para dosimetria completa",
      "Calibracao quantitativa da gama-camara para 177Lu: fotopicos em 113 keV (6,2%) e 208 keV (10,4%), com janela de energia de ±10-20%",
      "Colimadores recomendados: media-energia para uso geral (MEGP); alta-energia pode reduzir penetracao septal mas com perda de sensibilidade",
      "Reconstrucao iterativa OSEM (4-10 iteracoes, 8-16 subsets) com correcao de atenuacao (CT), scatter (DEW ou TEW) e resolucao (recovery coefficient)",
      "Calibracao com phantom cilindrico preenchido com atividade conhecida de 177Lu — fator de calibracao camera-especifico (cps/MBq) deve ser validado periodicamente",
      "Limites de dose renal: 23 Gy cumulativo (derivado da radioterapia externa com BED corrigido); ajuste para 18-20 Gy em pacientes com fatores de risco (diabetes, hipertensao, rim unico)",
      "Limites de dose medular: 2 Gy a corpo inteiro como proxy conservador para seguranca hematologica",
      "Dosimetria tumoral: doses absorvidas tumorais >100 Gy em PRRT correlacionam com melhor controle local; dados emergentes para PSMA-RLT sugerem >40-60 Gy por ciclo como preditivo de resposta",
      "Metodo single-timepoint (STD): imagem unica em 24h com curva de clearance populacional pre-definida — incerteza de 10-20% vs metodo completo, mas viavel em rotina clinica",
      "Dosimetria baseada em voxel: geracao de mapa 3D de dose intratumoral para avaliacao de heterogeneidade — DVH (dose-volume histogram) como metrica complementar",
      "Softwares dosimetricos validados clinicamente: OLINDA/EXM 2.0 (organ-level), PLANET Dose (Dosisoft), Hermes Hybrid Dosimetry, MIM SurePlan MRT, QDOSE (ABX-CRO)",
      "Tempo de residencia calculado por ajuste de curva mono ou bi-exponencial aos dados de atividade vs tempo — integracao analitica ou trapezoidal",
      "Relatorio dosimetrico por ciclo com dose acumulada obrigatorio — modelo padronizado inclui atividade administrada, timepoints, metodo, dose por orgao e incerteza estimada",
      "Integracao de IA para segmentacao automatica de orgaos e tumores em imagens SPECT/CT — reduz variabilidade inter-observador e tempo de processamento",
      "Correlacao dose-resposta varia entre radioligantes: mais robusta para 177Lu-DOTATATE (dados NETTER-1/Basel) do que para 177Lu-PSMA-617 (dados emergentes do TheraP e VISION substudy)",
      "Variabilidade inter-ciclo de farmacocinetica (ate 30-40%) justifica dosimetria repetida a cada ciclo para ajuste fino de atividade",
      "Conformidade regulatoria: a Diretiva 2013/59/Euratom (Art. 56) exige dosimetria individual para exposicoes terapeuticas — implementacao progressiva recomendada"
    ],
    radiopharmaceuticals: "177Lu-DOTATATE (Lutathera) e 177Lu-PSMA-617 (Pluvicto) sao os radioligantes-alvo primarios deste documento. O 177Lu possui meia-vida fisica de 6,647 dias, emitindo particulas beta com energia maxima de 498 keV (Ebeta media 133 keV) e fotons gama de 113 keV e 208 keV que permitem imageamento SPECT pos-terapeutico. A janela de imagem ideal para dosimetria situa-se entre 4h e 168h pos-administracao, com timepoints em 24h e 96h sendo os mais informativos para ajuste farmacocinetico. As propriedades fisicas do 177Lu — alcance beta maximo de ~2 mm em tecido e emissao gama imageavel — tornam-o ideal para dosimetria quantitativa in vivo.",
    practicalAspects: "O protocolo dosimetrico completo inicia-se com calibracao da gama-camara usando phantom cilindrico com atividade conhecida de 177Lu — o fator de calibracao (cps/MBq) deve ser determinado para cada camara e revisado semestralmente. Aquisicao SPECT/CT: 60 projecoes de 30 segundos cada, matriz 128x128, orbita body-contour, fotopico de 208 keV com janela de ±10%. CT de baixa dose (120 kV, 30-50 mAs) para correcao de atenuacao e localizacao anatomica. As imagens SPECT sao reconstruidas com algoritmo iterativo OSEM (tipicamente 4-8 iteracoes, 8-16 subsets) com correcao de atenuacao baseada em CT, correcao de scatter por janela de energia dupla ou tripla (DEW/TEW), e correcao de resolucao quando disponivel. A segmentacao de orgaos (rins, figado, baco) e tumores pode ser realizada manualmente, semi-automaticamente ou com ferramentas de IA. Os volumes de interesse (VOIs) devem ser consistentes entre timepoints. A curva atividade-tempo e ajustada por funcao mono ou bi-exponencial para cada ROI, com integracao analitica fornecendo o tempo de residencia. A dose absorvida e calculada usando fatores S (OLINDA) ou kernel de dose pontual (voxel-level). O relatorio dosimetrico final deve incluir: atividade administrada, metodo de dosimetria, timepoints de imagem, dose por orgao de risco (Gy), dose tumoral (Gy quando disponivel), dose cumulativa e estimativa de incerteza.",
    limitations: "A dosimetria clinica ainda nao e rotina na maioria dos centros que realizam RLT, principalmente por barreiras de infraestrutura (gama-camara calibrada, software, tempo de aquisicao), expertise (fisico medico treinado em dosimetria interna) e custo operacional. A dosimetria simplificada (single-timepoint) oferece uma alternativa pratica, mas com incerteza de 10-20% comparada ao protocolo multi-timepoint completo. A correlacao dose-resposta tumoral e mais bem estabelecida para PRRT com 177Lu-DOTATATE do que para PSMA-RLT, onde dados prospectivos ainda estao em construcao. A variabilidade inter-ciclo na farmacocinetica individual (ate 30-40%) e uma limitacao intrinseca que requer dosimetria repetida. A quantificacao absoluta em SPECT/CT, embora tenha avancado significativamente, ainda apresenta incertezas superiores as do PET/CT (15-25% vs 5-10%). A heterogeneidade regulatoria entre paises na exigencia de dosimetria dificulta a padronizacao internacional.",
    reference: "Sjoegreen Gleisner K, et al. EANM dosimetry committee recommendations for dosimetry of 177Lu-labelled somatostatin-receptor- and PSMA-targeting ligands. Eur J Nucl Med Mol Imaging. 2022;49(6):1778-1809."
  },
  {
    id: "dosim-eanm-targeted-2026",
    title: "EANM recommendations for dosimetry in targeted radionuclide therapy",
    year: "2026",
    society: "EANM",
    type: "Recommendation",
    badges: ["recent","dosimetry"],
    category: "dosimetria",
    categoryName: "Dosimetria para RLT",
    categoryColor: "#60A5FA",
    scope: "Documento abrangente e atualizado da EANM que expande o escopo dosimetrico para alem do 177Lu, contemplando radionuclideos emergentes como 225Ac, 212Pb e 161Tb, e propondo um framework escalonavel para implementacao clinica. O guideline posiciona a dosimetria como pilar da medicina de precisao nuclear, analogamente ao treatment planning da radioterapia externa (EBRT), e define niveis de complexidade dosimetrica adaptaveis a infraestrutura de cada centro. A regulacao europeia (Diretiva 2013/59/Euratom, Art. 56) e reafirmada como mandato para individualizacao de doses em exposicoes terapeuticas, impulsionando a transicao de esquemas de atividade fixa para abordagens orientadas por dose absorvida. O documento integra avancos recentes em imageamento quantitativo (SPECT e PET), modelagem farmacocinetica computacional, dosimetria baseada em voxel com DVH e aplicacoes de inteligencia artificial para automacao de pipeline dosimetrico. A imagem pos-terapia e reconhecida como elemento indissociavel da dosimetria, conectando diretamente avaliacao de biodistribuicao e calculo de dose absorvida.",
    indications: [
      "Framework dosimetrico universal aplicavel a qualquer RLT (177Lu, 90Y, 131I, 225Ac, 212Pb, 161Tb)",
      "Transicao institucional de dosimetria baseada em atividade fixa para dosimetria personalizada orientada por dose absorvida",
      "Implementacao de dosimetria clinica conforme Diretiva Europeia 2013/59/Euratom (Art. 56) e regulacoes nacionais equivalentes",
      "Dosimetria para alfa-emissores (225Ac-PSMA-617, 212Pb-DOTAMTATE) — desafios especificos de imageamento e quantificacao",
      "Dosimetria tumoral para individualizacao de atividade e predicao de resposta terapeutica",
      "Dosimetria de orgaos de risco com niveis escalonaveis de complexidade (corpo inteiro, organ-level, voxel-level)",
      "Integracao de dosimetria com IA para segmentacao automatica, predicao de dose e modelagem farmacocinetica",
      "Estudos dosimetricos multicentricos: padronizacao metodologica para comparabilidade de resultados",
      "Planejamento dosimetrico pre-terapeutico (treatment planning) usando atividade tracer ou ciclo inicial como referencia",
      "Documentacao dosimetrica para ensaios clinicos de novas terapias radiofarmaceuticas"
    ],
    keyPoints: [
      "Dosimetria personalizada: conceito de treatment planning analogamente a EBRT — prescrever dose ao tumor e respeitar limites de dose a orgaos de risco",
      "Framework escalonavel de 3 niveis: Nivel 1 (corpo inteiro, taxa de dose com camara de ionizacao), Nivel 2 (SPECT single-timepoint com curva populacional), Nivel 3 (SPECT/CT multi-timepoint com ajuste farmacocinetico individual e dosimetria voxel-level)",
      "Dosimetria baseada em voxel: distribuicao de dose 3D com resolucao espacial de 4-5 mm, geracao de DVH (dose-volume histogram) para avaliacao de heterogeneidade intratumoral e intra-orgao",
      "Inteligencia artificial aplicada a dosimetria: segmentacao automatica de orgaos e tumores com redes neurais (U-Net, nnU-Net), predicao de farmacocinetica e dose baseada em caracteristicas da imagem",
      "Modelagem farmacocinetica compartimental: modelos de 1-3 compartimentos para predicao de dose em ciclos subsequentes a partir de dados de ciclos anteriores",
      "Dosimetria para 225Ac: meia-vida de 9,92 dias, emissao alfa com LET alto (~80 keV/microm), imageamento SPECT com fotons de 440 keV (filhas 221Fr/213Bi) — estatistica de contagem extremamente baixa requer protocolos dedicados de aquisicao e reconstrucao",
      "Dosimetria para 212Pb e 161Tb: novas modalidades com vantagens teoricas de imageamento — 161Tb emite eletrons Auger adicionais e fotons de baixa energia imageaveis",
      "Regulacao europeia: Art. 56 da Diretiva 2013/59 exige que exposicoes medicas individuais com fins terapeuticos sejam individualmente planejadas, com doses otimizadas — dosimetria e a ferramenta para cumprir esse mandato",
      "Roadmap de implementacao: inicio com Nivel 1 (investimento minimo), progredindo para Nivel 2 (software dosimetrico basico + calibracao SPECT) e Nivel 3 (equipe dedicada, software avancado, dosimetria voxel)",
      "Correlacao dose-resposta: compilacao de dados publicados — PRRT com 177Lu-DOTATATE: BED tumoral >40-50 Gy associada a melhor resposta; PSMA-RLT com 177Lu-PSMA-617: dados emergentes sugerem limiares semelhantes mas com maior variabilidade",
      "Templates de relatorio dosimetrico padronizados para uso clinico e em ensaios clinicos, facilitando comparacao multicentrica e meta-analises",
      "Controle de qualidade dosimetrico: phantom studies periodicos (NEMA, Jaszczak), cross-calibracao entre camaras, auditorias dosimetricas internas e externas",
      "Dosimetria como endpoint secundario em ensaios clinicos de fase II/III: recomendacao de incorporar protocolo dosimetrico padronizado em todos os estudos de novas RLTs",
      "Integracao com radiomics: extracao de features dosimetricas (dose heterogeneity, DVH metrics) como biomarcadores preditivos de resposta e toxicidade",
      "Desafios de dosimetria para emissores alfa: redistribuicao de filhas radioativas, microdosimetria vs macrodosimetria, modelos de RBE (relative biological effectiveness) para particulas alfa",
      "Treinamento e capacitacao: curriculo minimo sugerido para fisicos medicos em dosimetria interna — cursos teoricos, hands-on com software e phantoms, mentoria clinica"
    ],
    radiopharmaceuticals: "O documento abrange 177Lu (DOTATATE, PSMA-617) com meia-vida de 6,647 dias e emissao beta/gama imageavel; 90Y (microesferas hepaticas) com meia-vida de 64,1h e emissao beta pura (imagem por Bremsstrahlung SPECT ou PET 90Y); 131I (NaI para tireoide, MIBG para neuroblastoma/feocromocitoma) com meia-vida de 8,02 dias e gama de 364 keV; 225Ac (PSMA-617) com meia-vida de 9,92 dias e cascata de emissao alfa com fotons imageaveis em 440 keV; 212Pb (DOTAMTATE) como gerador in vivo de 212Bi alfa-emissor; e 161Tb com emissao beta, eletrons Auger e fotons de baixa energia, considerado potencial substituto do 177Lu com maior eficacia biologica por dano de curto alcance.",
    practicalAspects: "O framework propoe implementacao escalonavel: Nivel 1 requer apenas camara de ionizacao calibrada para medidas de taxa de dose a corpo inteiro em multiplos timepoints (0,5h, 2h, 24h, 48h pos-infusao), planilha de calculo para integracao e relatorio basico — investimento minimo e viavel em qualquer servico de medicina nuclear. Nivel 2 adiciona SPECT/CT quantitativo single-timepoint (24h) com software dosimetrico basico (OLINDA 2.0 ou equivalente), usando curvas de clearance populacional pre-definidas para calcular dose organ-level — requer calibracao da gama-camara com phantom e treinamento do fisico medico (40-80h). Nivel 3 e o padrao de referencia: SPECT/CT multi-timepoint (3-4 imagens entre 4h e 168h), software avancado de dosimetria voxel (PLANET Dose, MIM SurePlan MRT, Hermes Hybrid Dosimetry), segmentacao semi-automatica ou com IA, ajuste farmacocinetico individual com modelos compartimentais, geracao de DVH e mapa de dose 3D — requer equipe dedicada (fisico medico + tecnico), tempo de camara alocado para dosimetria e integracao no workflow clinico. Para cada nivel, templates de relatorio padronizado estao disponiveis com campos obrigatorios (atividade, radionuclideo, timepoints, dose por orgao, incerteza) e opcionais (dose tumoral, DVH, mapas de dose). O controle de qualidade inclui phantom studies trimestrais e cross-calibracao anual entre camaras.",
    limitations: "A dosimetria para alfa-emissores (225Ac, 212Pb) permanece em fase de validacao clinica — o imageamento SPECT com estatistica de contagem extremamente baixa resulta em incertezas dosimetricas de 30-50% ou mais, significativamente superiores as do 177Lu. A implementacao ampla de dosimetria Nivel 2-3 requer investimento significativo em treinamento (fisicos medicos especializados sao escassos), software licenciado (custos anuais de 15.000-50.000 EUR) e tempo de camara dedicado (15-30 min por SPECT). A correlacao dose-resposta para novos agentes (225Ac-PSMA, 212Pb-DOTAMTATE, 161Tb) ainda esta sendo estabelecida em coortes pequenas, limitando a utilidade clinica imediata da dosimetria personalizada para esses compostos. A heterogeneidade regulatoria entre paises europeus na exigencia e no nivel de dosimetria cria barreiras para padronizacao. A variabilidade inter-camara e inter-software nas quantificacoes SPECT dificulta comparacoes multicentricas sem harmonizacao rigorosa. Modelos de RBE para particulas alfa permanecem controversos, afetando a interpretacao de doses absorvidas convertidas em dose biologica efetiva.",
    reference: "EANM recommendations for dosimetry in targeted radionuclide therapy. Eur J Nucl Med Mol Imaging. 2026."
  },
  {
    id: "dosim-eanm-reporting",
    title: "EANM Dosimetry Committee guidance document: good practice of clinical dosimetry reporting",
    year: null,
    society: "EANM — Dosimetry Committee",
    type: "Guidance document",
    badges: ["dosimetry"],
    category: "dosimetria",
    categoryName: "Dosimetria para RLT",
    categoryColor: "#60A5FA",
    scope: "Orientacao do Comite de Dosimetria da EANM para padronizacao da estrutura, conteudo e formato do relatorio dosimetrico clinico em terapia com radionuclideos. O documento reconhece que a ausencia de um padrao de relato dosimetrico tem sido uma barreira critica para a comparacao de resultados entre centros, auditoria regulatoria e avaliacao de correlacao dose-resposta em estudos multicentricos. Com a Diretiva Europeia 2013/59/Euratom exigindo documentacao de doses individuais em terapia, a padronizacao do relatorio torna-se mandatoria. O guideline define campos obrigatorios e opcionais, metricas de dose a serem reportadas, estimativa de incertezas e formato de apresentacao. O objetivo e viabilizar comparabilidade entre centros, rastreabilidade regulatoria e construcao de bancos de dados dosimetricos para correlacao dose-desfecho em larga escala.",
    indications: [
      "Padronizacao de laudos dosimetricos em todos os centros que realizam RLT com dosimetria",
      "Documentacao para auditoria regulatoria conforme Diretiva 2013/59/Euratom e regulacoes nacionais",
      "Pesquisa clinica: uniformizacao de dados dosimetricos para estudos multicentricos e meta-analises",
      "Comparacao multicentric: benchmark de doses absorvidas entre instituicoes usando mesma metodologia de relato",
      "Controle de qualidade interno: verificacao de consistencia dosimetrica entre ciclos e entre pacientes",
      "Documentacao para comites de etica e agencias regulatorias em ensaios clinicos de novas RLTs",
      "Comunicacao interdisciplinar: relatorio padronizado facilita discussao entre medico nuclear, fisico medico e oncologista",
      "Construcao de bancos de dados institucionais e colaborativos para correlacao dose-resposta e dose-toxicidade"
    ],
    keyPoints: [
      "Estrutura minima obrigatoria do relatorio: identificacao do paciente, radionuclideo, radiofarmaco, atividade administrada (MBq), data e hora da administracao, numero do ciclo, timepoints de imagem (data/hora de cada aquisicao)",
      "Metricas de dose obrigatorias: dose absorvida (Gy) em orgaos criticos — rins (cortex e/ou total), medula ossea (ou corpo inteiro como proxy), glandulas salivares (para PSMA-RLT), figado (especialmente com metastases hepaticas)",
      "Dose tumoral: reportar quando disponivel, com descricao do metodo de segmentacao (manual, semi-automatica, IA), volume tumoral (mL) e localizacao anatomica",
      "Incertezas: estimar e reportar fontes de incerteza — calibracao da camara (tipicamente 5-10%), segmentacao (5-15%), ajuste de curva farmacocinetica (5-20%), modelo dosimetrico utilizado",
      "Metodo dosimetrico: especificar claramente — single-timepoint vs multi-timepoint, numero e timing dos timepoints, tipo de reconstrucao SPECT, correcoes aplicadas (atenuacao, scatter, resolucao)",
      "Reproducibilidade: protocolo de aquisicao descrito com detalhe suficiente para permitir replicacao — parametros de camara, colimador, janela de energia, algoritmo de reconstrucao",
      "Dose cumulativa: rastreamento entre ciclos com soma de doses por orgao — fundamental para decisao de continuidade terapeutica vs suspensao",
      "Tendencia de dose tumoral entre ciclos: aumento pode indicar maior captacao por reducao de volume (concentracao), diminuicao pode sugerir perda de alvo",
      "DVH (dose-volume histogram) quando disponivel: reportar D50, D90, Dmax, Dmin para tumores e orgaos criticos — informacao complementar a dose media",
      "Software utilizado: identificar nome, versao e parametros de calculo — essencial para reproducibilidade e comparacao entre centros",
      "Formato de apresentacao: tabela padronizada com dose por orgao/tumor, incerteza e dose cumulativa; graficos de curva atividade-tempo quando disponivel",
      "Recomendacao de armazenamento digital: dados dosimetricos em formato estruturado (DICOM-RDSR ou planilha padronizada) para alimentar bancos de dados",
      "Integracao com prontuario eletronico: relatorio dosimetrico como documento clinico vinculado ao tratamento do paciente",
      "Template de relatorio sugerido com campos obrigatorios e opcionais — disponivel como material suplementar do guideline",
      "Validacao do relatorio: revisao por fisico medico qualificado antes de incorporacao ao prontuario"
    ],
    radiopharmaceuticals: "Aplicavel a qualquer radiofarmaco terapeutico submetido a dosimetria quantitativa, incluindo 177Lu-DOTATATE, 177Lu-PSMA-617, 90Y-microesferas, 131I (NaI e MIBG), 225Ac-PSMA-617 e compostos em desenvolvimento. O formato de relatorio e generico e adaptavel, com campos especificos para radionuclideo (meia-vida, tipo de emissao) e radiofarmaco (alvo molecular, via de administracao).",
    practicalAspects: "O template de relatorio sugerido inclui secoes padronizadas: (1) Dados do paciente — nome, ID, diagnostico, tratamento previo; (2) Tratamento atual — radionuclideo, radiofarmaco, atividade administrada (MBq), data/hora, numero do ciclo; (3) Protocolo de imagem — equipamento (fabricante, modelo), colimador, janela de energia, numero de projecoes, tempo por projecao, reconstrucao, correcoes; (4) Dosimetria — metodo (single vs multi-timepoint), timepoints utilizados, software, volumes segmentados (mL), curva atividade-tempo, tempo de residencia; (5) Resultados — tabela com dose absorvida (Gy) por orgao e por tumor, incerteza estimada (%), dose cumulativa; (6) Conclusao e recomendacoes — adequacao para proximo ciclo, necessidade de ajuste de atividade, alertas de dose cumulativa. O exemplo pratico fornecido para 177Lu-DOTATATE demonstra relatorio com 4 timepoints, dosimetria renal bilateral e tumoral, incluindo DVH. Para centros implementando dosimetria pela primeira vez, o template funciona como guia estruturado para construcao do workflow de relato. A revisao obrigatoria por fisico medico qualificado antes da assinatura garante qualidade e consistencia.",
    limitations: "Documento de orientacao sem forca vinculante — adesao e voluntaria e depende de motivacao institucional e requisitos regulatorios locais. Muitos centros que realizam RLT ainda nao implementam dosimetria rotineira, tornando o relatorio dosimetrico inaplicavel. A estimativa de incertezas, embora recomendada, e frequentemente omitida na pratica por complexidade de calculo. A falta de ferramentas integradas em softwares dosimetricos comerciais para geracao automatica de relatorios no formato padronizado e uma barreira pratica. Centros com recursos limitados podem considerar o relatorio detalhado como oneroso em tempo. A interoperabilidade entre softwares dosimetricos e sistemas de prontuario eletronico (HIS/RIS) ainda e insuficiente na maioria das instalacoes.",
    reference: "EANM Dosimetry Committee guidance document: good practice of clinical dosimetry reporting. Eur J Nucl Med Mol Imaging."
  },
  {
    id: "dosim-eanm-bone-marrow",
    title: "EANM Dosimetry Committee guidelines for bone marrow and whole-body dosimetry",
    year: null,
    society: "EANM — Dosimetry Committee",
    type: "Guideline",
    badges: ["dosimetry"],
    category: "dosimetria",
    categoryName: "Dosimetria para RLT",
    categoryColor: "#60A5FA",
    scope: "Guideline do Comite de Dosimetria da EANM focado especificamente na dosimetria de medula ossea e corpo inteiro, parametros criticos para seguranca hematologica em terapia com radioligantes. A mielotoxicidade e a toxicidade dose-limitante mais comum em PRRT e PSMA-RLT, e a dosimetria medular permite estimar o risco cumulativo de citopenias clinicamente significativas. O documento detalha dois metodos complementares — dosimetria baseada em amostragem sanguinea (sangue como proxy de medula ossea vermelha) e dosimetria de corpo inteiro por camara de ionizacao ou imageamento — e discute suas vantagens, limitacoes e cenarios de aplicacao. A correlacao entre dose medular e nadir hematologico pos-terapia e revisada com dados publicados. O guideline e particularmente relevante para decisoes de retratamento (re-PRRT ou re-PSMA), quando a dose cumulativa a medula e o fator limitante para continuidade terapeutica. Avancos recentes em modelagem computacional e IA para predicao de toxicidade hematologica tambem sao abordados.",
    indications: [
      "Monitoramento de dose medular cumulativa em ciclos repetidos de RLT (177Lu-DOTATATE, 177Lu-PSMA-617, 131I-MIBG)",
      "Avaliacao de risco hematologico antes de retratamento (re-PRRT ou re-PSMA) — dose cumulativa como criterio de elegibilidade",
      "Decisao sobre suspensao de terapia ou reducao de atividade baseada em dose medular cumulativa atingindo 2 Gy",
      "Dosimetria medular em pacientes com fatores de risco aumentado: metastases osseas difusas, QT mielotoxica previa, infiltracao medular tumoral, idade avancada",
      "Protocolo de amostragem sanguinea para calculo de dose a sangue como proxy de dose medular em centros com infraestrutura dedicada",
      "Dosimetria de corpo inteiro simplificada com camara de ionizacao como alternativa em centros sem capacidade de coleta sanguinea seriada",
      "Pesquisa clinica: correlacao dose-toxicidade para novos radiofarmaceuticos em ensaios de fase I/II",
      "Documentacao dosimetrica de seguranca hematologica para auditorias regulatorias e comites de etica",
      "Predicao de nadir hematologico e recuperacao medular para planejamento de ciclos subsequentes"
    ],
    keyPoints: [
      "Metodos de dosimetria medular: (1) amostragem sanguinea seriada com contagem em poco gama — sangue como proxy de dose a medula ossea vermelha; (2) dosimetria de corpo inteiro com camara de ionizacao ou contagem externa",
      "Limite de dose a corpo inteiro: 2 Gy como limiar conservador para seguranca hematologica, derivado de dados historicos de terapia com 131I e PRRT com 90Y",
      "Coleta de sangue seriada: minimo de 4 amostras em timepoints padronizados (1h, 4h, 24h, 48-72h pos-infusao) — idealmente 5-6 amostras incluindo 96-168h",
      "Preparacao das amostras: tubos heparinizados (3-5 mL por amostra), pesagem precisa em balanca analitica (±0,01g), contagem em poco gama calibrado para 177Lu",
      "Dose a sangue calculada como soma de self-dose (atividade no sangue irradiando o proprio sangue) e cross-dose (contribuicao de orgaos com alta captacao irradiando o sangue circulante)",
      "Fatores S padronizados (OLINDA/EXM) para calculo de cross-dose — orgaos contribuintes: rins, figado, baco, tumores volumosos",
      "Fatores de risco para mielotoxicidade aumentada: metastases osseas difusas (dose direta a medula vermelha), QT previa com agentes mielotoxicos (cisplatina, temozolomida, capecitabina), infiltracao medular tumoral, idade >70 anos, funcao renal comprometida (clearance prolongado)",
      "Correlacao entre dose a corpo inteiro e nadir hematologico: estudos publicados mostram que doses >2 Gy associam-se a risco significativamente maior de toxicidade G3-G4",
      "Dosimetria de corpo inteiro com camara de ionizacao: medidas de taxa de dose a 1-2 metros em multiplos timepoints, com correcao para background e geometria — metodo simples e de baixo custo",
      "Metodo imagenologico: imagens planares anterior/posterior de corpo inteiro em multiplos timepoints — media geometrica para correcao de atenuacao — integracao para tempo de residencia de corpo inteiro",
      "Dose medular diferencial: metastases osseas podem receber dose direta significativa — dosimetria baseada em sangue subestima a dose local em medula adjacente a lesoes osseas",
      "Recuperacao medular inter-ciclo: monitoramento com hemograma seriado a cada 2-4 semanas — nadir tipicamente em 4-6 semanas pos-177Lu; recuperacao em 6-8 semanas",
      "IA e modelagem computacional: modelos preditivos de nadir hematologico baseados em dose a sangue, hemograma pre-terapia e fatores clinicos — em fase de validacao",
      "Integracao com dosimetria de orgaos: relatorio combinado incluindo dose renal, dose medular/corpo inteiro e dose tumoral para visao dosimetrica completa",
      "Protocolos de decisao: se dose cumulativa a corpo inteiro se aproxima de 2 Gy, considerar reducao de atividade (50-75% da dose padrao) ou dosimetria pre-terapeutica antes do proximo ciclo",
      "Padronizacao de coleta e contagem: protocolo detalhado para minimizar erros pre-analiticos (contaminacao, erro de pesagem, decaimento) e analiticos (calibracao do poco gama, janela de energia)"
    ],
    radiopharmaceuticals: "Aplicavel a todos os radiofarmacos terapeuticos com potencial de mielotoxicidade: 177Lu-DOTATATE (meia-vida 6,647 dias, beta 498 keV max, gama 113/208 keV), 177Lu-PSMA-617 (mesmas caracteristicas fisicas, diferente biodistribuicao), 131I-MIBG (meia-vida 8,02 dias, beta 606 keV max, gama 364 keV) e 90Y-DOTATOC (meia-vida 64,1h, beta puro 2,28 MeV max — maior alcance tissular e potencial de mielotoxicidade). Para cada radionuclideo, os timepoints de coleta sanguinea e imagem devem ser ajustados conforme a meia-vida efetiva e o clearance sanguineo especifico.",
    practicalAspects: "O protocolo de coleta sanguinea inicia-se imediatamente antes da infusao (amostra basal/background) e segue com coletas em timepoints padronizados: 1h, 2-4h, 24h, 48-72h e opcionalmente 96-168h pos-administracao. Cada amostra (3-5 mL de sangue venoso periferico) e coletada em tubo heparinizado previamente etiquetado e pesada em balanca analitica (precisao ±0,01g). As amostras sao contadas em poco gama calibrado para o radionuclideo de interesse, com padrao de atividade conhecida medido no mesmo equipamento para determinacao de eficiencia de contagem. O calculo de dose a sangue segue o modelo de Sgouros (2005): concentracao de atividade no sangue (Bq/g) versus tempo e integrada analiticamente (funcao bi-exponencial) para obter o tempo de residencia. A self-dose e calculada com fator S (sangue-para-sangue) do OLINDA; a cross-dose soma contribuicoes de rins, figado, baco e corpo restante usando fatores S orgao-para-sangue. Para dosimetria de corpo inteiro com camara de ionizacao, o paciente permanece a distancia fixa (2-3 metros) da camara de ionizacao pressurizada ou detector NaI de corpo inteiro, com medidas em pelo menos 4 timepoints coincidentes com as coletas sanguineas. A correcao de background ambiental e a geometria reprodutivel sao criticas para precisao. Os valores de dose medular devem ser integrados com hemograma seriado (completo + reticulocitos) a cada 2-4 semanas para correlacao farmacodinamica e tomada de decisao clinica sobre continuidade ou modificacao terapeutica.",
    limitations: "O sangue e um proxy imperfeito para a medula ossea vermelha — pode superestimar a dose medular em cenarios de clearance sanguineo rapido e subestimar significativamente em pacientes com metastases osseas difusas, onde a medula recebe dose direta por contiguidade tumoral. O metodo de corpo inteiro e mais simples e de menor custo, porem menos preciso para dose medular especifica, pois integra contribuicoes de todos os tecidos. A coleta sanguinea seriada requer logistica dedicada (acesso venoso mantido ou multiplas puncoes, equipe treinada, poco gama disponivel), que nao esta universalmente acessivel. A variabilidade inter-paciente na farmacocinetica sanguinea e significativa (CV 20-40%), dificultando o uso de curvas populacionais como substituto. O limite de 2 Gy para corpo inteiro, embora amplamente utilizado, foi derivado de dados historicos limitados e pode nao refletir com precisao o risco individual, especialmente em pacientes com reserva medular comprometida. A correlacao entre dose a sangue e nadir hematologico, embora estatisticamente significativa em nivel populacional, apresenta consideravel variabilidade individual, limitando a capacidade preditiva para pacientes isolados. Modelos preditivos baseados em IA estao em desenvolvimento mas ainda nao validados prospectivamente para uso clinico de rotina.",
    reference: "EANM Dosimetry Committee guidelines for bone marrow and whole-body dosimetry. Eur J Nucl Med Mol Imaging."
  },

  // ═══════════════════════════════════════════════
  //  9. Imagem pos-terapia
  // ═══════════════════════════════════════════════
  {
    id: "posttherapy-snmmi-acnm-lu177-2025",
    title: "SNMMI/ACNM Procedure Standard for Post-Treatment Imaging of 177Lu-Based Radiopharmaceuticals",
    year: "2025",
    society: "SNMMI · ACNM",
    type: "Procedure standard",
    badges: ["recent","imaging","essential"],
    category: "imagem",
    categoryName: "Imagem pos-terapia e monitoramento",
    categoryColor: "#C084FC",
    scope: "Primeiro documento a padronizar especificamente a imagem pos-administracao de radiofarmacos baseados em 177Lu, cobrindo tanto 177Lu-DOTATATE (Lutathera) para tumores neuroendocrinos quanto 177Lu-PSMA-617 (Pluvicto) para cancer de prostata metastatico. O guideline reconhece que a imagem pos-terapia com SPECT/CT e um componente essencial da RLT moderna, servindo simultaneamente para verificacao de biodistribuicao, deteccao de deposicao nao-alvo, avaliacao qualitativa de captacao tumoral e, quando quantificada, para dosimetria simplificada ou completa. Com a aprovacao regulatoria de ambos os radiofarmacos e sua expansao global, a padronizacao de protocolos de imagem pos-dose torna-se imperativa para garantir qualidade, reprodutibilidade e comparabilidade entre centros. O documento define parametros de aquisicao, protocolos de reconstrucao, criterios de interpretacao e integracao com dosimetria, posicionando a imagem pos-terapia como ponte entre administracao terapeutica e otimizacao dosimetrica personalizada.",
    indications: [
      "Verificacao de biodistribuicao apos cada ciclo de 177Lu-DOTATATE ou 177Lu-PSMA-617 — mandatorio para confirmacao de captacao tumoral adequada",
      "Deteccao de deposicao nao-alvo: infiltracao perivascular (extravascular), captacao em orgaos nao esperados, retencao no local de injecao",
      "Dosimetria simplificada (single-timepoint) usando imagem SPECT/CT quantitativa em 24h como base de calculo",
      "Dosimetria completa (multi-timepoint) com imagens em 4h, 24h, 48-72h e 96-168h para ajuste farmacocinetico individual",
      "Avaliacao qualitativa de progressao ou resposta tumoral entre ciclos (lesoes novas, desaparecimento de captacao)",
      "Comparacao com PET diagnostico previo (68Ga-DOTATATE ou 68Ga/18F-PSMA) para concordancia lesional e deteccao de discordancias",
      "Identificacao de achados inesperados que podem modificar conduta: fistula, obstrucao renal, hemorragia tumoral, captacao meningea",
      "Documentacao de imagem pos-dose para arquivo clinico, pesquisa e auditoria regulatoria",
      "Base imagenologica para discussao em equipe multidisciplinar (tumor board) sobre continuidade terapeutica"
    ],
    keyPoints: [
      "Timing de aquisicao: SPECT/CT em 24h (±4h) pos-infusao como padrao minimo e obrigatorio; imagens adicionais em 4h (fase precoce de distribuicao), 48-72h e 96-168h para dosimetria multi-timepoint",
      "Protocolo de aquisicao SPECT: fotopico primario de 208 keV (abundancia 10,4%) com janela de ±10%; fotopico secundario de 113 keV (6,2%) pode ser adquirido simultaneamente mas com maior contribuicao de scatter",
      "Colimadores: media-energia de proposito geral (MEGP) recomendados como padrao; alta-energia (HEGP) oferecem melhor rejeicao de penetracao septal mas com perda de sensibilidade — escolha depende das caracteristicas especificas da gama-camara",
      "Parametros de aquisicao: 60 projecoes (ou 120 views em step-and-shoot), 30 segundos por projecao, matriz 128x128, orbita body-contour ou circular, rotacao de 360 graus",
      "TC componente: baixa dose (120 kV, 20-50 mAs) para correcao de atenuacao e localizacao anatomica — nao substitui TC diagnostica",
      "Reconstrucao SPECT: algoritmo iterativo OSEM (4-10 iteracoes, 8-16 subsets) com correcao de atenuacao baseada em mapa mu do CT, correcao de scatter (DEW ou TEW) e correcao de resolucao (PSF modeling) quando disponivel",
      "Calibracao quantitativa: fator de calibracao da gama-camara (cps/MBq) determinado com phantom cilindrico preenchido com atividade conhecida de 177Lu — validacao periodica (trimestral) mandatoria",
      "Interpretacao: comparacao sistematica com PET-SSTR ou PET-PSMA previo para confirmar concordancia de captacao lesional — registro mental ou fusion software quando disponivel",
      "Achados normais: captacao fisiologica em rins, baco, figado (DOTATATE), glandulas salivares, lacrimais e intestino (PSMA-617 em 24h) — conhecimento da biodistribuicao normal e essencial para evitar falsos positivos",
      "Achados patologicos: falha de captacao tumoral em lesao previamente positiva (progressao SSTR-negativa ou PSMA-negativa), captacao focal nova (metastase nova vs fisiologica), assimetria renal (obstrucao)",
      "Quantificacao: metricas SUV-like (counts/volume normalizado por atividade administrada e peso corporal) ou dose absorvida (Gy) para correlacao dose-resposta",
      "Single-timepoint dosimetry (STD): metodo usando imagem de 24h + curva de clearance populacional pre-definida (derivada de coortes de referencia) — incerteza de 10-20% vs metodo completo mas viavel em rotina clinica",
      "Relatorio de imagem pos-dose: descricao sistematica de biodistribuicao, comparacao com imagem previa, identificacao de achados normais e anormais, quantificacao quando disponivel, recomendacao para proximo ciclo",
      "Integracao com dosimetria: imagem pos-dose e o dado de entrada primario para qualquer calculo dosimetrico — qualidade da imagem determina diretamente a precisao da dosimetria",
      "Protecao radiologica durante imageamento: paciente emite radiacao residual significativa em 24h — precaucoes de distancia e tempo para equipe tecnica durante posicionamento",
      "Imagem planar de corpo inteiro (anterior + posterior) como complemento ao SPECT/CT: util para visao panoramica de biodistribuicao e dosimetria de corpo inteiro"
    ],
    radiopharmaceuticals: "177Lu-DOTATATE (Lutathera) para TNE SSTR-positivos, 177Lu-PSMA-617 (Pluvicto) para cancer de prostata metastatico PSMA-positivo, e 177Lu-PSMA-I&T como alternativa academica. O 177Lu possui meia-vida de 6,647 dias com emissao beta (Emax 498 keV) e fotons gama de 113 keV (abundancia 6,2%) e 208 keV (abundancia 10,4%), sendo este ultimo o fotopico preferencial para SPECT por menor interferencia de scatter. A janela terapeutica de imageamento situa-se entre 4h e 168h, com 24h sendo o timepoint mais informativo para balanco entre estatistica de contagem e representatividade da fase de clearance.",
    practicalAspects: "O paciente pode ser imageado ambulatorialmente apos a administracao terapeutica, desde que a taxa de dose residual esteja dentro dos limites de liberacao locais. O posicionamento ideal e em decubito dorsal com bracos ao longo do corpo (ou acima da cabeca para campo de visao abdominal estendido). SPECT/CT deve ser adquirido com gama-camara calibrada quantitativamente para 177Lu — a calibracao requer phantom cilindrico (volume 6-10 L) preenchido com atividade conhecida (200-500 MBq de 177Lu), escaneado com o mesmo protocolo clinico e reconstruido para derivacao do fator de calibracao (cps/MBq/voxel). A janela de energia primaria e 208 keV ±10% (ou ±20% conforme recomendacao do fabricante); janela de 113 keV pode ser adquirida simultaneamente mas seu uso para quantificacao requer correcao de scatter mais robusta. A reconstrucao iterativa (OSEM, tipicamente 4-8 iteracoes com 8-16 subsets) deve incluir correcao de atenuacao baseada em CT, correcao de scatter por metodo de janela de energia (DEW ou TEW) e, quando disponivel, correcao de resolucao (PSF/collimator-detector response modeling). O protocolo SPECT cobre tipicamente o abdome (rins, figado, baco, lesoes abdominais); aquisicoes adicionais podem ser necessarias para torax ou pelve conforme distribuicao lesional. Para dosimetria single-timepoint, a imagem de 24h e processada com software dosimetrico que aplica curva de clearance populacional para estimativa de tempo de residencia e calculo de dose organ-level. O relatorio de imagem pos-dose deve seguir formato padronizado incluindo descricao de biodistribuicao, comparacao com imagem funcional previa, achados relevantes e, quando quantificado, metricas de captacao ou dose absorvida. Protecao radiologica: a equipe tecnica deve manter distancia maxima viavel durante posicionamento, usar avental plumbifero e monitorar dose ocupacional com dosimetro pessoal.",
    limitations: "A resolucao espacial do SPECT (12-15 mm FWHM para 177Lu) e significativamente inferior a do PET (4-6 mm), resultando em efeito de volume parcial que subestima a captacao em lesoes menores que 1,5-2 cm e limita a deteccao de lesoes submilimetricas. A quantificacao absoluta em SPECT/CT, embora tenha avancado consideravelmente na ultima decada, ainda apresenta incertezas superiores as do PET/CT (15-25% vs 5-10%), afetando a precisao dosimetrica. A variabilidade entre gama-camaras de diferentes fabricantes e modelos requer calibracao local cuidadosa — resultados nao sao diretamente transferiveis entre equipamentos sem harmonizacao. Nem todos os centros que administram 177Lu-DOTATATE ou 177Lu-PSMA-617 implementam imagem pos-dose de rotina, particularmente em contextos onde a dosimetria nao e exigida regulatoriamente. A logistica de imageamento em 24h pode ser desafiadora se o paciente recebe alta no mesmo dia da infusao — requer retorno ambulatorial ou permanencia hospitalar prolongada. A interpretacao de captacao intestinal fisiologica em 24h para 177Lu-PSMA-617 e uma fonte conhecida de duvida diagnostica, requerendo experiencia do interpretador. A correcao de scatter no fotopico de 113 keV e particularmente complexa devido a sobreposicao com scatter do fotopico de 208 keV, limitando sua utilidade para quantificacao independente.",
    reference: "SNMMI/ACNM Procedure Standard for Post-Treatment Imaging of 177Lu-Based Radiopharmaceuticals. J Nucl Med. 2025."
  },

  // ═══════════════════════════════════════════════
  //  10. Estruturacao de servico
  // ═══════════════════════════════════════════════
  {
    id: "service-eanm-snmmi-iaea-2022",
    title: "Joint EANM, SNMMI, and IAEA Enabling Guide: How to Set up a Theranostics Centre",
    year: "2022",
    society: "EANM · SNMMI · IAEA",
    type: "Enabling guide",
    badges: ["service","essential"],
    category: "servico",
    categoryName: "Estruturacao de servico teranostico",
    categoryColor: "#0EA5B7",
    scope: "Guia pratico multissociedade (EANM, SNMMI e IAEA) para planejamento, montagem e operacao de um centro de teranostica, cobrindo desde a infraestrutura fisica ate o treinamento de equipe, fluxo regulatorio e sustentabilidade financeira. O documento reconhece que o crescimento exponencial da RLT com 177Lu-DOTATATE e 177Lu-PSMA-617 criou uma demanda urgente por servicos especializados em todo o mundo, mas muitos hospitais e servicos de medicina nuclear nao possuem a infraestrutura, equipe ou autorizacao regulatoria necessarias. O guia fornece um roadmap pratico, modular e adaptavel a diferentes contextos nacionais e economicos, cobrindo os requisitos minimos de espaco fisico (quartos plumbiferos, laboratorio quente, sala de administracao), equipamentos (gama-camara/SPECT-CT, calibrador de dose, monitores de contaminacao), equipe multidisciplinar (medico nuclear, radiofarmaceutico, fisico medico, enfermagem especializada), treinamento e certificacao, e compliance regulatorio com autoridades nucleares nacionais.",
    indications: [
      "Hospitais e centros de medicina nuclear planejando implementar programa de teranostica com radioligantes terapeuticos",
      "Expansao de servico de medicina nuclear diagnostica convencional para incluir terapias com radionuclideos (177Lu, 131I, 223Ra, 90Y)",
      "Compliance regulatorio para obtencao de licenca de manipulacao de radionuclideos terapeuticos junto a autoridade nuclear nacional (CNEN no Brasil, NRC nos EUA, IRSN na Franca)",
      "Planejamento arquitetonico de novas instalacoes ou reforma de espacos existentes para adequacao a terapia com radionuclideos",
      "Definicao de equipe multiprofissional minima e modelo de capacitacao para operacao segura e eficiente",
      "Estabelecimento de protocolos operacionais padronizados (POPs) para administracao, imagem pos-dose, manejo de residuos e emergencias radiologicas",
      "Analise de viabilidade financeira e modelos de sustentabilidade para programas de teranostica",
      "Adequacao a padroes internacionais de qualidade (IAEA QUANUM, EANM accreditation) e preparacao para auditorias",
      "Integracao de programa de dosimetria clinica no workflow do centro de teranostica"
    ],
    keyPoints: [
      "Infraestrutura minima: quarto terapeutico com blindagem adequada (paredes plumbiferas ou concreto baricitico calculado para atividades maximas previstas), banheiro privativo com sistema de esgoto para residuos radioativos liquidos com tanque de retencao e decaimento, deposito de decaimento para residuos solidos",
      "Laboratorio quente (hot lab): capaz de receber, fracionar e dispensar radiofarmacos terapeuticos — requer capela de fluxo laminar com blindagem, calibrador de dose (ionizacao) certificado, sistema de registro de atividades",
      "Equipamentos obrigatorios: gama-camara SPECT/CT para imagem pos-dose, calibrador de dose com certificacao rastreavel, monitor de contaminacao de superficie (Geiger-Mueller), dosimetros pessoais (TLD ou OSL) para toda equipe exposta",
      "Equipe multidisciplinar: medico nuclear (responsavel clinico e tecnico), radiofarmaceutico ou quimico (manipulacao de radiofarmacos), fisico medico (dosimetria, radioprotecao, controle de qualidade), enfermeiro especializado em medicina nuclear (administracao, monitoramento), tecnico em medicina nuclear (aquisicao de imagem)",
      "Treinamento: certificacao em manipulacao de radionuclideos terapeuticos conforme regulacao local, curso de radioprotecao nivel 3 (supervisor de radioprotecao), treinamento pratico em dosimetria clinica (minimo 40h), simulacros de emergencia radiologica anuais",
      "Fluxo de paciente padronizado: consulta pre-terapia (avaliacao clinica, laboratorio, PET diagnostico) -> agendamento -> preparo (consentimento, antiemeticos, hidratacao) -> administracao (sala dedicada, com monitoramento) -> imagem pos-dose (SPECT/CT em 24h) -> internacao ou liberacao conforme regulacao -> seguimento ambulatorial",
      "Regulacao: licenciamento por autoridade nuclear nacional (CNEN no Brasil — Norma CNEN NN 3.05 para medicina nuclear) incluindo autorizacao para posse, transporte e utilizacao de material radioativo selado e nao-selado para terapia",
      "Manejo de residuos radioativos: decaimento in situ para residuos com meia-vida curta (<120 dias), coleta especifica para materiais contaminados, limite de descarga no esgoto conforme regulacao local (CNEN: 1 ALI por descarga), registro de todas as descargas",
      "Emergencias radiologicas: protocolos escritos para derramamento de material radioativo, contaminacao pessoal, reacao adversa durante infusao, obito de paciente com carga radioativa — kit de emergencia sempre acessivel (luvas, coberturas absorventes, detector, bolsas de coleta)",
      "Modelo financeiro: analise de custo incluindo investimento inicial (infraestrutura, equipamentos), custos operacionais (radiofarmacos, equipe, manutencao, dosimetria) e fontes de receita (reembolso SUS/planos, pesquisa clinica) — payback estimado em 2-4 anos para centros com volume >50 pacientes/ano",
      "Documentacao obrigatoria: termos de consentimento informado padronizados, checklists pre-tratamento (laboratorio, imagem, elegibilidade), orientacoes de alta com instrucoes de radioprotecao domiciliar, registro de atividade administrada e dose ao paciente",
      "Controle de qualidade: programa de QA incluindo calibracao de equipamentos (calibrador de dose, gama-camara), monitoramento ambiental (wipe tests, dosimetria de area), auditorias internas periodicas e participacao em programas de intercomparacao",
      "Capacidade de dosimetria: o centro deve implementar progressivamente capacidade dosimetrica (Nivel 1-3 conforme framework EANM) — minimo Nivel 1 (corpo inteiro) como requisito para centros iniciantes, Nivel 2-3 para centros de referencia",
      "Teleconsultoria e redes de referencia: centros iniciantes podem beneficiar-se de parcerias com centros experientes para mentoria em protocolos, dosimetria e manejo de complicacoes",
      "Aspectos eticos: comite de etica institucional deve avaliar protocolos terapeuticos com radionuclideos; consentimento informado detalhado obrigatorio incluindo riscos de radiotoxicidade a longo prazo"
    ],
    radiopharmaceuticals: "O guia e aplicavel a todos os radiofarmacos terapeuticos utilizados em teranostica: 177Lu-DOTATATE (Lutathera) e 177Lu-PSMA-617 (Pluvicto) como drivers primarios da expansao de servicos; 131I (iodeto de sodio para tireoide, MIBG para tumores neuroectodermicos); 223Ra-dicloreto (Xofigo) para metastases osseas de cancer de prostata; 90Y-microesferas (SIR-Spheres, TheraSphere) para radioembolizacao hepatica; e compostos em investigacao como 225Ac-PSMA-617 e 212Pb-DOTAMTATE. Cada radiofarmaco tem requisitos especificos de infraestrutura, blindagem e manejo que devem ser considerados no planejamento do centro.",
    practicalAspects: "O planejamento arquitetonico deve seguir principio de fluxo unidirecional (limpo -> contaminado), com separacao clara entre areas de preparo de radiofarmacos (hot lab), administracao, internacao terapeutica e imagem pos-dose. A blindagem estrutural e calculada por fisico medico com base nas atividades maximas previstas, tipo de radionuclideo, fator de ocupacao e limites de dose para areas adjacentes. A sala de administracao deve ter superficie facilmente descontaminavel (piso epoxi, paredes lavaveis), ponto de agua e esgoto com tanque de decaimento, e sistema de ventilacao com pressao negativa quando aplicavel (131I volatil). O hot lab requer capela de manipulacao com blindagem para 177Lu (L-block plumbifero de 5-10 mm Pb), calibrador de dose certificado com liners adequados para cada radionuclideo, e sistema de registro informatizado de atividades recebidas, preparadas e administradas. Para internacao terapeutica (quando aplicavel — 131I em altas atividades, por exemplo), o quarto deve ter blindagem calculada, banheiro privativo com coleta separada, sistema de comunicacao com equipe sem necessidade de entrada no quarto, e monitoramento por CFTV. Os protocolos de emergencia devem cobrir: derramamento de material radioativo (kits de descontaminacao pre-preparados em locais estrategicos), contaminacao pessoal (procedimento de descontaminacao cutanea, monitoramento e registro), reacao adversa do paciente durante infusao (protocolo de suporte clinico com atencao a exposicao da equipe de resgate), e obito de paciente durante ou apos terapia (notificacao a autoridade nuclear, cuidados para equipe de patologia e servico funerario, documentacao de atividade residual estimada). O modelo de fluxo de pacientes deve prever agenda dedicada com slots protegidos para terapia, evitando conflito com procedimentos diagnosticos de rotina. O treinamento de equipe deve incluir componente teorico (radioprotecao, farmacocinetica, dosimetria basica) e pratico (simulacao de administracao, manejo de emergencia, operacao de equipamentos), com reciclagem anual documentada.",
    limitations: "As orientacoes sao gerais e cada pais possui regulacao especifica com requisitos que podem diferir significativamente — por exemplo, no Brasil a CNEN exige autorizacao especifica para cada radionuclideo terapeutico, enquanto em outros paises a autorizacao e mais generica. Os custos de implementacao variam enormemente por regiao e nivel de complexidade pretendido, com investimento inicial estimado de USD 200.000-1.000.000+ dependendo de necessidade de construcao nova vs adaptacao. O acesso a radiofarmacos terapeuticos e um fator limitante critico em muitos paises em desenvolvimento, com cadeias de suprimento frageis e custos proibitivos. O documento nao aborda profundamente os aspectos de reembolso e financiamento, que sao determinantes para sustentabilidade do programa em contextos de saude publica (SUS no Brasil) e sistemas de planos de saude. A contratacao de equipe especializada (fisico medico com experiencia em dosimetria interna, radiofarmaceutico) pode ser desafiadora em regioes com escassez de profissionais qualificados. A manutencao do programa a longo prazo requer volume minimo de pacientes para viabilidade financeira — centros com baixo volume podem nao atingir sustentabilidade. A integracao com programas de pesquisa clinica, embora recomendada, adiciona camada de complexidade regulatoria e operacional.",
    reference: "Basu S, et al. Joint EANM, SNMMI, and IAEA Enabling Guide: How to Set up a Theranostics Centre. J Nucl Med. 2022;63(12):1797-1803."
  },
  {
    id: "service-iaea-release",
    title: "IAEA — Release of Patients After Radionuclide Therapy",
    year: null,
    society: "IAEA",
    type: "Radiation protection guidance",
    badges: ["service"],
    category: "servico",
    categoryName: "Estruturacao de servico teranostico",
    categoryColor: "#0EA5B7",
    scope: "Documento da IAEA para definicao de criterios de liberacao de pacientes apos terapia com radionuclideos, cobrindo limites de taxa de dose, tempo de isolamento e orientacoes de radioprotecao para familiares e publico. A liberacao segura do paciente pos-terapia e um componente critico do workflow teranostico, equilibrando a necessidade de radioprotecao publica com o conforto e bem-estar do paciente — internacoes desnecessariamente prolongadas aumentam custos e impacto psicossocial. O documento estabelece um framework baseado em risco, considerando o tipo de radionuclideo (meia-vida, tipo de emissao, retencao corporal), a atividade residual estimada no momento da liberacao e as circunstancias domiciliares do paciente (presenca de criancas, gestantes, idosos dependentes). A regulacao varia consideravelmente entre paises, com limites de taxa de dose para liberacao oscilando entre 5 e 50 microSv/h a 1 metro dependendo da jurisdicao. O guideline posiciona-se como referencia internacional harmonizadora, sendo amplamente citado por autoridades regulatorias nacionais como base para normativas locais.",
    indications: [
      "Definicao de criterios de alta hospitalar pos-terapia com 131I (carcinoma de tireoide), 177Lu (DOTATATE e PSMA-617), 90Y (microesferas hepaticas), 223Ra (metastases osseas) e outros radionuclideos terapeuticos",
      "Orientacoes de radioprotecao domiciliar para pacientes liberados: instrucoes sobre distancia, tempo de contato e cuidados com fluidos corporais",
      "Framework regulatorio de referencia para autoridades nacionais de protecao radiologica na elaboracao de normativas locais de liberacao",
      "Calculo de tempo de isolamento domiciliar pos-liberacao para cada radionuclideo e faixa de atividade residual",
      "Situacoes especiais: pacientes com criancas menores de 5 anos no domicilio, gestantes, pacientes incontinentes, pacientes com deficit cognitivo",
      "Manejo de obito de paciente durante ou apos terapia com radionuclideos — orientacoes para equipe de patologia, necropsia e servico funerario",
      "Documentacao obrigatoria de liberacao: formularios de alta com radionuclideo, atividade residual estimada, instrucoes ao paciente e contato de emergencia",
      "Orientacao para equipe de saude em situacoes de emergencia (internacao hospitalar nao-programada, cirurgia urgente) em paciente recentemente tratado com radionuclideo"
    ],
    keyPoints: [
      "Limite de taxa de dose para liberacao: recomendacao IAEA de 25 microSv/h a 1 metro como padrao geral — pode variar por pais (CNEN no Brasil: 30 microSv/h; NRC nos EUA: criterio baseado em dose efetiva ao individuo mais exposto <5 mSv total)",
      "Tempo de isolamento estimado: funcao do radionuclideo (meia-vida fisica e efetiva), atividade administrada, taxa de retencao corporal e condicoes domiciliares — calculavel com tabelas e formulas fornecidas no documento",
      "131I (carcinoma diferenciado de tireoide): para atividades de 3,7-7,4 GBq (100-200 mCi), internacao tipica de 24-72h; meia-vida efetiva de ~12h (rapida por excrecao renal); orientacao domiciliar de 1-3 semanas conforme atividade",
      "177Lu (DOTATATE e PSMA-617): liberacao frequentemente no mesmo dia para atividades de 7,4 GBq — atividade retida no paciente e predominantemente intratumoral/intra-orgao, com taxa de dose externa relativamente baixa; meia-vida efetiva renal de ~50-60h",
      "223Ra (Xofigo): sem necessidade de internacao — emissor alfa com minima radiacao externa, meia-vida de 11,4 dias mas sem emissao gama significativa para exposicao publica; precaucoes basicas de higiene por 1 semana",
      "90Y (microesferas): emissao beta pura sem gama — exposicao externa desprezivel; liberacao no mesmo dia; sem restricoes domiciliares significativas",
      "Orientacoes ao paciente e familiares: instrucoes escritas e verbais sobre manter distancia (>1 metro) de gestantes e criancas por periodo definido, uso de toalete exclusivo, descarga dupla, lavagem separada de roupas e lencois por 1 semana, evitar contato intimo prolongado",
      "Situacoes especiais com criancas: pacientes com filhos menores de 5 anos devem ter planejamento de cuidado alternativo durante periodo de restricao — considerar internacao prolongada quando nao ha alternativa de cuidado",
      "Gestantes no domicilio: restricao mais rigorosa com periodos de distanciamento estendidos e limites de dose ao feto (1 mSv durante toda gestacao remanescente como referencia)",
      "Pacientes incontinentes: consideracao especial para contaminacao de roupas e superficies — orientacoes sobre uso de protecao descartavel, limpeza de superficies contaminadas com solucao diluida de hipoclorito",
      "Manejo de obito durante ou apos terapia: notificacao obrigatoria a autoridade nuclear local, orientacoes para equipe de patologia (uso de EPIs de radioprotecao, monitor de contaminacao durante necropsia), restricoes para cremacao (periodo de espera dependendo de meia-vida do radionuclideo)",
      "Emergencia hospitalar: paciente recentemente tratado que necessita internacao de emergencia em hospital sem servico de medicina nuclear — cartao de informacao do paciente deve conter radionuclideo, data de tratamento, atividade administrada e contato da equipe de medicina nuclear para orientacao",
      "Viagens: pacientes podem acionar alarmes em aeroportos e fronteiras por semanas apos terapia — carta explicativa do servico de medicina nuclear com dados do tratamento deve ser fornecida ao paciente",
      "Monitoramento pos-liberacao: taxa de dose medida com detector calibrado (camara de ionizacao ou Geiger-Mueller) a 1 metro do paciente — documentada no formulario de alta",
      "Instrucoes ao paciente: devem ser fornecidas por escrito em linguagem acessivel (nivel de leitura de 5a-6a serie) e reforcadas verbalmente; incluir contato telefonico 24h da equipe de medicina nuclear para duvidas"
    ],
    radiopharmaceuticals: "O documento abrange todos os radionuclideos terapeuticos utilizados em medicina nuclear: 131I (meia-vida 8,02 dias, beta 606 keV max, gama 364 keV — a emissao gama de alta energia e o principal determinante de exposicao externa e tempo de internacao); 177Lu (meia-vida 6,647 dias, beta 498 keV max, gama 113/208 keV — menor taxa de dose externa que 131I, permitindo liberacao mais precoce); 90Y (meia-vida 64,1h, beta puro 2,28 MeV max — sem emissao gama, exposicao externa desprezivel); 223Ra (meia-vida 11,4 dias, emissor alfa, gama residual de baixa abundancia — minima exposicao externa); 131I-MIBG (mesma fisica do 131I mas farmacocinetica diferente com retencao tumoral prolongada); 89Sr e 153Sm (paliativos osseos, cada vez menos utilizados).",
    practicalAspects: "A medicao de taxa de dose para liberacao e realizada com detector calibrado (camara de ionizacao portatil tipo Victoreen 451P ou similar, ou detector Geiger-Mueller de janela fina) posicionado a 1 metro do tronco do paciente, na linha media anterior. A medida deve ser realizada com o paciente em pe ou sentado, apos esvaziamento vesical (bexiga cheia superestima taxa de dose para 177Lu e 131I). O valor deve ser registrado no formulario de liberacao junto com data, hora e atividade residual estimada. O cartao de informacao ao paciente (wallet card) deve conter: nome do paciente, radionuclideo utilizado, atividade administrada, data e hora do tratamento, nome e contato da instituicao e do medico nuclear responsavel, instrucoes resumidas de radioprotecao. As orientacoes domiciliares devem ser entregues por escrito em linguagem clara e revisadas verbalmente com o paciente e acompanhante. Orientacoes especificas por radionuclideo: para 131I, enfase em excrecao urinaria e salivar (evitar compartilhar utensilios, distancia de criancas por 5-7 dias); para 177Lu, orientacoes mais brandas com foco em cuidados com urina por 48h e distancia de criancas/gestantes por 3-5 dias; para 223Ra, apenas precaucoes basicas de higiene. O servico deve manter registro cronologico de todas as liberacoes com dados dosimetricos para auditoria regulatoria. Protocolos devem incluir procedimento para situacoes imprevistas: paciente que necessita retorno hospitalar de emergencia (informar equipe do pronto-socorro sobre status radioativo), contaminacao domiciliar (orientacao telefonica para descontaminacao basica), e contato acidental com gestante ou crianca (avaliacao de dose e documentacao). O planejamento de alta deve iniciar na consulta pre-terapia, identificando precocemente situacoes domiciliares que podem prolongar internacao (criancas pequenas, gestante coabitante, domicilio compartilhado sem banheiro exclusivo).",
    limitations: "As recomendacoes da IAEA sao de carater geral e de referencia — cada pais estabelece seus proprios limites, que podem ser mais ou menos restritivos. No Brasil, a CNEN segue limite de 30 microSv/h a 1 metro (ligeiramente acima da recomendacao IAEA), enquanto nos EUA o NRC utiliza criterio de dose efetiva total ao individuo mais exposto (<5 mSv), permitindo abordagem mais liberal. Essa heterogeneidade regulatoria entre paises cria inconsistencias para pacientes tratados em diferentes jurisdicoes e dificulta harmonizacao internacional. O compliance domiciliar e dificil de monitorar e frequentemente subotimo — estudos mostram que ate 30-40% dos pacientes nao seguem integralmente as orientacoes de distanciamento. Os aspectos psicossociais do isolamento (solidao, ansiedade, impacto nas relacoes familiares) sao frequentemente subestimados no planejamento terapeutico e podem afetar adesao e qualidade de vida. A avaliacao de dose a familiares e baseada em modelos conservadores com premissas de distancia e tempo de contato que podem nao refletir a realidade domiciliar. Para radionuclideos mais novos (225Ac), os dados de retencao corporal e taxa de dose externa sao limitados, criando incerteza nos criterios de liberacao. A situacao de obito pos-terapia, embora rara, envolve interface complexa entre regulacao nuclear, legislacao funeraria e aspectos eticos que nao esta uniformemente regulamentada.",
    reference: "IAEA Safety Reports Series — Release of Patients After Radionuclide Therapy. International Atomic Energy Agency."
  },
];
'''

with open(target, 'a', encoding='utf-8') as f:
    f.write(content)

print("Batch D written: 7 guidelines (Dosimetria + Imagem + Servico) + array closed")
