/* ============================================================================
 * ferramentas/ajcc.js — Estadiamento AJCC/TNM (15 tumores): dados, modal e fechamento por backdrop.
 *
 * Extraído LITERALMENTE de ferramentas.html (26/set/2026), sem nenhuma linha
 * reescrita. A indentação herdada do HTML foi mantida de propósito: os corpos
 * de modal são template strings, e preservá-los byte a byte é o que permite
 * provar a equivalência contra a versão inline (ver o harness de snapshot).
 *
 * Carregado como script CLÁSSICO e SÍNCRONO, na mesma posição em que o bloco
 * inline estava — mesma ordem de execução, mesmo escopo global compartilhado
 * (`const` de topo e `function` continuam visíveis aos handlers inline).
 * Depende de: nada. Usado por: 15 botões onclick="openTNM(...)".
 * ==========================================================================*/

      // ====== TNM DATA — Estadiamento AJCC ======
      const TNM_DATA = {
        prostata: {
          title: 'Próstata',
          edition: 'AJCC 8ª · prognóstico',
          icon: 'target',
          color: '#FF8400',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tx</span>Não pode ser avaliado</li>
              <li><span class="code">T0</span>Sem evidência de tumor primário</li>
              <li><span class="code">T1</span>Não palpável e não visível em imagem
                <ul>
                  <li>T1a: achado histológico em ≤5% do tecido ressecado</li>
                  <li>T1b: achado em &gt;5% do tecido ressecado</li>
                  <li>T1c: identificado por biópsia (PSA elevado), uni ou bilateral, não palpável</li>
                </ul>
              </li>
              <li><span class="code">T2</span>Palpável, confinado à próstata
                <ul>
                  <li>T2a: ≤½ de um lobo</li>
                  <li>T2b: &gt;½ de um lobo, mas só um lobo</li>
                  <li>T2c: ambos os lobos</li>
                </ul>
              </li>
              <li><span class="code">T3</span>Extensão extra-prostática
                <ul>
                  <li>T3a: extensão extracapsular (uni/bilateral) ou invasão microscópica do colo vesical</li>
                  <li>T3b: invasão de vesícula(s) seminal(is)</li>
                </ul>
              </li>
              <li><span class="code">T4</span>Fixo ou invade estruturas adjacentes (esfíncter externo, reto, bexiga, levantador, parede pélvica)</li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos regionais</h5>
            <ul class="tnm-list">
              <li><span class="code">Nx</span>Não avaliados</li>
              <li><span class="code">N0</span>Sem metástase em LN regionais</li>
              <li><span class="code">N1</span>Metástase em LN regional(is) (ilíaca interna/externa/comum, obturatória, sacral, perirretal, pélvica)</li>
            </ul>
            <h5><span class="pill">M</span>Metástases à distância</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástase à distância</li>
              <li><span class="code">M1</span>Metástase à distância
                <ul>
                  <li>M1a: linfonodo(s) não-regional(is)</li>
                  <li>M1b: osso(s)</li>
                  <li>M1c: outros sítios viscerais (com/sem doença óssea)</li>
                </ul>
              </li>
            </ul>
            <h5>Grupos de estágio prognóstico</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th><th>PSA · Grade Group</th></tr></thead>
              <tbody>
                <tr><td class="stg">I</td><td>cT1a-c, cT2a · pT2</td><td>N0</td><td>M0</td><td>PSA &lt;10 · GG1</td></tr>
                <tr><td class="stg">IIA</td><td>cT1-cT2a · pT2</td><td>N0</td><td>M0</td><td>PSA 10-20 · GG1</td></tr>
                <tr><td class="stg">IIA</td><td>cT2b-c</td><td>N0</td><td>M0</td><td>PSA &lt;20 · GG1</td></tr>
                <tr><td class="stg">IIB</td><td>T1-2</td><td>N0</td><td>M0</td><td>PSA &lt;20 · GG2</td></tr>
                <tr><td class="stg">IIC</td><td>T1-2</td><td>N0</td><td>M0</td><td>PSA &lt;20 · GG3-4</td></tr>
                <tr><td class="stg">IIIA</td><td>T1-2</td><td>N0</td><td>M0</td><td>PSA ≥20 · GG1-4</td></tr>
                <tr><td class="stg">IIIB</td><td>T3-4</td><td>N0</td><td>M0</td><td>qualquer PSA · GG1-4</td></tr>
                <tr><td class="stg">IIIC</td><td>qualquer T</td><td>N0</td><td>M0</td><td>qualquer PSA · GG5</td></tr>
                <tr><td class="stg">IVA</td><td>qualquer T</td><td>N1</td><td>M0</td><td>qualquer PSA · GG</td></tr>
                <tr><td class="stg">IVB</td><td>qualquer T</td><td>qualquer N</td><td>M1</td><td>qualquer PSA · GG</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>Grade Group ISUP:</strong> GG1 = Gleason 6 (3+3) · GG2 = Gleason 7 (3+4) · GG3 = Gleason 7 (4+3) · GG4 = Gleason 8 · GG5 = Gleason 9-10. Estadiamento prognóstico AJCC 8ª usa T+N+M+PSA+GG.</div>
          `
        },
        mama: {
          title: 'Mama',
          edition: 'AJCC 8ª · prognóstico',
          icon: 'flower-2',
          color: '#ec4899',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tis</span>Carcinoma in situ
                <ul><li>Tis (DCIS): carcinoma ductal in situ</li><li>Tis (Paget): doença de Paget sem tumor invasivo</li></ul>
              </li>
              <li><span class="code">T1</span>≤2 cm
                <ul><li>T1mi: ≤1 mm</li><li>T1a: 1-5 mm</li><li>T1b: 5-10 mm</li><li>T1c: 10-20 mm</li></ul>
              </li>
              <li><span class="code">T2</span>2-5 cm</li>
              <li><span class="code">T3</span>&gt;5 cm</li>
              <li><span class="code">T4</span>Qualquer tamanho com extensão direta
                <ul>
                  <li>T4a: parede torácica (excluindo peitoral isolado)</li>
                  <li>T4b: pele (ulceração, edema, nódulos satélite)</li>
                  <li>T4c: T4a + T4b</li>
                  <li>T4d: carcinoma inflamatório</li>
                </ul>
              </li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos</h5>
            <ul class="tnm-list">
              <li><span class="code">cN0</span>Sem evidência</li>
              <li><span class="code">cN1</span>Axilares ipsi nível I-II móveis</li>
              <li><span class="code">cN2</span>Axilares ipsi I-II fixos OU mamária interna ipsi sem axilar</li>
              <li><span class="code">cN3</span>Infraclaviculares (nível III), supraclaviculares OU mamária interna + axilar</li>
              <li><span class="code">pN1mi</span>Micrometástase 0,2-2 mm (200 células)</li>
              <li><span class="code">pN1</span>1-3 LN axilares com mets &gt;2 mm</li>
              <li><span class="code">pN2</span>4-9 LN axilares</li>
              <li><span class="code">pN3</span>≥10 LN OU infraclaviculares OU supraclaviculares</li>
            </ul>
            <h5><span class="pill">M</span>Metástases</h5>
            <ul class="tnm-list">
              <li><span class="code">cM0</span>Sem evidência clínica/radiológica</li>
              <li><span class="code">cM0(i+)</span>Sem evidência clínica, mas células tumorais em circulação/medula sem outros sítios</li>
              <li><span class="code">M1</span>Mets à distância detectada por exames clínicos ou histologicamente confirmada &gt;0,2 mm</li>
            </ul>
            <h5>Grupos de estágio anatômico</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IA</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IB</td><td>T0-T1</td><td>N1mi</td><td>M0</td></tr>
                <tr><td class="stg">IIA</td><td>T0-T1 / T2</td><td>N1 / N0</td><td>M0</td></tr>
                <tr><td class="stg">IIB</td><td>T2 / T3</td><td>N1 / N0</td><td>M0</td></tr>
                <tr><td class="stg">IIIA</td><td>T0-T2 / T3</td><td>N2 / N1-2</td><td>M0</td></tr>
                <tr><td class="stg">IIIB</td><td>T4</td><td>N0-2</td><td>M0</td></tr>
                <tr><td class="stg">IIIC</td><td>qualquer T</td><td>N3</td><td>M0</td></tr>
                <tr><td class="stg">IV</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>Estadiamento prognóstico AJCC 8ª</strong> incorpora ER, PR, HER2, grau histológico e Oncotype DX (RS) em N0 HR+/HER2−. Pode reduzir o estágio quando biologia favorável.</div>
          `
        },
        nsclc: {
          title: 'Pulmão · NSCLC',
          edition: 'AJCC 9ª (2024)',
          icon: 'wind',
          color: '#22d3ee',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tis</span>Carcinoma in situ</li>
              <li><span class="code">T1</span>≤3 cm circundado por pulmão/pleura visceral
                <ul><li>T1mi: minimamente invasivo</li><li>T1a: ≤1 cm</li><li>T1b: &gt;1-2 cm</li><li>T1c: &gt;2-3 cm</li></ul>
              </li>
              <li><span class="code">T2</span>&gt;3 e ≤5 cm OU brônquio principal/pleura visceral OU atelectasia
                <ul><li>T2a: &gt;3-4 cm</li><li>T2b: &gt;4-5 cm</li></ul>
              </li>
              <li><span class="code">T3</span>&gt;5-7 cm OU invade parede torácica, pericárdio parietal, n. frênico OU nódulos no mesmo lobo</li>
              <li><span class="code">T4</span>&gt;7 cm OU invade diafragma, mediastino, coração, grandes vasos, traqueia, esôfago, vértebra, carina OU nódulos em lobo ipsi diferente</li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem mets linfonodais</li>
              <li><span class="code">N1</span>Peribrônquicos e/ou hilares ipsi e intrapulmonares</li>
              <li><span class="code">N2</span>Mediastinais ipsi e/ou subcarinais
                <ul><li>N2a: estação única <em>(novidade 9ª ed)</em></li><li>N2b: múltiplas estações <em>(novidade 9ª ed)</em></li></ul>
              </li>
              <li><span class="code">N3</span>Mediastinais contra, hilares contra, escalênicos ou supraclaviculares</li>
            </ul>
            <h5><span class="pill">M</span>Metástases</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástases</li>
              <li><span class="code">M1</span>Metástases à distância
                <ul>
                  <li>M1a: nódulo em lobo contra; nódulos pleurais/pericárdicos; derrame maligno</li>
                  <li>M1b: metástase única extratorácica em órgão único</li>
                  <li>M1c1: múltiplas mets em órgão único <em>(novidade 9ª ed)</em></li>
                  <li>M1c2: múltiplas mets em múltiplos órgãos <em>(novidade 9ª ed)</em></li>
                </ul>
              </li>
            </ul>
            <h5>Grupos de estágio</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th><th>Notas</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td><td></td></tr>
                <tr><td class="stg">IA1-3</td><td>T1mi-T1c</td><td>N0</td><td>M0</td><td>IA1: T1mi-T1a · IA2: T1b · IA3: T1c</td></tr>
                <tr><td class="stg">IB</td><td>T2a</td><td>N0</td><td>M0</td><td></td></tr>
                <tr><td class="stg">IIA</td><td>T2b</td><td>N0</td><td>M0</td><td></td></tr>
                <tr><td class="stg">IIB</td><td>T1-T2b</td><td>N1</td><td>M0</td><td>OU T3 N0</td></tr>
                <tr><td class="stg">IIIA</td><td>T1-T2 / T3 / T4</td><td>N2a / N1 / N0-1</td><td>M0</td><td>9ª ed: N2a única estação</td></tr>
                <tr><td class="stg">IIIB</td><td>T1-T2 / T3-T4</td><td>N2b-N3 / N2</td><td>M0</td><td>múltiplas estações N2</td></tr>
                <tr><td class="stg">IIIC</td><td>T3-T4</td><td>N3</td><td>M0</td><td></td></tr>
                <tr><td class="stg">IVA</td><td>qualquer</td><td>qualquer</td><td>M1a-b ou M1c1</td><td>oligometastático elegível à abordagem local</td></tr>
                <tr><td class="stg">IVB</td><td>qualquer</td><td>qualquer</td><td>M1c2</td><td>múltiplos órgãos com múltiplas mets</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>AJCC 9ª edição (2024):</strong> refinamentos em N2 (estação única vs múltiplas) e M1c (subdivisão por número de órgãos). Importante para selecionar candidatos a abordagem local em oligometastático.</div>
          `
        },
        hcc: {
          title: 'Hepatocelular (HCC)',
          edition: 'AJCC 8ª + BCLC',
          icon: 'droplet',
          color: '#FBBF24',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">T1</span>Tumor solitário sem invasão vascular
                <ul><li>T1a: ≤2 cm</li><li>T1b: &gt;2 cm sem invasão vascular</li></ul>
              </li>
              <li><span class="code">T2</span>Tumor solitário com invasão vascular OU múltiplos ≤5 cm</li>
              <li><span class="code">T3</span>Múltiplos tumores, ≥1 com &gt;5 cm</li>
              <li><span class="code">T4</span>Invasão de ramo maior da veia porta/hepática OU órgãos vizinhos (exceto vesícula) OU peritônio visceral</li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem metástases</li>
              <li><span class="code">N1</span>LN regionais (porta hepática, hepáticos, periarteriais)</li>
            </ul>
            <h5><span class="pill">M</span>Metástases</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástases</li>
              <li><span class="code">M1</span>Metástases à distância</li>
            </ul>
            <h5>Grupos AJCC</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">IA</td><td>T1a</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IB</td><td>T1b</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T2</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIIA</td><td>T3</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIIB</td><td>T4</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IVA</td><td>qualquer</td><td>N1</td><td>M0</td></tr>
                <tr><td class="stg">IVB</td><td>qualquer</td><td>qualquer</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>BCLC (sistema clínico — mais usado)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>Descrição</th><th>Critérios</th><th>Tratamento</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Muito precoce</td><td>Solitário ≤2 cm, CP A, ECOG 0</td><td>Ressecção · ablação</td></tr>
                <tr><td class="stg">A</td><td>Precoce</td><td>Solitário ou ≤3 nódulos ≤3 cm, CP A-B, ECOG 0</td><td>Ressecção · transplante · ablação</td></tr>
                <tr><td class="stg">B</td><td>Intermediário</td><td>Multinodular, CP A-B, ECOG 0</td><td>TARE · TACE · sistêmico em selecionados</td></tr>
                <tr><td class="stg">C</td><td>Avançado</td><td>Invasão vascular ou mets, CP A-B, ECOG 1-2</td><td>Atezo+bev · trem+durva · sorafenibe</td></tr>
                <tr><td class="stg">D</td><td>Terminal</td><td>CP C ou ECOG 3-4</td><td>Cuidados de suporte</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>BCLC</strong> é o sistema mais usado clinicamente — incorpora extensão tumoral, função hepática (Child-Pugh) e performance (ECOG). Define a terapia. AJCC TNM é usado mais para registro/cirurgia.</div>
          `
        },
        net: {
          title: 'NETs (GEP-NET)',
          edition: 'AJCC 8ª · WHO 2019',
          icon: 'heart-pulse',
          color: '#0EA5B7',
          body: `
            <p style="margin:0 0 0.8rem; color:var(--stone); font-size:0.84rem">TNM varia por sítio. Resumo abaixo cobre pNET e siNET (jejuno-íleo). Classificação WHO complementar é mandatória.</p>
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">pNET T1</span>Pâncreas: limitado, &lt;2 cm</li>
              <li><span class="code">pNET T2</span>Pâncreas: limitado, 2-4 cm</li>
              <li><span class="code">pNET T3</span>Pâncreas: &gt;4 cm OU invade duodeno ou ducto biliar</li>
              <li><span class="code">pNET T4</span>Pâncreas: invade órgãos adjacentes ou parede de grandes vasos</li>
              <li><span class="code">siNET T1</span>Jejuno-íleo: ≤1 cm, mucosa/submucosa</li>
              <li><span class="code">siNET T2</span>Jejuno-íleo: &gt;1 cm OU muscular própria</li>
              <li><span class="code">siNET T3</span>Jejuno-íleo: subserosa</li>
              <li><span class="code">siNET T4</span>Jejuno-íleo: peritônio visceral ou outros órgãos</li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem metástases</li>
              <li><span class="code">N1</span>LN regionais positivos</li>
              <li><span class="code">N2</span>Massa(s) mesentérica(s) ≥2 cm e/ou LN extensos (siNET, AJCC 8ª)</li>
            </ul>
            <h5><span class="pill">M</span>Metástases</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástase à distância</li>
              <li><span class="code">M1</span>Metástase à distância
                <ul>
                  <li>M1a: apenas hepática</li>
                  <li>M1b: ≥1 sítio extra-hepático (pulmão, ovário, peritônio não-mesentérico, osso)</li>
                  <li>M1c: ambos (hepática + extra-hepática)</li>
                </ul>
              </li>
            </ul>
            <h5>Grupos AJCC</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">I</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T2-3</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T4 / qualquer T</td><td>N0 / N1-N2</td><td>M0</td></tr>
                <tr><td class="stg">IV</td><td>qualquer</td><td>qualquer</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>WHO 2019 — grade tumoral</h5>
            <table class="stage-tbl">
              <thead><tr><th>Categoria</th><th>Diferenciação</th><th>Critérios</th><th>Manejo típico</th></tr></thead>
              <tbody>
                <tr><td class="stg">NET G1</td><td>Bem-diferenciado</td><td>Ki-67 &lt;3% e &lt;2 mitoses/2 mm2</td><td>Análogo SS · observação</td></tr>
                <tr><td class="stg">NET G2</td><td>Bem-diferenciado</td><td>Ki-67 3-20% ou 2-20 mitoses</td><td>SS · everolimus · PRRT (NETTER-2)</td></tr>
                <tr><td class="stg">NET G3</td><td>Bem-diferenciado</td><td>Ki-67 &gt;20%, morfologia bem-dif</td><td>QT, PRRT, alvo</td></tr>
                <tr><td class="stg">NEC</td><td>Mal-diferenciado</td><td>Ki-67 frequentemente &gt;55%, morfologia pouco-dif</td><td>QT à base de platina (similar SCLC)</td></tr>
                <tr><td class="stg">MiNEN</td><td>Misto NE/não-NE</td><td>≥30% de cada componente</td><td>Tratamento por componente dominante</td></tr>
              </tbody>
            </table>
            <div class="notes">TNM por sítio (estômago, duodeno, apêndice, cólon, reto, pâncreas, jejuno-íleo) tem regras próprias. PRRT é elegível conforme captação SSTR no PET 68Ga-DOTATATE.</div>
          `
        },
        rcc: {
          title: 'Renal (ccRCC)',
          edition: 'AJCC 8ª + IMDC',
          icon: 'shield-half',
          color: '#38BDF8',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">T1</span>≤7 cm, limitado ao rim
                <ul><li>T1a: ≤4 cm</li><li>T1b: &gt;4 e ≤7 cm</li></ul>
              </li>
              <li><span class="code">T2</span>&gt;7 cm, limitado ao rim
                <ul><li>T2a: &gt;7 e ≤10 cm</li><li>T2b: &gt;10 cm</li></ul>
              </li>
              <li><span class="code">T3</span>Invade veia renal, gordura perinéfrica/seio renal, sem ultrapassar Gerota
                <ul>
                  <li>T3a: veia renal ou ramos OU gordura perinéfrica/seio renal</li>
                  <li>T3b: veia cava abaixo do diafragma</li>
                  <li>T3c: veia cava acima do diafragma OU invade parede da cava</li>
                </ul>
              </li>
              <li><span class="code">T4</span>Invade fáscia de Gerota OU adrenal ipsi por contiguidade</li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem mets regional</li>
              <li><span class="code">N1</span>Mets em LN regional(is)</li>
            </ul>
            <h5><span class="pill">M</span>Metástases</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástase</li>
              <li><span class="code">M1</span>Mets à distância</li>
            </ul>
            <h5>Grupos AJCC</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">I</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T2</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T1-T2 / T3</td><td>N1 / N0-N1</td><td>M0</td></tr>
                <tr><td class="stg">IV</td><td>T4 / qualquer</td><td>qualquer / qualquer</td><td>M0 / M1</td></tr>
              </tbody>
            </table>
            <h5>Risco IMDC (Heng) — guia de terapia sistêmica em mRCC</h5>
            <table class="stage-tbl">
              <thead><tr><th>Categoria</th><th>Fatores</th><th>Critérios (qualquer)</th><th>Tratamento</th></tr></thead>
              <tbody>
                <tr><td class="stg">Bom</td><td>0</td><td>KPS ≥80%, Ca normal, Hb normal, neutrófilos normais, plaquetas normais, dx → tx ≥1 ano</td><td>Cabozantinibe ± nivo · sunitinibe · pazopanibe</td></tr>
                <tr><td class="stg">Intermediário</td><td>1-2</td><td>Qualquer dos critérios alterado</td><td>Nivo+ipi · pembro+axi · pembro+lenva · cabozantinibe</td></tr>
                <tr><td class="stg">Pobre</td><td>≥3</td><td>Múltiplos critérios alterados</td><td>Nivo+ipi (preferido) · pembro+axi · pembro+lenva · cabozantinibe</td></tr>
              </tbody>
            </table>
            <div class="notes">Estadiamento TNM define cirurgia (radical vs parcial) e necessidade de adjuvante. IMDC define tratamento sistêmico em metastático.</div>
          `
        },
        crc: {
          title: 'Colorretal',
          edition: 'AJCC 8ª',
          icon: 'activity-square',
          color: '#fb923c',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tis</span>In situ (intramucoso, sem ultrapassar muscular da mucosa)</li>
              <li><span class="code">T1</span>Invade submucosa</li>
              <li><span class="code">T2</span>Invade muscular própria</li>
              <li><span class="code">T3</span>Invade subserosa ou tecidos pericólicos/perirretais não-peritonizados</li>
              <li><span class="code">T4</span>Invade peritônio visceral OU órgãos
                <ul><li>T4a: penetra peritônio visceral</li><li>T4b: invade direta ou aderência a outros órgãos</li></ul>
              </li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem metástases regionais</li>
              <li><span class="code">N1</span>1-3 LN positivos
                <ul><li>N1a: 1 LN</li><li>N1b: 2-3 LN</li><li>N1c: depósitos tumorais sem mets em LN</li></ul>
              </li>
              <li><span class="code">N2</span>≥4 LN
                <ul><li>N2a: 4-6 LN</li><li>N2b: ≥7 LN</li></ul>
              </li>
            </ul>
            <h5><span class="pill">M</span>Metástases</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem mets</li>
              <li><span class="code">M1</span>Mets à distância
                <ul><li>M1a: 1 órgão (fígado, pulmão, ovário, LN não-regional)</li><li>M1b: ≥2 órgãos sem peritônio</li><li>M1c: peritoneal, com ou sem outros sítios</li></ul>
              </li>
            </ul>
            <h5>Grupos de estágio</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">I</td><td>T1-T2</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIA</td><td>T3</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIB</td><td>T4a</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIC</td><td>T4b</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIIA</td><td>T1-T2 / T1</td><td>N1 / N2a</td><td>M0</td></tr>
                <tr><td class="stg">IIIB</td><td>T3-T4a / T2-T3 / T1-T2</td><td>N1 / N2a / N2b</td><td>M0</td></tr>
                <tr><td class="stg">IIIC</td><td>T4a / T3-T4a / T4b</td><td>N2a / N2b / N1-N2</td><td>M0</td></tr>
                <tr><td class="stg">IVA</td><td>qualquer</td><td>qualquer</td><td>M1a</td></tr>
                <tr><td class="stg">IVB</td><td>qualquer</td><td>qualquer</td><td>M1b</td></tr>
                <tr><td class="stg">IVC</td><td>qualquer</td><td>qualquer</td><td>M1c</td></tr>
              </tbody>
            </table>
            <div class="notes">Adjuvância em estágio II depende de fatores de risco (T4, perfuração, &lt;12 LN avaliados, MSI alto, perineural). MSI/dMMR define elegibilidade para imunoterapia em metastático (KEYNOTE-177).</div>
          `
        },
        gastric: {
          title: 'Gástrico / GEJ',
          edition: 'AJCC 8ª',
          icon: 'circle',
          color: '#f87171',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tis</span>In situ, sem invasão da lâmina própria</li>
              <li><span class="code">T1</span>Lâmina própria, muscular da mucosa ou submucosa
                <ul><li>T1a: lâmina própria/muscular da mucosa</li><li>T1b: submucosa</li></ul>
              </li>
              <li><span class="code">T2</span>Invade muscular própria</li>
              <li><span class="code">T3</span>Penetra subserosa sem invasão de peritônio visceral</li>
              <li><span class="code">T4</span>Invade serosa ou estruturas adjacentes
                <ul><li>T4a: serosa (peritônio visceral)</li><li>T4b: invade estruturas/órgãos adjacentes</li></ul>
              </li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem mets</li>
              <li><span class="code">N1</span>1-2 LN positivos</li>
              <li><span class="code">N2</span>3-6 LN</li>
              <li><span class="code">N3</span>≥7 LN
                <ul><li>N3a: 7-15</li><li>N3b: ≥16</li></ul>
              </li>
            </ul>
            <h5><span class="pill">M</span>Metástases</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástase</li>
              <li><span class="code">M1</span>Mets à distância (incluindo peritoneal)</li>
            </ul>
            <h5>Grupos de estágio</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IA</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IB</td><td>T1 / T2</td><td>N1 / N0</td><td>M0</td></tr>
                <tr><td class="stg">IIA</td><td>T1 / T2 / T3</td><td>N2 / N1 / N0</td><td>M0</td></tr>
                <tr><td class="stg">IIB</td><td>T1 / T2 / T3 / T4a</td><td>N3a / N2 / N1 / N0</td><td>M0</td></tr>
                <tr><td class="stg">IIIA</td><td>T2-T4a</td><td>N1-N3</td><td>M0</td></tr>
                <tr><td class="stg">IIIB</td><td>T1-T4a / T4b</td><td>N3b / N0-N2</td><td>M0</td></tr>
                <tr><td class="stg">IIIC</td><td>T4b</td><td>N3a-N3b</td><td>M0</td></tr>
                <tr><td class="stg">IV</td><td>qualquer</td><td>qualquer</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>Tipo histológico Lauren</h5>
            <table class="stage-tbl">
              <thead><tr><th>Tipo</th><th>Características</th><th>Perfil clínico</th><th>Cirurgia</th></tr></thead>
              <tbody>
                <tr><td class="stg">Intestinal</td><td>Bem-diferenciado, glandular</td><td>Idoso, distal, melhor prognóstico</td><td>Gastrectomia subtotal</td></tr>
                <tr><td class="stg">Difuso</td><td>Pouco coeso, anel de sinete</td><td>Jovem, proximal, prognóstico pior; CDH1</td><td>Gastrectomia total</td></tr>
                <tr><td class="stg">Misto</td><td>Componentes dos dois</td><td>~10-15% dos casos</td><td>Conforme componente dominante</td></tr>
              </tbody>
            </table>
            <div class="notes">HER2 (IHC + ISH), MSI/dMMR e PD-L1 (CPS) são marcadores essenciais antes de tratamento avançado. CLDN18.2 emergente (zolbetuximabe). EBV+ é subgrupo distinto (5-10%) com alta resposta à IO.</div>
          `
        },
        bexiga: {
          title: 'Bexiga · Carcinoma Urotelial',
          edition: 'AJCC 8ª · NMIBC vs MIBC',
          icon: 'droplets',
          color: '#EAB308',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tx</span>Não pode ser avaliado</li>
              <li><span class="code">T0</span>Sem evidência de tumor primário</li>
              <li><span class="code">Ta</span>Carcinoma papilar não-invasivo (NMIBC, low-grade ou high-grade)</li>
              <li><span class="code">Tis</span>Carcinoma in situ (CIS) plano de alto grau ("flat tumor")</li>
              <li><span class="code">T1</span>Tumor invade tecido conjuntivo subepitelial (lâmina própria) — NMIBC alto risco</li>
              <li><span class="code">T2</span>Tumor invade muscular própria (MIBC inicia aqui)
                <ul>
                  <li>T2a: invade muscular superficial (metade interna)</li>
                  <li>T2b: invade muscular profunda (metade externa)</li>
                </ul>
              </li>
              <li><span class="code">T3</span>Tumor invade tecido perivesical
                <ul>
                  <li>T3a: invasão microscópica</li>
                  <li>T3b: invasão macroscópica (massa extravesical)</li>
                </ul>
              </li>
              <li><span class="code">T4</span>Tumor invade órgãos adjacentes
                <ul>
                  <li>T4a: invade próstata, vesículas seminais, útero ou vagina</li>
                  <li>T4b: invade parede pélvica ou parede abdominal</li>
                </ul>
              </li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos regionais (pélvicos)</h5>
            <ul class="tnm-list">
              <li><span class="code">Nx</span>Não avaliados</li>
              <li><span class="code">N0</span>Sem metástase em LN regionais</li>
              <li><span class="code">N1</span>1 LN pélvico verdadeiro (hipogástrico, obturador, ilíaco externo, presacral)</li>
              <li><span class="code">N2</span>Múltiplos LN pélvicos (≥2 LN da pelve verdadeira)</li>
              <li><span class="code">N3</span>LN ilíaco comum (acima da bifurcação aórtica) — antes era M1</li>
            </ul>
            <h5><span class="pill">M</span>Metástases à distância</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástase à distância</li>
              <li><span class="code">M1a</span>Metástase em LN não-regional (acima de ilíaca comum, retroperitoneal)</li>
              <li><span class="code">M1b</span>Outras metástases à distância (víscera, osso, etc.)</li>
            </ul>
            <h5>Grupos de estágio</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">0a</td><td>Ta</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">0is</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">I</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T2a-T2b</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIIA</td><td>T3a-T4a · T1-T4a</td><td>N0 · N1</td><td>M0</td></tr>
                <tr><td class="stg">IIIB</td><td>T1-T4a</td><td>N2-N3</td><td>M0</td></tr>
                <tr><td class="stg">IVA</td><td>T4b · qualquer T</td><td>qualquer N · qualquer N</td><td>M0 · M1a</td></tr>
                <tr><td class="stg">IVB</td><td>qualquer T</td><td>qualquer N</td><td>M1b</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>NMIBC vs MIBC:</strong> NMIBC (Ta, Tis, T1) — tratamento local: RTU + intravesical (BCG ou MMC ou novos agentes — Adstiladrin, TAR-200, Anktiva). MIBC (T2-T4) — cistectomia radical ± neoadj/adj sistêmico (NIAGARA, CheckMate-274, AMBASSADOR).</div>
            <h5>BCG Schedule (SWOG)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Fase</th><th>Esquema</th><th>Indicação</th></tr></thead>
              <tbody>
                <tr><td>Indução</td><td>1 instilação semanal × 6 sem</td><td>Após RTU completa, NMIBC alto risco</td></tr>
                <tr><td>Manutenção</td><td>3 instilações semanais (1×/sem × 3 sem) aos 3, 6, 12, 18, 24, 30, 36 meses</td><td>SWOG 8507 — reduz recorrência e progressão</td></tr>
                <tr><td>BCG-unresponsive</td><td>—</td><td>Persistência ou recidiva ≤6m após adequada exposição (≥5 instilações indução + ≥2 manutenção)</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>Trato superior urotelial:</strong> mesmo TNM aplicado a pelve renal e ureter, com particularidades: T1 invade lâmina própria, T2 muscular, T3 perirrenal/periuretérica, T4 órgãos adjacentes. Tratamento: nefroureterectomia ± POUT (gem-cis/gem-carbo adjuvante x4 ciclos). Refs: Amin MB et al. AJCC Manual 8ª ed. 2017; Babjuk M et al. Eur Urol 2022 (NMIBC); Witjes JA et al. Eur Urol 2024 (MIBC).</div>
          `
        },
        tireoide: {
          title: 'Tireoide',
          edition: 'AJCC 8ª · DTC/MTC/ATC',
          icon: 'circle-dot',
          color: '#D946EF',
          body: `
            <h5><span class="pill">T</span>Tumor primário (DTC e MTC)</h5>
            <ul class="tnm-list">
              <li><span class="code">Tx/T0</span>Não avaliado / sem evidência</li>
              <li><span class="code">T1</span>Tumor ≤2 cm limitado à tireoide
                <ul>
                  <li>T1a: ≤1 cm</li>
                  <li>T1b: &gt;1 cm e ≤2 cm</li>
                </ul>
              </li>
              <li><span class="code">T2</span>Tumor &gt;2 cm e ≤4 cm limitado à tireoide</li>
              <li><span class="code">T3</span>Tumor &gt;4 cm ou com extensão extratireoidiana mínima
                <ul>
                  <li>T3a: &gt;4 cm limitado à tireoide</li>
                  <li>T3b: extensão extratireoidiana mínima (esternotireoideo, peri-tireoidiano)</li>
                </ul>
              </li>
              <li><span class="code">T4</span>Extensão extratireoidiana extensa
                <ul>
                  <li>T4a: invade tecido subcutâneo, laringe, traqueia, esôfago ou nervo laríngeo recorrente</li>
                  <li>T4b: invade fáscia pré-vertebral ou envolve carótida ou vasos mediastinais</li>
                </ul>
              </li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos regionais</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem metástase
                <ul>
                  <li>N0a: ≥1 LN benigno citologia/histologia</li>
                  <li>N0b: ausência de evidência clínica/radiológica</li>
                </ul>
              </li>
              <li><span class="code">N1a</span>LN nível VI ou VII (pré-traqueal, paratraqueal, pré-laríngeo/Delphian, mediastinal superior)</li>
              <li><span class="code">N1b</span>LN cervical lateral unilateral (níveis I-V), bilateral ou contralateral, OU retrofaríngeo</li>
            </ul>
            <h5><span class="pill">M</span>Metástases à distância</h5>
            <ul class="tnm-list">
              <li><span class="code">M0/M1</span>Sem / com metástase à distância</li>
            </ul>
            <h5>Estadiamento DTC (papilífero/folicular) — cutoff 55 anos</h5>
            <table class="stage-tbl">
              <thead><tr><th>Idade</th><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td><strong>&lt;55 a</strong></td><td class="stg">I</td><td>qualquer T</td><td>qualquer N</td><td>M0</td></tr>
                <tr><td><strong>&lt;55 a</strong></td><td class="stg">II</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
                <tr><td><strong>≥55 a</strong></td><td class="stg">I</td><td>T1, T2</td><td>N0/Nx</td><td>M0</td></tr>
                <tr><td><strong>≥55 a</strong></td><td class="stg">II</td><td>T1, T2 · T3a-3b</td><td>N1 · qualquer N</td><td>M0</td></tr>
                <tr><td><strong>≥55 a</strong></td><td class="stg">III</td><td>T4a</td><td>qualquer N</td><td>M0</td></tr>
                <tr><td><strong>≥55 a</strong></td><td class="stg">IVA</td><td>T4b</td><td>qualquer N</td><td>M0</td></tr>
                <tr><td><strong>≥55 a</strong></td><td class="stg">IVB</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>Estadiamento MTC (medular)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">I</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T2-T3</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T1-T3</td><td>N1a</td><td>M0</td></tr>
                <tr><td class="stg">IVA</td><td>T4a · T1-T3</td><td>qualquer N · N1b</td><td>M0</td></tr>
                <tr><td class="stg">IVB</td><td>T4b</td><td>qualquer N</td><td>M0</td></tr>
                <tr><td class="stg">IVC</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>Estadiamento ATC (anaplásico) — sempre estágio IV</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">IVA</td><td>T1-T3a</td><td>N0/Nx</td><td>M0</td></tr>
                <tr><td class="stg">IVB</td><td>T1-T3a · T3b-T4</td><td>N1 · qualquer N</td><td>M0</td></tr>
                <tr><td class="stg">IVC</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>DTC:</strong> tireoidectomia + 131I ablativo conforme risco ATA (low/intermediate/high). <strong>MTC:</strong> tireoidectomia total + dissecção VI; calcitonina e CEA seriados; testar RET (MEN2). <strong>ATC:</strong> sempre IV; mutação BRAF V600E em 30-40% (dabrafenib + trametinibe), considerar lenvatinibe e PD-1. <strong>Imagem nuclear:</strong> 131I para DTC tireoglobulina-elevado; 68Ga-DOTATATE em MTC; 18F-FDG em DTC iodo-refratário e em ATC.</div>
          `
        },
        hnscc: {
          title: 'Cabeça e Pescoço (HNSCC)',
          edition: 'AJCC 8ª · HPV+ vs HPV-',
          icon: 'user',
          color: '#A855F7',
          body: `
            <h5>Sistema HPV-positivo (orofaringe p16+) — clínico (cT/cN)</h5>
            <ul class="tnm-list">
              <li><span class="code">cT1</span>Tumor ≤2 cm</li>
              <li><span class="code">cT2</span>Tumor &gt;2 cm e ≤4 cm</li>
              <li><span class="code">cT3</span>Tumor &gt;4 cm ou extensão à superfície lingual da epiglote</li>
              <li><span class="code">cT4</span>Doença localmente avançada
                <ul>
                  <li>cT4 (não T4a/b separados em HPV+): invade laringe, língua extrínseca, pterigoideo medial, palato duro, mandíbula ou estruturas além</li>
                </ul>
              </li>
              <li><span class="code">cN0</span>Sem LN regional</li>
              <li><span class="code">cN1</span>LN ipsilateral, ≤6 cm</li>
              <li><span class="code">cN2</span>LN contralateral ou bilateral, ≤6 cm</li>
              <li><span class="code">cN3</span>LN &gt;6 cm</li>
            </ul>
            <h5>Sistema HPV-positivo — patológico (pN)</h5>
            <ul class="tnm-list">
              <li><span class="code">pN0</span>Sem metástase em LN dissecado</li>
              <li><span class="code">pN1</span>≤4 LN+</li>
              <li><span class="code">pN2</span>≥5 LN+</li>
            </ul>
            <h5>Estadiamento HPV+ (orofaringe p16+)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>cT</th><th>cN</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">I</td><td>T1-T2</td><td>N0-N1</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T1-T2 · T3</td><td>N2 · N0-N2</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T1-T3 · T4</td><td>N3 · N0-N3</td><td>M0</td></tr>
                <tr><td class="stg">IV</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>Sistema HPV-negativo (oral, hipofaringe, laringe, cavidade nasal/seios)</h5>
            <ul class="tnm-list">
              <li><span class="code">T1</span>≤2 cm</li>
              <li><span class="code">T2</span>&gt;2 e ≤4 cm</li>
              <li><span class="code">T3</span>&gt;4 cm ou extensão profunda (depth of invasion &gt;10 mm em cavidade oral)</li>
              <li><span class="code">T4a</span>Doença moderadamente avançada (invade osso, língua extrínseca, pele)</li>
              <li><span class="code">T4b</span>Doença muito avançada (espaço mastigatório, pterigoide, base do crânio, encartar carótida)</li>
              <li><span class="code">N1</span>1 LN ipsilateral ≤3 cm, ENE-</li>
              <li><span class="code">N2a</span>1 LN ipsilateral &gt;3 e ≤6 cm, ENE-</li>
              <li><span class="code">N2b</span>Múltiplos LN ipsilaterais ≤6 cm, ENE-</li>
              <li><span class="code">N2c</span>LN bilateral ou contralateral ≤6 cm, ENE-</li>
              <li><span class="code">N3a</span>Qualquer LN &gt;6 cm, ENE-</li>
              <li><span class="code">N3b</span>Qualquer LN com ENE+ (extensão extranodal clínica/patológica)</li>
            </ul>
            <h5>Estadiamento HPV-</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">I</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T2</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T3 · T1-3</td><td>N0 · N1</td><td>M0</td></tr>
                <tr><td class="stg">IVA</td><td>T1-3 · T4a</td><td>N2 · N0-2</td><td>M0</td></tr>
                <tr><td class="stg">IVB</td><td>T4b · qualquer T</td><td>qualquer N · N3</td><td>M0</td></tr>
                <tr><td class="stg">IVC</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>HPV+:</strong> melhor prognóstico — RT sozinha em estágios precoces; quimiorradio (cisplatina) em avançado; deintensificação em estudo. <strong>HPV-:</strong> tratamento mais agressivo; ENE+ é fator prognóstico crítico (estágio IVB). <strong>Imagem:</strong> 18F-FDG PET/CT é padrão para staging inicial avançado, planejamento de RT e avaliação de resposta (NI-RADS após 12 sem). Refs: AJCC 8ª ed. 2017; Lydiatt WM et al. CA Cancer J Clin 2017.</div>
          `
        },
        esofago: {
          title: 'Esôfago e Junção Esofagogástrica (EGJ)',
          edition: 'AJCC 8ª · ESCC + EAC',
          icon: 'circle',
          color: '#F43F5E',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tis</span>Displasia de alto grau / carcinoma in situ</li>
              <li><span class="code">T1</span>Invade lâmina própria, muscular da mucosa ou submucosa
                <ul>
                  <li>T1a: lâmina própria ou muscular da mucosa</li>
                  <li>T1b: submucosa</li>
                </ul>
              </li>
              <li><span class="code">T2</span>Invade muscular própria</li>
              <li><span class="code">T3</span>Invade adventícia</li>
              <li><span class="code">T4</span>Invade estruturas adjacentes
                <ul>
                  <li>T4a: pleura, pericárdio, ázigos, diafragma ou peritônio</li>
                  <li>T4b: aorta, traquéia, vértebra ou outras estruturas adjacentes (irrecíavel)</li>
                </ul>
              </li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos regionais (cervicais a celíacos)</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem LN+ regional</li>
              <li><span class="code">N1</span>1-2 LN+</li>
              <li><span class="code">N2</span>3-6 LN+</li>
              <li><span class="code">N3</span>≥7 LN+</li>
            </ul>
            <h5><span class="pill">M</span>Metástase à distância</h5>
            <ul class="tnm-list">
              <li><span class="code">M0/M1</span>Sem / com metástase à distância (incluindo LN não-regionais)</li>
            </ul>
            <h5>Estadiamento clínico (cTNM) — Adenocarcinoma (EAC)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>cT</th><th>cN</th><th>cM</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">I</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIA</td><td>T1</td><td>N1</td><td>M0</td></tr>
                <tr><td class="stg">IIB</td><td>T2</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T2 · T3 · T4a</td><td>N1 · N0-N1 · N0-N1</td><td>M0</td></tr>
                <tr><td class="stg">IVA</td><td>T1-T4a · T4b · qualquer T</td><td>N2 · qualquer N · N3</td><td>M0</td></tr>
                <tr><td class="stg">IVB</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>Estadiamento clínico (cTNM) — Carcinoma escamoso (ESCC)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>cT</th><th>cN</th><th>cM</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">I</td><td>T1</td><td>N0-N1</td><td>M0</td></tr>
                <tr><td class="stg">II</td><td>T2 · T3</td><td>N0-N1 · N0</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T1-T2 · T3</td><td>N2 · N1-N2</td><td>M0</td></tr>
                <tr><td class="stg">IVA</td><td>T4a-T4b · qualquer T</td><td>N0-N2 · N3</td><td>M0</td></tr>
                <tr><td class="stg">IVB</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>Classificação Siewert (junção esofagogástrica)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Tipo</th><th>Localização do epicentro</th><th>Tratamento (regra geral)</th></tr></thead>
              <tbody>
                <tr><td>I</td><td>1-5 cm acima da JEG</td><td>Esofagectomia (regras esôfago)</td></tr>
                <tr><td>II</td><td>1 cm acima a 2 cm abaixo (cárdia)</td><td>Esofagectomia distal/gastrectomia proximal</td></tr>
                <tr><td>III</td><td>2-5 cm abaixo da JEG</td><td>Gastrectomia total/proximal (regras gástrico)</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>Sistemas de estadiamento separados:</strong> AJCC 8ª inclui clínico (cTNM), patológico (pTNM) e pós-neoadjuvante (ypTNM) com critérios distintos. Siewert tipo I/II é estadiado como esôfago; Siewert III como gástrico. <strong>Tratamento moderno:</strong> CROSS regimen (carboplatina/paclitaxel + RT 41,4 Gy) → cirurgia para EAC localmente avançado; CheckMate-577 (nivolumab adjuvante 1 ano após neoadj+cirurgia com doença residual). FDG-PET é padrão para staging e resposta. Refs: AJCC 8ª ed.; Rice TW et al. Ann Cardiothorac Surg 2017; Kelly RJ et al. NEJM 2021 (CheckMate-577).</div>
          `
        },
        pancreas: {
          title: 'Pâncreas (Adenocarcinoma)',
          edition: 'AJCC 8ª · PDAC',
          icon: 'hexagon',
          color: '#84CC16',
          body: `
            <h5><span class="pill">T</span>Tumor primário</h5>
            <ul class="tnm-list">
              <li><span class="code">Tis</span>Carcinoma in situ (PanIN-3, NIM, MCN, IPMN com displasia alto grau)</li>
              <li><span class="code">T1</span>Tumor ≤2 cm
                <ul>
                  <li>T1a: ≤0,5 cm</li>
                  <li>T1b: &gt;0,5 cm e &lt;1 cm</li>
                  <li>T1c: 1-2 cm</li>
                </ul>
              </li>
              <li><span class="code">T2</span>Tumor &gt;2 cm e ≤4 cm</li>
              <li><span class="code">T3</span>Tumor &gt;4 cm</li>
              <li><span class="code">T4</span>Tumor envolve eixo celíaco, AMS (artéria mesentérica superior) ou artéria hepática comum (independente do tamanho) — irressecável</li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos regionais</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem metástase em LN regionais</li>
              <li><span class="code">N1</span>1-3 LN+ regionais</li>
              <li><span class="code">N2</span>≥4 LN+ regionais</li>
            </ul>
            <h5><span class="pill">M</span>Metástase à distância</h5>
            <ul class="tnm-list">
              <li><span class="code">M0/M1</span>Sem / com metástase à distância (incluindo carcinomatose peritoneal)</li>
            </ul>
            <h5>Grupos de estágio</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IA</td><td>T1</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IB</td><td>T2</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIA</td><td>T3</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIB</td><td>T1-T3</td><td>N1</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>T1-T3 · T4</td><td>N2 · qualquer N</td><td>M0</td></tr>
                <tr><td class="stg">IV</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <h5>Resectability — NCCN/ISGPS</h5>
            <table class="stage-tbl">
              <thead><tr><th>Categoria</th><th>Definição vascular</th><th>Tratamento</th></tr></thead>
              <tbody>
                <tr><td><strong>Ressecável</strong></td><td>Sem contato com AMS, eixo celíaco ou hepática comum; contato &lt;180° com VMS/VP sem irregularidade</td><td>Cirurgia upfront (Whipple, distal, total)</td></tr>
                <tr><td><strong>Borderline</strong></td><td>Contato 180° com AMS/VMS/VP recuperável; ou contato com hepática comum sem extensão eixo celíaco</td><td>Quimio neoadj (FOLFIRINOX ou Gem-NabP) → cirurgia se resposta</td></tr>
                <tr><td><strong>Locally advanced (LAPC)</strong></td><td>Contato &gt;180° com AMS, eixo celíaco; oclusão VMS/VP irrecuperável</td><td>Quimio sistêmica ± RT; cirurgia se conversão</td></tr>
                <tr><td><strong>Metastático</strong></td><td>Mets a distância (M1) — fígado, peritônio, pulmão</td><td>Quimio paliativa (FOLFIRINOX, Gem-NabP); IO em MSI-H/dMMR; PARPi em BRCA1/2</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>Marcadores:</strong> CA 19-9 (cuidado em Lewis-negativos ~10%). <strong>Quimio:</strong> FOLFIRINOX modificado (PRODIGE 35) supera Gem-NabP em performance status bom; Gem-NabP em ECOG 1-2. <strong>Adjuvante:</strong> mFOLFIRINOX por 6 meses (PRODIGE 24) é padrão. <strong>Genômica:</strong> testar BRCA1/2, MSI-H, NTRK, KRAS G12C (sotorasibe/adagrasibe em fase clínica). <strong>Imagem:</strong> 68Ga-FAPI-PET emergente (especialmente para fibrose e implantes peritoneais que 18F-FDG perde). Refs: Tempero MA et al. NCCN Guidelines 2024; Conroy T et al. NEJM 2018 (PRODIGE 24).</div>
          `
        },
        linfoma: {
          title: 'Linfoma (Hodgkin e não-Hodgkin)',
          edition: 'Lugano 2014 · Ann Arbor revisado',
          icon: 'git-branch',
          color: '#14B8A6',
          body: `
            <h5>Estadiamento de Lugano (2014) — substitui Ann Arbor para HL e NHL</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>Definição</th></tr></thead>
              <tbody>
                <tr><td class="stg">I</td><td>1 região linfonodal OU 1 sítio extralinfático isolado (IE)</td></tr>
                <tr><td class="stg">II</td><td>≥2 regiões linfonodais no <strong>mesmo lado do diafragma</strong> · IIE = + extensão extralinfática contígua</td></tr>
                <tr><td class="stg">II bulky</td><td>Estágio II com massa volumosa: HL ≥10 cm ou ≥1/3 do diâmetro torácico em CT; NHL definição variável</td></tr>
                <tr><td class="stg">III</td><td>Regiões em <strong>ambos os lados do diafragma</strong> · IIIE = + sítio extralinfático contíguo · IIIS = + baço</td></tr>
                <tr><td class="stg">IV</td><td>Doença extralinfática difusa (medula óssea, fígado, pulmão, SNC) — não contígua a sítio nodal</td></tr>
              </tbody>
            </table>
            <h5>Modificadores</h5>
            <ul class="tnm-list">
              <li><span class="code">A</span>Sem sintomas B</li>
              <li><span class="code">B</span>Presença de pelo menos 1 sintoma B
                <ul>
                  <li>Febre &gt;38°C inexplicada</li>
                  <li>Sudorese noturna profusa</li>
                  <li>Perda de peso &gt;10% nos últimos 6 meses</li>
                </ul>
              </li>
              <li><span class="code">E</span>Extensão extranodal contígua a partir de sítio linfonodal</li>
              <li><span class="code">X</span>Bulky disease (não mais usado em Lugano — incorporado descritivamente)</li>
              <li><span class="code">S</span>Envolvimento esplênico (incluído nas categorias III)</li>
            </ul>
            <h5>Resposta — Critérios de Deauville (FDG-PET)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Score</th><th>Captação vs referência</th><th>Interpretação</th></tr></thead>
              <tbody>
                <tr><td>1</td><td>Sem captação acima do background</td><td>Resposta completa metabólica (CMR)</td></tr>
                <tr><td>2</td><td>Captação ≤ pool sanguíneo mediastinal</td><td>CMR</td></tr>
                <tr><td>3</td><td>Captação &gt; pool mediastinal e ≤ fígado</td><td>CMR (em maioria dos contextos; PMR em interim de HL primário)</td></tr>
                <tr><td>4</td><td>Captação &gt; fígado moderadamente</td><td>Resposta parcial metabólica (PMR) se redução; doença residual se não</td></tr>
                <tr><td>5</td><td>Captação &gt;&gt; fígado ou novas lesões</td><td>Doença em progressão (PMD) ou refratária</td></tr>
              </tbody>
            </table>
            <h5>Critérios de bulky · LDH · IPI</h5>
            <table class="stage-tbl">
              <thead><tr><th>Sistema</th><th>Componentes</th><th>Uso</th></tr></thead>
              <tbody>
                <tr><td>IPI (NHL agressivo)</td><td>Idade &gt;60 · LDH alta · ECOG ≥2 · Estágio III/IV · ≥2 sítios extranodais</td><td>Risco baixo (0-1), int-baixo (2), int-alto (3), alto (4-5) — preditor de OS em DLBCL</td></tr>
                <tr><td>FLIPI (folicular)</td><td>Idade &gt;60 · LDH alta · Hb &lt;12 · &gt;4 áreas nodais · Estágio III/IV</td><td>Risco baixo, intermediário, alto</td></tr>
                <tr><td>HL bulky</td><td>Massa ≥10 cm OU &gt;1/3 do diâmetro torácico em CT</td><td>Indica intensificação RT/QT</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>Imagem:</strong> 18F-FDG PET/CT é padrão para staging inicial e avaliação de resposta em HL e NHL agressivo (DLBCL). Lugano define "interim PET" (após 2-4 ciclos) como ferramenta para escalar/desescalar tratamento (RAPID, RATHL para HL; PETAL para DLBCL). Estudo medular (BMB) não é mais obrigatório em HL e DLBCL se PET claramente positivo ou negativo. <strong>Tratamento:</strong> HL — ABVD ± BV (BrECADD em estudos); BEACOPP em alto risco. DLBCL — R-CHOP × 6 (ou Pola-R-CHP no POLARIX); CAR-T em recidiva (ZUMA-7, TRANSFORM). Refs: Cheson BD et al. J Clin Oncol 2014 (Lugano); Meignan M et al. Leuk Lymphoma 2009 (Deauville).</div>
          `
        },
        melanoma: {
          title: 'Melanoma cutâneo',
          edition: 'AJCC 8ª · LDH',
          icon: 'sparkles',
          color: '#8B5CF6',
          body: `
            <h5><span class="pill">T</span>Tumor primário (Breslow + ulceração)</h5>
            <ul class="tnm-list">
              <li><span class="code">Tis</span>Melanoma in situ</li>
              <li><span class="code">T1</span>Espessura ≤1,0 mm
                <ul>
                  <li>T1a: &lt;0,8 mm sem ulceração</li>
                  <li>T1b: &lt;0,8 mm com ulceração OU 0,8-1,0 mm com/sem ulceração</li>
                </ul>
              </li>
              <li><span class="code">T2</span>1,01-2,0 mm
                <ul>
                  <li>T2a: sem ulceração · T2b: com ulceração</li>
                </ul>
              </li>
              <li><span class="code">T3</span>2,01-4,0 mm
                <ul>
                  <li>T3a: sem ulceração · T3b: com ulceração</li>
                </ul>
              </li>
              <li><span class="code">T4</span>&gt;4,0 mm
                <ul>
                  <li>T4a: sem ulceração · T4b: com ulceração</li>
                </ul>
              </li>
            </ul>
            <h5><span class="pill">N</span>Linfonodos regionais e MIT/satélite</h5>
            <ul class="tnm-list">
              <li><span class="code">N0</span>Sem LN+ regional</li>
              <li><span class="code">N1</span>1 LN+ OU presença de microsatélite/MIT/in-transit
                <ul>
                  <li>N1a: 1 LN clinicamente oculto (SLN+)</li>
                  <li>N1b: 1 LN clinicamente detectado</li>
                  <li>N1c: 0 LN+ mas presença de MIT/satélite/in-transit</li>
                </ul>
              </li>
              <li><span class="code">N2</span>2-3 LN+ OU 1 LN+ com MIT/satélite/in-transit
                <ul>
                  <li>N2a: 2-3 LN clinicamente ocultos (SLN+)</li>
                  <li>N2b: 2-3 LN, ≥1 detectado clinicamente</li>
                  <li>N2c: 1 LN+ (oculto ou detectado) com MIT/satélite/in-transit</li>
                </ul>
              </li>
              <li><span class="code">N3</span>≥4 LN+ OU 2-3 LN+ com MIT/satélite OU LN matted (agregados)
                <ul>
                  <li>N3a: ≥4 LN ocultos · N3b: ≥4 LN, ≥1 clínico ou matted · N3c: ≥2 LN+ com MIT/satélite/in-transit</li>
                </ul>
              </li>
            </ul>
            <h5><span class="pill">M</span>Metástase à distância (com LDH)</h5>
            <ul class="tnm-list">
              <li><span class="code">M0</span>Sem metástase à distância</li>
              <li><span class="code">M1a</span>Pele, subcutâneo, mama, LN distantes (não SNC)
                <ul><li>M1a(0): LDH normal · M1a(1): LDH elevada</li></ul>
              </li>
              <li><span class="code">M1b</span>Pulmão (com ou sem M1a)
                <ul><li>M1b(0): LDH normal · M1b(1): LDH elevada</li></ul>
              </li>
              <li><span class="code">M1c</span>Vísceras não-SNC (com ou sem M1a/M1b)
                <ul><li>M1c(0): LDH normal · M1c(1): LDH elevada</li></ul>
              </li>
              <li><span class="code">M1d</span>SNC (com ou sem outros sítios)
                <ul><li>M1d(0): LDH normal · M1d(1): LDH elevada</li></ul>
              </li>
            </ul>
            <h5>Grupos de estágio (clinical · cTNM)</h5>
            <table class="stage-tbl">
              <thead><tr><th>Estágio</th><th>T</th><th>N</th><th>M</th></tr></thead>
              <tbody>
                <tr><td class="stg">0</td><td>Tis</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IA</td><td>T1a</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IB</td><td>T1b · T2a</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIA</td><td>T2b · T3a</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIB</td><td>T3b · T4a</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">IIC</td><td>T4b</td><td>N0</td><td>M0</td></tr>
                <tr><td class="stg">III</td><td>qualquer T</td><td>≥N1</td><td>M0</td></tr>
                <tr><td class="stg">IV</td><td>qualquer T</td><td>qualquer N</td><td>M1</td></tr>
              </tbody>
            </table>
            <div class="notes"><strong>Pesquisa molecular obrigatória em estágio III/IV:</strong> BRAF V600 (40-50%) — dabrafenib/trametinibe ou encorafenib/binimetinibe. NRAS, c-KIT (mucoso/acral). PD-L1 não é decisor mas biomarcador exploratório. <strong>Tratamento moderno:</strong> Estágio III adjuvante — pembro (KEYNOTE-054), nivo (CheckMate-238), dabra+tram (COMBI-AD em BRAF+). Estágio IV — IO 1L (nivo+ipi RELATIVITY-047, nivo+rela; pembro), terapia-alvo BRAF se mutação positiva. <strong>Imagem:</strong> FDG-PET/CT padrão para staging III/IV; MRI cérebro obrigatório em III/IV. Refs: Gershenwald JE et al. CA Cancer J Clin 2017; AJCC 8ª ed.; Larkin J et al. NEJM 2019 (CheckMate-067 5-yr).</div>
          `
        }
      };

      // ====== CTCAE DATA — Eventos Adversos por categoria ======
      function openTNM(id) {
        const data = TNM_DATA[id];
        if (!data) { console.warn('TNM key not found:', id); return; }
        const dlg = document.getElementById('tnm-modal');
        if (!dlg) { console.error('tnm-modal element missing'); return; }
        try {
          document.getElementById('tnm-modal-title').textContent = data.title;
          document.getElementById('tnm-modal-ed').textContent = data.edition;
          const iconBox = document.getElementById('tnm-modal-icon');
          iconBox.style.background = 'rgba(' + hexToRgbStr(data.color) + ', 0.15)';
          // Render do ícone com fallback SVG inline, evita dependência do lucide loader
          iconBox.innerHTML = '<i data-lucide="' + data.icon + '" style="width:20px;height:20px;color:' + data.color + '"></i>';
          document.getElementById('tnm-modal-body').innerHTML = data.body;
        } catch (err) {
          console.error('TNM render error:', err);
        }
        // ABRE PRIMEIRO — garantia de que o modal aparece mesmo se o lucide falhar
        if (typeof dlg.showModal === 'function') {
          dlg.showModal();
        } else {
          dlg.setAttribute('open', '');
        }
        // Renderiza ícones depois (não bloqueia o modal)
        try {
          if (window.lucide && typeof window.lucide.createIcons === 'function') {
            window.lucide.createIcons();
          }
        } catch (err) {
          console.warn('lucide.createIcons failed:', err);
        }
      }

      function hexToRgbStr(hex) {
        const h = hex.replace('#', '');
        const r = parseInt(h.substring(0,2), 16);
        const g = parseInt(h.substring(2,4), 16);
        const b = parseInt(h.substring(4,6), 16);
        return r + ', ' + g + ', ' + b;
      }

      // Fechar modal ao clicar no backdrop do <dialog>.
      // Em modal mode, cliques no backdrop têm e.target === dlg (o conteúdo
      // interno tem outros targets). Usamos listener próprio do dialog para
      // evitar que cliques fora do dialog (ex: no card que ABRIU o modal)
      // façam o modal fechar antes mesmo de aparecer.
      document.addEventListener('DOMContentLoaded', function() {
        const dlg = document.getElementById('tnm-modal');
        if (!dlg) return;
        dlg.addEventListener('click', function(e) {
          if (e.target === dlg) dlg.close();
        });
      });
    