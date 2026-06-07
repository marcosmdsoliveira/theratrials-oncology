/* =============================================================================
   secondary-cards.js  —  window.THERA_SECONDARY
   Publicações secundárias / análises derivadas / atualizações / substudos /
   protocolos / abstracts / press releases vinculados aos estudos teranósticos.
   NÃO faz parte do schema congelado de 40 campos do data.js.
   Cada card confirmado em fonte Nível 1-2 (PubMed E-utilities + Crossref).
   Campo `deep` (objetivo/método/achados/interpretação/limitações) extraído dos
   abstracts oficiais — nenhum número inventado; linguagem cautelosa.
   Atualizado: 2026-06-07.
============================================================================= */
window.THERA_SECONDARY = [
  {
    "id": "vision-hrqol-2023",
    "title": "VISION — HRQoL, dor e eventos esqueléticos sintomáticos",
    "recordType": "secondary_publication",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise secundária do ensaio fase III VISION",
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
    "clinicalTakeaway": "Relatou atraso na piora de qualidade de vida, dor e eventos esqueléticos sintomáticos com 177Lu-PSMA-617 + standard of care em comparação ao standard of care isolado.",
    "deep": {
      "objetivo": "Avaliar, no VISION (fase III), o efeito do 177Lu-PSMA-617 + standard of care (SoC) sobre qualidade de vida (HRQoL), dor e eventos esqueléticos sintomáticos (SSE) versus SoC isolado.",
      "metodo": "Desfechos relatados pelo paciente (FACT-P, EQ-5D-5L, BPI-SF) e tempo até o 1º SSE; randomização 2:1; população analisável para HRQoL n=581.",
      "achados": [
        "Tempo até 1º SSE ou óbito: mediana 11,5 vs 6,8 m; HR 0,50 (IC95% 0,40–0,62).",
        "Tempo até piora do FACT-P: HR 0,54 (0,45–0,66).",
        "Tempo até piora da dor (BPI-SF): HR 0,52 (0,42–0,63).",
        "Tempo até piora da utilidade EQ-5D-5L: HR 0,65 (0,54–0,78).",
        "Linfopenia G3–4: 51% (269/529) vs 19% (39/205)."
      ],
      "interpretacao": "Retardou a piora de HRQoL, da dor e o tempo até eventos esqueléticos sintomáticos, de forma consistente com o benefício de eficácia do estudo principal. Desfechos secundários/relatados pelo paciente.",
      "limitacoes": "5 óbitos relacionados ao tratamento no braço experimental vs 0 no controle."
    }
  },
  {
    "id": "vision-safety-2024",
    "title": "VISION — Análise detalhada de segurança",
    "recordType": "secondary_publication",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise de segurança do ensaio fase III VISION",
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
    "clinicalTakeaway": "Avaliação detalhada de eventos adversos no cenário do VISION, consistente com o perfil benefício-risco do 177Lu-PSMA-617 relatado no estudo principal.",
    "deep": {
      "objetivo": "Avaliar a segurança de ciclos adicionais (≤4 vs 5–6) e da exposição mais longa ao 177Lu-PSMA-617 no VISION.",
      "metodo": "Análise de segurança por número de ciclos na população randomizada 2:1 do VISION.",
      "achados": [
        "Incidência de TEAE de qualquer grau semelhante entre ciclos 1–4 e 5–6.",
        "Frequência de TEAE semelhante entre todos os ciclos; sem novos sinais de segurança com mais de 4 ciclos."
      ],
      "interpretacao": "Exposição mais longa (até 6 ciclos) não se associou a maior risco de toxicidade, apoiando o perfil benefício-risco favorável de até 6 ciclos.",
      "limitacoes": "Não detalhadas no abstract."
    }
  },
  {
    "id": "vision-renal-multiorgan-dosimetry-2024",
    "title": "VISION — Dosimetria renal e multiorgânica",
    "recordType": "substudy",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Subestudo de dosimetria do ensaio fase III VISION",
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
    "clinicalTakeaway": "Subestudo de dosimetria que quantificou doses absorvidas em rins e outros órgãos, consistente com a segurança do regime utilizado no VISION.",
    "deep": {
      "objetivo": "Quantificar as doses absorvidas em rins e outros órgãos no regime do VISION.",
      "metodo": "Coorte de dosimetria separada, não-randomizada (n=30); 177Lu-PSMA-617 7,4 GBq/ciclo até 6 ciclos.",
      "achados": [
        "Dose renal média: 0,43±0,16 Gy/GBq (ciclo 1) e 0,44±0,21 Gy/GBq (ciclos 2–6).",
        "Dose renal cumulativa observada em 6 ciclos: 15±6 Gy (prevista 19±7 Gy).",
        "Sem TEAE renal de grau >3."
      ],
      "interpretacao": "Dose renal cumulativa abaixo do limite estabelecido; baixa radiotoxicidade renal — não foi preocupação de segurança no regime do VISION.",
      "limitacoes": "Coorte pequena, não-randomizada; limitações não detalhadas no abstract."
    }
  },
  {
    "id": "vision-baseline-psma-pet-biomarkers-2024",
    "title": "VISION — Biomarcadores quantitativos no PET PSMA basal",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Análise exploratória de biomarcadores de imagem do ensaio fase III VISION",
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
    "clinicalTakeaway": "Análise exploratória sugerindo que parâmetros quantitativos do PSMA PET basal, sobretudo o SUVmean tumoral de corpo inteiro, podem se associar ao benefício do 177Lu-PSMA-617. Necessita confirmação prospectiva.",
    "deep": {
      "objetivo": "Explorar a associação entre parâmetros quantitativos do 68Ga-PSMA-11 PET basal e a resposta ao 177Lu-PSMA-617.",
      "metodo": "Análise secundária do VISION (n=826); parâmetros de PET basais extraídos.",
      "achados": [
        "SUVmean tumoral de corpo inteiro foi o melhor preditor: aumento de 1 unidade associado a 12% menor risco de progressão (rPFS, p<0,001) e 10% menor risco de óbito (p<0,001).",
        "Maior volume/carga tumoral associou-se a piores desfechos (HR ~1,44–1,53)."
      ],
      "interpretacao": "A melhora de rPFS e OS foi maior em pacientes com maior SUVmean tumoral, com evidência de benefício em todos os níveis de SUVmean. Análise exploratória/de imagem.",
      "limitacoes": "Análise exploratória; limitações não detalhadas no abstract."
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
    "relationshipToParent": "Análise exploratória de associação biomarcador-desfecho do VISION",
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
    "clinicalTakeaway": "Análise exploratória avaliando a associação entre a magnitude do declínio de PSA e desfechos clínicos no braço tratado com 177Lu-PSMA-617.",
    "deep": {
      "objetivo": "Avaliar a associação entre a magnitude do declínio de PSA e desfechos clínicos no braço tratado com 177Lu-PSMA-617.",
      "metodo": "Análise post hoc do VISION (n=551 no braço 177Lu-PSMA-617).",
      "achados": [
        "Declínio de PSA ≥0–<50%: 61% menor risco de progressão/óbito; ≥50–<90%: 72%; ≥90%: 88% (vs PSA em elevação).",
        "Reduções correspondentes no risco de óbito: 51%, 70% e 87%."
      ],
      "interpretacao": "O declínio de PSA parece ter valor prognóstico durante o tratamento com 177Lu-PSMA-617. Análise post hoc — interpretar com cautela.",
      "limitacoes": "Declínio de PSA não confirmado; natureza post hoc."
    }
  },
  {
    "id": "vision-multivariable-outcome-models-2024",
    "title": "VISION — Modelos multivariáveis de desfechos",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_0",
    "parentTrialName": "VISION",
    "parentTrialPublication": "Sartor O, et al. N Engl J Med 2021;385:1091-1103 (NCT03511664)",
    "relationshipToParent": "Modelagem multivariável usando dados do VISION",
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
    "clinicalTakeaway": "Modelagem multivariável baseada em dados do VISION para explorar fatores associados a desfechos com 177Lu-PSMA-617. Necessita confirmação prospectiva.",
    "deep": {
      "objetivo": "Desenvolver modelos multivariáveis para predizer desfechos com 177Lu-PSMA-617.",
      "metodo": "Análise post hoc do VISION (n=551 no braço tratado); regressão de Cox/logística multivariável com validação por bootstrap.",
      "achados": [
        "Nomograma de OS: C-index 0,73 (IC95% 0,70–0,76).",
        "rPFS: C-index 0,68 (0,65–0,72).",
        "PSA50: AUC-ROC 0,72 (0,68–0,77)."
      ],
      "interpretacao": "A combinação de parâmetros pré-tratamento influencia os desfechos e pode auxiliar a seleção de pacientes e o desenho de ensaios. Análise post hoc; necessita validação prospectiva.",
      "limitacoes": "Análise post hoc (com o framework prospectivo do VISION como força)."
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
    "relationshipToParent": "Análise de biomarcadores do ensaio randomizado fase II TheraP",
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
    "clinicalTakeaway": "Relatou papel preditivo/prognóstico de métricas do PSMA PET e FDG PET, sobretudo o SUVmean no PSMA PET e o volume metabólico no FDG PET.",
    "deep": {
      "objetivo": "Avaliar se métricas do PSMA-PET e do FDG-PET predizem a resposta de PSA ao 177Lu-PSMA-617 versus cabazitaxel no TheraP.",
      "metodo": "Análise de biomarcadores na população randomizada (177Lu-PSMA-617 n=99; cabazitaxel n=101); resposta de PSA (queda ≥50%) por estratos de SUVmean (PSMA-PET) e de volume tumoral metabólico/MTV (FDG-PET).",
      "achados": [
        "SUVmean ≥10 (PSMA-PET): resposta de PSA 91% (32/35) vs 47% (14/30).",
        "SUVmean <10: 52% (33/64) vs 32% (23/71).",
        "Interação tratamento×SUVmean alto: OR 12,19 (IC95% 3,42–58,76); p=0,039.",
        "FDG-PET MTV ≥200 mL: resposta 38% (23/60) vs 56% (79/140) com MTV <200 mL; OR 0,44 (0,23–0,84); p=0,035."
      ],
      "interpretacao": "O SUVmean no PSMA-PET foi preditivo de maior probabilidade de resposta favorável ao 177Lu-PSMA-617 (vs cabazitaxel); o alto MTV no FDG-PET foi prognóstico de menor resposta independentemente do braço. Necessita confirmação prospectiva.",
      "limitacoes": "Análise de biomarcadores de ensaio fase II."
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
    "clinicalTakeaway": "Atualização de OS com seguimento maduro, reportada como desfecho secundário; deve ser interpretada como tal, sem inferir superioridade de OS.",
    "deep": {
      "objetivo": "Comparar a sobrevida global entre 177Lu-PSMA-617 e cabazitaxel no TheraP, após progressão a docetaxel.",
      "metodo": "Desfecho secundário do TheraP (fase II); n=200 (99 vs 101).",
      "achados": [
        "RMST (tempo médio de sobrevida restrito): 19,1 m (IC95% 16,9–21,4) vs 19,6 m (17,4–21,8); diferença −0,5 m (−3,7 a 2,7); p=0,77.",
        "Óbitos: 78% (77/99) vs 69% (70/101)."
      ],
      "interpretacao": "OS semelhante entre os braços; o resultado apoia o 177Lu-PSMA-617 como alternativa ao cabazitaxel em doença PSMA-positiva. Desfecho secundário — não interpretar como superioridade de OS.",
      "limitacoes": "Não detalhadas no abstract."
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
    "relationshipToParent": "Análise final de OS e segurança do ensaio fase III PSMAfore",
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
    "clinicalTakeaway": "Atualização final de OS e segurança; deve ser interpretada considerando o crossover do braço controle.",
    "deep": {
      "objetivo": "Avaliar a OS final e a segurança do 177Lu-PSMA-617 versus troca de ARPI no PSMAfore (mCRPC taxane-naïve).",
      "metodo": "Fase III, internacional, aberto; n=468 (234 por braço).",
      "achados": [
        "OS mediana: 24,5 m (IC95% 19,6–28,9) vs 23,1 m (19,6–25,5); HR 0,91 (0,72–1,14); p=0,20 (ITT).",
        "HR ajustado para crossover: 0,59 (0,38–0,91).",
        "EA grau ≥3: 60,8 vs 85,1 por 100 pessoas-ano de tratamento."
      ],
      "interpretacao": "A OS não mostrou diferença estatisticamente significativa na ITT; a alta taxa de crossover provavelmente confundiu o resultado; perfil de segurança favorável. Interpretar a OS considerando o crossover.",
      "limitacoes": "Crossover elevado do braço controle."
    }
  },
  {
    "id": "psmafore-hrqol-pain-skeletal-events-2025",
    "title": "PSMAfore — HRQoL, dor e eventos esqueléticos sintomáticos",
    "recordType": "secondary_publication",
    "parentUid": "lupsma_prostata_2",
    "parentTrialName": "PSMAfore",
    "parentTrialPublication": "Morris MJ, et al. Lancet 2024;404:1227-1239 (NCT04689828; PMID 39293462)",
    "relationshipToParent": "Análise secundária de HRQoL/dor/SSE do PSMAfore",
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
    "clinicalTakeaway": "Análise de qualidade de vida, dor e eventos esqueléticos sintomáticos em pacientes taxane-naïve tratados no PSMAfore.",
    "deep": {
      "objetivo": "Analisar o tempo até piora de HRQoL, dor e eventos esqueléticos sintomáticos com 177Lu-PSMA-617 versus troca de ARPI no PSMAfore.",
      "metodo": "Fase III, aberto; n=468 (234 por braço); seguimento mediano ~24 m.",
      "achados": [
        "Tempo até piora do FACT-P: 7,46 m vs 4,27 m; HR 0,61 (0,50–0,75).",
        "EQ-5D-5L: 6,28 vs 3,88 m; HR 0,67 (0,54–0,82).",
        "Dor (BPI-SF): 5,03 vs 3,65 m; HR 0,72 (0,59–0,88).",
        "Eventos esqueléticos sintomáticos: HR 0,41 (0,26–0,63)."
      ],
      "interpretacao": "O 177Lu-PSMA-617 pode retardar a piora dos desfechos relatados pelo paciente e prevenir eventos esqueléticos versus troca de ARPI.",
      "limitacoes": "Não detalhadas no abstract."
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
    "relationshipToParent": "Desfechos secundários do ENZA-p com seguimento mais longo",
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
    "clinicalTakeaway": "Atualização dos desfechos secundários de OS e HRQoL com maior tempo de seguimento.",
    "deep": {
      "objetivo": "Reportar OS e qualidade de vida (desfechos secundários) com seguimento mais longo no ENZA-p.",
      "metodo": "Fase II randomizado, multicêntrico; n=162 (79 enzalutamida vs 83 combinação).",
      "achados": [
        "OS mediana: 34 m (IC95% 30–37) vs 26 m (23–31); HR 0,55 (0,36–0,84); p=0,0053.",
        "Sobrevida livre de deterioração — função física: HR 0,51 (p<0,0001); QoL: HR 0,47 (p=0,0001).",
        "Redução de dor (p=0,012) e melhora de fadiga (p=0,016) favoreceram a combinação.",
        "EA grau 3–5: 44% vs 46%; sem óbitos relacionados ao tratamento."
      ],
      "interpretacao": "A adição de 177Lu-PSMA-617 associou-se a melhor sobrevida e a aspectos de QoL; os autores consideram que justifica avaliação fase III. Desfechos secundários de ensaio fase II.",
      "limitacoes": "Não detalhadas no abstract."
    }
  },
  {
    "id": "enzap-baseline-psma-pet-biomarker-2025",
    "title": "ENZA-p — PET PSMA basal (TTV e SUVmean) como biomarcador",
    "recordType": "exploratory_analysis",
    "parentUid": "lupsma_prostata_5",
    "parentTrialName": "ENZA-p (ANZUP 1901)",
    "parentTrialPublication": "Emmett L, et al. Lancet Oncol 2024;25:563-571 (NCT04419402; PMID 38621400)",
    "relationshipToParent": "Análise de biomarcador PSMA-PET basal do ENZA-p",
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
    "clinicalTakeaway": "Análise de biomarcador de imagem avaliando o PSMA-PET basal (volume tumoral total e SUVmean) como marcador prognóstico e potencialmente preditivo no ENZA-p.",
    "deep": {
      "objetivo": "Avaliar PSMA-TTV (volume tumoral total) e SUVmean basais como biomarcadores prognósticos/preditivos no ENZA-p.",
      "metodo": "Subestudo pré-especificado do ENZA-p; n=160 tratados (79 vs 81).",
      "achados": [
        "PSMA-TTV basal mediano 234 mL; SUVmean mediano 7,7.",
        "Efeito do PSMA-TTV (braço enzalutamida): 39 vs 20 m; HR 0,23 (0,13–0,42); p<0,0001.",
        "Braço combinação: 35 vs 28 m; HR 0,66 (0,36–1,21); p=0,18.",
        "Interação tratamento×PSMA-TTV: p=0,0078; SUVmean sem valor prognóstico."
      ],
      "interpretacao": "PSMA-TTV basal é prognóstico e preditivo de benefício de OS com a combinação; o SUVmean não foi prognóstico.",
      "limitacoes": "Não detalhadas no abstract."
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
    "relationshipToParent": "Coorte lead-in do ensaio fase III SPLASH",
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
    "clinicalTakeaway": "Coorte lead-in avaliando dosimetria tecidual, segurança preliminar e eficácia antes da expansão randomizada do SPLASH.",
    "deep": {
      "objetivo": "Avaliar dosimetria tecidual, segurança e eficácia preliminar do 177Lu-PNT2002 na coorte lead-in do SPLASH.",
      "metodo": "Fase lead-in do ensaio fase III SPLASH; n=27.",
      "achados": [
        "19/27 (70,4%) completaram os 4 ciclos.",
        "Dose média: glândula lacrimal 1,2 Gy/GBq; rim 0,73 Gy/GBq; tumor 4,3 Gy/GBq.",
        "Declínio de PSA ≥50%: 42,3% (11/26); ORR confirmada 50% (5/10).",
        "rPFS mediana 11,5 m (IC95% 9,2–19,1); sem TEAE grau ≥3 relacionado; sem óbitos."
      ],
      "interpretacao": "Dosimetria e segurança favoráveis e eficácia preliminar promissora antes da expansão randomizada do SPLASH. Coorte pequena.",
      "limitacoes": "Coorte lead-in pequena; limitações não detalhadas no abstract."
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
    "relationshipToParent": "Subestudo de dosimetria do ensaio prospectivo fase 2",
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
    "clinicalTakeaway": "Relatou doses tumorais absorvidas elevadas e correlação entre a dose tumoral de corpo inteiro e a resposta de PSA.",
    "deep": {
      "objetivo": "Determinar a dosimetria do 177Lu-PSMA-617 e correlações com imagem pré-terapêutica e desfechos.",
      "metodo": "Ensaio prospectivo; n=30.",
      "achados": [
        "Dose renal média 0,39 Gy/MBq; glândula submandibular 0,44 Gy/MBq.",
        "Dose tumoral de corpo inteiro mediana 11,55 Gy.",
        "Declínio de PSA ≥50% associou-se a maior dose tumoral (mediana 14,1 vs 9,6 Gy; p<0,01).",
        "Correlação SUVmean tumoral × dose absorvida r=0,62."
      ],
      "interpretacao": "Doses tumorais absorvidas elevadas, com correlação significativa entre a dose tumoral de corpo inteiro e a resposta de PSA.",
      "limitacoes": "Não detalhadas no abstract."
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
    "clinicalTakeaway": "Coorte expandida com seguimento prolongado e dados de retratamento/rechallenge após resposta inicial.",
    "deep": {
      "objetivo": "Reportar desfechos de longo prazo e retratamento na coorte expandida (50 pacientes) do ensaio fase II.",
      "metodo": "Fase II prospectivo, centro único; n=50; seguimento mediano 31,4 m.",
      "achados": [
        "Declínio de PSA ≥50%: 64% (32/50); ≥80%: 44% (22/50).",
        "Resposta objetiva RECIST: 56% (15/27).",
        "OS mediana 13,3 m (IC95% 10,5–18,7); com PSA ≥50%: 18,4 m.",
        "Retratamento: resposta de PSA ≥50% em 73% (11/15)."
      ],
      "interpretacao": "A coorte expandida confirma altas taxas de resposta e baixa toxicidade, com melhora de qualidade de vida; o retratamento mostrou taxas de resposta elevadas.",
      "limitacoes": "Não detalhadas no abstract."
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
    "clinicalTakeaway": "Relatou atraso na deterioração de múltiplas dimensões de qualidade de vida com 177Lu-DOTATATE.",
    "deep": {
      "objetivo": "Avaliar o impacto do 177Lu-DOTATATE no tempo até deterioração da qualidade de vida no NETTER-1.",
      "metodo": "Fase III; 177Lu-DOTATATE n=117 vs controle n=114.",
      "achados": [
        "Tempo até deterioração — estado de saúde global: 28,8 vs 6,1 m (HR 0,406).",
        "Função física: 25,2 vs 11,5 m (HR 0,518).",
        "Fadiga HR 0,621; dor HR 0,566; diarreia HR 0,473; imagem corporal HR 0,425."
      ],
      "interpretacao": "Benefício significativo de QoL com 177Lu-DOTATATE versus octreotida em alta dose em NETs de intestino médio progressivos.",
      "limitacoes": "Não detalhadas no abstract."
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
    "clinicalTakeaway": "Análise final de OS e segurança de longo prazo; OS numericamente maior, porém sem significância estatística, em contexto de crossover/PRRT subsequente.",
    "deep": {
      "objetivo": "Reportar a análise final pré-especificada de OS e a segurança de longo prazo do NETTER-1.",
      "metodo": "Fase III, aberto; n=231 (177Lu-DOTATATE n=111, controle n=120); seguimento mediano ~76 m; 142 óbitos.",
      "achados": [
        "OS mediana: 48,0 m (IC95% 37,4–55,2) vs 36,3 m (25,9–51,7); HR 0,84 (0,60–1,17); p=0,30.",
        "Síndrome mielodisplásica: 2% (2 pacientes); EA grave grau ≥3: 3 (3%)."
      ],
      "interpretacao": "O 177Lu-DOTATATE não melhorou significativamente a OS mediana versus octreotida em alta dose; a diferença de 11,7 m pode ser considerada clinicamente relevante. Interpretar no contexto de crossover/PRRT subsequente.",
      "limitacoes": "Desenho aberto; OS sem significância estatística."
    }
  },
  {
    "id": "netter1-dosimetry-substudy-2025",
    "title": "NETTER-1 — Subestudo de dosimetria",
    "recordType": "substudy",
    "parentUid": "net_gep_0",
    "parentTrialName": "NETTER-1",
    "parentTrialPublication": "Strosberg J, et al. N Engl J Med 2017;376:125-135 (NCT01578239)",
    "relationshipToParent": "Subestudo de dosimetria do ensaio fase III NETTER-1",
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
    "clinicalTakeaway": "Subestudo de dosimetria do NETTER-1 avaliando dose absorvida e a relação potencial com toxicidade e resposta tumoral.",
    "deep": {
      "objetivo": "Avaliar a dosimetria do protocolo padrão de 4 ciclos de 177Lu-DOTATATE e a relação com toxicidade.",
      "metodo": "Subestudo de dosimetria do NETTER-1; n=20; 65 lesões avaliadas.",
      "achados": [
        "Dose renal média 19,4 Gy (DP 8,7); medula óssea 1,0 Gy (DP 0,8); 3 pacientes com rim 28–33 Gy.",
        "Dose tumoral cumulativa mediana 134 Gy (7–2.218); 90% das lesões reduziram ao longo de 72 semanas.",
        "Toxicidade hematológica leve-moderada."
      ],
      "interpretacao": "O regime padrão de 177Lu-DOTATATE foi bem tolerado e manejável, com possibilidade de ajustes personalizados.",
      "limitacoes": "Limitações dos métodos de imagem e da avaliação de volume tumoral; sem correlação entre redução de tamanho e dose absorvida."
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
    "relationshipToParent": "Análise de subgrupo pré-especificada do ALSYMPCA por docetaxel prévio",
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
    "clinicalTakeaway": "Subanálise pré-especificada relatando benefício de rádio-223 independentemente do uso prévio de docetaxel, com avaliação específica de segurança.",
    "deep": {
      "objetivo": "Avaliar o efeito do uso prévio de docetaxel na eficácia e segurança do rádio-223 no ALSYMPCA.",
      "metodo": "Análise de subgrupo pré-especificada; com docetaxel prévio n=526 (rádio-223 352, placebo 174); sem docetaxel n=395 (262, 133).",
      "achados": [
        "Com docetaxel prévio: OS HR 0,70 (IC95% 0,56–0,88; p=0,002).",
        "Sem docetaxel prévio: OS HR 0,69 (0,52–0,92; p=0,01).",
        "Trombocitopenia G3–4 com docetaxel prévio: 9% vs 3%."
      ],
      "interpretacao": "Rádio-223 foi eficaz e bem tolerado independentemente do uso prévio de docetaxel.",
      "limitacoes": "Não detalhadas no abstract."
    }
  },
  {
    "id": "alsympca-quality-of-life-2016",
    "title": "ALSYMPCA — Qualidade de vida reportada pelo paciente",
    "recordType": "secondary_publication",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise de QoL reportada pelo paciente do ALSYMPCA",
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
    "clinicalTakeaway": "Relatou que o benefício de sobrevida com rádio-223 foi acompanhado de benefícios em qualidade de vida reportada pelo paciente.",
    "deep": {
      "objetivo": "Analisar a qualidade de vida reportada pelo paciente no ALSYMPCA (EQ-5D, FACT-P).",
      "metodo": "População ITT; rádio-223 n=614, placebo n=307.",
      "achados": [
        "Melhora significativa do EQ-5D: 29,2% vs 18,5% (p=0,004; OR 1,82).",
        "Melhora do FACT-P: 24,6% vs 16,1% (p=0,020; OR 1,70).",
        "EQ-5D médio 0,56 vs 0,50 (p=0,002); FACT-P 99,08 vs 95,22 (p=0,004)."
      ],
      "interpretacao": "A melhora de sobrevida com rádio-223 foi acompanhada de benefícios significativos de QoL, com declínio mais lento ao longo do tempo.",
      "limitacoes": "Não detalhadas no abstract."
    }
  },
  {
    "id": "alsympca-chemotherapy-after-radium-2016",
    "title": "ALSYMPCA — Quimioterapia após rádio-223",
    "recordType": "exploratory_analysis",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise post hoc de quimioterapia após rádio-223 no ALSYMPCA",
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
    "clinicalTakeaway": "Análise post hoc avaliando a segurança da quimioterapia subsequente após rádio-223. Deve ser interpretada com cautela.",
    "deep": {
      "objetivo": "Avaliar a segurança e a eficácia da quimioterapia subsequente após rádio-223 no ALSYMPCA.",
      "metodo": "Análise exploratória; 142 (rádio-223) e 64 (placebo) receberam QT subsequente.",
      "achados": [
        "Docetaxel: 70% (rádio-223) vs 72% (placebo).",
        "Valores hematológicos G3–4 <10% em ambos os grupos.",
        "OS mediana a partir do início da QT: 16,0 vs 15,8 m."
      ],
      "interpretacao": "Quimioterapia após rádio-223, independentemente de docetaxel prévio, é factível e parece bem tolerada. Análise exploratória.",
      "limitacoes": "Análise exploratória; limitações não detalhadas."
    }
  },
  {
    "id": "alsympca-alp-ldh-psa-2017",
    "title": "ALSYMPCA — ALP, LDH e PSA como marcadores dinâmicos",
    "recordType": "exploratory_analysis",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise exploratória de biomarcadores do ALSYMPCA",
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
    "clinicalTakeaway": "Análise exploratória da dinâmica de ALP, LDH e PSA durante o tratamento com rádio-223. Em análise exploratória; necessita confirmação.",
    "deep": {
      "objetivo": "Avaliar o valor prognóstico/preditivo da dinâmica de ALP, LDH e PSA com rádio-223.",
      "metodo": "ALSYMPCA; rádio-223 n=614, placebo n=307.",
      "achados": [
        "Declínio de fosfatase alcalina total (tALP) até a semana 12: 87% (rádio-223) vs 23% (placebo) (p<0,001).",
        "Variação média de tALP: −32,2% vs +37,2%.",
        "Declínio de tALP associado a 55% menor risco de óbito (HR 0,45; IC95% 0,34–0,61)."
      ],
      "interpretacao": "Declínios de tALP correlacionaram-se com maior OS, mas não atingiram os requisitos estatísticos de surrogacia. Análise exploratória.",
      "limitacoes": "tALP não validado como surrogate; limitações não detalhadas."
    }
  },
  {
    "id": "alsympca-hospitalisation-2017",
    "title": "ALSYMPCA — Impacto em hospitalizações",
    "recordType": "exploratory_analysis",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Análise exploratória de hospitalizações do ALSYMPCA",
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
    "clinicalTakeaway": "Análise exploratória do efeito do rádio-223 em hospitalizações em pacientes do ALSYMPCA.",
    "deep": {
      "objetivo": "Avaliar o uso de recursos de saúde e o impacto em hospitalizações com rádio-223.",
      "metodo": "ALSYMPCA; rádio-223 n=589, placebo n=292 (primeiros 12 meses).",
      "achados": [
        "Eventos de hospitalização: 37,0% vs 45,5% (p=0,016).",
        "Dias médios de hospitalização: 4,44 vs 6,68 (p=0,004).",
        "HR para tempo até SSE: 0,66 (IC95% 0,52–0,83; p=0,00037)."
      ],
      "interpretacao": "Menos dias de hospitalização com rádio-223, o que pode contribuir para melhora da qualidade de vida. Análise exploratória.",
      "limitacoes": "Análise exploratória; limitações não detalhadas."
    }
  },
  {
    "id": "alsympca-three-year-safety-2018",
    "title": "ALSYMPCA — Segurança de longo prazo em 3 anos",
    "recordType": "trial_update",
    "parentUid": "ra223_prostata_0",
    "parentTrialName": "ALSYMPCA",
    "parentTrialPublication": "Parker C, et al. N Engl J Med 2013;369:213-223 (NCT00699751)",
    "relationshipToParent": "Seguimento de segurança de longo prazo do ALSYMPCA",
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
    "clinicalTakeaway": "Seguimento de segurança de longo prazo do ALSYMPCA, sem novos sinais relevantes de segurança em 3 anos.",
    "deep": {
      "objetivo": "Reportar a segurança de longo prazo do rádio-223 até 3 anos após o tratamento.",
      "metodo": "ALSYMPCA; rádio-223 n=600, placebo n=301 (fase de tratamento); 405/167 no seguimento de longo prazo.",
      "achados": [
        "EA hematológicos G3/4 — anemia 13% (ambos); trombocitopenia 7% vs 2%; neutropenia 2% vs 1%.",
        "No longo prazo: sem LMA, SMD ou novo câncer ósseo primário; 1 caso de anemia aplásica (16 meses).",
        "Neoplasias secundárias: 4 (rádio-223) vs 3 (placebo)."
      ],
      "interpretacao": "Rádio-223 manteve-se bem tolerado, com baixa mielossupressão e sem novos sinais de segurança em 3 anos.",
      "limitacoes": "Seguimento curto (3 anos)."
    }
  }
];

if (typeof window !== 'undefined' && window.THERA_SECONDARY) {
  try { Object.freeze(window.THERA_SECONDARY); } catch (e) {}
}
