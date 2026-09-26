/* ============================================================================
 * ferramentas/ctcae.js — CTCAE v6.0 (9 categorias): dados, modal e fechamento por backdrop.
 *
 * Extraído LITERALMENTE de ferramentas.html (26/set/2026), sem nenhuma linha
 * reescrita. A indentação herdada do HTML foi mantida de propósito: os corpos
 * de modal são template strings, e preservá-los byte a byte é o que permite
 * provar a equivalência contra a versão inline (ver o harness de snapshot).
 *
 * Carregado como script CLÁSSICO e SÍNCRONO, na mesma posição em que o bloco
 * inline estava — mesma ordem de execução, mesmo escopo global compartilhado
 * (`const` de topo e `function` continuam visíveis aos handlers inline).
 * Depende de: nada. Usado por: 9 botões onclick="openCTCAE(...)".
 * ==========================================================================*/
      const CTCAE_DATA = {
        hema: {
          title: 'Hematológico',
          icon: 'droplet',
          color: '#FBBF24',
          events: [
            { name: 'Anemia (Hb)', g1: '<LSN-10,0 g/dL', g2: '8,0-10,0 g/dL', g3: '<8,0 g/dL · transfusão indicada', g4: 'Risco de vida; intervenção urgente' },
            { name: 'Neutropenia (ANC)', g1: '<LIN-1,5×109/L', g2: '1,0-1,5×109/L', g3: '0,5-1,0×109/L', g4: '<0,5×109/L' },
            { name: 'Trombocitopenia (PLQ)', g1: '<LIN-75×109/L', g2: '50-75×109/L', g3: '25-50×109/L', g4: '<25×109/L' },
            { name: 'Linfopenia', g1: '<LIN-800/mm3', g2: '500-800/mm3', g3: '200-500/mm3', g4: '<200/mm3' },
            { name: 'Leucopenia (WBC)', g1: '<LIN-3,0×109/L', g2: '2,0-3,0×109/L', g3: '1,0-2,0×109/L', g4: '<1,0×109/L' },
            { name: 'Neutropenia febril', g1: '—', g2: '—', g3: 'ANC <1,0 + temp ≥38,3°C única ou ≥38°C ≥1h · sem instabilidade', g4: 'Com sepse / instabilidade hemodinâmica' },
            { name: 'Hemorragia (geral)', g1: 'Sangramento leve · sem intervenção', g2: 'Sintomas moderados · transfusão única', g3: 'Transfusão recorrente · radiologia/endoscopia/cirurgia', g4: 'Risco de vida · intervenção urgente' },
            { name: 'Hemorragia SNC', g1: 'Microsangramento assintomático', g2: 'Sintomas leves (cefaleia, déficit transitório)', g3: 'Déficit moderado · intervenção médica', g4: 'Hemorragia massiva · risco de vida; cirurgia/UTI' },
            { name: 'TVP / TEP', g1: 'TVP venosa superficial', g2: 'TVP de extremidade · anticoagulação', g3: 'TEP estável · anticoagulação ativa', g4: 'TEP com instabilidade · trombólise/UTI' },
            { name: 'CIVD', g1: '—', g2: '—', g3: 'Coagulopatia laboratorial · transfusão de plasma/plaquetas', g4: 'Sangramento grave + falência multi-orgânica' }
          ],
          manage: '<strong>G1-G2:</strong> manter terapia, monitorar 1-2x/sem; suporte (ferro, folato, EPO conforme indicação). <strong>G3:</strong> suspender ciclo até recuperação ≥G1; transfusão (Hb &lt;7-8, plaquetas &lt;10 ou &lt;20 com sangramento, neutrófilos com FN); G-CSF profilático em risco alto. <strong>G4:</strong> suspender permanente em maioria das terapias. <strong>Em teranóstico:</strong> Lu-PSMA — mielossupressão acumulativa em ciclos 4-6; Lu-DOTATATE — neutropenia tardia leve; Y-90 — pancitopenia rara (REILD).'
        },
        gi: {
          title: 'Gastrointestinal',
          icon: 'utensils',
          color: '#FBBF24',
          events: [
            { name: 'Diarreia', g1: '<4 evac/d acima do basal', g2: '4-6 evac/d acima do basal · líquidos EV indicados', g3: '≥7 evac/d · incontinência · hospitalização', g4: 'Risco de vida · intervenção urgente · sepse' },
            { name: 'Náusea', g1: 'Perda de apetite sem alteração de hábitos', g2: 'Redução de ingesta sem perda significativa de peso', g3: 'Ingesta calórica/líquida inadequada · NPT/hospitalização', g4: '—' },
            { name: 'Vômito', g1: '1-2 episódios em 24h', g2: '3-5 episódios/24h', g3: '≥6 episódios/24h · NPT/hospitalização', g4: 'Risco de vida · intervenção urgente' },
            { name: 'Mucosite oral', g1: 'Assintomático ou sintomas leves · sem intervenção', g2: 'Dor moderada · não interfere com ingesta', g3: 'Dor grave · interfere com ingesta', g4: 'Risco de vida · intervenção urgente; NPT' },
            { name: 'Constipação', g1: 'Ocasional · uso ocasional de laxativo', g2: 'Persistente · laxativos regulares · não impacta AVDs', g3: 'Obstipação com manuseio manual · impacta AVDs', g4: 'Risco de vida · intervenção urgente; obstrução' },
            { name: 'Obstrução intestinal', g1: 'Assintomático · achado radiológico', g2: 'Sintomática · intervenção não-cirúrgica (sonda, jejum)', g3: 'Sintomática · cirúrgica indicada', g4: 'Risco de vida · perfuração / sepse' },
            { name: 'Perfuração GI', g1: '—', g2: 'Sintomas mínimos · cirurgia minor', g3: 'Sintomas moderados · cirurgia indicada', g4: 'Risco de vida · cirurgia urgente' },
            { name: 'Fístula GI', g1: 'Assintomática · radiológico', g2: 'Sintomática · drenagem/dieta', g3: 'Cirurgia indicada · radiológica/endoscópica', g4: 'Risco de vida · sepse / hemorragia' },
            { name: 'Sangramento GI', g1: 'Microscópico · sem alteração Hb', g2: 'Macroscópico · transfusão única', g3: 'Transfusão recorrente · endoscopia/intervenção', g4: 'Risco de vida · intervenção urgente' },
            { name: 'Esofagite', g1: 'Assintomática · achado endoscópico', g2: 'Sintomas · não interfere com ingesta', g3: 'Interfere com ingesta · NPT/dilatação', g4: 'Perfuração / risco de vida' }
          ],
          manage: '<strong>Diarreia G2+ em IO:</strong> sempre descartar colite imuno-mediada — se confirmada, colonoscopia + corticoide. <strong>G3-4 IO:</strong> hospitalizar, metilprednisolona 1-2 mg/kg/d EV; se refratário em 3-5 d → infliximabe ou vedolizumabe. <strong>Náusea/vômito em PRRT:</strong> profilaxia com antagonista 5-HT3 + dexa antes da infusão de aminoácidos. <strong>Mucosite (everolimus, lenva, T-DXd):</strong> bochechos com bicarbonato + dexa; severo → drug holiday.'
        },
        hepato: {
          title: 'Hepatobiliar',
          icon: 'hexagon',
          color: '#FBBF24',
          events: [
            { name: 'ALT (TGP)', g1: '>LSN-3× LSN', g2: '3-5× LSN', g3: '5-20× LSN', g4: '>20× LSN' },
            { name: 'AST (TGO)', g1: '>LSN-3× LSN', g2: '3-5× LSN', g3: '5-20× LSN', g4: '>20× LSN' },
            { name: 'Bilirrubina total', g1: '>LSN-1,5× LSN', g2: '1,5-3× LSN', g3: '3-10× LSN', g4: '>10× LSN' },
            { name: 'Fosfatase alcalina', g1: '>LSN-2,5× LSN', g2: '2,5-5× LSN', g3: '5-20× LSN', g4: '>20× LSN' },
            { name: 'GGT', g1: '>LSN-2,5× LSN', g2: '2,5-5× LSN', g3: '5-20× LSN', g4: '>20× LSN' },
            { name: 'Hepatite (clínica)', g1: 'Assintomática · só labs ↑', g2: 'Sintomas · interferência mínima AVDs', g3: 'Sintomas graves · interfere com AVDs', g4: 'Risco de vida · descompensação hepática' },
            { name: 'Falência hepática', g1: '—', g2: 'INR <1,5 · Bili <2× LSN sem encefalopatia', g3: 'INR 1,5-2,5 · sem encefalopatia', g4: 'INR >2,5 com encefalopatia · risco de vida' },
            { name: 'Pancreatite', g1: 'Assintomática · enzimas ↑', g2: 'Sintomas · enzimas ≥3× LSN', g3: 'Imagem com necrose <30% · hospitalização', g4: 'Necrose >30% · falência orgânica · UTI' }
          ],
          manage: '<strong>Regra de Hy:</strong> ALT/AST &gt;3× LSN + Bili total &gt;2× LSN sem obstrução = sinal de hepatotoxicidade grave (mortalidade ~10%). Suspender e investigar imediatamente. <strong>Hepatite IO G2:</strong> suspender ICI · prednisona 0,5-1 mg/kg/d. <strong>G3-G4:</strong> hospitalizar · metilprednisolona 1-2 mg/kg/d EV; se refratário em 3 d → micofenolato (NÃO infliximabe — hepatotóxico); ICI permanentemente descontinuado em G3-G4 hepatite.'
        },
        renal: {
          title: 'Renal',
          icon: 'filter',
          color: '#FBBF24',
          events: [
            { name: 'Creatinina sérica', g1: '>LSN-1,5× LSN OU 1,5-2× basal', g2: '1,5-3× basal · 1,5-3× LSN', g3: '>3× basal · 3× LSN OU Cr ≥4 mg/dL', g4: 'Risco de vida · diálise indicada' },
            { name: 'Proteinúria', g1: '1+ ou 0,15-1 g/24h', g2: '2-3+ ou 1-3,5 g/24h', g3: '4+ ou >3,5 g/24h', g4: 'Síndrome nefrótica grave · diálise' },
            { name: 'Hematúria', g1: 'Microscópica', g2: 'Macroscópica · sem coágulos · cateterização', g3: 'Coágulos · cateterismo + irrigação · transfusão', g4: 'Risco de vida · intervenção urgente · cirurgia' },
            { name: 'Cistite (rad/hemorr.)', g1: 'Assintomática · achado endoscópico', g2: 'Sintomas urinários · sem coágulos', g3: 'Coágulos · cateterização · transfusão', g4: 'Risco de vida · cistectomia/embolização' },
            { name: 'Lesão renal aguda', g1: 'Cr ↑ leve sem oligúria', g2: 'Cr ↑ moderada · oligúria <0,5 mL/kg/h por 6-12h', g3: 'Cr ↑ severa · oligúria persistente >12h · diálise possível', g4: 'Falência renal · diálise · risco de vida' },
            { name: 'Síndrome de lise tumoral', g1: '—', g2: 'Laboratorial · assintomática · hidratação', g3: 'Sintomas (arritmia, oligúria) · intervenção urgente', g4: 'Risco de vida · diálise · UTI' },
            { name: 'Acidose metabólica', g1: 'pH 7,3-7,35', g2: 'pH 7,2-7,3', g3: 'pH <7,2 · intervenção médica', g4: 'Risco de vida · ventilação' },
            { name: 'Nefrite tubulointersticial', g1: 'Assintomática · só labs', g2: 'Sintomas leves · interferência mínima AVDs', g3: 'Hospitalização · biópsia/corticoide', g4: 'Risco de vida · diálise' }
          ],
          manage: '<strong>Lu-PSMA / Lu-DOTATATE:</strong> nefrotoxicidade dose-dependente. Lu-DOTATATE — proteção com aminoácidos (lisina 25 g + arginina 25 g em 2 L SF) iniciados 30 min antes e por 4h. <strong>Y-90 TARE:</strong> precaução em CrCl &lt;30. <strong>Cisplatina:</strong> hidratação 2-3 L/d com manitol; CrCl ≥60 mL/min obrigatório. <strong>Nefrite IO G2:</strong> suspender ICI · prednisona 0,5-1 mg/kg/d. <strong>G3-G4:</strong> metilprednisolona 1-2 mg/kg/d EV; refratário → micofenolato.'
        },
        irae: {
          title: 'Imuno-mediado (irAEs)',
          icon: 'shield-plus',
          color: '#FBBF24',
          events: [
            { name: 'Pneumonite', g1: 'Assintomática · achado radiológico', g2: 'Sintomática · interfere AIVDs · O₂ não indicado', g3: 'Sintomas graves · O₂ indicado · hospitalização', g4: 'Insuf respiratória · UTI · ventilação' },
            { name: 'Colite', g1: 'Assintomática ou diarreia leve', g2: '4-6 evac/d acima do basal · dor abd', g3: '≥7 evac/d · sangue/muco · peritonismo', g4: 'Perfuração · hemorragia · risco de vida' },
            { name: 'Hepatite IO', g1: 'ALT/AST 1-3× LSN · Bili 1-1,5× LSN', g2: 'ALT 3-5× LSN · Bili 1,5-3×', g3: 'ALT 5-20× LSN · Bili 3-10×', g4: 'ALT >20× LSN · Bili >10× · descompensação' },
            { name: 'Hipotireoidismo', g1: 'Assintomático · TSH 4,5-10', g2: 'Sintomático · substituição', g3: 'Sintomas severos · hospitalização', g4: 'Coma mixedematoso' },
            { name: 'Hipertireoidismo', g1: 'Assintomático · TSH suprimido', g2: 'Sintomático · betabloq / antitireoideanos', g3: 'Sintomas severos · hospitalização', g4: 'Crise tireotóxica · UTI' },
            { name: 'Hipofisite', g1: 'Assintomática · achado RM', g2: 'Cefaleia · achados endócrinos · substituição', g3: 'Sintomas severos · hospitalização · alta dose corticoide', g4: 'Risco de vida · adrenal aguda' },
            { name: 'Insuf adrenal', g1: 'Assintomática · achado lab', g2: 'Sintomática · substituição', g3: 'Sintomas severos · hospitalização · estresse', g4: 'Crise adrenal · choque' },
            { name: 'Diabetes IO (T1)', g1: 'Glicose 161-200 jejum · sem sintomas', g2: '201-250 ou cetoacidose leve', g3: '251-500 · cetoacidose · hospitalização', g4: 'Cetoacidose grave · UTI' },
            { name: 'Miocardite IO', g1: 'Assintomática · troponina ↑', g2: 'Sintomas leves · alterações ECG/ECO', g3: 'Sintomas severos · IC · hospitalização', g4: 'IC grave · UTI · arritmia letal' },
            { name: 'Nefrite intersticial IO', g1: 'Cr 1-1,5× basal · assintomática', g2: 'Cr 1,5-3× basal · sintomas leves', g3: 'Cr >3× basal · hospitalização · biópsia', g4: 'Diálise · risco de vida' },
            { name: 'Encefalite IO', g1: 'Assintomática · achado RM', g2: 'Sintomas leves · cefaleia · confusão leve', g3: 'Sintomas severos · hospitalização · plasmaferese', g4: 'Coma · UTI · risco de vida' },
            { name: 'Miosite/Miastenia IO', g1: 'CPK 2-5× LSN · assintomática', g2: 'CPK 5-10× LSN · fraqueza leve', g3: 'CPK >10× LSN · fraqueza moderada · hospitalização', g4: 'Falência respiratória · UTI · IVIg/plasma' }
          ],
          manage: '<strong>G1:</strong> manter, monitorar mais perto. <strong>G2:</strong> suspender ICI · prednisona 0,5-1 mg/kg/d com taper de 4-6 sem. <strong>G3:</strong> hospitalizar · metilprednisolona 1-2 mg/kg/d IV · suspender ICI permanentemente em maioria. <strong>G4:</strong> UTI · permanente em todos. <strong>Refratário em 3-5 d:</strong> escalar — colite/hepatite → infliximabe (NÃO em hepatite por hepatotoxicidade) ou vedolizumabe; pneumonite → micofenolato/IVIg/ciclofosfamida; miocardite → metilpred 1g/d 3-5 d + IVIg/ATG. <strong>Endocrinopatias:</strong> não exigem corticoide (exceto hipofisite/adrenalite agudas) — substituir hormônio.'
        },
        derm: {
          title: 'Dermatológico',
          icon: 'user',
          color: '#FBBF24',
          events: [
            { name: 'Rash maculopapular', g1: '<10% SC · sem sintomas', g2: '10-30% SC · prurido · interferência mínima', g3: '>30% SC · interfere AVDs', g4: 'Pápulas/pústulas confluentes · superinfecção · SSJ' },
            { name: 'Síndrome mão-pé (HFS)', g1: 'Dormência/disestesia · eritema · sem dor', g2: 'Eritema doloroso · descamação · não interfere AVDs', g3: 'Descamação úmida · ulceração · dor severa · interfere AVDs', g4: '—' },
            { name: 'Prurido', g1: 'Leve · localizado · sem ou com poucas escoriações', g2: 'Difuso · escoriações · interferência mínima AIVDs', g3: 'Generalizado · contínuo · interfere AVDs/sono', g4: '—' },
            { name: 'Alopecia', g1: 'Perda <50% do volume · não exige peruca', g2: '≥50% · cobertura completa exigindo peruca', g3: '—', g4: '—' },
            { name: 'Vitiligo', g1: 'Hipopigmentação <10% SC · sem psicossocial', g2: 'Hipopigmentação ≥10% SC · associada com efeito psicossocial', g3: '—', g4: '—' },
            { name: 'SSJ / NET', g1: '—', g2: '—', g3: 'SSJ: <10% SC com epidermólise · hospitalização', g4: 'NET: >30% SC com epidermólise · UTI · risco de vida' },
            { name: 'Fotossensibilidade', g1: 'Eritema discreto · resolve sem tto', g2: 'Eritema doloroso · reação tardia · interfere AIVDs', g3: 'Reação severa · queimadura grave · interfere AVDs', g4: 'Necrose pele · risco de vida' },
            { name: 'Hiperpigmentação', g1: 'Hiperpigmentação leve · localizada', g2: 'Generalizada · psicossocial · cosmético', g3: '—', g4: '—' },
            { name: 'Onicólise / distrofia ungueal', g1: 'Assintomática · cosmética', g2: 'Sintomática · sem alteração AIVDs', g3: 'Sintomática · interfere AVDs', g4: '—' }
          ],
          manage: '<strong>Rash IO G2:</strong> corticoide tópico médio (mometasona) + anti-histamínico oral · pode manter ICI. <strong>G3-G4:</strong> suspender ICI · prednisona 0,5-1 mg/kg/d; consulta dermatologia urgente; biópsia se atípico. <strong>SSJ/NET:</strong> emergência — suspender permanentemente ICI · UTI/queimaduras · IVIg ou ciclosporina. <strong>HFS (cabozantinibe, lenva, sorafenibe, capecitabina, EV):</strong> emolientes preventivos com ureia 10-20%; corticoide tópico G2; reduzir dose 25-50% em G3.'
        },
        radio: {
          title: 'Específico de radioligante',
          icon: 'atom',
          color: '#FBBF24',
          events: [
            { name: 'Xerostomia', g1: 'Sintomática · sem alteração de dieta · saliva basal >0,2 mL/min', g2: 'Modera de dieta (umidificação) · saliva 0,1-0,2 mL/min', g3: 'Incapaz de mastigar/engolir · saliva <0,1 mL/min · NPT', g4: '—' },
            { name: 'Parotidite / sialadenite', g1: 'Eritema/edema leve sem dor · imagem positiva', g2: 'Edema doloroso · interfere com ingesta · antibiótico', g3: 'Abscesso · drenagem · NPT', g4: 'Risco de vida · sepse' },
            { name: 'REILD (Y-90)', g1: 'Achado lab assintomático', g2: 'Bili 2-3× LSN · ascite leve · ictericía', g3: 'Bili >3× LSN · ascite refratária · falência hepática progressiva', g4: 'Coma hepático · risco de vida' },
            { name: 'Hipotireoidismo (MIBG)', g1: 'Assintomático · TSH ↑ leve', g2: 'Sintomático · substituição com levotiroxina', g3: 'Sintomas severos · hospitalização', g4: 'Coma mixedematoso' },
            { name: 'Mielossupressão tardia', g1: 'Cito leve · sem intervenção', g2: 'Cito moderada · transfusão pontual', g3: 'Cito severa · transfusão recorrente · suspender próximos ciclos', g4: 'SMD / leucemia secundária · risco de vida' },
            { name: 'Hematúria pós Lu-PSMA', g1: 'Microscópica · sem coágulos', g2: 'Macroscópica · sem instabilidade', g3: 'Coágulos · cateterismo · transfusão', g4: 'Risco de vida · intervenção urgente' },
            { name: 'Crise carcinoide pós-PRRT', g1: '—', g2: 'Sintomas leves · flushing · diarreia', g3: 'Sintomas severos · taquicardia · hipotensão · hospitalização', g4: 'Choque · risco de vida' },
            { name: 'Tumor flare (pós-MIBG/PRRT)', g1: 'Dor leve no sítio tumoral · sem analgésico', g2: 'Dor moderada · analgésico simples', g3: 'Dor severa · opioide · hospitalização', g4: 'Edema obstrutivo (medular, encefálico) · risco de vida' },
            { name: 'Tox alfa-emissor (225Ac)', g1: 'Xerostomia leve', g2: 'Xerostomia moderada · queratite', g3: 'Xerostomia severa irreversível · falha medular', g4: 'Múltiplas falências · risco de vida' }
          ],
          manage: '<strong>Xerostomia:</strong> proteção com gelo parotídeo durante e 30 min após Lu-PSMA reduz dose absorvida. Pilocarpina 5 mg 3x/d; saliva artificial; hidratação. 225Ac-PSMA — xerostomia é dose-limitante e cumulativa; reduzir kBq/kg em ciclos subsequentes. <strong>REILD:</strong> ocorre 4-8 sem pós-Y-90 em pacientes com função hepática limítrofe (Child A/B); manejo de suporte. <strong>Crise carcinoide:</strong> octreotida 100-500 µg SC/EV antes de PRRT em pacientes com sintomas; manter LAR durante (mas suspender 4-6 sem antes do ciclo). <strong>Tumor flare:</strong> aumentar dexa peri-infusão.'
        },
        crs: {
          title: 'CRS / ICANS (CAR-T e BiTE)',
          icon: 'zap',
          color: '#FBBF24',
          events: [
            { name: 'CRS (ASTCT)', g1: 'Febre ≥38°C · sem hipotensão · sem hipóxia', g2: 'Febre + hipotensão sem vasopressor · O₂ baixo (FiO₂ <40%)', g3: 'Febre + 1 vasopressor · O₂ ≥40%', g4: 'Febre + ≥2 vasopressores ou ventilação mecânica' },
            { name: 'ICANS (ICE score)', g1: 'ICE 7-9 · acordado · sem alterações motoras', g2: 'ICE 3-6 · acordado e responsivo · disfasia leve', g3: 'ICE 0-2 · diminuição de consciência · convulsões focais', g4: 'ICE 0 · estado convulsivo · coma · pressão IC ↑' },
            { name: 'HLH-secundário', g1: '—', g2: 'Citopenia + ↑ferritina + esplenomegalia', g3: '+ falência orgânica · etoposídeo + dexa', g4: 'Refratário · risco de vida · UTI' },
            { name: 'Reativação CMV', g1: 'PCR detectável sem doença', g2: 'Doença leve (febre)', g3: 'Doença orgânica (pneumonia, hepatite, retinite) · ganciclovir', g4: 'Doença disseminada · risco de vida' },
            { name: 'EBV-PTLD', g1: 'PCR detectável sem doença', g2: 'Linfopatia leve · monitorização', g3: 'Linfoma associado · rituximabe · quimio', g4: 'Linfoma fulminante · risco de vida' },
            { name: 'Linfopenia profunda', g1: '—', g2: 'CD4 200-500 · monitorar', g3: 'CD4 <200 · profilaxia PCP/HSV', g4: 'Sepse oportunista · risco de vida' },
            { name: 'Aplasia B-celular', g1: 'IgG <LIN sem infecções', g2: 'Infecções leves · IgG suplementar', g3: 'Infecções recorrentes · IGIV mensal', g4: 'Sepse refratária · risco de vida' },
            { name: 'Neurotoxicidade tardia', g1: 'Tremor leve · sem disfunção', g2: 'Disfunção motora leve · interferência mínima AVDs', g3: 'Convulsões · ataxia severa · interferência AVDs', g4: 'Demência · estado vegetativo' }
          ],
          manage: '<strong>CRS G1:</strong> antitérmico · líquidos · monitor. <strong>CRS G2:</strong> tocilizumabe 8 mg/kg EV (max 800 mg) · O₂; considerar dexa 10 mg q6h. <strong>CRS G3-G4:</strong> tocilizumabe + dexa em dose alta · vasopressor · UTI; considerar anakinra ou siltuximabe se refratário. <strong>ICANS G1:</strong> observar · evitar BZD; <strong>G2:</strong> dexa 10 mg q6h; <strong>G3-G4:</strong> dexa 1g/d · anakinra · UTI; tocilizumabe NÃO penetra BHE — usar para CRS concomitante. <strong>Profilaxia:</strong> aciclovir, fluconazol, sulfa (PCP) em todos pós-CAR-T; IGIV mensal se IgG <400.'
        },
        sist: {
          title: 'Geral / sistêmico',
          icon: 'thermometer',
          color: '#FBBF24',
          events: [
            { name: 'Fadiga', g1: 'Leve · não modera AVDs', g2: 'Modera AIVDs · não AVDs básicas', g3: 'Limita AVDs · auto-cuidado', g4: 'Incapacitante · cama' },
            { name: 'Febre', g1: '38,0-39,0°C', g2: '39,1-40,0°C ≤24h', g3: '>40,0°C ≤24h · com sintomas', g4: '>40,0°C >24h ou hipotensão' },
            { name: 'Hipertensão', g1: 'PAS 120-139 ou PAD 80-89', g2: 'PAS 140-159 ou PAD 90-99 · monoterapia', g3: 'PAS ≥160 ou PAD ≥100 · terapia múltipla', g4: 'Emergência hipertensiva · ↓consciência · IRA' },
            { name: 'Hipotensão', g1: 'Assintomática · transitória · sem intervenção', g2: 'Sintomática · líquidos EV · não PIA', g3: 'Persistente · vasopressor · hospitalização', g4: 'Choque · UTI · arritmia' },
            { name: 'Edema periférico', g1: '<10% inter-membros · sem dor', g2: '10-30% · dor leve · interfere AIVDs', g3: '>30% · dor severa · interfere AVDs', g4: 'Risco anasarca · IC · UTI' },
            { name: 'Perda de peso', g1: '5-10% basal', g2: '10-20% · NPT/sup', g3: '>20% · NPT · hospitalização', g4: '—' },
            { name: 'Anorexia', g1: 'Perda apetite · sem alteração ingesta', g2: 'Redução ingesta · sem perda peso significativa', g3: 'Perda peso significativa · NPT', g4: 'Risco vida' },
            { name: 'Insônia', g1: 'Leve · sem interferência', g2: 'Modera AIVDs · soníferos', g3: 'Severa · não responde a soníferos', g4: '—' },
            { name: 'Dor (geral)', g1: 'Leve · não modera AVDs', g2: 'Modera · analgésico não-opioide', g3: 'Severa · opioides · interfere AVDs', g4: 'Incapacitante' },
            { name: 'Reação infusional', g1: 'Leve · transitória · interrupção infusão não indicada', g2: 'Sintomas moderados · interrupção + pré-medicação', g3: 'Prolongada · sintomas severos · suspender infusão · hospitalização', g4: 'Anafilaxia · risco de vida' }
          ],
          manage: '<strong>HTN em IO+TKI (lenva/cabo/axi):</strong> meta &lt;140/90; iniciar antiHTA precoce (IECA/BRA primeira linha); reduzir dose TKI em G3 refratário. <strong>Reação infusional:</strong> rituximabe, T-DXd, cetuximabe têm risco; pré-medicação com dexa + difenidramina + paracetamol; em G3-G4 anafilática suspender permanentemente. <strong>Fadiga IO/QT/PRRT:</strong> excluir hipotireoidismo, anemia, ↓adrenal; intervenção: exercício aeróbico, suporte psicológico.'
        }
      };

      function openCTCAE(id) {
        const data = CTCAE_DATA[id];
        if (!data) { console.warn('CTCAE key not found:', id); return; }
        const dlg = document.getElementById('ctcae-modal');
        if (!dlg) { console.error('ctcae-modal element missing'); return; }
        try {
          document.getElementById('ctcae-modal-title').textContent = 'CTCAE v6.0 · ' + data.title;
          document.getElementById('ctcae-modal-ed').textContent = data.events.length + ' eventos';
          const iconBox = document.getElementById('ctcae-modal-icon');
          iconBox.style.background = 'rgba(251, 191, 36, 0.15)';
          iconBox.innerHTML = '<i data-lucide="' + data.icon + '" style="width:20px;height:20px;color:#FBBF24"></i>';
          let html = '<table class="stage-tbl" style="margin-top:0.5rem"><thead><tr><th>Evento</th><th>G1</th><th>G2</th><th>G3</th><th>G4</th></tr></thead><tbody>';
          for (const ev of data.events) {
            html += '<tr>';
            html += '<td class="stg" style="color:var(--off-white)">' + ev.name + '</td>';
            html += '<td style="color:#6EE7B7">' + (ev.g1 || '—') + '</td>';
            html += '<td style="color:#FCD34D">' + (ev.g2 || '—') + '</td>';
            html += '<td style="color:#FBA74A">' + (ev.g3 || '—') + '</td>';
            html += '<td style="color:#F87171">' + (ev.g4 || '—') + '</td>';
            html += '</tr>';
          }
          html += '</tbody></table>';
          html += '<div class="notes" style="margin-top:1.25rem; padding:0.85rem 1rem; background:rgba(251,191,36,0.06); border-left:3px solid #FBBF24; border-radius:0 var(--radius-sm) var(--radius-sm) 0; line-height:1.55"><strong style="color:#FCD34D">Manejo:</strong> ' + data.manage + '</div>';
          document.getElementById('ctcae-modal-body').innerHTML = html;
        } catch (err) {
          console.error('CTCAE render error:', err);
        }
        if (typeof dlg.showModal === 'function') {
          dlg.showModal();
        } else {
          dlg.setAttribute('open', '');
        }
        try {
          if (window.lucide && typeof window.lucide.createIcons === 'function') {
            window.lucide.createIcons();
          }
        } catch (err) {
          console.warn('lucide.createIcons failed:', err);
        }
      }

      document.addEventListener('DOMContentLoaded', function() {
        const dlg = document.getElementById('ctcae-modal');
        if (!dlg) return;
        dlg.addEventListener('click', function(e) {
          if (e.target === dlg) dlg.close();
        });
      });

