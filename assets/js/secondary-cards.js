/* =============================================================================
   secondary-cards.js  —  window.THERA_SECONDARY
   Publicações secundárias / análises derivadas / atualizações / substudos /
   protocolos / abstracts / press releases vinculados aos estudos teranósticos.
   NÃO faz parte do schema congelado de 40 campos do data.js.
   Cada card confirmado em fonte Nível 1-2 (PubMed E-utilities + Crossref).
   Campo `deep` (objetivo/método/achados/interpretação/limitações) extraído dos
   abstracts oficiais — nenhum número inventado; linguagem cautelosa.
   Atualizado: 2026-09-30 (24 cards enriquecidos e verificados; proveniência em scripts/db_secundarios_proveniencia.json).
============================================================================= */
window.THERA_SECONDARY = [
  {
    "id": "vision-hrqol-2023",
    "title": "VISION — HRQoL, dor e eventos esqueléticos sintomáticos",
    "recordType": "secondary_publication",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise do desfecho secundário-chave (SSE) e dos desfechos secundários de PRO pré-especificados do VISION, com análises post hoc adicionais",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise secundária (HRQoL, dor, SSE)",
    "evidenceMaturity": "Análise secundária revisada por pares",
    "year": 2023,
    "journal": "The Lancet Oncology",
    "titleOriginal": "Health-related quality of life and pain outcomes with [177Lu]Lu-PSMA-617 plus standard of care versus standard of care in patients with metastatic castration-resistant prostate cancer (VISION): a multicentre, open-label, randomised, phase 3 trial",
    "authors": "Fizazi K, et al.",
    "doi": "10.1016/S1470-2045(23)00158-4",
    "pmid": "37269841",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/37269841/",
    "category": [
      "HRQoL",
      "Dor",
      "Eventos esqueléticos sintomáticos"
    ],
    "clinicalTakeaway": "No VISION, 177Lu-PSMA-617 + SoC adiou a piora de HRQoL e dor (HR 0,52–0,65; desfechos compostos, p nominais) e o tempo até SSE ou óbito (HR 0,50) vs SoC. A incidência de SSE isolado foi semelhante (16% vs 17%). Estudo aberto, com PROs só durante o tratamento e maior abandono no controle.",
    "collapsedSummary": "177Lu-PSMA-617 + SoC retardou a piora de HRQoL e dor e o tempo até SSE ou óbito. Estudo aberto, com desfechos compostos e p nominais: não é evidência confirmatória de benefício em HRQoL.",
    "deep": {
      "objetivo": "Relatar, no VISION (fase III, aberto, randomização 2:1), o desfecho secundário-chave tempo até o 1º evento esquelético sintomático (SSE) ou óbito e os desfechos secundários de HRQoL (FACT-P, EQ-5D-5L) e dor (BPI-SF) com 177Lu-PSMA-617 + SoC vs SoC isolado.",
      "metodo": "PROs e SSE analisados nos 581 pacientes randomizados a partir de 5/mar/2019 (385 vs 196), após medidas para reduzir o abandono no controle; segurança nos 734 tratados (529 vs 205). Nas análises pré-especificadas, a 'piora' de PRO era composta (piora do escore, progressão clínica ou óbito); análises post hoc consideraram só a piora do escore. Cox estratificado; desfechos de HRQoL/dor fora do controle de erro tipo I (p nominais).",
      "achados": [
        "Tempo até 1º SSE ou óbito: mediana 11,5 vs 6,8 meses; HR 0,50 (IC95% 0,40–0,62). Em análise post hoc que não contou o óbito como evento, o tempo até o 1º SSE também foi retardado com 177Lu-PSMA-617.",
        "Piora do FACT-P total (pré-especificada, composta): HR 0,54 (0,45–0,66); post hoc só escore: HR 0,46 (0,35–0,61).",
        "Piora da intensidade de dor BPI-SF (composta): HR 0,52 (0,42–0,63); post hoc: HR 0,45 (0,33–0,60).",
        "Piora da utilidade EQ-5D-5L: HR 0,65 (0,54–0,78); a definição de piora (qualquer queda ou ausência de mudança) produz piora aparente rápida.",
        "Efeito sobre SSE ou óbito semelhante com e sem agente ósseo-dirigido (HR 0,49 e 0,50; post hoc).",
        "Toxicidade hematológica G3–4 maior com 177Lu: linfócitos 51% vs 19%, hemoglobina 15% vs 6%, plaquetas 9% vs 2%; 5 (1%) óbitos relacionados ao tratamento vs 0."
      ],
      "interpretacao": "177Lu-PSMA-617 + SoC retardou a piora de HRQoL e dor e o tempo até SSE ou óbito, em linha com o ganho de rPFS e OS do estudo principal. Os desfechos de PRO eram compostos (incluíam progressão clínica e óbito) e têm p nominais, sem controle de multiplicidade; indicam ausência de prejuízo à qualidade de vida mais do que um benefício isolado e confirmatório de HRQoL.",
      "limitacoes": "Estudo aberto, sem placebo; PROs coletados só durante o tratamento; abandono maior e seguimento de PRO muito mais curto no controle (mediana FACT-P 0,76 vs 4,37 meses); piora sustentada não avaliada; EQ-5D pouco sensível nessa população; HRQoL fora do controle de erro tipo I."
    },
    "analysis": {
      "populacao": "581 randomizados em ou após 5/mar/2019 (385 177Lu-PSMA-617 + SoC; 196 SoC) para PRO e SSE; segurança em 734 tratados (529 vs 205). mCRPC PSMA+ pós-ARPI e 1–2 taxanos.",
      "desenho_relacao": "Mesma coorte randomizada do VISION: desfecho secundário-chave (SSE ou óbito) e secundários de PRO pré-especificados, mais análises post hoc não compostas e de subgrupos por agente ósseo-dirigido.",
      "endpoints": "Tempo até 1º SSE ou óbito; tempo até piora de FACT-P (total e subescalas), BPI-SF e EQ-5D-5L (composto com progressão clínica/óbito nas análises pré-especificadas).",
      "estatistica": "Cox estratificado pelos fatores de randomização; Kaplan-Meier; HRQoL/dor fora do controle de erro tipo I; todos os p nominais e descritivos.",
      "cutoff_followup": "Seguimento mediano de PRO (FACT-P) 4,37 vs 0,76 meses; SSE ~17 meses em ambos; segurança 14,78 vs 10,64 meses. Data de cutoff não informada nesta fonte.",
      "subgrupos": "SSE ou óbito com agente ósseo-dirigido HR 0,49 (0,36–0,68); sem agente HR 0,50 (0,37–0,68) (post hoc).",
      "seguranca": "G3–4: linfócitos 51% vs 19%, hemoglobina 15% vs 6%, plaquetas 9% vs 2%; 5 (1%) óbitos relacionados ao tratamento vs 0; creatinina G≥3 baixa e semelhante entre braços.",
      "conclusao_autores": "177Lu-PSMA-617 + SoC retardou a piora de HRQoL e o tempo até eventos esqueléticos vs SoC isolado, apoiando seu uso após ARPI e taxano."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "vision-safety-2024",
    "title": "VISION — Análise detalhada de segurança",
    "recordType": "secondary_publication",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análises de segurança do VISION: por número de ciclos (pré-especificadas) e ajustada por exposição (post hoc)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de segurança",
    "evidenceMaturity": "Análise secundária revisada por pares",
    "year": 2024,
    "journal": "European Urology",
    "titleOriginal": "Safety Analyses of the Phase 3 VISION Trial of [177Lu]Lu-PSMA-617 in Patients with Metastatic Castration-resistant Prostate Cancer",
    "authors": null,
    "doi": "10.1016/j.eururo.2023.12.004",
    "pmid": "38185538",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/38185538/",
    "category": [
      "Segurança",
      "Eventos adversos"
    ],
    "clinicalTakeaway": "No VISION, 5–6 ciclos de 177Lu-PSMA-617 não mostraram acúmulo de toxicidade (TEAE G≥3 por ciclo de 17% no C1 a 12% no C6), mas os subgrupos por ciclos têm viés de sobrevivência. Ajustado pela exposição (7,8 vs 2,1 meses), o excesso global de TEAE vs SoC diminui; a xerostomia e a mielossupressão seguem maiores.",
    "collapsedSummary": "5–6 ciclos de 177Lu-PSMA-617 não mostraram acúmulo de toxicidade. Xerostomia e mielossupressão seguem maiores após ajuste por exposição; subgrupos por ciclos têm viés de sobrevivência.",
    "deep": {
      "objetivo": "Avaliar, no VISION, se ciclos adicionais (5–6) de 177Lu-PSMA-617 aumentam a toxicidade e quanto do excesso de eventos adversos vs SoC se deve ao maior tempo de observação no braço experimental.",
      "metodo": "Conjunto de segurança: 529 tratados com 177Lu-PSMA-617 + SoC (240 com 1–4 ciclos; 289 com 5–6) e 205 com SoC. Incidência de TEAE/TRAE por subgrupo de ciclos (pré-especificado) e por ciclo de início; tempo até o 1º evento (Kaplan-Meier); incidência ajustada por exposição por 100 paciente-anos de tratamento (post hoc). Análise descritiva.",
      "achados": [
        "TEAE de qualquer grau: 98% (1–4 ciclos) vs 99% (5–6 ciclos); G≥3: 60% vs 46%, provavelmente por viés de seleção/sobrevivência.",
        "Por ciclo de início, TEAE G≥3 não aumentou nos ciclos tardios (17% no ciclo 1; 12% no ciclo 6); os primeiros eventos se concentraram no início do tratamento.",
        "Exposição mediana 7,8 vs 2,1 meses; ajustada por exposição, a incidência global de TEAE foi semelhante entre braços (1415,7 vs 1137,0 por 100 PTY).",
        "Após ajuste, boca seca (75,1 vs 1,4/100 PTY), olho seco, mielossupressão, diarreia e vômitos seguiram maiores com 177Lu; eventos musculoesqueléticos, renais, hepáticos e dispneia foram menores.",
        "Redução de dose por TEAE em 5,7%; toxicidade renal tardia em 2,7% dos que iniciaram o ciclo 6; segunda neoplasia em 11/529 vs 2/205."
      ],
      "interpretacao": "Os dados não sugerem acúmulo de toxicidade com 5–6 ciclos em pacientes selecionados que seguem respondendo e tolerando o tratamento. Parte do excesso bruto de eventos vs SoC reflete o maior tempo de observação, mas a toxicidade específica (xerostomia, mielossupressão) persiste após o ajuste.",
      "limitacoes": "Os subgrupos por número de ciclos são definidos após a randomização e sujeitos a viés de sobrevivência; a análise não foi desenhada para comparar 1–4 vs 5–6 ciclos. O ajuste por exposição é post hoc. Eventos novos e recorrentes não foram separados, TEAEs podem refletir progressão e as reduções de dose não foram consideradas."
    },
    "analysis": {
      "populacao": "734/831 tratados: 529 com 177Lu-PSMA-617 + SoC (240 com 1–4 ciclos; 289 com 5–6) e 205 com SoC.",
      "desenho_relacao": "Análises de segurança do VISION: por número de ciclos e por ciclo (pré-especificadas) e incidência ajustada por exposição (post hoc).",
      "endpoints": "TEAE/TRAE (qualquer grau, G≥3, graves) por subgrupo e por ciclo; tempo até o 1º evento de classes de interesse; incidência por 100 paciente-anos de tratamento.",
      "estatistica": "Descritiva; Kaplan-Meier para incidência cumulativa; taxa = n/PTY × 100.",
      "cutoff_followup": "Exposição/observação de segurança mediana de 7,8 meses (177Lu) vs 2,1 meses (controle). Data de cutoff não informada nesta fonte.",
      "subgrupos": "1–4 vs 5–6 ciclos: TEAE 98% vs 99%; G≥3 60% vs 46%; TEAE grave 42% vs 32%.",
      "seguranca": "Após ajuste por exposição, mielossupressão, xerostomia, olho seco, diarreia e vômitos seguiram maiores com 177Lu. Redução de dose por TEAE em 5,7%; toxicidade renal tardia em 7/257 (2,7%); segunda neoplasia em 11/529 vs 2/205.",
      "conclusao_autores": "Exposição mais longa não se associou a maior risco de toxicidade; os achados apoiam até 6 ciclos em pacientes com benefício clínico e boa tolerância."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "vision-renal-multiorgan-dosimetry-2024",
    "title": "VISION — Dosimetria renal e multiorgânica",
    "recordType": "substudy",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Subestudo de dosimetria do VISION, com coorte separada e não randomizada",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Subestudo de dosimetria (segurança renal/multiorgânica)",
    "evidenceMaturity": "Subestudo revisado por pares",
    "year": 2024,
    "journal": "Journal of Nuclear Medicine",
    "titleOriginal": "Renal and Multiorgan Safety of 177Lu-PSMA-617 in Patients with Metastatic Castration-Resistant Prostate Cancer in the VISION Dosimetry Substudy",
    "authors": null,
    "doi": "10.2967/jnumed.123.265448",
    "pmid": "38050121",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/38050121/",
    "category": [
      "Dosimetria",
      "Segurança renal",
      "Segurança multiorgânica"
    ],
    "clinicalTakeaway": "Subestudo não randomizado do VISION (n=30): dose renal de 0,43 Gy/GBq por ciclo e cumulativa observada de 15±6 Gy em 6 ciclos (n=10), abaixo do limite de 23 Gy derivado da radioterapia externa. Sem toxicidade renal G≥3. Glândulas lacrimais e salivares recebem as maiores doses. A dosimetria do ciclo 1 estimou bem a dose cumulativa.",
    "collapsedSummary": "A dose renal cumulativa ficou abaixo do limite de referência, sem toxicidade renal G≥3. Coorte pequena e não randomizada; glândulas lacrimais e salivares recebem as maiores doses.",
    "deep": {
      "objetivo": "Quantificar as doses absorvidas de 177Lu-PSMA-617 nos rins e em outros órgãos de risco (glândulas lacrimais e salivares, medula) no regime do VISION e testar se a dosimetria do ciclo 1 prediz a dose cumulativa em 6 ciclos.",
      "metodo": "Coorte separada, não randomizada, de 30 pacientes em 4 centros alemães (7,4 GBq a cada 6 semanas, até 6 ciclos). SPECT/CT e planar em 2, 24, 48 e 168 h no ciclo 1 (n=29) e ponto único em 48 h nos ciclos 2–6; medula por amostras de sangue; OLINDA/EXM. Dose prevista (extrapolação do ciclo 1, n=29) vs observada (n=10 com 6 ciclos). Análise descritiva.",
      "achados": [
        "Dose por ciclo nos rins: 0,43±0,16 Gy/GBq (ciclo 1) e 0,44±0,21 Gy/GBq (ciclos 2–6); as maiores doses foram nas glândulas lacrimais (2,10±0,47) e salivares (0,63±0,36); medula 0,035±0,020 Gy/GBq.",
        "Dose renal cumulativa em 6 ciclos: observada 15±6 Gy (n=10) vs prevista 19±7,3 Gy (n=29), abaixo do limite histórico de 23 Gy da radioterapia externa.",
        "Cumulativa observada vs prevista: lacrimais 77 vs 92 Gy; salivares 30 vs 28 Gy; medula 1,30 vs 1,5 Gy; sem diferença significativa (P = 0,19–0,54). A previsão tendeu a superestimar.",
        "Toxicidade renal em 5/30 (16,7%), nenhuma de grau ≥3; mielossupressão (qualquer grau) em 11/30 (36,7%); boca seca 16,7%.",
        "Dose renal cumulativa maior nos pacientes com toxicidade renal (24,42 vs 17,55 Gy; descritivo)."
      ],
      "interpretacao": "No regime do VISION, a dose renal cumulativa ficou abaixo do limite de referência e não houve toxicidade renal de grau ≥3 nesta coorte pequena. A dosimetria do ciclo 1 estimou razoavelmente a dose cumulativa. As glândulas lacrimais e salivares recebem as maiores doses por GBq.",
      "limitacoes": "Coorte não randomizada (30; só 10 completaram 6 ciclos); dosimetria de ponto único nos ciclos 2–6; o limite de 23 Gy vem da radioterapia externa; análise descritiva."
    },
    "analysis": {
      "populacao": "30 pacientes com mCRPC PSMA+ numa coorte separada, não randomizada (4 centros, Alemanha); dosimetria do ciclo 1 em 29; 10 com os 6 ciclos.",
      "desenho_relacao": "Subestudo prospectivo de dosimetria do VISION, com coorte separada e análise descritiva independente do estudo principal.",
      "endpoints": "Dose absorvida por atividade (Gy/GBq) por ciclo; dose cumulativa prevista e observada em 6 ciclos (44,4 GBq); segurança, QTc, farmacocinética e radiometabólitos urinários.",
      "estatistica": "Descritiva; previsto vs observado por Hotelling T² com Bonferroni (P = 0,19–0,54).",
      "cutoff_followup": "Exposição mediana de 5,52 meses; mediana de 4 ciclos; atividade total média 28,7±10,5 GBq. Data de cutoff não informada.",
      "subgrupos": "Dose renal cumulativa de 24,42±7,41 Gy com toxicidade renal vs 17,55±7,80 Gy sem (descritivo).",
      "seguranca": "Toxicidade renal em 5/30 (16,7%), sem grau ≥3; mielossupressão (qualquer grau) em 11/30 (36,7%); náusea/vômito 36,7%; boca seca 16,7%; variação mínima do QTcF.",
      "conclusao_autores": "Dose renal cumulativa abaixo do limite estabelecido, boa segurança global e baixa radiotoxicidade renal; a dose cumulativa pode ser prevista a partir do ciclo 1."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "vision-baseline-psma-pet-biomarkers-2024",
    "title": "VISION — Biomarcadores quantitativos no PET PSMA basal",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise secundária exploratória (exigida pela FDA) de biomarcadores do PET PSMA basal no VISION",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de biomarcador de imagem (PSMA PET quantitativo)",
    "evidenceMaturity": "Análise exploratória revisada por pares",
    "year": 2024,
    "journal": "Radiology",
    "titleOriginal": "Quantitative 68Ga-PSMA-11 PET and Clinical Outcomes in Metastatic Castration-resistant Prostate Cancer Following 177Lu-PSMA-617 (VISION Trial)",
    "authors": "Kuo PH, et al.",
    "doi": "10.1148/radiol.233460",
    "pmid": "39162634",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/39162634/",
    "category": [
      "Biomarcador",
      "PSMA PET",
      "SUVmean",
      "Imagem quantitativa"
    ],
    "clinicalTakeaway": "Análise secundária exploratória do VISION (826 participantes incluídos). Segundo os autores, o SUVmean tumoral de corpo inteiro no 68Ga-PSMA-11 PET/CT basal foi o melhor preditor de eficácia do 177Lu-PSMA-617. O aumento de 1 unidade no SUVmean associou-se a redução de 12% e 10% no risco de evento de rPFS e de óbito, respectivamente. Os ganhos de rPFS e OS com 177Lu-PSMA-617 + SOC foram maiores com SUVmean mais alto. Os autores relatam evidência de potencial benefício clínico independentemente do SUVmean, mas no quartil mais baixo os IC95% dos HR de rPFS e OS cruzaram 1. Não foi identificado ponto ótimo de SUVmean entre os tratados com 177Lu-PSMA-617.",
    "collapsedSummary": "SUVmean tumoral basal mais elevado associou-se a maiores ganhos de rPFS e OS com 177Lu-PSMA-617. Embora os autores relatem potencial benefício independentemente do SUVmean, no quartil mais baixo os IC95% cruzaram 1; não houve ponto de corte ótimo.",
    "deep": {
      "objetivo": "Explorar, no VISION, a associação entre parâmetros quantitativos do 68Ga-PSMA-11 PET/CT basal (SUVmean, SUVmax, volume tumoral PSMA+, carga tumoral; corpo inteiro e regiões anatômicas) e rPFS, OS, ORR e resposta de PSA.",
      "metodo": "Análise secundária exploratória, exigida pela FDA, em 826/831 randomizados com PET quantificável (548 177Lu-PSMA-617 + SoC; 278 SoC). Cox e regressão logística univariáveis e multivariáveis (seleção stepwise), com tratamento como única outra covariável e sem ajuste clínico; análise por quartis de SUVmean; busca de ponto de corte ótimo. Não inferencial; p nominais, sem ajuste de multiplicidade.",
      "achados": [
        "SUVmean tumoral de corpo inteiro (mediana 7,6) foi o parâmetro mais associado aos desfechos no braço 177Lu (rPFS HR 0,86; OS HR 0,88). Na amostra geral do estudo, +1 unidade associou-se a 12% menos risco de evento de rPFS e 10% menos risco de óbito.",
        "SUVmean também se associou a ORR (OR 1,39) e a resposta de PSA (OR 1,23) no braço 177Lu.",
        "Quartil mais alto de SUVmean: rPFS 13,8 vs 3,9 meses (HR 0,34) e OS 21,4 vs 15,0 meses (HR 0,47) vs SoC. Quartil mais baixo: rPFS 5,8 vs 4,0 meses (HR 0,75; IC95% 0,45–1,26) e OS 14,5 vs 11,3 meses (HR 0,87; 0,60–1,27), com ICs que cruzam 1.",
        "Nenhum ponto de corte ótimo de SUVmean foi identificado dentro do braço 177Lu.",
        "Maior carga tumoral (rPFS HR 1,02; OS HR 1,04 por 1000 g) e maior volume tumoral PSMA+ regional (rPFS HR 1,48–1,53; OS HR 1,38–2,12) associaram-se a piores desfechos."
      ],
      "interpretacao": "Na população do VISION, selecionada por leitura visual, SUVmean mais alto associou-se a maior magnitude de benefício, mas o SUVmean não definiu um limiar de exclusão. No quartil mais baixo a diferença foi numericamente favorável e não significativa (IC incluindo 1). SUVmean alto também pode ter valor prognóstico no braço SoC. Análise exploratória, que gera hipótese e não serve para selecionar pacientes.",
      "limitacoes": "VISION sem poder para subgrupos de PET quantitativo; p nominais sem ajuste de multiplicidade; modelos sem covariáveis clínicas; variação de equipamentos e reconstrução entre centros; resultados restritos ao 68Ga-PSMA-11; pacientes inelegíveis pela leitura visual não foram avaliados."
    },
    "analysis": {
      "populacao": "826/831 randomizados com PET basal quantificável (548 vs 278); rPFS e resposta de PSA no subconjunto randomizado a partir de 5/mar/2019 (rPFS: 382 vs 194); OS no conjunto completo.",
      "desenho_relacao": "Análise secundária exploratória, exigida pela FDA, de biomarcador de imagem basal no VISION; não inferencial.",
      "endpoints": "rPFS, OS, ORR (RECIST 1.1) e resposta de PSA.",
      "estatistica": "Cox e logística univariável/multivariável (backward/forward; covariável de tratamento, sem covariáveis clínicas); quartis com Cox estratificado; pontos de corte por estatística de rank maximamente selecionada; p nominais.",
      "cutoff_followup": null,
      "subgrupos": "Quartis de SUVmean: maior quartil rPFS HR 0,34 e OS HR 0,47; menor quartil rPFS HR 0,75 (0,45–1,26) e OS HR 0,87 (0,60–1,27); benefício significativo nos 3 quartis superiores; sem ponto de corte ótimo.",
      "seguranca": null,
      "conclusao_autores": "SUVmean tumoral de corpo inteiro no PET basal foi o melhor preditor de eficácia do 177Lu-PSMA-617; ganhos maiores com SUVmean mais alto, com evidência de benefício em todos os níveis."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "vision-prior-concomitant-treatment-subgroups-2022",
    "title": "VISION — Subgrupos por tratamentos prévios e concomitantes (abstract)",
    "recordType": "congress_abstract",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise de subgrupos do VISION apresentada em congresso",
    "publicationStatus": "Congress abstract",
    "analysisType": "Análise de subgrupos (tratamentos prévios/concomitantes)",
    "evidenceMaturity": "Abstract de congresso — não é artigo completo",
    "year": 2022,
    "journal": "Journal of Clinical Oncology (ASCO Annual Meeting, suppl)",
    "titleOriginal": "[177Lu]Lu-PSMA-617 in PSMA-positive metastatic castration-resistant prostate cancer: Prior and concomitant treatment subgroup analyses of the VISION trial",
    "authors": "Vaishampayan N, Morris MJ, et al.",
    "doi": "10.1200/JCO.2022.40.16_suppl.5001",
    "pmid": null,
    "sourceUrl": "https://ascopubs.org/doi/10.1200/JCO.2022.40.16_suppl.5001",
    "category": [
      "Subgrupos",
      "Terapia prévia",
      "Terapia concomitante",
      "Abstract"
    ],
    "clinicalTakeaway": "Abstract de congresso avaliando a consistência dos benefícios de rPFS e OS em subgrupos definidos por tratamentos prévios e concomitantes. Congress abstract — deve ser interpretado com cautela.",
    "deep": {
      "objetivo": "Avaliar a consistência do benefício do 177Lu-PSMA-617 em subgrupos definidos por tratamentos prévios e concomitantes no VISION.",
      "metodo": "Análise de subgrupos apresentada em congresso (ASCO 2022).",
      "achados": [
        "Abstract de congresso — avaliou a consistência dos benefícios de rPFS e OS entre subgrupos; magnitudes numéricas por subgrupo não foram extraídas de fonte primária direta nesta sessão (ver abstract oficial, JCO 2022 suppl, abstr 5001)."
      ],
      "interpretacao": "Congress abstract — sugere consistência do benefício entre subgrupos; deve ser interpretado com cautela.",
      "limitacoes": "Abstract de congresso; não revisado por pares no nível de artigo completo."
    }
  },
  {
    "id": "vision-psa-decline-clinical-outcomes-2024",
    "title": "VISION — Declínio de PSA e desfechos clínicos",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise post hoc exploratória do braço 177Lu-PSMA-617 do VISION (declínio de PSA durante o tratamento × desfechos)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise exploratória (associação PSA-desfecho)",
    "evidenceMaturity": "Análise exploratória revisada por pares",
    "year": 2024,
    "journal": "European Urology",
    "titleOriginal": "Association of Declining Prostate-specific Antigen Levels with Clinical Outcomes in Patients with Metastatic Castration-resistant Prostate Cancer Receiving [177Lu]Lu-PSMA-617 in the Phase 3 VISION Trial",
    "authors": null,
    "doi": "10.1016/j.eururo.2024.08.021",
    "pmid": "39242323",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/39242323/",
    "category": [
      "PSA",
      "Biomarcador",
      "Desfechos clínicos"
    ],
    "clinicalTakeaway": "Análise post hoc do braço 177Lu-PSMA-617 do VISION (n=551): quanto maior o declínio de PSA até a semana 12, maiores a rPFS e a OS (mediana de OS 9,8 meses com aumento vs não atingida com declínio ≥90%). O declínio parece ter valor prognóstico, e é uma associação sem causalidade; o braço SoC foi excluído. Aumento precoce de PSA não indica, por si só, falha: 15% com aumento na semana 6 declinaram na semana 12.",
    "collapsedSummary": "Maior declínio de PSA até a semana 12 associou-se a maiores rPFS e OS com 177Lu-PSMA-617. Associação prognóstica, sem causalidade; aumento precoce de PSA não indica, por si só, falha.",
    "deep": {
      "objetivo": "Avaliar, no braço 177Lu-PSMA-617 do VISION, a associação entre a magnitude do declínio de PSA não confirmado e rPFS, OS, ORR e tempo até piora de HRQoL/dor.",
      "metodo": "Análise post hoc exploratória com os 551 randomizados para 177Lu-PSMA-617 + SoC (controle excluído por poucos declínios ≥50%). Categorias de melhor declínio até a semana 12 (aumento; 0–<50%; 50–<90%; ≥90%), sem confirmação; landmarks de 6 e 12 semanas; Kaplan-Meier e Cox vs aumento de PSA; Cox multivariado com seleção stepwise. Sem teste inferencial formal; cutoff de 27/jan/2021.",
      "achados": [
        "Melhor variação até a semana 12: aumento 29%; declínio 0–<50% 17%; 50–<90% 28%; ≥90% 15%.",
        "rPFS mediana: 5,8 (aumento) vs 8,7, 11,3 e 20,3 meses; modelo multivariado: risco de rPFS 61%, 72% e 88% menor vs aumento de PSA.",
        "OS mediana: 9,8 (aumento) vs 14,0, 18,3 meses e não atingida (≥90%); risco de óbito 51%, 70% e 87% menor.",
        "ORR 4,9% com aumento vs 13%, 47% e 52% com declínio; o tempo até piora de FACT-P também foi maior com declínios maiores (5,7 vs 16,0 meses no grupo ≥90%).",
        "15% dos pacientes com aumento de PSA na semana 6 tiveram declínio na semana 12; 26% dos com aumento até a semana 12 tiveram doença estável."
      ],
      "interpretacao": "A magnitude do declínio de PSA durante o 177Lu-PSMA-617 associou-se a melhores desfechos e parece ter valor prognóstico; a análise incluiu só o braço 177Lu-PSMA-617. Um aumento precoce de PSA não significa necessariamente falha: parte dos pacientes tem declínio posterior. Associação descritiva entre duas variáveis pós-basais, sem inferência causal.",
      "limitacoes": "Post hoc, sem teste inferencial formal; uso de duas variáveis pós-basais nas análises de associação (variação de PSA e desfechos de eficácia); declínio de PSA não confirmado; ~7% excluídos por falta de PSA, sem imputação; seleção stepwise pode enviesar; sem estratificação por terapia concomitante (ARPI em 53%)."
    },
    "analysis": {
      "populacao": "551 randomizados para 177Lu-PSMA-617 + SoC (VISION); 491 avaliáveis para o declínio até a semana 12. Braço controle excluído.",
      "desenho_relacao": "Análise post hoc exploratória de biomarcador on-treatment (PSA), restrita ao braço 177Lu-PSMA-617.",
      "endpoints": "rPFS, OS, ORR, PFS, tempo até progressão de PSA, tempo até piora de FACT-P, EQ-5D-5L e BPI-SF, por categoria de declínio de PSA.",
      "estatistica": "Landmarks de 6 e 12 semanas; Kaplan-Meier; Cox por categoria vs aumento de PSA; Cox multivariado (stepwise); p nominais.",
      "cutoff_followup": "Cutoff de 27/jan/2021; seguimento mediano de OS de 19,8–22,6 meses por subgrupo.",
      "subgrupos": "Resultados semelhantes com 1 ou 2 taxanos prévios; nos que receberam 5–6 ciclos, declínio do C5 ao C6 associou-se a rPFS mais longa (17,4 e 20,6 vs 11,1 meses).",
      "seguranca": null,
      "conclusao_autores": "A magnitude do declínio de PSA associou-se a melhores desfechos clínicos e relatados; o declínio de PSA parece ter valor prognóstico durante o 177Lu-PSMA-617."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "vision-multivariable-outcome-models-2024",
    "title": "VISION — Modelos multivariáveis de desfechos",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise post hoc de modelagem prognóstica com dados do VISION (braço 177Lu-PSMA-617)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Modelagem multivariável",
    "evidenceMaturity": "Análise exploratória revisada por pares",
    "year": 2024,
    "journal": "EClinicalMedicine",
    "titleOriginal": "Multivariable models of outcomes with [177Lu]Lu-PSMA-617: analysis of the phase 3 VISION trial",
    "authors": null,
    "doi": "10.1016/j.eclinm.2024.102862",
    "pmid": "39430616",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/39430616/",
    "category": [
      "Modelagem preditiva",
      "Modelagem de desfechos",
      "Biomarcador"
    ],
    "clinicalTakeaway": "Nomogramas post hoc do braço 177Lu-PSMA-617 do VISION (n=551) estimam o prognóstico (C-index 0,73 para OS; 0,68 para rPFS; AUC 0,72 para PSA50), usando SUVmax, LDH, FA, linfócitos e outros fatores. São prognósticos, não preditivos de benefício vs SoC, e só têm validação interna.",
    "collapsedSummary": "Nomogramas estimam o prognóstico de OS, rPFS e PSA50 com 177Lu-PSMA-617. São prognósticos, não preditivos de benefício vs SoC, e têm só validação interna.",
    "deep": {
      "objetivo": "Construir, com dados do braço 177Lu-PSMA-617 do VISION, modelos multivariáveis e nomogramas de OS, rPFS e PSA50 a partir de parâmetros pré-tratamento clínicos, laboratoriais e de PET PSMA.",
      "metodo": "Análise post hoc. Foram avaliados 29 parâmetros pré-tratamento. Modelos de parâmetro único usaram os dois braços (n=831), testando associação e interação com o tratamento (FDR). Os modelos multivariáveis usaram só o braço 177Lu (n=551): seleção bayesiana com horseshoe priors, Cox (OS, rPFS) e logística (PSA50), com validação interna por bootstrap e sem coorte de validação externa.",
      "achados": [
        "Nomograma de OS (10 variáveis: SUVmax, tempo desde o diagnóstico, uso de opioide, AST, hemoglobina, linfócitos, linfonodos PSMA+, LDH, FA e neutrófilos): C-index 0,73 (IC95% 0,70–0,76).",
        "Nomograma de rPFS (7 variáveis): C-index 0,68 (0,65–0,72). Nomograma de PSA50 (SUVmax, linfócitos, FA): AUC 0,72 (0,68–0,77).",
        "Sem SUVmax, o desempenho se manteve para OS (0,73) e rPFS (0,67), mas caiu para PSA50 (AUC 0,64).",
        "Nos modelos de parâmetro único, menos parâmetros se associaram a desfechos diferenciais com 177Lu vs controle: SUVmax ou SUVmean mais altos associaram-se a maior PSA50 com 177Lu vs controle, e nenhum parâmetro se associou significativamente a benefício de OS ou rPFS.",
        "Aplicados ao VISION, os nomogramas prévios de Gafita et al. tiveram C-index de 0,67 (OS) e 0,61 (rPFS)."
      ],
      "interpretacao": "Os nomogramas estimam o prognóstico de pacientes tratados com 177Lu-PSMA-617 (C-index 0,68–0,73) e podem ajudar a informar expectativas e estratificar ensaios. Foram construídos só no braço 177Lu e não estimam desfechos com SoC isolado; nos modelos de parâmetro único, nenhum parâmetro se associou significativamente a benefício de OS ou rPFS com 177Lu vs controle. Análise post hoc, sem validação externa.",
      "limitacoes": "Post hoc; validação apenas interna (bootstrap), sem coorte de validação; necessita validação no mundo real; radiossensibilidade individual não considerada; modelos só para o braço 177Lu (não preditivos de benefício vs SoC); não generalizável a doença PSMA-negativa nem a fases mais precoces."
    },
    "analysis": {
      "populacao": "Modelos multivariáveis: 551 pacientes do braço 177Lu-PSMA-617 + SoC do VISION. Modelos de parâmetro único: 831 (ambos os braços).",
      "desenho_relacao": "Análise post hoc de modelagem prognóstica com dados do VISION.",
      "endpoints": "OS, rPFS e PSA50 (queda de PSA ≥50%).",
      "estatistica": "29 parâmetros pré-tratamento; correlação de Spearman para colinearidade; seleção bayesiana com horseshoe priors (ICr 80%); Cox/logística; C-index e AUC-ROC com IC por bootstrap; DeLong para comparar modelos.",
      "cutoff_followup": null,
      "subgrupos": "Nenhum parâmetro se associou a benefício diferencial de OS ou rPFS vs controle; SUVmax e SUVmean associaram-se a maior PSA50 diferencial. Modelos sem SUVmax: OS 0,73; rPFS 0,67; PSA50 0,64.",
      "seguranca": null,
      "conclusao_autores": "Primeiros modelos de desfechos com 177Lu-PSMA-617 a partir de dados prospectivos de fase III; a combinação de parâmetros laboratoriais, clínicos e de imagem influencia os desfechos e pode auxiliar a seleção, o manejo e o desenho de ensaios."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "vision-tumor-dosimetry-asco-2023",
    "title": "VISION — Dosimetria tumoral (abstract)",
    "recordType": "congress_abstract",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise de dosimetria tumoral do subestudo de dosimetria do VISION",
    "publicationStatus": "Congress abstract",
    "analysisType": "Subestudo de dosimetria tumoral",
    "evidenceMaturity": "Abstract de congresso — não é artigo completo",
    "year": 2023,
    "journal": "Journal of Clinical Oncology (ASCO Annual Meeting, suppl)",
    "titleOriginal": "Tumor dosimetry of [177Lu]Lu-PSMA-617 for the treatment of metastatic castration-resistant prostate cancer: Results from the VISION trial sub-study",
    "authors": "Krause BJ, et al.",
    "doi": "10.1200/JCO.2023.41.16_suppl.5046",
    "pmid": null,
    "sourceUrl": "https://ascopubs.org/doi/10.1200/JCO.2023.41.16_suppl.5046",
    "category": [
      "Dosimetria",
      "Dose absorvida tumoral",
      "Abstract"
    ],
    "clinicalTakeaway": "Abstract de congresso reportando dose absorvida tumoral no subestudo de dosimetria do VISION. Congress abstract — não é artigo completo.",
    "deep": {
      "objetivo": "Estimar a dose absorvida tumoral no subestudo de dosimetria do VISION.",
      "metodo": "Subestudo de dosimetria (coorte de 29 pacientes; 104 lesões analisadas no ciclo 1). Abstract ASCO 2023.",
      "achados": [
        "Dose absorvida tumoral média (todas as lesões): 6,5 Gy/GBq.",
        "Por sítio: osso 5,4 Gy/GBq; tecido linfático 9,7 Gy/GBq.",
        "(Valores de abstract de congresso.)"
      ],
      "interpretacao": "Quantificou a dose absorvida tumoral no regime do VISION. Congress abstract — valores preliminares, não revisados por pares no nível de artigo completo.",
      "limitacoes": "Abstract de congresso; coorte pequena de dosimetria."
    }
  },
  {
    "id": "therap-psma-fdg-pet-biomarkers-2022",
    "title": "TheraP — Biomarcadores por PSMA PET e FDG PET",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_1",
    "parentTrialName": "TheraP (ANZUP 1603)",
    "parentTrialPublication": "Hofman MS, et al. Lancet 2021;397:797-804 (NCT03392428)",
    "relationshipToParent": "Análise de biomarcadores (endpoint terciário pré-especificado) do ensaio randomizado fase II TheraP",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de biomarcador de imagem",
    "evidenceMaturity": "Análise revisada por pares",
    "year": 2022,
    "journal": "The Lancet Oncology",
    "titleOriginal": "PSMA and FDG-PET as predictive and prognostic biomarkers in patients given [177Lu]Lu-PSMA-617 versus cabazitaxel for metastatic castration-resistant prostate cancer (TheraP): a biomarker analysis from a randomised, open-label, phase 2 trial",
    "authors": "Buteau JP, et al.",
    "doi": "10.1016/S1470-2045(22)00605-2",
    "pmid": "36261050",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/36261050/",
    "category": [
      "Biomarcador",
      "PSMA PET",
      "FDG PET",
      "SUVmean",
      "Volume metabólico"
    ],
    "clinicalTakeaway": "Em análise pré-especificada do TheraP, SUVmean ≥10 no PSMA-PET associou-se a maior vantagem de resposta de PSA do 177Lu-PSMA-617 sobre o cabazitaxel (91% vs 47%; interação p ajustado 0,039), e MTV ≥200 mL no FDG-PET a menor resposta em ambos os braços. Desfecho de PSA em fase II; exige software quantitativo.",
    "collapsedSummary": "SUVmean alto no PSMA-PET associou-se a maior vantagem de resposta de PSA do 177Lu-PSMA-617 sobre o cabazitaxel. Desfecho de PSA, não de sobrevida, em subgrupos de ensaio fase II.",
    "deep": {
      "objetivo": "Avaliar parâmetros quantitativos do PSMA-PET (SUVmean) e do FDG-PET (volume tumoral metabólico, MTV) como biomarcadores preditivos e prognósticos de resposta de PSA ao 177Lu-PSMA-617 versus cabazitaxel no TheraP.",
      "metodo": "Endpoint terciário pré-especificado do TheraP (fase II randomizado, 11 centros na Austrália; mCRPC pós-docetaxel); n=200 (177Lu-PSMA-617 n=99; cabazitaxel n=101). Cortes pré-especificados: SUVmean ≥10 no PSMA-PET (testado como preditivo) e MTV ≥200 mL no FDG-PET (testado como prognóstico). Análise ITT por regressão logística; desfecho: resposta de PSA. Cutoff 20/jul/2020, seguimento mediano 18,4 m.",
      "achados": [
        "SUVmean ≥10 em 35% (35/99) do braço 177Lu-PSMA-617 e 30% (30/101) do braço cabazitaxel.",
        "SUVmean ≥10: resposta de PSA 91% (32/35) com 177Lu-PSMA-617 vs 47% (14/30) com cabazitaxel; OR 12,19 (IC95% 3,42–58,76).",
        "SUVmean <10: 52% (33/64) vs 32% (23/71); OR 2,22 (1,11–4,51). Interação tratamento×SUVmean: p ajustado=0,039.",
        "FDG-PET MTV ≥200 mL (30% de cada braço): resposta de PSA 38% (23/60) vs 56% (79/140) com MTV <200 mL, braços combinados; OR 0,44 (0,23–0,84); p ajustado=0,035."
      ],
      "interpretacao": "Segundo os autores, o SUVmean no PSMA-PET foi preditivo de maior probabilidade de resposta de PSA ao 177Lu-PSMA-617 do que ao cabazitaxel, e o MTV alto no FDG-PET associou-se a menor resposta independentemente do braço. O desfecho avaliado é resposta de PSA, não sobrevida; os achados vêm de subgrupos de um ensaio fase II.",
      "limitacoes": "Endpoint terciário em ensaio fase II, com subgrupos pequenos (35 e 30 pacientes com SUVmean ≥10) e IC amplos; desfecho restrito à resposta de PSA. Os autores ressaltam que os parâmetros quantitativos exigem software especializado, ainda não disponível na rotina da maioria das clínicas."
    },
    "analysis": {
      "populacao": "200 homens com mCRPC após docetaxel, aptos a cabazitaxel, randomizados 1:1 (177Lu-PSMA-617 n=99; cabazitaxel n=101).",
      "desenho_relacao": "Análise de biomarcador de endpoint terciário pré-especificado do ensaio fase II TheraP, com cortes pré-especificados.",
      "endpoints": "Associação de SUVmean (PSMA-PET) e MTV (FDG-PET) com resposta de PSA.",
      "estatistica": "ITT; regressão logística; teste de interação tratamento×SUVmean (p ajustado).",
      "cutoff_followup": "Cutoff 20/jul/2020; seguimento mediano 18,4 m (IQR 12,8–21,8).",
      "subgrupos": "SUVmean ≥10 vs <10; MTV ≥200 mL vs <200 mL.",
      "seguranca": null,
      "conclusao_autores": "SUVmean no PSMA-PET preditivo de resposta favorável ao 177Lu-PSMA-617 vs cabazitaxel; MTV alto no FDG-PET associado a menor resposta independentemente do tratamento."
    },
    "auditStatus": {
      "classification": "INCORRECT",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "therap-overall-survival-2024",
    "title": "TheraP — Sobrevida global (desfecho secundário)",
    "recordType": "trial_update",
    "parentUid": "lupsma_prostata_1",
    "parentTrialName": "TheraP (ANZUP 1603)",
    "parentTrialPublication": "Hofman MS, et al. Lancet 2021;397:797-804 (NCT03392428)",
    "relationshipToParent": "Desfecho secundário / seguimento maduro do TheraP",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Atualização de sobrevida global (desfecho secundário)",
    "evidenceMaturity": "Desfecho secundário revisado por pares",
    "year": 2024,
    "journal": "The Lancet Oncology",
    "titleOriginal": "Overall survival with [177Lu]Lu-PSMA-617 versus cabazitaxel in metastatic castration-resistant prostate cancer (TheraP): secondary outcomes of a randomised, open-label, phase 2 trial",
    "authors": "Hofman MS, et al.",
    "doi": "10.1016/S1470-2045(23)00529-6",
    "pmid": "38043558",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/38043558/",
    "category": [
      "Sobrevida global",
      "Seguimento de longo prazo",
      "Desfecho secundário"
    ],
    "clinicalTakeaway": "Com seguimento mediano de 35,7 m, a OS foi semelhante entre 177Lu-PSMA-617 e cabazitaxel (RMST 19,1 vs 19,6 m; p=0,77), com crossover pós-tratamento de 20–32%. Desfecho secundário de fase II: não demonstra superioridade nem equivalência formal de OS.",
    "collapsedSummary": "A OS foi semelhante entre 177Lu-PSMA-617 e cabazitaxel. Desfecho secundário de fase II, com crossover pós-tratamento: não demonstra superioridade nem equivalência formal.",
    "deep": {
      "objetivo": "Relatar a sobrevida global (desfecho secundário) com seguimento maduro no TheraP (177Lu-PSMA-617 vs cabazitaxel após docetaxel), além dos desfechos dos pacientes excluídos pelo PET de triagem.",
      "metodo": "Desfecho secundário do TheraP (fase II aberto, 11 centros na Austrália); 291 registrados, 200 randomizados após PSMA-PET e FDG-PET (177Lu-PSMA-617 n=99; cabazitaxel n=101). OS por ITT, resumida como tempo médio de sobrevida restrito (RMST, restrição de 36 m) por riscos não proporcionais. Seguimento mediano 35,7 m.",
      "achados": [
        "RMST: 19,1 m (IC95% 16,9–21,4) com 177Lu-PSMA-617 vs 19,6 m (17,4–21,8) com cabazitaxel; diferença −0,5 m (−3,7 a 2,7); p=0,77.",
        "Óbitos: 78% (77/99) com 177Lu-PSMA-617 vs 69% (70/101) com cabazitaxel.",
        "Após o tratamento do estudo, 32% do braço 177Lu-PSMA-617 recebeu cabazitaxel e 20% do braço cabazitaxel recebeu 177Lu-PSMA-617.",
        "Excluídos após PET (baixa expressão de PSMA ou discordância FDG): 27% (80/291); RMST 11,0 m (9,0–13,1) nos 61 com seguimento.",
        "Sem novos sinais de segurança com o seguimento mais longo."
      ],
      "interpretacao": "Não houve evidência de diferença de OS entre os braços; os autores consideram que os resultados apoiam o 177Lu-PSMA-617 como alternativa ao cabazitaxel em doença PSMA-positiva após docetaxel. OS é desfecho secundário. A OS mais curta nos excluídos pelo PET é descritiva (não randomizada).",
      "limitacoes": "Fase II com OS como desfecho secundário; crossover pós-tratamento (20–32%); comparação dos excluídos é observacional e com seguimento incompleto (61/80)."
    },
    "analysis": {
      "populacao": "200 randomizados (99 vs 101) de 291 registrados; mCRPC progressivo pós-docetaxel, PSMA-positivo sem lesões FDG+/PSMA−.",
      "desenho_relacao": "Desfecho secundário (OS) do ensaio fase II TheraP, com seguimento maduro; inclui análise descritiva dos excluídos pelo PET.",
      "endpoints": "OS (secundário).",
      "estatistica": "ITT; RMST com restrição de 36 m (riscos não proporcionais).",
      "cutoff_followup": "Seguimento mediano 35,7 m (IQR 31,1–39,2).",
      "subgrupos": "Excluídos pelo PET: 80/291; RMST 11,0 m nos 61 com seguimento.",
      "seguranca": "Sem novos sinais de segurança com seguimento mais longo.",
      "conclusao_autores": "Apoia 177Lu-PSMA-617 como alternativa ao cabazitaxel; sem evidência de diferença de OS entre os grupos."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "therap-ctdna-fraction-asco-2024",
    "title": "TheraP — Fração de ctDNA como preditor (abstract)",
    "recordType": "congress_abstract",
    "parentUid": "lupsma_prostata_1",
    "parentTrialName": "TheraP (ANZUP 1603)",
    "parentTrialPublication": "Hofman MS, et al. Lancet 2021;397:797-804 (NCT03392428)",
    "relationshipToParent": "Análise exploratória de ctDNA do TheraP apresentada em congresso",
    "publicationStatus": "Congress abstract",
    "analysisType": "Análise exploratória de biomarcador (ctDNA)",
    "evidenceMaturity": "Abstract de congresso — não é artigo completo",
    "year": 2024,
    "journal": "Journal of Clinical Oncology (ASCO Annual Meeting, suppl)",
    "titleOriginal": "Circulating tumour DNA fraction as a predictor of treatment efficacy in a randomized phase 2 trial of [177Lu]Lu-PSMA-617 (LuPSMA) versus cabazitaxel in metastatic castration-resistant prostate cancer (mCRPC) progressing after docetaxel (TheraP ANZUP 1603)",
    "authors": "Kwan EM, Hofman MS, et al.",
    "doi": "10.1200/JCO.2024.42.16_suppl.5055",
    "pmid": null,
    "sourceUrl": "https://ascopubs.org/doi/10.1200/JCO.2024.42.16_suppl.5055",
    "category": [
      "ctDNA",
      "Biomarcador",
      "Oncologia de precisão",
      "Abstract"
    ],
    "clinicalTakeaway": "Análise exploratória de fração de ctDNA apresentada em congresso. Congress abstract — evitar conclusões definitivas; necessita confirmação.",
    "deep": {
      "objetivo": "Avaliar a fração de ctDNA como preditor de eficácia no TheraP (177Lu-PSMA-617 vs cabazitaxel).",
      "metodo": "Análise exploratória de ctDNA apresentada em congresso (ASCO 2024).",
      "achados": [
        "Abstract de congresso — desfechos numéricos não extraídos de fonte primária direta nesta sessão (ver abstract oficial, JCO 2024 suppl, abstr 5055)."
      ],
      "interpretacao": "Análise exploratória de biomarcador (ctDNA). Congress abstract — evitar conclusões definitivas; necessita confirmação.",
      "limitacoes": "Abstract de congresso; valores não verificados em fonte primária direta nesta sessão."
    }
  },
  {
    "id": "psmafore-final-os-safety-2025",
    "title": "PSMAfore — Análise final de OS e segurança",
    "recordType": "trial_update",
    "parentUid": "lupsma_prostata_2",
    "parentTrialName": "PSMAfore",
    "parentTrialPublication": "Morris MJ, et al. Lancet 2024;404:1227-1239 (NCT04689828; PMID 39293462)",
    "relationshipToParent": "Análise final de OS (desfecho secundário-chave) e segurança do ensaio fase III PSMAfore",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise final de sobrevida global e segurança",
    "evidenceMaturity": "Análise final revisada por pares",
    "year": 2025,
    "journal": "Annals of Oncology",
    "titleOriginal": "Final overall survival and safety analyses of the phase III PSMAfore trial of [177Lu]Lu-PSMA-617 versus change of androgen receptor pathway inhibitor in taxane-naive patients with metastatic castration-resistant prostate cancer",
    "authors": "Fizazi K, et al.",
    "doi": "10.1016/j.annonc.2025.07.003",
    "pmid": "40680993",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/40680993/",
    "category": [
      "Sobrevida global",
      "Segurança",
      "Seguimento de longo prazo"
    ],
    "clinicalTakeaway": "Na análise final do PSMAfore, a OS não diferiu na ITT (24,5 vs 23,1 m; HR 0,91; P=0,20), com 60,3% de crossover no braço controle. O HR 0,59 ajustado por IPCW é análise suplementar; sua suposição não é verificável, embora os autores relatem apoio à sua adequação. Segurança sem novos sinais.",
    "collapsedSummary": "A OS não diferiu na análise ITT, com crossover elevado no controle. O ajuste IPCW é análise suplementar, com suposição não verificável, e não substitui o resultado ITT.",
    "deep": {
      "objetivo": "Relatar a análise final de sobrevida global (desfecho secundário-chave) e a segurança atualizada do 177Lu-PSMA-617 versus troca de ARPI no PSMAfore (mCRPC PSMA-positivo, taxane-naive, com progressão a um ARPI prévio).",
      "metodo": "Fase III internacional, aberto; n=468 (234 por braço). Crossover para 177Lu-PSMA-617 permitido após progressão radiográfica confirmada centralmente. Análise final planejada após ~297 óbitos (poder 80% para HR 0,72; α unilateral 0,025), por ITT; análises suplementares de ajuste do crossover (IPCW e RPSFT). EA ajustados por exposição (por 100 pessoas-ano de tratamento). Cutoff 1/jan/2025; mediana desde a randomização 34,27 m.",
      "achados": [
        "Crossover: 60,3% (141/234) do braço troca de ARPI recebeu 177Lu-PSMA-617 (75,4% dos com progressão confirmada), após mediana de 7,66 m.",
        "OS mediana (ITT): 24,48 m (IC95% 19,55–28,94) com 177Lu-PSMA-617 vs 23,13 m (19,61–25,53) com troca de ARPI; HR 0,91 (0,72–1,14); P=0,20. Óbitos: 60,7% vs 67,1% (299 no total).",
        "HR ajustado para crossover por IPCW (modelo completo): 0,59 (0,38–0,91); demais modelos IPCW 0,54–0,62. RPSFT: 0,84 (0,55–1,28).",
        "EA grau ≥3: 60,8 vs 85,1 e EA graves: 32,5 vs 49,9 por 100 pessoas-ano de tratamento (177Lu-PSMA-617 vs troca de ARPI).",
        "No braço 177Lu-PSMA-617: boca seca 59,5% (grau ≥3 em 2/227) e anemia 27,3% (grau ≥3 em 14/227); sem novos sinais de segurança."
      ],
      "interpretacao": "A OS não diferiu de forma estatisticamente significativa na análise ITT pré-especificada. Os autores atribuem esse resultado provavelmente ao crossover elevado; o benefício sugerido pelo ajuste IPCW é análise suplementar, dependente de suposições não verificáveis, e não substitui o resultado ITT. Perfil de segurança considerado favorável, sem novos sinais.",
      "limitacoes": "Crossover elevado e precoce; IPCW supõe ausência de confundidores não medidos e o RPSFT provavelmente não atendeu sua suposição; poder de 80% para OS, possivelmente reduzido pelo crossover; exclusão de pacientes com alterações de DDR elegíveis a outras terapias, sem testagem genômica obrigatória."
    },
    "analysis": {
      "populacao": "468 randomizados (234 vs 234); safety set 227 vs 232.",
      "desenho_relacao": "Análise final pré-planejada da OS (secundário-chave) e atualização de segurança do ensaio fase III PSMAfore.",
      "endpoints": "OS (secundário-chave); segurança (secundário).",
      "estatistica": "ITT (método pré-especificado); poder 80% para HR 0,72; ajustes de crossover suplementares por IPCW e RPSFT; EA ajustados por exposição.",
      "cutoff_followup": "Cutoff 1/jan/2025; mediana desde a randomização 34,27 m (26,9–42,2).",
      "subgrupos": "Crossover 141/234 (60,3%); mediana até crossover 7,66 m.",
      "seguranca": "EA grau ≥3 60,8 vs 85,1 e graves 32,5 vs 49,9 por 100 pessoas-ano de tratamento; boca seca 59,5%, anemia 27,3% com 177Lu-PSMA-617.",
      "conclusao_autores": "Sem diferença significativa de OS na ITT, provavelmente confundida pelo crossover; segurança favorável sem novos sinais."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "psmafore-hrqol-pain-skeletal-events-2025",
    "title": "PSMAfore — HRQoL, dor e eventos esqueléticos sintomáticos",
    "recordType": "secondary_publication",
    "parentUid": "lupsma_prostata_2",
    "parentTrialName": "PSMAfore",
    "parentTrialPublication": "Morris MJ, et al. Lancet 2024;404:1227-1239 (NCT04689828; PMID 39293462)",
    "relationshipToParent": "Análise de desfechos secundários (HRQoL, dor, SSE) do PSMAfore, no corte da 3ª análise interina de OS",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise secundária (HRQoL, dor, SSE)",
    "evidenceMaturity": "Análise secundária revisada por pares",
    "year": 2025,
    "journal": "The Lancet Oncology",
    "titleOriginal": "Health-related quality of life, pain, and symptomatic skeletal events with [177Lu]Lu-PSMA-617 in patients with progressive metastatic castration-resistant prostate cancer (PSMAfore): an open-label, randomised, phase 3 trial",
    "authors": "Fizazi K, et al.",
    "doi": "10.1016/S1470-2045(25)00189-5",
    "pmid": "40441170",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/40441170/",
    "category": [
      "HRQoL",
      "Dor",
      "Eventos esqueléticos sintomáticos"
    ],
    "clinicalTakeaway": "No PSMAfore, 177Lu-PSMA-617 retardou a piora do FACT-P (7,46 vs 4,27 m; HR 0,61), da dor (HR 0,72) e o primeiro evento esquelético sintomático (HR 0,41) vs troca de ARPI. Desfechos secundários de ensaio aberto, em corte interino.",
    "collapsedSummary": "177Lu-PSMA-617 retardou a piora do FACT-P e da dor e o primeiro evento esquelético sintomático vs troca de ARPI. Desfechos secundários de ensaio aberto, em corte interino.",
    "deep": {
      "objetivo": "Analisar em profundidade o tempo até piora de HRQoL e dor e o tempo até o primeiro evento esquelético sintomático (SSE) com 177Lu-PSMA-617 versus troca de ARPI no PSMAfore.",
      "metodo": "Desfechos secundários do PSMAfore (fase III, aberto, 74 centros em 14 países); mCRPC PSMA-positivo taxane-naive após uma progressão a ARPI; n=468 (234 por braço). Instrumentos: FACT-P, EQ-5D-5L, BPI-SF; análise ITT. Dados do cutoff da 3ª análise interina de OS (27/fev/2024); seguimento mediano ~24,1 m em ambos os braços.",
      "achados": [
        "Tempo até piora do FACT-P total: 7,46 m (IC95% 6,08–8,54) com 177Lu-PSMA-617 vs 4,27 m (3,45–4,50) com troca de ARPI; HR 0,61 (0,50–0,75).",
        "EQ-5D-5L (utilidade): 6,28 vs 3,88 m; HR 0,67 (0,54–0,82).",
        "Intensidade de dor (BPI-SF): 5,03 vs 3,65 m; HR 0,72 (0,59–0,88).",
        "Primeiro SSE: mediana não atingida com 177Lu-PSMA-617 vs 17,97 m com troca de ARPI; HR 0,41 (0,26–0,63).",
        "Anemia grau ≥3 (EA grau ≥3 mais comum): 6% (14/227) vs 7% (16/232); nenhum óbito relacionado ao tratamento com 177Lu-PSMA-617 e 1 com troca de ARPI (AVC)."
      ],
      "interpretacao": "Segundo os autores, o 177Lu-PSMA-617 pode retardar a piora dos desfechos relatados pelo paciente e prevenir SSE versus troca de ARPI. São desfechos secundários, sem efeito demonstrado sobre OS nesta publicação.",
      "limitacoes": "Ensaio aberto; desfechos secundários avaliados no corte da 3ª análise interina de OS. O resumo não detalha limitações."
    },
    "analysis": {
      "populacao": "468 randomizados (234 vs 234); safety set 227 vs 232.",
      "desenho_relacao": "Análise de desfechos secundários (HRQoL, dor, SSE) do ensaio fase III PSMAfore, no cutoff da 3ª análise interina de OS.",
      "endpoints": "Tempo até piora de FACT-P, EQ-5D-5L e BPI-SF; tempo até primeiro SSE.",
      "estatistica": "ITT; HR com IC95%.",
      "cutoff_followup": "Cutoff 27/fev/2024; seguimento mediano 24,11 vs 24,13 m.",
      "subgrupos": null,
      "seguranca": "Anemia grau ≥3 6% vs 7%; 0 vs 1 óbito relacionado ao tratamento.",
      "conclusao_autores": "177Lu-PSMA-617 pode retardar a piora de desfechos relatados pelo paciente e prevenir SSE vs troca de ARPI."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "enzap-protocol-2021",
    "title": "ENZA-p — Protocolo do estudo",
    "recordType": "protocol",
    "parentUid": "lupsma_prostata_5",
    "parentTrialName": "ENZA-p (ANZUP 1901)",
    "parentTrialPublication": "Emmett L, et al. Lancet Oncol 2024;25:563-571 (NCT04419402; PMID 38621400)",
    "relationshipToParent": "Protocolo do ensaio ENZA-p",
    "publicationStatus": "Peer-reviewed protocol article",
    "analysisType": "Protocolo de estudo",
    "evidenceMaturity": "Protocolo — sem resultados de eficácia",
    "year": 2021,
    "journal": "BJU International",
    "titleOriginal": "ENZA-p trial protocol: a randomized phase II trial using prostate-specific membrane antigen as a therapeutic target and prognostic indicator in men with metastatic castration-resistant prostate cancer treated with enzalutamide (ANZUP 1901)",
    "authors": "Emmett L, et al.",
    "doi": "10.1111/bju.15491",
    "pmid": "34028967",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/34028967/",
    "category": [
      "Protocolo",
      "Desenho do estudo"
    ],
    "clinicalTakeaway": "Protocolo descrevendo racional, desenho e endpoints do ENZA-p. Sem dados de eficácia.",
    "deep": {
      "objetivo": "Descrever o protocolo do ENZA-p: atividade e segurança do 177Lu-PSMA-617 adicionado à enzalutamida em mCRPC de alto risco de progressão precoce; biomarcadores prognósticos/preditivos.",
      "metodo": "Protocolo de ensaio fase II randomizado (1:1), n=160 planejado; desfecho primário PSA-PFS.",
      "achados": [
        "Artigo de protocolo — sem dados de eficácia. Poder de 80% para detectar HR 0,625 (PSA-PFS; mediana esperada de 5 m com enzalutamida isolada)."
      ],
      "interpretacao": "Descreve racional, desenho e endpoints; hipótese de sinergia entre 177Lu-PSMA-617 e enzalutamida. Sem resultados de eficácia.",
      "limitacoes": "Protocolo; sem dados de eficácia."
    }
  },
  {
    "id": "enzap-os-hrqol-2025",
    "title": "ENZA-p — OS e qualidade de vida (seguimento mais longo)",
    "recordType": "trial_update",
    "parentUid": "lupsma_prostata_5",
    "parentTrialName": "ENZA-p (ANZUP 1901)",
    "parentTrialPublication": "Emmett L, et al. Lancet Oncol 2024;25:563-571 (NCT04419402; PMID 38621400)",
    "relationshipToParent": "Desfechos secundários-chave pré-especificados (OS, HRQoL) do ENZA-p com seguimento mais longo",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Desfechos secundários / seguimento mais longo",
    "evidenceMaturity": "Desfechos secundários revisados por pares",
    "year": 2025,
    "journal": "The Lancet Oncology",
    "titleOriginal": "Overall survival and quality of life with [177Lu]Lu-PSMA-617 plus enzalutamide versus enzalutamide alone in metastatic castration-resistant prostate cancer (ENZA-p): secondary outcomes from a multicentre, open-label, randomised, phase 2 trial",
    "authors": "Emmett L, et al.",
    "doi": "10.1016/S1470-2045(25)00009-9",
    "pmid": "39956124",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/39956124/",
    "category": [
      "Sobrevida global",
      "HRQoL",
      "Seguimento mais longo"
    ],
    "clinicalTakeaway": "No ENZA-p (fase II), adicionar 177Lu-PSMA-617 à enzalutamida associou-se a maior OS (34 vs 26 m; HR 0,55) e a maior tempo sem deterioração de função física e QoL, com mais xerostomia. Desfechos secundários: os autores pedem confirmação em fase III.",
    "collapsedSummary": "Adicionar 177Lu-PSMA-617 à enzalutamida associou-se a maior OS e a melhora de alguns aspectos de HRQoL, com mais xerostomia. Desfechos secundários de fase II; os autores pedem fase III.",
    "deep": {
      "objetivo": "Reportar os desfechos secundários-chave de sobrevida global e qualidade de vida relacionada à saúde (HRQoL), com seguimento mais longo, no ENZA-p (enzalutamida ± 177Lu-PSMA-617 em mCRPC de alto risco).",
      "metodo": "Fase II randomizado, aberto, 15 hospitais na Austrália; mCRPC sem docetaxel/ARPI prévio para mCRPC, PSMA-PET positivo e ≥2 fatores de risco para progressão precoce com enzalutamida. n=162 (enzalutamida n=79; enzalutamida + 177Lu-PSMA-617 adaptativo, 2 ou 4 doses de 7,5 GBq, n=83). OS e HRQoL (EORTC QLQ-C30; sobrevida livre de deterioração com piora ≥10 pontos, morte, progressão clínica ou descontinuação) pré-especificados, por ITT. Seguimento mediano 34 m.",
      "achados": [
        "OS mediana: 34 m (IC95% 30–37) com enzalutamida + 177Lu-PSMA-617 vs 26 m (23–31) com enzalutamida; HR 0,55 (0,36–0,84); log-rank p=0,0053. Óbitos: 52% (43/83) vs 67% (53/79).",
        "Sobrevida livre de deterioração — função física: 10,64 vs 3,42 m; HR 0,51 (0,36–0,72); p<0,0001. Saúde global/QoL: 8,71 vs 3,32 m; HR 0,47 (0,33–0,67); p=0,0001.",
        "Escores médios até a progressão favoreceram a combinação para dor (diferença 7,3; p=0,012) e fadiga (5,9; p=0,016).",
        "Xerostomia autorrelatada mais frequente com a combinação: 74% (58/78) vs 57% (43/75); p=0,039.",
        "EA grau 3–5: 46% (37/81) com a combinação vs 44% (35/79) com enzalutamida; nenhum óbito atribuído ao tratamento."
      ],
      "interpretacao": "A adição de 177Lu-PSMA-617 à enzalutamida associou-se a maior OS e a melhora de alguns aspectos de HRQoL, à custa de mais xerostomia. São desfechos secundários de um ensaio fase II; os autores consideram que os achados justificam avaliação em fase III.",
      "limitacoes": "Fase II aberto, com OS e HRQoL como desfechos secundários (n=162), em 15 centros na Austrália."
    },
    "analysis": {
      "populacao": "162 randomizados (79 enzalutamida; 83 enzalutamida + 177Lu-PSMA-617); HRQoL respondida por 154/162 (95%).",
      "desenho_relacao": "Desfechos secundários-chave pré-especificados (OS, HRQoL) do ensaio fase II ENZA-p, com seguimento mais longo.",
      "endpoints": "OS; sobrevida livre de deterioração (função física; saúde global/QoL); escores de sintomas.",
      "estatistica": "ITT; log-rank estratificado; HR com IC95%.",
      "cutoff_followup": "Seguimento mediano 34 m (IQR 29–39); 96 óbitos.",
      "subgrupos": null,
      "seguranca": "EA grau 3–5 44% vs 46%; sem óbitos atribuídos ao tratamento; xerostomia 57% vs 74%.",
      "conclusao_autores": "177Lu-PSMA-617 + enzalutamida associou-se a melhor sobrevida e alguns aspectos de HRQoL; justifica fase III."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "enzap-baseline-psma-pet-biomarker-2025",
    "title": "ENZA-p — PET PSMA basal (TTV e SUVmean) como biomarcador",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_5",
    "parentTrialName": "ENZA-p (ANZUP 1901)",
    "parentTrialPublication": "Emmett L, et al. Lancet Oncol 2024;25:563-571 (NCT04419402; PMID 38621400)",
    "relationshipToParent": "Subestudo pré-especificado de biomarcador PSMA-PET basal do ENZA-p",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de biomarcador de imagem",
    "evidenceMaturity": "Análise revisada por pares",
    "year": 2025,
    "journal": "The Lancet Oncology",
    "titleOriginal": "Prognostic and predictive value of baseline PSMA-PET total tumour volume and SUVmean in metastatic castration-resistant prostate cancer in ENZA-p (ANZUP1901): a substudy from a multicentre, open-label, randomised, phase 2 trial",
    "authors": "Emmett L, et al.",
    "doi": "10.1016/S1470-2045(25)00339-0",
    "pmid": "40752515",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/40752515/",
    "category": [
      "PSMA PET",
      "Biomarcador",
      "Volume tumoral total",
      "SUVmean"
    ],
    "clinicalTakeaway": "Em subestudo pré-especificado do ENZA-p, PSMA-TTV basal acima da mediana associou-se a menor OS com enzalutamida isolada (20 vs 39 m; HR 0,23), com efeito atenuado na combinação (interação p=0,0078); SUVmean não se associou a OS.",
    "collapsedSummary": "PSMA-TTV basal acima da mediana associou-se a menor OS com enzalutamida isolada, com efeito atenuado pela adição de 177Lu-PSMA-617. O sinal preditivo vem de teste de interação em fase II.",
    "deep": {
      "objetivo": "Avaliar o volume tumoral total (PSMA-TTV) e o SUVmean do PSMA-PET basal como biomarcadores prognósticos e preditivos de OS com enzalutamida isolada ou combinada a 177Lu-PSMA-617 no ENZA-p.",
      "metodo": "Subestudo pré-especificado do ENZA-p (fase II randomizado, 15 hospitais na Austrália); desfecho primário do subestudo: OS. n=160 dos 162 randomizados que receberam tratamento (enzalutamida n=79; combinação n=81), analisados por tratamento recebido. PSMA-TTV e SUVmean quantificados por software semiautomático; limiares: mediana de PSMA-TTV e quartil superior de SUVmean (Q4 vs Q1–3). Kaplan-Meier e Cox. Cutoff final 31/jul/2024; seguimento mediano 34 m; 96 eventos de OS.",
      "achados": [
        "PSMA-TTV basal mediano 234 mL (IQR 76–687); SUVmean mediano 7,7 (6,5–9,8).",
        "Braço enzalutamida — PSMA-TTV abaixo vs acima da mediana: OS mediana 39 vs 20 m; HR 0,23 (0,13–0,42); p<0,0001.",
        "Braço enzalutamida + 177Lu-PSMA-617 — abaixo vs acima da mediana: 35 vs 28 m; HR 0,66 (0,36–1,21); p=0,18.",
        "Interação PSMA-TTV × tratamento para OS: p=0,0078.",
        "SUVmean Q4 vs Q1–3: HR 0,84 (0,44–1,60; p=0,59) com enzalutamida e 0,80 (0,38–1,68; p=0,56) com a combinação; interação p=0,88."
      ],
      "interpretacao": "Os autores concluem que o PSMA-TTV basal é prognóstico para OS e preditivo de benefício de OS com a adição de 177Lu-PSMA-617; o sinal preditivo vem de teste de interação em subestudo de fase II, com o efeito prognóstico concentrado no braço enzalutamida. O SUVmean não mostrou associação com OS.",
      "limitacoes": "Subestudo de fase II (n=160) analisado por tratamento recebido, com limiares derivados da própria coorte (mediana, quartil); exige quantificação por software semiautomático. O resumo não detalha outras limitações."
    },
    "analysis": {
      "populacao": "160/162 randomizados que receberam tratamento (79 enzalutamida; 81 combinação).",
      "desenho_relacao": "Subestudo pré-especificado de biomarcador de imagem do ensaio fase II ENZA-p.",
      "endpoints": "OS (primário do subestudo); PSA-PFS.",
      "estatistica": "Kaplan-Meier, Cox, teste de interação; por tratamento recebido; limiares mediana (TTV) e Q4 (SUVmean).",
      "cutoff_followup": "Cutoff 31/jul/2024; seguimento mediano 34 m (IQR 29–39); 96 eventos.",
      "subgrupos": "PSMA-TTV abaixo/acima de 234 mL; SUVmean Q4 vs Q1–3, por braço.",
      "seguranca": null,
      "conclusao_autores": "PSMA-TTV basal prognóstico e preditivo de benefício de OS com 177Lu-PSMA-617 + enzalutamida; SUVmean não prognóstico com a combinação."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "enzap-interim-psma-ttv-2026",
    "title": "ENZA-p — Volume tumoral total no PSMA PET interino",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_5",
    "parentTrialName": "ENZA-p (ANZUP 1901)",
    "parentTrialPublication": "Emmett L, et al. Lancet Oncol 2024;25:563-571 (NCT04419402; PMID 38621400)",
    "relationshipToParent": "Subestudo de biomarcador PSMA-PET interino do ENZA-p",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de biomarcador de imagem (interino)",
    "evidenceMaturity": "Análise revisada por pares",
    "year": 2026,
    "journal": "European Urology",
    "titleOriginal": "Prognostic Value of Interim PSMA-PET Total Tumor Volume for Overall Survival Within ENZA-p, A Randomized Phase 2 Trial of Enzalutamide Versus Enzalutamide Plus [177Lu]Lu-PSMA-617 (ANZUP1901)",
    "authors": "Emmett L, et al.",
    "doi": "10.1016/j.eururo.2026.03.026",
    "pmid": "41956861",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/41956861/",
    "category": [
      "PSMA PET",
      "Volume tumoral total",
      "Sobrevida global",
      "Biomarcador"
    ],
    "clinicalTakeaway": "Subestudo de imagem sugerindo valor prognóstico do PSMA-PET total tumor volume interino (3 meses) para OS. Necessita confirmação prospectiva.",
    "deep": {
      "objetivo": "Avaliar o PSMA-TTV de 3 meses (interino) como biomarcador prognóstico de OS no ENZA-p.",
      "metodo": "Subestudo do ENZA-p; n=152/162 (94%) com PSMA-PET de 3 meses.",
      "achados": [
        "PSMA-TTV basal mediano 230 mL; aos 3 meses 103 mL; OS mediana 27 m.",
        "Aumento vs redução do PSMA-TTV: HR 2,52 (1,65–3,85); p<0,0001; sobrevida em 2 anos 30% vs 67%.",
        "PSMA-TTV residual de 3 meses acima vs abaixo da mediana: HR 3,76 (2,39–5,92); p<0,0001; 2 anos 34% vs 76%."
      ],
      "interpretacao": "O PSMA-TTV aos 3 meses foi prognóstico de OS independentemente do tratamento e da resposta de PSA; sugere valor de critérios de resposta interina (a validar).",
      "limitacoes": "Não detalhadas no abstract."
    }
  },
  {
    "id": "splash-lead-in-dosimetry-safety-efficacy-2024",
    "title": "SPLASH — Coorte lead-in: dosimetria, segurança e eficácia inicial",
    "recordType": "substudy",
    "parentUid": "lupsma_prostata_3",
    "parentTrialName": "SPLASH (177Lu-PNT2002)",
    "parentTrialPublication": "Ensaio fase III SPLASH — NCT04647526",
    "relationshipToParent": "Coorte lead-in de braço único (segurança e dosimetria), anterior à porção randomizada do ensaio fase III SPLASH; não é a publicação primária da fase randomizada",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Coorte lead-in (dosimetria, segurança, eficácia preliminar)",
    "evidenceMaturity": "Coorte lead-in revisada por pares",
    "year": 2024,
    "journal": "Frontiers in Oncology",
    "titleOriginal": "Initial clinical experience with [177Lu]Lu-PNT2002 radioligand therapy in metastatic castration-resistant prostate cancer: dosimetry, safety, and efficacy from the lead-in cohort of the SPLASH trial",
    "authors": "Hansen AR, et al.",
    "doi": "10.3389/fonc.2024.1483953",
    "pmid": "39839782",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/39839782/",
    "category": [
      "Dosimetria",
      "Segurança",
      "Eficácia preliminar",
      "177Lu-PNT2002"
    ],
    "clinicalTakeaway": "Na coorte lead-in de braço único do SPLASH (n=27), 177Lu-PNT2002 6,8 GBq × 4 ciclos teve dose renal cumulativa média estimada de 19,9 Gy, abaixo do limiar de 23 Gy, mas 6 participantes tiveram dose renal cumulativa prevista acima desse limiar; toxicidade majoritariamente grau 1–2 (grau ≥3 relacionado em 7,4%); PSA50 42,3% e rPFS mediana 11,5 m são dados preliminares, sem comparador.",
    "collapsedSummary": "A dose renal média ficou abaixo do limiar de referência, com dose prevista acima dele em alguns participantes, e toxicidade sobretudo grau 1–2. Braço único: eficácia preliminar, sem comparador.",
    "deep": {
      "objetivo": "Avaliar dosimetria tecidual e segurança e eficácia preliminares do 177Lu-PNT2002 (6,8 GBq a cada 8 semanas, até 4 ciclos) na porção lead-in de braço único do SPLASH, antes da fase randomizada, confirmando que a atividade planejada não excedia tolerâncias de dose pré-especificadas.",
      "metodo": "Coorte lead-in prospectiva, aberta, braço único, 12 centros na América do Norte; n=27 (mCRPC com progressão após um ARPI, sem quimioterapia para mCRPC, PSMA-PET positivo). Dosimetria planar em 27 e híbrida planar+SPECT/CT em 7; dose cumulativa extrapolada do ciclo 1. Análise descritiva; rPFS e ORR por revisão central independente cega.",
      "achados": [
        "19/27 (70,4%) completaram os 4 ciclos.",
        "Dose específica média: glândulas lacrimais 1,2 Gy/GBq; rins 0,73 Gy/GBq; lesões tumorais 4,3 Gy/GBq (21 lesões em 7 pacientes). Dose cumulativa estimada (27,2 GBq): tumor 117 Gy, rins 19,9 Gy, medula 0,9 Gy; 6/27 (22,2%) com dose renal extrapolada >23 Gy, sem sinais de segurança adicionais.",
        "TEAE grau ≥3 em 7/27 (25,9%), relacionados ao tratamento em 2/27 (7,4%: anemia; trombocitopenia e neutropenia em um). Sem EA grave, descontinuação ou óbito relacionados; 1 óbito por CIVD considerado não relacionado.",
        "PSA50 42,3% (11/26; confirmado em 9, 34,6%); ORR confirmada 50% (5/10 com doença avaliável); rPFS mediana 11,5 m (IC95% 9,2–19,1); OS mediana 20,8 m (IC95% 11,3–não avaliável), seguimento mediano de sobrevida 19,9 m."
      ],
      "interpretacao": "Dados de fase lead-in, descritivos e sem comparador, compatíveis com perfil dosimétrico e de segurança aceitável para o regime de 6,8 GBq × 4 ciclos e que sustentaram a passagem à fase randomizada. Os dados de eficácia são preliminares e não permitem inferência comparativa.",
      "limitacoes": "Amostra pequena e braço único limitam a interpretação de rPFS e OS; dose cumulativa extrapolada do ciclo 1 (provável superestimação tumoral); dosimetria planar isolada na maioria e SPECT/CT em apenas 7 pacientes, com potencial superestimação de doses em órgãos; limiar renal de 23 Gy derivado de radioterapia externa."
    },
    "analysis": {
      "populacao": "27 participantes com mCRPC PSMA-positivo, progressão após um ARPI, sem quimioterapia para mCRPC; 34 triados; América do Norte.",
      "desenho_relacao": "Porção lead-in (segurança e dosimetria) de braço único do fase III SPLASH, anterior à porção randomizada; não é a publicação do ensaio randomizado.",
      "endpoints": "Dosimetria, segurança, rPFS (BICR), OS, ORR, resposta de PSA.",
      "estatistica": "Descritiva; alvo de 25 participantes; Kaplan-Meier para OS e Kaplan-Meier reverso para seguimento.",
      "cutoff_followup": "Data de corte não informada; seguimento mediano de imagem 9,2 m e de sobrevida 19,9 m.",
      "subgrupos": "6/27 com dose renal cumulativa extrapolada >23 Gy, sem sinais de segurança adicionais.",
      "seguranca": "TEAE grau ≥3 25,9% (relacionados 7,4%); sem EA grave, descontinuação ou óbito relacionados; boca seca 22,2% (G1).",
      "conclusao_autores": "Perfil favorável de dosimetria e segurança e eficácia preliminar promissora; eficácia em avaliação na porção randomizada."
    },
    "auditStatus": {
      "classification": "INCORRECT",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "splash-primary-analysis-esmo-2024",
    "title": "SPLASH — Análise primária fase III (press release / ESMO 2024)",
    "recordType": "press_release",
    "parentUid": "lupsma_prostata_3",
    "parentTrialName": "SPLASH (177Lu-PNT2002)",
    "parentTrialPublication": "Ensaio fase III SPLASH — NCT04647526",
    "relationshipToParent": "Análise primária do ensaio fase III SPLASH",
    "publicationStatus": "Press release — dados não revisados por pares",
    "analysisType": "Análise primária apresentada em congresso (press release)",
    "evidenceMaturity": "Press release / dados preliminares — não revisados por pares",
    "year": 2024,
    "journal": "Lantheus press release / ESMO 2024",
    "titleOriginal": "Lantheus Presents Results from the Primary Analysis of Phase 3 Pivotal SPLASH Trial in PSMA-Positive Metastatic Castration-Resistant Prostate Cancer",
    "authors": null,
    "doi": null,
    "pmid": null,
    "sourceUrl": "https://lantheusholdings.gcs-web.com/news-releases/news-release-details/lantheus-presents-results-primary-analysis-phase-3-pivotal",
    "category": [
      "Press release",
      "rPFS",
      "Análise primária"
    ],
    "clinicalTakeaway": "Resultados primários comunicados via press release / apresentação em congresso. Dados preliminares, NÃO revisados por pares; necessita confirmação em artigo completo. Marcado como press release.",
    "deep": {
      "objetivo": "Comunicar os resultados da análise primária fase III do SPLASH (177Lu-PNT2002) em mCRPC PSMA-positivo.",
      "metodo": "Press release / apresentação em congresso (ESMO 2024). Dados não revisados por pares.",
      "achados": [
        "Press release — dados preliminares; nenhum valor numérico é reproduzido aqui (sem números além do comunicado e sem fonte revisada por pares)."
      ],
      "interpretacao": "Resultados primários comunicados publicamente; aguardam publicação em artigo completo revisado por pares. NÃO interpretar como evidência definitiva.",
      "limitacoes": "Press release; dados preliminares, não revisados por pares."
    }
  },
  {
    "id": "lupsma-2018-primary",
    "title": "LuPSMA trial (Hofman 2018) — fase II em mCRPC",
    "recordType": "primary_trial",
    "parentUid": null,
    "parentTrialName": "LuPSMA trial (Hofman 2018)",
    "parentTrialPublication": null,
    "relationshipToParent": "Estudo principal (grupo auto-contido — fora do database de 40 campos)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Ensaio prospectivo fase 2, single-arm",
    "evidenceMaturity": "Ensaio fase 2 revisado por pares",
    "year": 2018,
    "journal": "The Lancet Oncology",
    "titleOriginal": "[177Lu]-PSMA-617 radionuclide treatment in patients with metastatic castration-resistant prostate cancer (LuPSMA trial): a single-centre, single-arm, phase 2 study",
    "authors": "Hofman MS, et al.",
    "doi": "10.1016/S1470-2045(18)30198-0",
    "pmid": "29752180",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/29752180/",
    "category": [
      "177Lu-PSMA-617",
      "mCRPC",
      "Fase II"
    ],
    "clinicalTakeaway": "Estudo prospectivo fase 2 (single-arm) que ajudou a estabelecer a atividade clínica e a segurança do 177Lu-PSMA-617 antes dos ensaios randomizados maiores.",
    "deep": {
      "objetivo": "Avaliar segurança, eficácia e qualidade de vida do 177Lu-PSMA-617 em mCRPC com progressão após terapias-padrão.",
      "metodo": "Ensaio fase 2 single-arm, single-center; n=30 tratados.",
      "achados": [
        "Declínio de PSA ≥50%: 57% (17/30; IC95% 37–75).",
        "Resposta objetiva (doença nodal/visceral mensurável): 82% (14/17).",
        "Trombocitopenia G3–4: 13% (4/30); boca seca G1: 87%; melhora de saúde global ≥10 pontos: 37%.",
        "Sem óbitos relacionados ao tratamento."
      ],
      "interpretacao": "Altas taxas de resposta, baixa toxicidade e redução de dor apoiaram a realização de ensaios randomizados. Fase 2 de braço único.",
      "limitacoes": "Estudo de braço único, centro único e pequeno."
    }
  },
  {
    "id": "lupsma-2018-dosimetry-2019",
    "title": "LuPSMA trial — Dosimetria tumoral e resposta de PSA",
    "recordType": "substudy",
    "parentUid": null,
    "parentCardId": "lupsma-2018-primary",
    "parentTrialName": "LuPSMA trial (Hofman 2018)",
    "parentTrialPublication": "Hofman MS, et al. Lancet Oncol 2018;19:825-833 (PMID 29752180)",
    "relationshipToParent": "Análise dosimétrica correlacional dos 30 pacientes do ensaio prospectivo LuPSMA (ACTRN12615000912583)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de dosimetria tumoral",
    "evidenceMaturity": "Subestudo revisado por pares",
    "year": 2019,
    "journal": "Journal of Nuclear Medicine",
    "titleOriginal": "Dosimetry of 177Lu-PSMA-617 in Metastatic Castration-Resistant Prostate Cancer: Correlations Between Pretherapeutic Imaging and Whole-Body Tumor Dosimetry with Treatment Outcomes",
    "authors": "Violet J, et al.",
    "doi": "10.2967/jnumed.118.219352",
    "pmid": "30291192",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/30291192/",
    "category": [
      "Dosimetria",
      "Dose absorvida tumoral",
      "Resposta de PSA"
    ],
    "clinicalTakeaway": "Em 30 pacientes do LuPSMA trial, maior dose tumoral de corpo inteiro associou-se a resposta de PSA (14,1 vs 9,6 Gy); apenas 1 de 11 pacientes com <10 Gy teve PSA50. Associação correlacional, sem validação prospectiva de dosagem guiada por dosimetria.",
    "collapsedSummary": "Maior dose tumoral de corpo inteiro associou-se a resposta de PSA. Associação correlacional em amostra pequena; a dosagem guiada por dosimetria não foi testada.",
    "deep": {
      "objetivo": "Determinar a dosimetria do 177Lu-PSMA-617 e suas correlações com parâmetros do 68Ga-PSMA-11 PET pré-terapêutico e com a resposta de PSA.",
      "metodo": "Análise dosimétrica nos 30 pacientes de um ensaio clínico prospectivo (ACTRN12615000912583); SPECT/CT quantitativo a 4, 24 e 96 h após a terapia, dosimetria em nível de voxel; definida uma dose tumoral de corpo inteiro; análises de correlação com PSA em 12 semanas.",
      "achados": [
        "Doses médias: rins 0,39; submandibulares 0,44; parótidas 0,58; fígado 0,1; baço 0,06; medula 0,11 (unidade relatada no resumo como Gy/MBq — conferir no texto completo).",
        "Dose tumoral de corpo inteiro mediana 11,55 Gy; mediana 14,1 Gy nos pacientes com queda de PSA ≥50% vs 9,6 Gy nos demais (p<0,01).",
        "Entre 11 pacientes com dose tumoral <10 Gy, apenas 1 atingiu queda de PSA ≥50%.",
        "SUVmean tumoral no PSMA PET correlacionou-se com a dose média (r=0,62); maior volume tumoral associou-se a menor dose em parótidas (r=-0,41) e rins (r=-0,43)."
      ],
      "interpretacao": "Associação (não causal) entre maior dose tumoral estimada e resposta de PSA, em análise correlacional de 30 pacientes; os autores veem racional para dosagem individualizada, hipótese ainda não testada nesta análise.",
      "limitacoes": "Amostra pequena (n=30); análise correlacional; resumo não detalha limitações, ciclo avaliado nem se a análise era pré-especificada; unidade 'Gy/MBq' do resumo não pôde ser conferida (texto completo indisponível)."
    },
    "analysis": {
      "populacao": "30 pacientes com mCRPC e alta expressão de PSMA tratados no ensaio prospectivo ACTRN12615000912583.",
      "desenho_relacao": "Análise dosimétrica correlacional nos pacientes do ensaio prospectivo LuPSMA; pré-especificação não informada.",
      "endpoints": "Doses absorvidas em órgãos e tumor; correlação com resposta de PSA em 12 semanas e com parâmetros do PSMA PET.",
      "estatistica": "Dosimetria voxel (SPECT/CT 4/24/96 h); correlações (r) e comparação de medianas.",
      "cutoff_followup": "PSA em 12 semanas; data de corte não informada.",
      "subgrupos": "<10 Gy (n=11): 1 com PSA50. Correlações inversas volume tumoral × dose em parótidas/rins; massa corporal × dose parotídea.",
      "seguranca": null,
      "conclusao_autores": "Doses tumorais elevadas, correlação significativa dose tumoral × resposta de PSA; <10 Gy improvável PSA50; racional para dosagem individualizada."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "lupsma-2018-long-term-retreatment-2020",
    "title": "LuPSMA trial — Seguimento prolongado e retratamento",
    "recordType": "trial_update",
    "parentUid": null,
    "parentCardId": "lupsma-2018-primary",
    "parentTrialName": "LuPSMA trial (Hofman 2018)",
    "parentTrialPublication": "Hofman MS, et al. Lancet Oncol 2018;19:825-833 (PMID 29752180)",
    "relationshipToParent": "Coorte expandida e análise de retratamento do ensaio fase 2",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Seguimento de longo prazo e retratamento",
    "evidenceMaturity": "Análise revisada por pares",
    "year": 2020,
    "journal": "Journal of Nuclear Medicine",
    "titleOriginal": "Long-Term Follow-Up and Outcomes of Retreatment in an Expanded 50-Patient Single-Center Phase II Prospective Trial of 177Lu-PSMA-617 Theranostics in Metastatic Castration-Resistant Prostate Cancer",
    "authors": "Violet J, et al.",
    "doi": "10.2967/jnumed.119.236414",
    "pmid": "31732676",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/31732676/",
    "category": [
      "Seguimento de longo prazo",
      "Retratamento",
      "Rechallenge"
    ],
    "clinicalTakeaway": "Com 50 pacientes e seguimento mediano de 31,4 m, PSA50 foi 64% e OS mediana 13,3 m; no retratamento de 15 respondedores prévios, 73% tiveram PSA50 — dado descritivo, em subgrupo selecionado e sem comparação randomizada.",
    "collapsedSummary": "A coorte expandida confirmou alta resposta de PSA e toxicidade majoritariamente leve; no retratamento, 73% tiveram PSA50. Dados descritivos, em subgrupo selecionado e sem comparação randomizada.",
    "deep": {
      "objetivo": "Relatar desfechos de longo prazo do ensaio fase 2 LuPSMA ampliado para 50 pacientes (30 originais + 20 de extensão) e descrever os desfechos de terapias sistêmicas subsequentes, incluindo retratamento com 177Lu-PSMA.",
      "metodo": "Fase 2 prospectivo, centro único, braço único; n=50 (75 triados) com mCRPC PSMA-ávido e tratamento prévio extenso (docetaxel 84%, cabazitaxel 48%, abiraterona/enzalutamida 92%; PSADT mediano 2,3 m); até 4 ciclos a cada 6 semanas (média 7,5 GBq/ciclo); seguimento mediano 31,4 m.",
      "achados": [
        "Queda de PSA ≥50%: 64% (32/50; IC95% 50–77); ≥80%: 44% (22/50). Resposta objetiva RECIST 56% (15/27).",
        "OS mediana 13,3 m (IC95% 10,5–18,7); 18,4 m (IC95% 13,8–23,8) nos pacientes com queda de PSA ≥50% (comparação entre respondedores e não respondedores).",
        "Toxicidade: boca seca G1–2 66%, náusea G1–2 48%, trombocitopenia G3–4 10%, anemia G3 10%.",
        "Na progressão após resposta, 15 (30%) receberam retratamento (mediana 2 ciclos): queda de PSA ≥50% em 11 (73%); com outras terapias sistêmicas, 4/21 (19%). Sem EA inesperado no retratamento."
      ],
      "interpretacao": "A coorte expandida é consistente com o relato inicial (altas taxas de resposta de PSA e toxicidade majoritariamente leve). As respostas ao retratamento ocorreram em subgrupo selecionado de respondedores prévios e a comparação com outras terapias não é randomizada; são dados descritivos e geradores de hipótese.",
      "limitacoes": "Centro único e braço único; retratamento em pequeno subgrupo selecionado (n=15) e comparação não randomizada com outras terapias; limitações não enumeradas no resumo (texto completo não disponível nas fontes)."
    },
    "analysis": {
      "populacao": "50 pacientes com mCRPC PSMA-ávido extensamente pré-tratados (30 do ensaio original + 20 de extensão).",
      "desenho_relacao": "Atualização de longo prazo do fase 2 LuPSMA com coorte de extensão; análise descritiva de terapias subsequentes/retratamento.",
      "endpoints": "PSA (PCWG2), toxicidade (CTCAE 4.03), imagem, HRQoL, PFS, OS.",
      "estatistica": "Proporções e medianas com IC95%; variação dos escores de dor (BPI) com IC95% e valor de P (P = 0,001 e P = 0,013); OS significativamente maior nos pacientes com declínio de PSA ≥50%.",
      "cutoff_followup": "Seguimento mediano 31,4 m; data de corte não informada.",
      "subgrupos": "Respondedores PSA50: OS 18,4 m. Retratamento (n=15): PSA50 73%; outras terapias (n=21): 19%.",
      "seguranca": "Boca seca G1–2 66%, náusea G1–2 48%, trombocitopenia G3–4 10%, anemia G3 10%; nenhum EA inesperado no retratamento.",
      "conclusao_autores": "Confirma altas taxas de resposta, baixa toxicidade e melhora de QoL; rechallenge com maiores taxas de resposta que outras terapias sistêmicas."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 7,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "netter1-hrqol-2018",
    "title": "NETTER-1 — Qualidade de vida",
    "recordType": "secondary_publication",
    "parentUid": "net_gep_0",
    "parentTrialName": "NETTER-1",
    "parentTrialPublication": "Strosberg J, et al. N Engl J Med 2017;376:125-135 (NCT01578239)",
    "relationshipToParent": "Análise de HRQoL do ensaio fase III NETTER-1",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise secundária de HRQoL",
    "evidenceMaturity": "Análise secundária revisada por pares",
    "year": 2018,
    "journal": "Journal of Clinical Oncology",
    "titleOriginal": "Health-Related Quality of Life in Patients With Progressive Midgut Neuroendocrine Tumors Treated With 177Lu-Dotatate in the Phase III NETTER-1 Trial",
    "authors": "Strosberg J, et al.",
    "doi": "10.1200/JCO.2018.78.5865",
    "pmid": "29878866",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/29878866/",
    "category": [
      "HRQoL",
      "Desfechos relatados pelo paciente",
      "NET"
    ],
    "clinicalTakeaway": "No NETTER-1, 177Lu-DOTATATE retardou a deterioração da qualidade de vida versus octreotida em alta dose (saúde global: 28,8 vs 6,1 m; HR 0,406), com avaliação limitada ao período até a progressão.",
    "collapsedSummary": "177Lu-DOTATATE retardou a deterioração da qualidade de vida versus octreotida em alta dose. Mede tempo até deterioração, não melhora absoluta, e só até a progressão.",
    "deep": {
      "objetivo": "Avaliar o impacto do 177Lu-DOTATATE no tempo até deterioração (TTD) da qualidade de vida relacionada à saúde no NETTER-1.",
      "metodo": "Análise de HRQoL do fase III NETTER-1 (população ITT: 177Lu-DOTATATE n=117 vs octreotida em alta dose n=114). EORTC QLQ-C30 e G.I.NET-21 no basal e a cada 12 semanas até progressão; TTD = tempo da randomização até a primeira piora ≥10 pontos no domínio; sem deterioração, censura na última avaliação.",
      "achados": [
        "Saúde global: TTD mediano 28,8 vs 6,1 m (HR 0,406).",
        "Função física: 25,2 vs 11,5 m (HR 0,518); função de papel HR 0,580.",
        "Fadiga HR 0,621; dor HR 0,566; diarreia HR 0,473; preocupações com a doença HR 0,572; imagem corporal HR 0,425."
      ],
      "interpretacao": "O 177Lu-DOTATATE retardou a deterioração de vários domínios de QoL versus octreotida em alta dose, segundo os autores com diferenças clinicamente significativas em saúde global e função física. O desfecho é tempo até deterioração, não melhora absoluta de QoL.",
      "limitacoes": "Questionários aplicados apenas até a progressão, com censura na última avaliação; IC95% e valores de p não apresentados no resumo; pré-especificação da análise não informada no resumo."
    },
    "analysis": {
      "populacao": "ITT do NETTER-1: 117 (177Lu-DOTATATE) vs 114 (octreotida em alta dose), NET de intestino médio progressivo.",
      "desenho_relacao": "Análise de HRQoL do ensaio fase III randomizado NETTER-1.",
      "endpoints": "TTD ≥10 pontos por domínio (QLQ-C30, G.I.NET-21).",
      "estatistica": "Escala 0–100; HR por domínio; censura na última avaliação; ITT.",
      "cutoff_followup": "Avaliações a cada 12 semanas até progressão; data de corte não informada.",
      "subgrupos": null,
      "seguranca": null,
      "conclusao_autores": "Benefício significativo de QoL além do ganho de PFS versus octreotida em alta dose."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 7,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "netter1-final-os-long-term-safety-2021",
    "title": "NETTER-1 — OS final e segurança de longo prazo",
    "recordType": "trial_update",
    "parentUid": "net_gep_0",
    "parentTrialName": "NETTER-1",
    "parentTrialPublication": "Strosberg J, et al. N Engl J Med 2017;376:125-135 (NCT01578239)",
    "relationshipToParent": "Análise final de OS e segurança de longo prazo do NETTER-1",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise final de sobrevida global e segurança de longo prazo",
    "evidenceMaturity": "Análise final revisada por pares",
    "year": 2021,
    "journal": "The Lancet Oncology",
    "titleOriginal": "177Lu-Dotatate plus long-acting octreotide versus high-dose long-acting octreotide in patients with midgut neuroendocrine tumours (NETTER-1): final overall survival and long-term safety results from an open-label, randomised, controlled, phase 3 trial",
    "authors": "Strosberg JR, et al.",
    "doi": "10.1016/S1470-2045(21)00572-6",
    "pmid": "34793718",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/34793718/",
    "category": [
      "Sobrevida global",
      "Segurança de longo prazo",
      "SMD",
      "LMA"
    ],
    "clinicalTakeaway": "Na análise final do NETTER-1, a OS não foi significativamente maior com 177Lu-DOTATATE (48,0 vs 36,3 m; HR 0,84; p=0,30), sem novos sinais de segurança em ~76 m de seguimento; SMD em 2% dos tratados.",
    "collapsedSummary": "A OS final não foi significativamente maior com 177Lu-DOTATATE, embora os autores considerem a diferença de 11,7 meses possivelmente relevante. Sem novos sinais de segurança.",
    "deep": {
      "objetivo": "Reportar a análise final pré-especificada de sobrevida global (desfecho secundário-chave) e a segurança de longo prazo do NETTER-1.",
      "metodo": "Fase III aberto, randomizado 1:1 (41 centros, 8 países); n=231 randomizados; 177Lu-DOTATATE 7,4 GBq a cada 8 semanas × 4 + octreotida LAR 30 mg vs octreotida LAR 60 mg a cada 4 semanas. Análise final de OS pré-especificada após 158 óbitos ou 5 anos da última randomização; ocorreu aos 5 anos, com 142 óbitos; seguimento mediano ~76 m. Segurança de longo prazo coletada apenas no braço 177Lu (n=111).",
      "achados": [
        "OS mediana: 48,0 m (IC95% 37,4–55,2) vs 36,3 m (25,9–51,7); HR 0,84 (0,60–1,17); p=0,30 — desfecho secundário não atingido.",
        "EA grave relacionado grau ≥3 no seguimento longo: 3/111 (3%); nenhum novo após o cutoff de segurança.",
        "Síndrome mielodisplásica em 2/111 (2%), um óbito aos 33 meses (único óbito relacionado ao tratamento); nenhum novo caso de SMD ou LMA no seguimento de longo prazo."
      ],
      "interpretacao": "O 177Lu-DOTATATE não melhorou significativamente a OS versus octreotida em alta dose; os autores consideram que a diferença de 11,7 m nas medianas pode ser clinicamente relevante. Sem novos sinais de segurança no seguimento prolongado.",
      "limitacoes": "Desenho aberto; análise final disparada por tempo com 142 dos 158 óbitos planejados; OS era desfecho secundário; EAs de interesse no longo prazo coletados apenas no braço 177Lu. O resumo não descreve crossover ou terapias subsequentes."
    },
    "analysis": {
      "populacao": "231 pacientes randomizados 1:1 com NET de intestino médio bem diferenciado SSTR+, progressivo com octreotida LAR; segurança de longo prazo em 111 do braço 177Lu.",
      "desenho_relacao": "Análise final pré-especificada de OS (secundário-chave) e segurança de longo prazo do fase III NETTER-1.",
      "endpoints": "OS na ITT; EAs de interesse especial no braço 177Lu.",
      "estatistica": "Gatilho: 158 óbitos ou 5 anos após a última randomização; HR (IC95%), p bicaudal.",
      "cutoff_followup": "5 anos após a última randomização (142 óbitos); seguimento mediano 76,3 e 76,5 m.",
      "subgrupos": null,
      "seguranca": "EA grave relacionado grau ≥3: 3/111; SMD 2/111 (1 óbito); sem novos SMD/LMA no seguimento longo.",
      "conclusao_autores": "OS sem melhora significativa; diferença de 11,7 m possivelmente relevante clinicamente; sem novos sinais de segurança."
    },
    "auditStatus": {
      "classification": "INCORRECT",
      "verification": "PASS",
      "appliedChanges": 7,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "netter1-dosimetry-substudy-2025",
    "title": "NETTER-1 — Subestudo de dosimetria",
    "recordType": "substudy",
    "parentUid": "net_gep_0",
    "parentTrialName": "NETTER-1",
    "parentTrialPublication": "Strosberg J, et al. N Engl J Med 2017;376:125-135 (NCT01578239)",
    "relationshipToParent": "Subestudo prospectivo de dosimetria vinculado ao fase III NETTER-1 (população majoritariamente não randomizada; 8/30 do braço randomizado 177Lu)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Subestudo de dosimetria",
    "evidenceMaturity": "Subestudo revisado por pares",
    "year": 2025,
    "journal": "Journal of Nuclear Medicine",
    "titleOriginal": "Dosimetry of [177Lu]Lu-DOTATATE in Patients with Advanced Midgut Neuroendocrine Tumors: Results from a Substudy of the Phase III NETTER-1 Trial",
    "authors": "Bodei L, et al.",
    "doi": "10.2967/jnumed.124.268903",
    "pmid": "39947918",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/39947918/",
    "category": [
      "Dosimetria",
      "Toxicidade",
      "Dose absorvida tumoral",
      "PRRT"
    ],
    "clinicalTakeaway": "No subestudo de dosimetria do NETTER-1 (20 avaliáveis, maioria não randomizada), as doses cumulativas médias em rins (19,4 Gy) e medula (1,0 Gy) ficaram abaixo dos limiares conservadores, com toxicidade manejável; não houve correlação entre dose tumoral e redução de tamanho.",
    "collapsedSummary": "Doses médias em rins e medula ficaram abaixo dos limiares conservadores, com toxicidade manejável. Amostra pequena; não se demonstrou relação entre dose tumoral e resposta.",
    "deep": {
      "objetivo": "Avaliar a dosimetria de corpo inteiro e de órgãos do protocolo padrão de 4 ciclos de 177Lu-DOTATATE e sua relação com toxicidade; dosimetria tumoral e resposta por dose absorvida foram desfechos exploratórios.",
      "metodo": "Subestudo prospectivo multicêntrico do NETTER-1: 30 inscritos (apenas 8 randomizados no braço 177Lu do estudo principal; demais não randomizados), 20 com dosimetria avaliável. 7,4 GBq × 4 a cada 8 semanas, com ajustes por toxicidade. Dosimetria planar (4–6 pontos até 7 dias) + SPECT/CT a 24/48 h, OLINDA/EXM 1.0; tumor por modelo de esfera (65 lesões em 17 pacientes). Seguimento mediano 62,9 m.",
      "achados": [
        "Dose cumulativa prevista: rins 19,4 Gy (DP 8,7); medula 1,0 Gy (DP 0,8); baço 25,1 Gy; corpo inteiro 1,6 Gy. Três pacientes com rim 28–33 Gy: 2 com creatinina G1 já presente no basal e 1 sem toxicidade renal.",
        "Sem toxicidade renal grave em até 5 anos; hematológica aguda majoritariamente G1–2 e sem associação com a dose; leucopenia G3 transitória 10% (2/20) e linfopenia G4 aguda 20% (4/20), com recuperação parcial; nenhum paciente com dosimetria desenvolveu SMD.",
        "Dose tumoral cumulativa mediana 134 Gy (7–2.218); ≥50 Gy em 73,8% das lesões.",
        "Sem correlação entre a melhor redução de tamanho e a dose absorvida; 47/52 lesões (90%) com redução em algum momento em 72 semanas (desfecho exploratório)."
      ],
      "interpretacao": "Doses médias em rins e medula ficaram abaixo dos limiares conservadores habituais, com toxicidade de órgãos manejável, apoiando a tolerabilidade do regime padrão com ajustes guiados pela toxicidade aguda. A relação dose tumoral–resposta não foi demonstrada nesta amostra; o estudo não testa dosimetria individualizada.",
      "limitacoes": "Amostra pequena, majoritariamente não randomizada e sem comparador; dosimetria planar, menos precisa para tumor; modelo de esfera e captação homogênea assumidos; dosimetria realizada em ciclos diferentes (1º a 3º); regressão tumoral possivelmente subestimada por fibrose e resposta tardia."
    },
    "analysis": {
      "populacao": "30 inscritos (8 randomizados no braço 177Lu do NETTER-1; demais não randomizados); 20 com dosimetria avaliável; 65 lesões/17 pacientes para tumor; 52 lesões/15 pacientes para tamanho.",
      "desenho_relacao": "Subestudo prospectivo de dosimetria, braço único, vinculado ao NETTER-1; tumor/resposta exploratórios.",
      "endpoints": "Primários: dosimetria de corpo inteiro e órgãos; exploratórios: dosimetria tumoral e resposta por dose.",
      "estatistica": "Descritiva; planar + SPECT/CT, OLINDA/EXM 1.0; correlação gráfica dose × melhor variação de tamanho.",
      "cutoff_followup": "Seguimento mediano 62,9 m (9–89); tamanho tumoral até 72 semanas.",
      "subgrupos": "Rim 28–33 Gy (n=3): sem toxicidade renal relevante atribuível; medula 3,2 Gy (n=1): linfopenia G3.",
      "seguranca": "Sem toxicidade renal grave em até 5 anos; leucopenia G3 10%; linfopenia G4 aguda 20%; sem SMD entre os pacientes com dosimetria.",
      "conclusao_autores": "Regime padrão com ajustes por toxicidade aguda é bem tolerado e manejável."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "netter2-subgroup-gep-net-grade-2024",
    "title": "NETTER-2 — Subgrupos por grau e origem tumoral (abstract)",
    "recordType": "congress_abstract",
    "parentUid": "net_gep_1",
    "parentTrialName": "NETTER-2",
    "parentTrialPublication": "Singh S, et al. Lancet 2024;403:2807-2817 (NCT03972488; PMID 38851203)",
    "relationshipToParent": "Análise de subgrupos do NETTER-2 apresentada em congresso",
    "publicationStatus": "Congress abstract",
    "analysisType": "Análise de subgrupos (grau, origem)",
    "evidenceMaturity": "Abstract de congresso — não é artigo completo",
    "year": 2024,
    "journal": "Annals of Oncology (ESMO GI 2024, abstract 211MO)",
    "titleOriginal": "First-line efficacy of [177Lu]Lu-DOTA-TATE in patients with advanced grade 2 and grade 3, well-differentiated gastroenteropancreatic neuroendocrine tumors by tumor grade and primary origin: Subgroup analysis of the phase III NETTER-2 study",
    "authors": null,
    "doi": "10.1016/j.annonc.2024.05.219",
    "pmid": null,
    "sourceUrl": "https://www.annalsofoncology.org/article/S0923-7534(24)00358-2/fulltext",
    "category": [
      "Subgrupos",
      "G2",
      "G3",
      "GEP-NET",
      "Abstract"
    ],
    "clinicalTakeaway": "Análise de subgrupos por grau e origem tumoral apresentada em congresso (abstract 211MO). Congress abstract — deve ser interpretado com cautela.",
    "deep": {
      "objetivo": "Avaliar a eficácia de 1ª linha do 177Lu-DOTATATE em GEP-NET grau 2 e grau 3 por grau e origem tumoral, no NETTER-2.",
      "metodo": "Análise de subgrupos do NETTER-2 (abstract ESMO GI 2024, 211MO).",
      "achados": [
        "Abstract de congresso — eficácia mantida em G2 e G3; magnitudes numéricas por subgrupo não foram extraídas de fonte primária direta nesta sessão (ver abstract oficial, Ann Oncol 2024, abstr 211MO)."
      ],
      "interpretacao": "Sugere que a eficácia de 1ª linha do 177Lu-DOTATATE se mantém em GEP-NET G2 e G3. Congress abstract — interpretar com cautela.",
      "limitacoes": "Abstract de congresso; valores não verificados em fonte primária direta nesta sessão."
    }
  },
  {
    "id": "alsympca-docetaxel-subgroup-2014",
    "title": "ALSYMPCA — Subanálise por uso prévio de docetaxel",
    "recordType": "secondary_publication",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise de subgrupo pré-especificada do ALSYMPCA por docetaxel prévio (fator de estratificação)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de subgrupo pré-especificada",
    "evidenceMaturity": "Análise de subgrupo pré-especificada revisada por pares",
    "year": 2014,
    "journal": "The Lancet Oncology",
    "titleOriginal": "Efficacy and safety of radium-223 dichloride in patients with castration-resistant prostate cancer and symptomatic bone metastases, with or without previous docetaxel use: a prespecified subgroup analysis from the randomised, double-blind, phase 3 ALSYMPCA trial",
    "authors": "Hoskin P, et al.",
    "doi": "10.1016/S1470-2045(14)70474-7",
    "pmid": "25439694",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/25439694/",
    "category": [
      "Docetaxel prévio",
      "Subgrupos",
      "Segurança",
      "Eficácia"
    ],
    "clinicalTakeaway": "Análise de subgrupo pré-especificada: o benefício de SG do rádio-223 foi semelhante com (HR 0,70) e sem (HR 0,69) docetaxel prévio; após docetaxel, a trombocitopenia G3–4 foi mais frequente com rádio-223 (9% vs 3%).",
    "collapsedSummary": "O benefício de SG do rádio-223 foi semelhante com e sem docetaxel prévio; após docetaxel, a trombocitopenia G3–4 foi mais frequente. Subgrupos não randomizados entre si.",
    "deep": {
      "objetivo": "Avaliar, em análise de subgrupo pré-especificada do ALSYMPCA, se o uso prévio de docetaxel modifica a eficácia e a segurança do rádio-223 versus placebo.",
      "metodo": "Subgrupos definidos por docetaxel prévio (fator de estratificação da randomização). ITT n=921: com docetaxel prévio n=526 (rádio-223 352, placebo 174); sem docetaxel prévio n=395 (262, 133) — pacientes inaptos ou que recusaram docetaxel. Eficácia em ITT (SG, principais endpoints secundários); segurança na população de segurança.",
      "achados": [
        "SG com docetaxel prévio: HR 0,70 (IC95% 0,56–0,88; p=0,002).",
        "SG sem docetaxel prévio: HR 0,69 (IC95% 0,52–0,92; p=0,01).",
        "Tempo até primeiro evento esquelético sintomático: redução de risco no subgrupo com docetaxel prévio; diferença não significativa no subgrupo sem docetaxel prévio.",
        "EA grau 3–4: 62% (322/518) com docetaxel prévio vs 54% (205/383) sem docetaxel prévio.",
        "Trombocitopenia G3–4 com docetaxel prévio: 9% (rádio-223) vs 3% (placebo); sem docetaxel prévio: 3% vs 1%. Anemia e neutropenia G3–4 semelhantes entre braços em ambos os subgrupos."
      ],
      "interpretacao": "O efeito sobre a SG foi de magnitude semelhante nos dois subgrupos, e os autores concluem que o rádio-223 é eficaz e bem tolerado independentemente de docetaxel prévio. Após docetaxel, a trombocitopenia G3–4 foi mais frequente com rádio-223 do que com placebo.",
      "limitacoes": "O resumo não relata limitações. Os subgrupos não são randomizados entre si (o grupo sem docetaxel reúne pacientes inaptos ou que recusaram docetaxel), e o resumo não informa teste de interação; o achado de eventos esqueléticos no subgrupo sem docetaxel não atingiu significância."
    },
    "analysis": {
      "populacao": "ITT n=921 (com docetaxel prévio 526: 352 rádio-223/174 placebo; sem docetaxel prévio 395: 262/133). Segurança: 518 com e 383 sem docetaxel prévio.",
      "desenho_relacao": "Análise de subgrupo pré-especificada do ensaio de fase 3 randomizado, duplo-cego ALSYMPCA; docetaxel prévio era fator de estratificação.",
      "endpoints": "SG (primário do ensaio), principais endpoints secundários de eficácia, segurança.",
      "estatistica": "Eficácia em ITT; segurança na população de segurança; HR com IC95% por subgrupo. Teste de interação não relatado no resumo.",
      "cutoff_followup": "Randomização jun/2008–fev/2011; data de corte não informada no resumo.",
      "subgrupos": "Com vs sem docetaxel prévio: SG HR 0,70 vs 0,69; tempo até 1º evento esquelético sintomático significativo apenas com docetaxel prévio.",
      "seguranca": "EA G3–4 62% vs 54% (com vs sem docetaxel prévio); trombocitopenia G3–4 9% vs 3% (rádio-223 vs placebo) com docetaxel prévio e 3% vs 1% sem.",
      "conclusao_autores": "Rádio-223 é eficaz e bem tolerado independentemente do uso prévio de docetaxel."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "alsympca-quality-of-life-2016",
    "title": "ALSYMPCA — Qualidade de vida reportada pelo paciente",
    "recordType": "secondary_publication",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise de QoL reportada pelo paciente do ALSYMPCA (endpoint secundário coletado prospectivamente; testes de hipótese post hoc)",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de qualidade de vida reportada pelo paciente",
    "evidenceMaturity": "Análise secundária revisada por pares",
    "year": 2016,
    "journal": "Annals of Oncology",
    "titleOriginal": "Patient-reported quality-of-life analysis of radium-223 dichloride from the phase III ALSYMPCA study",
    "authors": "Nilsson S, et al.",
    "doi": "10.1093/annonc/mdw065",
    "pmid": "26912557",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/26912557/",
    "category": [
      "HRQoL",
      "Desfechos relatados pelo paciente",
      "Radium-223"
    ],
    "clinicalTakeaway": "Em análises post hoc de QoL coletada prospectivamente, mais pacientes com rádio-223 tiveram melhora significativa (EQ-5D 29,2% vs 18,5%) e a QoL declinou mais devagar; com correção de Bonferroni, só a análise de respondedores do FACT-P deixaria de ser significativa (P = 0,020).",
    "collapsedSummary": "Mais pacientes com rádio-223 tiveram melhora significativa de QoL, e os escores declinaram mais devagar. Análises post hoc; um dos testes perde significância com correção para multiplicidade.",
    "deep": {
      "objetivo": "Avaliar o efeito de rádio-223 + SOC vs placebo + SOC sobre a qualidade de vida reportada pelo paciente (EQ-5D e FACT-P) no ALSYMPCA.",
      "metodo": "QoL coletada prospectivamente (endpoint secundário); testes de hipótese post hoc. ITT n=921 (614 vs 307), restrito a quem tinha avaliação basal e ≥1 pós-basal (semanas 16/24). Respondedor = ganho ≥ MID (EQ-5D 0,1; FACT-P total ≥10). Qui-quadrado para respondedores; ANCOVA de efeitos mistos para escores médios; dados faltantes assumidos MCAR, sem imputação.",
      "achados": [
        "Melhora significativa EQ-5D: 29,2% vs 18,5% (OR 1,82; IC95% 1,21–2,74; p=0,004).",
        "Melhora significativa FACT-P total: 24,6% vs 16,1% (OR 1,70; IC95% 1,08–2,65; p=0,020).",
        "Piora significativa EQ-5D: 36,0% vs 54,0% (p<0,001); FACT-P: 44,3% vs 51,6% (p=0,095, não significativo).",
        "Escores médios no estudo: EQ-5D 0,56 vs 0,50 (p=0,002); FACT-P 99,08 vs 95,22 (p=0,004); variação vs basal FACT-P −4,83 vs −8,69 — ambos os grupos pioraram, mais lentamente com rádio-223.",
        "Efeito consistente por docetaxel prévio; por bisfosfonato, interação apenas na variação média do EQ-5D (p=0,034)."
      ],
      "interpretacao": "Em análises post hoc, o rádio-223 associou-se a maior proporção de melhora e menor proporção de piora de QoL e a declínio mais lento dos escores; segundo os autores, os escores médios mais altos com rádio-223 refletem um declínio mais lento da QoL ao longo do tempo.",
      "limitacoes": "Testes de hipótese post hoc; dados faltantes crescentes ao longo do tempo (suposição MCAR; pattern-mixture sem evidência de viés); com correção de Bonferroni (α=0,008) a análise de respondedores do FACT-P (p=0,020) deixaria de ser significativa."
    },
    "analysis": {
      "populacao": "ITT n=921 (rádio-223 614; placebo 307), limitado a pacientes com avaliação basal e ≥1 pós-basal.",
      "desenho_relacao": "Análise de QoL do ALSYMPCA: coleta prospectiva (endpoint secundário), comparação descritiva pré-planejada; testes de hipótese post hoc.",
      "endpoints": "EQ-5D utility e FACT-P total/subescalas: % com melhora e piora significativas (semanas 16/24); escores médios e variação vs basal ao longo do estudo.",
      "estatistica": "Qui-quadrado; regressão logística para interação por subgrupos; ANCOVA de efeitos mistos; MCAR sem imputação; modelos pattern-mixture como sensibilidade.",
      "cutoff_followup": "Avaliações na randomização, semanas 16 e 24, descontinuação e seguimento; data de corte não informada.",
      "subgrupos": "Sem diferença de efeito por docetaxel prévio; interação por bisfosfonato apenas na variação do EQ-5D (p=0,034).",
      "seguranca": null,
      "conclusao_autores": "Melhor sobrevida com rádio-223 acompanhada de benefícios significativos de QoL, com maior proporção de melhora e declínio mais lento."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "alsympca-chemotherapy-after-radium-2016",
    "title": "ALSYMPCA — Quimioterapia após rádio-223",
    "recordType": "exploratory_analysis",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise exploratória de dados prospectivos do ALSYMPCA: subgrupo pós-randomização que recebeu quimioterapia após rádio-223 ou placebo",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise post hoc de segurança",
    "evidenceMaturity": "Análise post hoc revisada por pares",
    "year": 2016,
    "journal": "The Prostate",
    "titleOriginal": "Chemotherapy following radium-223 dichloride treatment in ALSYMPCA",
    "authors": "Sartor O, et al.",
    "doi": "10.1002/pros.23180",
    "pmid": "27004570",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/27004570/",
    "category": [
      "Post hoc",
      "Quimioterapia após rádio-223",
      "Segurança"
    ],
    "clinicalTakeaway": "Análise exploratória, sem poder e com grupos não comparáveis por randomização: em 206 pacientes que receberam QT (sobretudo docetaxel) após rádio-223 ou placebo, toxicidade hematológica G3–4 foi baixa (<10%, numericamente maior após rádio-223) e a SG a partir da QT foi semelhante (16,0 vs 15,8 meses).",
    "collapsedSummary": "Segundo os autores, a quimioterapia após rádio-223 é factível e parece bem tolerada, com toxicidade hematológica numericamente maior. Grupos não randomizados: comparação apenas descritiva.",
    "deep": {
      "objetivo": "Avaliar a segurança hematológica e a sobrevida com quimioterapia administrada após rádio-223 ou placebo no ALSYMPCA.",
      "metodo": "Análise exploratória de dados coletados prospectivamente (corte: março/2014). Subgrupo pós-randomização de 206/921 pacientes que receberam QT após o tratamento do estudo: 142 rádio-223 e 64 placebo (61% vs 58% com docetaxel prévio). Estatística descritiva; sem poder para comparar braços.",
      "achados": [
        "Docetaxel foi o agente mais usado: 70% (rádio-223) vs 72% (placebo); mitoxantrona 16% vs 20%.",
        "QT iniciada mais tarde com rádio-223 (9,1 vs 7,5 meses após randomização); duração da 1ª QT 4,6 vs 4,2 meses.",
        "Valores hematológicos G3–4 até 18 meses: Hb 8% vs 4%, neutrófilos 10% vs 2%, plaquetas 6% vs 2% — baixos, numericamente maiores com rádio-223, sem diferença estatística.",
        "Queda máxima de plaquetas numericamente maior após rádio-223, sem associação com docetaxel prévio.",
        "SG mediana a partir do início da QT: 16,0 vs 15,8 meses; a partir do docetaxel: 17,5 vs 16,7 meses."
      ],
      "interpretacao": "Os autores concluem que a quimioterapia após rádio-223, com ou sem docetaxel prévio, é factível e parece bem tolerada, sem prejuízo aparente de SG. Como os grupos não são comparáveis por randomização, a comparação de SG e toxicidade entre braços é apenas descritiva.",
      "limitacoes": "Subgrupo definido após a randomização (comparabilidade não assegurada); coletas hematológicas fora dos nadires esperados e medianas que podem ocultar mielossupressão grave transitória; doses/intervalos de QT não coletados; alto abandono e ausência de poder estatístico."
    },
    "analysis": {
      "populacao": "206/921 pacientes que receberam QT após o tratamento do estudo (rádio-223 142; placebo 64).",
      "desenho_relacao": "Análise exploratória de dados coletados prospectivamente no ALSYMPCA; subgrupo pós-randomização.",
      "endpoints": "Tipo/tempo/duração da QT; valores hematológicos e graus 3–4 até 18 meses; SG a partir do início da QT.",
      "estatistica": "Descritiva; Cox; teste exato de Fisher; Wilcoxon; sem poder para comparação entre braços.",
      "cutoff_followup": "Corte do ALSYMPCA em março/2014; hematologia até 18 meses após início da QT.",
      "subgrupos": "Subgrupo docetaxel pós-estudo (100 vs 46): SG 17,5 vs 16,7 meses; por docetaxel prévio, sem diferença aparente na queda de plaquetas.",
      "seguranca": "G3–4 Hb 8% vs 4%, neutrófilos 10% vs 2%, plaquetas 6% vs 2% (NS); mortes durante a QT 29% vs 33%.",
      "conclusao_autores": "QT após rádio-223 é factível e parece bem tolerada, independentemente de docetaxel prévio; estudos prospectivos são necessários."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "alsympca-alp-ldh-psa-2017",
    "title": "ALSYMPCA — ALP, LDH e PSA como marcadores dinâmicos",
    "recordType": "exploratory_analysis",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise exploratória post hoc de biomarcadores (tALP, LDH, PSA) do ALSYMPCA, fora do plano original",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise exploratória de biomarcadores",
    "evidenceMaturity": "Análise exploratória revisada por pares",
    "year": 2017,
    "journal": "Annals of Oncology",
    "titleOriginal": "An exploratory analysis of alkaline phosphatase, lactate dehydrogenase, and prostate-specific antigen dynamics in the phase 3 ALSYMPCA trial with radium-223",
    "authors": "Sartor O, et al.",
    "doi": "10.1093/annonc/mdx044",
    "pmid": "28453701",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/28453701/",
    "category": [
      "ALP",
      "LDH",
      "PSA",
      "Biomarcador"
    ],
    "clinicalTakeaway": "Análise post hoc: na semana 12, a tALP caiu em 87% dos pacientes com rádio-223 vs 23% com placebo (variação média: queda de 32,2% vs aumento de 37,2%), e o declínio associou-se a maior SG entre os tratados, mas tALP, LDH e PSA não atingiram critérios de surrogacia (PTE de tALP 0,34); os autores alertam contra usar a alta de PSA para decidir interromper o tratamento.",
    "collapsedSummary": "Declínios de tALP e LDH associaram-se a maior SG entre tratados com rádio-223, mas nenhum marcador serve de substituto. Os autores alertam contra interromper o tratamento por alta de PSA.",
    "deep": {
      "objetivo": "Avaliar o valor prognóstico de variáveis basais e o valor de surrogacia para SG da dinâmica de tALP, LDH e PSA com rádio-223 no ALSYMPCA.",
      "metodo": "Análise exploratória post hoc (fora do plano original). ITT 614 vs 307 para fatores basais (Cox multivariado); variação vs basal na semana 12 em quem tinha ambas as dosagens (tALP 497 vs 211). SG por declínio confirmado (≥3 semanas após a semana 12) apenas no braço rádio-223. Surrogacia pelos critérios de Prentice, quantificada por PTE.",
      "achados": [
        "Declínio na semana 12 (rádio-223 vs placebo): tALP 87% vs 23% (p<0,001); LDH 51% vs 34% (p=0,003); PSA 27% vs 14% (p=0,160).",
        "Variação média de tALP: −32,2% vs +37,2%; queda de tALP desde a semana 4.",
        "No braço rádio-223, declínio confirmado de tALP (n=400) vs sem declínio (n=97): SG mediana 17,8 vs 10,4 meses; HR 0,45 (IC95% 0,34–0,61). Declínio de LDH: HR 0,55 (0,42–0,73).",
        "PTE como surrogate de SG: tALP 0,34 (IC95% 0–0,746), LDH 0,07 (0–0,211), PSA 0 (0–0,082) — nenhum atingiu surrogacia.",
        "PSA aumentou em 73% dos pacientes com rádio-223 na semana 12, sem impacto relevante no risco de óbito."
      ],
      "interpretacao": "Declínios de tALP e LDH associaram-se a maior SG entre tratados com rádio-223 (associação, não causalidade), mas nenhum marcador explicou o efeito do tratamento o suficiente para servir de substituto. Os autores alertam que usar alta de PSA para interromper rádio-223 pode negar tratamento eficaz.",
      "limitacoes": "Análise post hoc fora do plano original; comparação por resposta do biomarcador dentro do braço rádio-223 (não randomizada); apenas declínio até a semana 12, marcadores avaliados isoladamente e sem CTC; IC do PTE de tALP amplo."
    },
    "analysis": {
      "populacao": "ITT 614 vs 307; semana 12 com dosagens pareadas (tALP 497 vs 211; LDH 473 vs 206; PSA 493 vs 210).",
      "desenho_relacao": "Análise exploratória post hoc de biomarcadores do ALSYMPCA, não incluída no plano original.",
      "endpoints": "Prognóstico basal para SG; variação de tALP/LDH/PSA; SG por declínio confirmado; surrogacia (PTE).",
      "estatistica": "Cox uni/multivariado; Kaplan–Meier; critérios de Prentice e PTE (surrogacia forte se IC95% inferior >0,5).",
      "cutoff_followup": "Semana 12 para variação; dinâmica até 24 semanas após a última dose; corte não informado.",
      "subgrupos": "Declínio de tALP confirmado vs não (braço rádio-223): HR 0,45; LDH: HR 0,55.",
      "seguranca": null,
      "conclusao_autores": "tALP/LDH correlacionam-se com SG mas não são surrogates; podem ser úteis para monitorar; alta de PSA não deve guiar suspensão do rádio-223."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "alsympca-hospitalisation-2017",
    "title": "ALSYMPCA — Impacto em hospitalizações",
    "recordType": "exploratory_analysis",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise de uso de recursos de saúde (hospitalizações, dados coletados prospectivamente) do ALSYMPCA",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise exploratória de desfecho",
    "evidenceMaturity": "Análise exploratória revisada por pares",
    "year": 2017,
    "journal": "European Journal of Cancer",
    "titleOriginal": "Effect of radium-223 dichloride (Ra-223) on hospitalisation: An analysis from the phase 3 randomised Alpharadin in Symptomatic Prostate Cancer Patients (ALSYMPCA) trial",
    "authors": "Parker C, et al.",
    "doi": "10.1016/j.ejca.2016.10.020",
    "pmid": "27930924",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/27930924/",
    "category": [
      "Hospitalização",
      "Desfechos de suporte",
      "Radium-223"
    ],
    "clinicalTakeaway": "No ALSYMPCA, menos pacientes com rádio-223 foram hospitalizados em 12 meses (37,0% vs 45,5%) e houve menos dias de internação (4,44 vs 6,68), mas o número de hospitalizações por paciente não diferiu (0,69 vs 0,79).",
    "collapsedSummary": "Menos pacientes com rádio-223 foram hospitalizados, com menos dias de internação; hospitalizações por paciente não diferiram. O seguimento foi desigual entre os braços.",
    "deep": {
      "objetivo": "Avaliar o efeito do rádio-223 sobre hospitalizações (eventos e dias) nos primeiros 12 meses após a randomização no ALSYMPCA.",
      "metodo": "Dados de uso de recursos de saúde coletados prospectivamente no ALSYMPCA; janela de 12 meses pós-randomização. Rádio-223 n=589, placebo n=292. O resumo não detalha métodos estatísticos nem se a análise era pré-especificada.",
      "achados": [
        "≥1 hospitalização: 37,0% (218/589) vs 45,5% (133/292) (p=0,016).",
        "Hospitalizações por paciente: 0,69 vs 0,79 (p=0,226, não significativo) — seguimento mais longo com rádio-223 (7,82 vs 6,92 meses; p<0,001).",
        "Dias de hospitalização por paciente: 4,44 vs 6,68 (p=0,004).",
        "Dias antes do 1º evento esquelético sintomático: 2,35 vs 3,36; após: 7,74 vs 9,19 (sem p-valor no resumo)."
      ],
      "interpretacao": "Menos pacientes com rádio-223 foram hospitalizados e houve menos dias de internação, mas o número médio de hospitalizações por paciente não diferiu. Os autores sugerem que isso pode contribuir para melhor qualidade de vida relacionada à saúde.",
      "limitacoes": "O resumo não relata limitações nem detalha método estatístico ou pré-especificação. Tempo de seguimento desigual entre braços dentro da janela de 12 meses; população analisada (589/292) não definida no resumo."
    },
    "analysis": {
      "populacao": "Rádio-223 n=589; placebo n=292.",
      "desenho_relacao": "Análise de uso de recursos de saúde (coletados prospectivamente) do ALSYMPCA; pré-especificação não informada no resumo.",
      "endpoints": "≥1 hospitalização; hospitalizações por paciente; dias de hospitalização por paciente (antes/após 1º SSE).",
      "estatistica": "Não detalhada no resumo (apenas p-valores).",
      "cutoff_followup": "Primeiros 12 meses pós-randomização; seguimento médio 7,82 vs 6,92 meses.",
      "subgrupos": "Dias antes do 1º SSE 2,35 vs 3,36; após SSE 7,74 vs 9,19.",
      "seguranca": null,
      "conclusao_autores": "Menos dias de hospitalização, com o benefício de sobrevida e o atraso de SSE, podem contribuir para melhor QoL."
    },
    "auditStatus": {
      "classification": "INCORRECT",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "alsympca-three-year-safety-2018",
    "title": "ALSYMPCA — Segurança de longo prazo em 3 anos",
    "recordType": "trial_update",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Atualização final de segurança de longo prazo (até 3 anos) do ALSYMPCA",
    "publicationStatus": "Peer-reviewed full article",
    "analysisType": "Análise de segurança de longo prazo",
    "evidenceMaturity": "Análise de segurança revisada por pares",
    "year": 2018,
    "journal": "European Urology",
    "titleOriginal": "Three-year Safety of Radium-223 Dichloride in Patients with Castration-resistant Prostate Cancer and Symptomatic Bone Metastases from Phase 3 Randomized Alpharadin in Symptomatic Prostate Cancer Trial",
    "authors": "Parker CC, et al.",
    "doi": "10.1016/j.eururo.2017.06.021",
    "pmid": "28705540",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/28705540/",
    "category": [
      "Segurança de longo prazo",
      "Mielossupressão",
      "Segunda neoplasia"
    ],
    "clinicalTakeaway": "Análise final de segurança do ALSYMPCA: em até 3 anos, sem LMA, SMD ou novo câncer ósseo primário e com mielossupressão pouco frequente (trombocitopenia G3/4 7% vs 2%); apenas 12% dos pacientes com rádio-223 completaram o seguimento, e os autores citam o seguimento curto (3 anos) como limitação.",
    "collapsedSummary": "Em até 3 anos, o rádio-223 manteve-se bem tolerado, sem LMA ou SMD, mas com trombocitopenia G3/4 numericamente maior. Poucos completaram o seguimento, que os autores consideram curto.",
    "deep": {
      "objetivo": "Relatar a segurança atualizada do ALSYMPCA, incluindo segurança de longo prazo até 3 anos após a primeira injeção de rádio-223.",
      "metodo": "População de segurança: rádio-223 n=600, placebo n=301. Todos os EA coletados até 12 semanas após a última injeção; depois, apenas EA relacionados ao tratamento, além de LMA, SMD, anemia aplásica e neoplasias secundárias. 405 vs 167 entraram no seguimento de longo prazo; 48 (12%) vs 12 (7%) o completaram. Estatística descritiva.",
      "achados": [
        "TEAE até 12 semanas após a última injeção: 94% vs 97%; grau 5: 16% vs 23%.",
        "EA hematológicos G3/4: anemia 13% vs 13%; trombocitopenia 7% vs 2%; neutropenia 2% vs 1%.",
        "Longo prazo: nenhum caso de LMA, SMD ou novo câncer ósseo primário; 1 anemia aplásica no braço rádio-223, 16 meses após a última injeção.",
        "Neoplasias secundárias não relacionadas ao tratamento: 4 (rádio-223) vs 3 (placebo)."
      ],
      "interpretacao": "Na análise final, o rádio-223 manteve-se bem tolerado, com mielossupressão pouco frequente (exceto trombocitopenia G3/4 numericamente maior) e sem novos sinais em até 3 anos. Os autores citam o seguimento curto (3 anos) como limitação.",
      "limitacoes": "Seguimento curto (3 anos), segundo os autores; apenas 12% (rádio-223) e 7% (placebo) completaram o seguimento de longo prazo; após 12 semanas, somente EA considerados relacionados ao tratamento foram coletados; análise descritiva."
    },
    "analysis": {
      "populacao": "Segurança: 600 rádio-223, 301 placebo; seguimento de longo prazo 405 vs 167 (completaram 48 vs 12).",
      "desenho_relacao": "Atualização final de segurança de longo prazo do ALSYMPCA.",
      "endpoints": "TEAE; EA relacionados ao tratamento no seguimento; LMA, SMD, anemia aplásica, neoplasias secundárias.",
      "estatistica": "Descritiva.",
      "cutoff_followup": "Até 3 anos após a primeira injeção; visitas a cada 2 meses por 6 meses, depois a cada 4 meses.",
      "subgrupos": null,
      "seguranca": "G3/4 anemia 13% vs 13%, trombocitopenia 7% vs 2%, neutropenia 2% vs 1%; grau 5 16% vs 23%; sem LMA/SMD/novo câncer ósseo; 1 anemia aplásica; neoplasias secundárias não relacionadas 4 vs 3.",
      "conclusao_autores": "Rádio-223 permaneceu bem tolerado, com baixa mielossupressão e sem novas preocupações de segurança."
    },
    "auditStatus": {
      "classification": "TOO_SHALLOW",
      "verification": "PASS",
      "appliedChanges": 8,
      "pendingChanges": 0,
      "auditedAt": "2026-09-30"
    }
  },
  {
    "id": "psma-rlt-protecao-salivar-evidencia-vision",
    "title": "Proteção das glândulas salivares na PSMA-RLT — revisão de evidência",
    "recordType": "evidence_review",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Tópico transversal de toxicidade da terapia com radioligantes PSMA (aplica-se a toda a classe Lu-PSMA)",
    "publicationStatus": "Síntese de evidência — múltiplas fontes primárias verificadas",
    "analysisType": "Toxicidade salivar — estratégias de proteção",
    "evidenceMaturity": "Baixo nível — sem ensaio randomizado com desfecho clínico de xerostomia",
    "year": 2026,
    "journal": null,
    "titleOriginal": "Estratégias de proteção das glândulas salivares na terapia com radioligantes PSMA (resfriamento externo, MSG, toxina botulínica, sialendoscopia, sialagogos, hidratação) — síntese de evidência",
    "authors": null,
    "doi": null,
    "pmid": null,
    "sourceUrl": null,
    "category": ["Xerostomia", "Glândulas salivares", "Proteção / toxicidade", "177Lu-PSMA-617"],
    "clinicalTakeaway": "Nenhuma estratégia de proteção das glândulas salivares na PSMA-RLT tem eficácia comprovada por ensaio randomizado com desfecho clínico de xerostomia ou redução de dose absorvida. O resfriamento externo com ice packs não reduz a captação durante a terapia com 177Lu-PSMA-617 (Yilmaz, J Nucl Med 2019); o MSG reduz a captação salivar mas também a tumoral, sendo inviável; toxina botulínica e sialendoscopia são apenas promissoras em séries pequenas.",
    "deep": {
      "objetivo": "Sintetizar a evidência clínica para prevenção/redução da xerostomia e da dose absorvida às glândulas salivares na terapia com radioligantes PSMA (177Lu/225Ac-PSMA), por estratégia de proteção.",
      "metodo": "Revisão de fontes primárias (ensaios prospectivos de imagem com SUV como surrogate, séries de uso compassivo e relatos de caso), com verificação adversarial das alegações. Desfechos: redução de captação/dose salivar e/ou incidência de xerostomia clínica.",
      "achados": [
        "Resfriamento externo (ice packs) — van Kalmthout et al., EJNMMI Res 2018 (n=89, 68Ga-PSMA PET): redução parotídea de apenas ~12%, sem efeito em submandibulares nem no grupo bilateral. Yilmaz et al., J Nucl Med 2019;60(10):1388 (n=19, durante 177Lu-PSMA-617): 'External cooling does not reduce uptake of 177Lu-PSMA-617 by the PGs'. Sem benefício comprovado.",
        "Monossódio glutamato (MSG) — Tönnesmann/Rousseau, J Nucl Med 2021;62(1):81 e Rauscher/Armstrong, J Nucl Med 2021;62(9):1244 (prospectivos randomizados, imagem): reduz a captação salivar em 45–53%, mas reduz em paralelo a captação tumoral em 38–52%; os autores concluem ser estratégia clinicamente inviável.",
        "Toxina botulínica intraglandular — Baum 2018 (relato n=1, queda de SUV de até 64%); Mueller et al., Toxins 2022 (uso compassivo n=10, bem tolerada, preservação salivar ~71% vs comparador histórico); TANDEM-PSMA-RLT 2025 (abstract, n=14). Promissora, porém sem ensaio randomizado e sem desfecho clínico de xerostomia.",
        "Sialendoscopia / lavagem ductal — Rathke/Bulut, Eur J Nucl Med Mol Imaging 2019 (n=11, 225Ac-PSMA): melhora sintomática (Xerostomia Questionnaire 77,7→42,7; Xerostomia Inventory 44,5→25,8) porém sem dosimetria; intervenção de resgate, não preventiva.",
        "Sialagogos (limão / ácido cítrico / vitamina C / balas), hidratação, losartana e pilocarpina — sem evidência primária em PSMA-RLT; uso empírico extrapolado da radioterapia externa e do 131I (lacuna de evidência)."
      ],
      "interpretacao": "Até o momento, nenhuma estratégia de proteção salivar tem eficácia comprovada por ensaio randomizado com desfecho clínico de xerostomia ou de dose absorvida real de 177Lu. A maioria dos dados usa captação/SUV em PET diagnóstico como surrogate, que não se transfere de forma confiável para a terapia — os ice packs reduzem o SUV na imagem, mas não durante a terapia. Parte da evidência de toxina botulínica/sialendoscopia provém de 225Ac-PSMA (emissor alfa, mais sialotóxico).",
      "limitacoes": "Predomínio de evidência de baixo nível (relato n=1, uso compassivo com comparador histórico, séries não controladas, abstracts de congresso). Não foram localizadas recomendações formais da EANM/SNMMI a favor de qualquer método específico. Campo em rápida evolução."
    }
  },
  {
    "id": "psma-rlt-protecao-salivar-evidencia-therap",
    "title": "Proteção das glândulas salivares na PSMA-RLT — revisão de evidência",
    "recordType": "evidence_review",
    "parentUid": "lupsma_prostata_1",
    "parentTrialName": "TheraP",
    "parentTrialPublication": "Hofman MS, et al. Lancet 2021;397:797-804 (NCT03392428)",
    "relationshipToParent": "Tópico transversal de toxicidade da terapia com radioligantes PSMA (aplica-se a toda a classe Lu-PSMA)",
    "publicationStatus": "Síntese de evidência — múltiplas fontes primárias verificadas",
    "analysisType": "Toxicidade salivar — estratégias de proteção",
    "evidenceMaturity": "Baixo nível — sem ensaio randomizado com desfecho clínico de xerostomia",
    "year": 2026,
    "journal": null,
    "titleOriginal": "Estratégias de proteção das glândulas salivares na terapia com radioligantes PSMA (resfriamento externo, MSG, toxina botulínica, sialendoscopia, sialagogos, hidratação) — síntese de evidência",
    "authors": null,
    "doi": null,
    "pmid": null,
    "sourceUrl": null,
    "category": ["Xerostomia", "Glândulas salivares", "Proteção / toxicidade", "177Lu-PSMA-617"],
    "clinicalTakeaway": "Nenhuma estratégia de proteção das glândulas salivares na PSMA-RLT tem eficácia comprovada por ensaio randomizado com desfecho clínico de xerostomia ou redução de dose absorvida. O resfriamento externo com ice packs não reduz a captação durante a terapia com 177Lu-PSMA-617 (Yilmaz, J Nucl Med 2019); o MSG reduz a captação salivar mas também a tumoral, sendo inviável; toxina botulínica e sialendoscopia são apenas promissoras em séries pequenas.",
    "deep": {
      "objetivo": "Sintetizar a evidência clínica para prevenção/redução da xerostomia e da dose absorvida às glândulas salivares na terapia com radioligantes PSMA (177Lu/225Ac-PSMA), por estratégia de proteção.",
      "metodo": "Revisão de fontes primárias (ensaios prospectivos de imagem com SUV como surrogate, séries de uso compassivo e relatos de caso), com verificação adversarial das alegações. Desfechos: redução de captação/dose salivar e/ou incidência de xerostomia clínica.",
      "achados": [
        "Resfriamento externo (ice packs) — van Kalmthout et al., EJNMMI Res 2018 (n=89, 68Ga-PSMA PET): redução parotídea de apenas ~12%, sem efeito em submandibulares nem no grupo bilateral. Yilmaz et al., J Nucl Med 2019;60(10):1388 (n=19, durante 177Lu-PSMA-617): 'External cooling does not reduce uptake of 177Lu-PSMA-617 by the PGs'. Sem benefício comprovado.",
        "Monossódio glutamato (MSG) — Tönnesmann/Rousseau, J Nucl Med 2021;62(1):81 e Rauscher/Armstrong, J Nucl Med 2021;62(9):1244 (prospectivos randomizados, imagem): reduz a captação salivar em 45–53%, mas reduz em paralelo a captação tumoral em 38–52%; os autores concluem ser estratégia clinicamente inviável.",
        "Toxina botulínica intraglandular — Baum 2018 (relato n=1, queda de SUV de até 64%); Mueller et al., Toxins 2022 (uso compassivo n=10, bem tolerada, preservação salivar ~71% vs comparador histórico); TANDEM-PSMA-RLT 2025 (abstract, n=14). Promissora, porém sem ensaio randomizado e sem desfecho clínico de xerostomia.",
        "Sialendoscopia / lavagem ductal — Rathke/Bulut, Eur J Nucl Med Mol Imaging 2019 (n=11, 225Ac-PSMA): melhora sintomática (Xerostomia Questionnaire 77,7→42,7; Xerostomia Inventory 44,5→25,8) porém sem dosimetria; intervenção de resgate, não preventiva.",
        "Sialagogos (limão / ácido cítrico / vitamina C / balas), hidratação, losartana e pilocarpina — sem evidência primária em PSMA-RLT; uso empírico extrapolado da radioterapia externa e do 131I (lacuna de evidência)."
      ],
      "interpretacao": "Até o momento, nenhuma estratégia de proteção salivar tem eficácia comprovada por ensaio randomizado com desfecho clínico de xerostomia ou de dose absorvida real de 177Lu. A maioria dos dados usa captação/SUV em PET diagnóstico como surrogate, que não se transfere de forma confiável para a terapia — os ice packs reduzem o SUV na imagem, mas não durante a terapia. Parte da evidência de toxina botulínica/sialendoscopia provém de 225Ac-PSMA (emissor alfa, mais sialotóxico).",
      "limitacoes": "Predomínio de evidência de baixo nível (relato n=1, uso compassivo com comparador histórico, séries não controladas, abstracts de congresso). Não foram localizadas recomendações formais da EANM/SNMMI a favor de qualquer método específico. Campo em rápida evolução."
    }
  }
];

if (typeof window !== 'undefined' && window.THERA_SECONDARY) {
  try { Object.freeze(window.THERA_SECONDARY); } catch (e) {}
}
