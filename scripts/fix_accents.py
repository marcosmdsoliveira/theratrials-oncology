#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_accents.py — Adds proper PT-BR accents to guidelines-data.js.
Phase 1: Regex suffix patterns (high confidence)
Phase 2: Prefix patterns
Phase 3: Word-level dictionary
Phase 4: Special fixes
Phase 5: Context-aware "e" -> "e-accent" (verb ser)
Phase 6: Specific remaining "e" -> "e-accent" fixes
Phase 7: "esta/estao" -> "esta-accent/estao-accent" (verb estar)
Phase 8: "ha" -> "ha-accent" (verb haver)
"""
import re

target = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\assets\js\guidelines-data.js"

with open(target, 'r', encoding='utf-8') as f:
    text = f.read()

# ─── PHASE 1: Suffix-based patterns ───
SUFFIXES = [
    # -ção/-ções
    ("cao", "ção"), ("coes", "ções"),
    # -são/-sões
    ("sao", "são"), ("soes", "sões"),
    # -ância/-âncias / -ência/-ências
    ("ancia", "ância"), ("ancias", "âncias"),
    ("encia", "ência"), ("encias", "ências"),
    # -ável/-áveis / -ível/-íveis
    ("avel", "ável"), ("aveis", "áveis"),
    ("ivel", "ível"), ("iveis", "íveis"),
    # -ário/-ários / -ório/-órios
    ("ario", "ário"), ("arios", "ários"),
    ("orio", "ório"), ("orios", "órios"),
    # -ático/-ática
    ("atico", "ático"), ("atica", "ática"),
    ("aticos", "áticos"), ("aticas", "áticas"),
    # -ético/-ética
    ("etico", "ético"), ("etica", "ética"),
    ("eticos", "éticos"), ("eticas", "éticas"),
    # -ógico/-ógica
    ("ogico", "ógico"), ("ogica", "ógica"),
    ("ogicos", "ógicos"), ("ogicas", "ógicas"),
    # -ônico/-ônica (BR circumflex)
    ("onico", "ônico"), ("onica", "ônica"),
    ("onicos", "ônicos"), ("onicas", "ônicas"),
    # -ômica/-ômico
    ("omica", "ômica"), ("omico", "ômico"),
    ("omicas", "ômicas"), ("omicos", "ômicos"),
    # -êutico/-êutica
    ("eutico", "êutico"), ("eutica", "êutica"),
    ("euticos", "êuticos"), ("euticas", "êuticas"),
    # -óstico/-óstica
    ("ostico", "óstico"), ("ostica", "óstica"),
    ("osticos", "ósticos"), ("osticas", "ósticas"),
    # -ístico/-ística
    ("istico", "ístico"), ("istica", "ística"),
    ("isticos", "ísticos"), ("isticas", "ísticas"),
    # -ídeo/-ídeos
    ("ideo", "ídeo"), ("ideos", "ídeos"),
    # -ômeno/-ômenos
    ("omeno", "ômeno"), ("omenos", "ômenos"),
    # -êmico/-êmica
    ("emico", "êmico"), ("emica", "êmica"),
    ("emicos", "êmicos"), ("emicas", "êmicas"),
    # -ogêneo/-ogênea
    ("ogeneo", "ogêneo"), ("ogenea", "ogênea"),
    ("ogeneos", "ogêneos"), ("ogeneas", "ogêneas"),
    # -âneo/-ânea
    ("utaneo", "utâneo"), ("utanea", "utânea"),
    ("utaneos", "utâneos"), ("utaneas", "utâneas"),
    ("ontaneo", "ontâneo"), ("ontanea", "ontânea"),
    ("ultaneo", "ultâneo"), ("ultanea", "ultânea"),
    ("oraneo", "orâneo"), ("oranea", "orânea"),
]

for unaccented, accented in SUFFIXES:
    pattern = r'\b(\w+)' + re.escape(unaccented) + r'\b'
    text = re.sub(pattern, r'\1' + accented, text)

# ─── PHASE 2: Prefix patterns ───
text = re.sub(r'\bpre-', 'pré-', text)
text = re.sub(r'\bpos-', 'pós-', text)
text = re.sub(r'\bPre-', 'Pré-', text)
text = re.sub(r'\bPos-', 'Pós-', text)

# ─── PHASE 3: Word-level dictionary ───
WORDS = {
    # Function words
    "nao": "não", "Nao": "Não",
    "sao": "são", "Sao": "São",
    "tambem": "também", "Tambem": "Também",
    "alem": "além", "Alem": "Além",
    "porem": "porém", "Porem": "Porém",
    "atraves": "através", "Atraves": "Através",
    "entao": "então", "Entao": "Então",
    "ate": "até", "Ate": "Até",
    "ja": "já", "Ja": "Já",
    "so": "só",
    "apos": "após", "Apos": "Após",
    "tres": "três", "Tres": "Três",
    "contem": "contém", "Contem": "Contém",
    "mantem": "mantém", "Mantem": "Mantém",
    "obtem": "obtém", "Obtem": "Obtém",
    # Verb haver
    "ha": "há", "Ha": "Há",
    # -ão words NOT caught by -ção/-são patterns
    "padrao": "padrão", "Padrao": "Padrão",
    "padroes": "padrões", "Padroes": "Padrões",
    "orgao": "órgão", "Orgao": "Órgão",
    "orgaos": "órgãos", "Orgaos": "Órgãos",
    "mao": "mão",
    # Nouns with accent
    "analise": "análise", "analises": "análises",
    "Analise": "Análise", "Analises": "Análises",
    "analogo": "análogo", "analogos": "análogos",
    "Analogo": "Análogo", "Analogos": "Análogos",
    "parametro": "parâmetro", "parametros": "parâmetros",
    "Parametro": "Parâmetro", "Parametros": "Parâmetros",
    "numero": "número", "numeros": "números",
    "Numero": "Número", "Numeros": "Números",
    "metodo": "método", "metodos": "métodos",
    "Metodo": "Método", "Metodos": "Métodos",
    "criterio": "critério", "criterios": "critérios",
    "Criterio": "Critério", "Criterios": "Critérios",
    "periodo": "período", "periodos": "períodos",
    "Periodo": "Período", "Periodos": "Períodos",
    "equilibrio": "equilíbrio",
    "beneficio": "benefício", "beneficios": "benefícios",
    "episodio": "episódio", "episodios": "episódios",
    "formula": "fórmula", "formulas": "fórmulas",
    "Formula": "Fórmula", "Formulas": "Fórmulas",
    "calculo": "cálculo", "calculos": "cálculos",
    "Calculo": "Cálculo", "Calculos": "Cálculos",
    "titulo": "título", "modulo": "módulo", "modulos": "módulos",
    "tecnica": "técnica", "tecnicas": "técnicas",
    "tecnico": "técnico", "tecnicos": "técnicos",
    "Tecnica": "Técnica", "Tecnicas": "Técnicas",
    "nivel": "nível", "niveis": "níveis",
    "Nivel": "Nível", "Niveis": "Níveis",
    "servico": "serviço", "servicos": "serviços",
    "Servico": "Serviço",
    "inicio": "início", "Inicio": "Início",
    "espaco": "espaço", "espacos": "espaços",
    "doenca": "doença", "doencas": "doenças",
    "Doenca": "Doença", "Doencas": "Doenças",
    "eficacia": "eficácia", "Eficacia": "Eficácia",
    "area": "área", "areas": "áreas",
    "Area": "Área", "Areas": "Áreas",
    "serie": "série", "series": "séries",
    "Serie": "Série", "Series": "Séries",
    "agua": "água",
    "farmaco": "fármaco", "farmacos": "fármacos",
    "Farmaco": "Fármaco",
    "radiofarmaco": "radiofármaco", "radiofarmacos": "radiofármacos",
    "Radiofarmaco": "Radiofármaco",
    "nucleo": "núcleo", "nucleos": "núcleos",
    "nuclideo": "nuclídeo", "nuclideos": "nuclídeos",
    "radionuclideo": "radionuclídeo", "radionuclideos": "radionuclídeos",
    "residuo": "resíduo", "residuos": "resíduos",
    "obito": "óbito", "obitos": "óbitos",
    "sindrome": "síndrome", "sindromes": "síndromes",
    "Sindrome": "Síndrome",
    "metastase": "metástase", "metastases": "metástases",
    "Metastase": "Metástase",
    "biopsia": "biópsia", "biopsias": "biópsias",
    "Biopsia": "Biópsia",
    "celula": "célula", "celulas": "células",
    "celular": "celular",
    "molecula": "molécula", "moleculas": "moléculas",
    "valido": "válido", "valida": "válida", "validos": "válidos",
    "hipotalamo": "hipotálamo",
    "vesicula": "vesícula", "vesiculas": "vesículas",
    "glandula": "glândula", "glandulas": "glândulas",
    "Glandula": "Glândula", "Glandulas": "Glândulas",
    "prostata": "próstata", "Prostata": "Próstata",
    "hipofise": "hipófise",
    "torax": "tórax", "Torax": "Tórax",
    "abdomen": "abdômen",
    "pelve": "pelve",
    "leucocito": "leucócito", "leucocitos": "leucócitos",
    "eritrocito": "eritrócito", "eritrocitos": "eritrócitos",
    "linfocito": "linfócito", "linfocitos": "linfócitos",
    "neutrofilo": "neutrófilo", "neutrofilos": "neutrófilos",
    "Neutrofilo": "Neutrófilo", "Neutrofilos": "Neutrófilos",
    "aminoacido": "aminoácido", "aminoacidos": "aminoácidos",
    "Aminoacido": "Aminoácido", "Aminoacidos": "Aminoácidos",
    # Adjectives
    "medio": "médio", "media": "média",
    "medios": "médios", "medias": "médias",
    "Medio": "Médio", "Media": "Média",
    "minimo": "mínimo", "minima": "mínima",
    "minimos": "mínimos", "minimas": "mínimas",
    "Minimo": "Mínimo",
    "maximo": "máximo", "maxima": "máxima",
    "maximos": "máximos", "maximas": "máximas",
    "Maximo": "Máximo",
    "proximo": "próximo", "proxima": "próxima",
    "Proximo": "Próximo",
    "ultimo": "último", "ultima": "última",
    "Ultimo": "Último",
    "rapido": "rápido", "rapida": "rápida",
    "Rapido": "Rápido",
    "unico": "único", "unica": "única",
    "Unico": "Único",
    "varios": "vários", "varias": "várias",
    "Varios": "Vários", "Varias": "Várias",
    "medico": "médico", "medica": "médica",
    "medicos": "médicos", "medicas": "médicas",
    "Medico": "Médico",
    "pratica": "prática", "praticas": "práticas",
    "pratico": "prático", "praticos": "práticos",
    "Pratica": "Prática", "Praticas": "Práticas",
    "solido": "sólido", "solida": "sólida",
    "liquido": "líquido", "liquida": "líquida",
    "liquidos": "líquidos",
    "ossea": "óssea", "osseo": "ósseo",
    "osseas": "ósseas", "osseos": "ósseos",
    "Ossea": "Óssea", "Osseas": "Ósseas",
    "serica": "sérica", "serico": "sérico",
    "sericas": "séricas", "sericos": "séricos",
    # Body/clinical
    "pais": "país", "paises": "países",
    "Pais": "País", "Paises": "Países",
    # Endocrine/organ adjectives
    "endocrino": "endócrino", "endocrina": "endócrina",
    "endocrinos": "endócrinos", "endocrinas": "endócrinas",
    "neuroendocrino": "neuroendócrino", "neuroendocrina": "neuroendócrina",
    "neuroendocrinos": "neuroendócrinos", "neuroendocrinas": "neuroendócrinas",
    "Neuroendocrino": "Neuroendócrino", "Neuroendocrinos": "Neuroendócrinos",
    "bronquico": "brônquico", "bronquica": "brônquica",
    "bronquicos": "brônquicos",
    "cenario": "cenário", "cenarios": "cenários",
    "Cenario": "Cenário", "Cenarios": "Cenários",
    "sintomatico": "sintomático", "sintomatica": "sintomática",
    "sintomaticos": "sintomáticos", "sintomaticas": "sintomáticas",
    "assintomatico": "assintomático", "assintomatica": "assintomática",
    "assintomaticos": "assintomáticos",
    "citotoxico": "citotóxico", "citotoxica": "citotóxica",
    "plumbifero": "plumbífero", "plumbiferos": "plumbíferos",
    "emetogenico": "emetogênico", "emetogenica": "emetogênica",
    "antemetico": "antiemético",
    "antiemetico": "antiemético", "antiemeticos": "antieméticos",
    "hipertensao": "hipertensão", "hipotensao": "hipotensão",
    "Hipertensao": "Hipertensão",
    "multicentrico": "multicêntrico", "multicentrica": "multicêntrica",
    "isquemico": "isquêmico", "isquemica": "isquêmica",
    "isquemicos": "isquêmicos",
    # Disease descriptors
    "metastatico": "metastático", "metastatica": "metastática",
    "metastaticos": "metastáticos", "metastaticas": "metastáticas",
    "Metastatico": "Metastático",
    "toxico": "tóxico", "toxica": "tóxica",
    "toxicos": "tóxicos", "toxicas": "tóxicas",
    "cronico": "crônico", "cronica": "crônica",
    "cronicos": "crônicos", "cronicas": "crônicas",
    "Cronico": "Crônico",
    "tipico": "típico", "tipica": "típica",
    "tipicos": "típicos", "tipicas": "típicas",
    "atipico": "atípico", "atipica": "atípica",
    "atipicos": "atípicos",
    # More science terms
    "dosimetrico": "dosimétrico", "dosimetrica": "dosimétrica",
    "dosimetricos": "dosimétricos", "dosimetricas": "dosimétricas",
    "volumetrico": "volumétrico", "volumetrica": "volumétrica",
    "volumetricos": "volumétricos",
    "cirurgico": "cirúrgico", "cirurgica": "cirúrgica",
    "cirurgicos": "cirúrgicos",
    "Cirurgico": "Cirúrgico",
    "toracico": "torácico", "toracica": "torácica",
    "pelvico": "pélvico", "pelvica": "pélvica",
    # Words commonly appearing without accent
    "ressonancia": "ressonância", "Ressonancia": "Ressonância",
    "priomario": "primário",
    "primario": "primário", "primaria": "primária",
    "primarios": "primários", "primarias": "primárias",
    "Primario": "Primário", "Primaria": "Primária",
    "secundario": "secundário", "secundaria": "secundária",
    "secundarios": "secundários",
    "terciario": "terciário", "terciaria": "terciária",
    # Radiology specific
    "gama": "gama",
    "camara": "câmara", "camaras": "câmaras",
    "Camara": "Câmara",
    "fantoma": "fantoma",
    "voxelizado": "voxelizado",
    # Missing cedilla (-ança)
    "seguranca": "segurança", "segurancas": "seguranças",
    "Seguranca": "Segurança",
    "crianca": "criança", "criancas": "crianças",
    "Crianca": "Criança", "Criancas": "Crianças",
    "balanca": "balança", "balancas": "balanças",
    "mudanca": "mudança", "mudancas": "mudanças",
    "Mudanca": "Mudança",
    "esperanca": "esperança",
    "semelhanca": "semelhança",
    "confianca": "confiança",
    "tolerancia": "tolerância",
    # -ória words (proparoxytones)
    "regulatoria": "regulatória", "regulatorias": "regulatórias",
    "Regulatoria": "Regulatória",
    "mandatoria": "mandatória", "mandatorias": "mandatórias",
    "Mandatoria": "Mandatória",
    "secretoria": "secretória",
    "historia": "história", "historias": "histórias",
    "Historia": "História",
    "transitoria": "transitória",
    "ambulatoria": "ambulatória",
    "inflamatoria": "inflamatória", "inflamatorias": "inflamatórias",
    "refrataria": "refratária",
    "Refrataria": "Refratária",
    "migratoria": "migratória",
    # -ária words (proparoxytones)
    "diaria": "diária", "diarias": "diárias",
    "Diaria": "Diária",
    "urinaria": "urinária", "urinarias": "urinárias",
    "Urinaria": "Urinária",
    "unitaria": "unitária",
    "voluntaria": "voluntária", "voluntarias": "voluntárias",
    "intermediaria": "intermediária",
    "funeraria": "funerária",
    "subsidiaria": "subsidiária",
    "complementaria": "complementária",
    "hereditaria": "hereditária",
    "involuntaria": "involuntária",
    "multidisciplinaria": "multidisciplinária",
    "solitaria": "solitária",
    # Other missing
    "micrometro": "micrômetro", "micrometros": "micrômetros",
    "dosimetro": "dosímetro", "dosimetros": "dosímetros",
    "especifico": "específico", "especifica": "específica",
    "especificos": "específicos", "especificas": "específicas",
    "Especifico": "Específico", "Especifica": "Específica",
    "peritonio": "peritônio",
    "peritoneal": "peritoneal",
    "necrose": "necrose",
    "eletronico": "eletrônico", "eletronica": "eletrônica",
    "eletronicos": "eletrônicos",
    # Remaining
    "subotimo": "subótimo", "subotima": "subótima",
    "dificil": "difícil", "Dificil": "Difícil",
    "facil": "fácil", "Facil": "Fácil",
    "util": "útil", "Util": "Útil",
    "volatil": "volátil",
    "fertil": "fértil",
    "fragil": "frágil",
    # ─── NEW additions ───
    # física/físico (adjective "physical")
    "fisica": "física", "fisicas": "físicas",
    "fisico": "físico", "fisicos": "físicos",
    "Fisica": "Física",
    # química/químico
    "quimica": "química", "quimicas": "químicas",
    "quimico": "químico", "quimicos": "químicos",
    "Quimica": "Química",
    "radioquimica": "radioquímica",
    "bioquimica": "bioquímica", "bioquimico": "bioquímico",
    # câncer/cânceres
    "cancer": "câncer", "canceres": "cânceres",
    "Cancer": "Câncer",
    # intrínseca/intrínseco
    "intrinseca": "intrínseca", "intrinseco": "intrínseco",
    "intrinsecas": "intrínsecas",
    # clássica/clássico
    "classica": "clássica", "classico": "clássico",
    "classicas": "clássicas", "classicos": "clássicos",
    "Classica": "Clássica",
    # prévio/prévia
    "previo": "prévio", "previa": "prévia",
    "previos": "prévios", "previas": "prévias",
    # sítio/sítios (anatomical site)
    "sitio": "sítio", "sitios": "sítios",
    # ruído
    "ruido": "ruído", "ruidos": "ruídos",
    # saúde
    "saude": "saúde", "Saude": "Saúde",
    # presença/ausência
    "presenca": "presença", "Presenca": "Presença",
    "ausencia": "ausência", "Ausencia": "Ausência",
    # licença
    "licenca": "licença",
    # glicoproteína/proteína
    "glicoproteina": "glicoproteína", "glicoproteinas": "glicoproteínas",
    "proteina": "proteína", "proteinas": "proteínas",
    # crânio
    "cranio": "crânio", "cranios": "crânios",
    "Cranio": "Crânio",
    # vértice
    "vertice": "vértice",
    # múltiplas
    "multiplas": "múltiplas", "multiplos": "múltiplos",
    "multipla": "múltipla", "multiplo": "múltiplo",
    "Multiplas": "Múltiplas",
    # síntese/sínteses
    "sintese": "síntese", "sinteses": "sínteses",
    # bioquímica already above
    # microscópica/microscópico
    "microscopica": "microscópica", "microscopico": "microscópico",
    "microscopicas": "microscópicas",
    # macroscópica
    "macroscopica": "macroscópica",
    # espécime
    "especime": "espécime",
    # náusea
    "nausea": "náusea", "nauseas": "náuseas",
    "Nausea": "Náusea",
    # fígado
    "figado": "fígado", "Figado": "Fígado",
    # baço
    "baco": "baço",
    # óleo
    "oleo": "óleo",
    # rígido/rígida
    "rigido": "rígido", "rigida": "rígida",
    "rigidos": "rígidos", "rigidas": "rígidas",
    # ácido (keep — noun)
    # sódio
    "sodio": "sódio",
    # potássio
    "potassio": "potássio",
    # crônica already above
    # domínio
    "dominio": "domínio", "dominios": "domínios",
    # partícula
    "particula": "partícula", "particulas": "partículas",
    # inespecífico
    "inespecifico": "inespecífico", "inespecifica": "inespecífica",
    "inespecificos": "inespecíficos", "inespecificas": "inespecíficas",
    # radiofarmácia
    "radiofarmacia": "radiofarmácia",
    "Radiofarmacia": "Radiofarmácia",
    # farmácia
    "farmacia": "farmácia",
    # ética already covered by suffix
    # lógica already covered by suffix
    # genérica already covered
    # básica/básico
    "basica": "básica", "basico": "básico",
    "basicas": "básicas", "basicos": "básicos",
    "Basica": "Básica",
    # específica already above
    # tóxico already above
    # questão
    "questao": "questão", "questoes": "questões",
    # época
    "epoca": "época", "epocas": "épocas",
    # peristáltica
    "peristaltica": "peristáltica", "peristaltico": "peristáltico",
    # metabólico
    "metabolico": "metabólico", "metabolica": "metabólica",
    "metabolicos": "metabólicos", "metabolicas": "metabólicas",
    # eletrólito
    "eletrolito": "eletrólito", "eletrolitos": "eletrólitos",
    # empírica/empírico
    "empirica": "empírica", "empirico": "empírico",
    "empiricas": "empíricas", "empiricos": "empíricos",
    # fóton/fótons
    "foton": "fóton", "fotons": "fótons",
    # elétron/elétrons
    "eletron": "elétron", "eletrons": "elétrons",
    # avançado/avançada
    "avancado": "avançado", "avancada": "avançada",
    "avancados": "avançados", "avancadas": "avançadas",
    "Avancado": "Avançado",
    # logística
    "logistica": "logística", "Logistica": "Logística",
    # académico → not BR (acadêmico already by suffix -êmico)
}

# Apply word-level replacements (longest first to avoid partial matches)
sorted_words = sorted(WORDS.keys(), key=len, reverse=True)
for word in sorted_words:
    replacement = WORDS[word]
    if word != replacement:
        text = re.sub(r'\b' + re.escape(word) + r'\b', replacement, text)

# ─── PHASE 4: Special fixes ───
text = text.replace("nefroproteao", "nefroproteção")
text = text.replace("Nefroproteao", "Nefroproteção")

# ─── PHASE 5: Fix "e" -> "e-accent" (verb ser, 3rd person singular present) ───
# Context-aware: looks backward in same clause for past participles or existing verbs.
# If a participle/verb found -> "e" is conjunction -> keep.
# Otherwise -> "e" is the verb "e-accent" (is) -> replace.

TARGET_RE = re.compile(
    r'(?:'
    # Past participles (passive voice)
    r'recomendad[oa]s?|realizad[oa]s?|administrad[oa]s?|'
    r'obtid[oa]s?|mantid[oa]s?|iniciad[oa]s?|definid[oa]s?|'
    r'basead[oa]s?|limitad[oa]s?|indicad[oa]s?|considerad[oa]s?|'
    r'utilizad[oa]s?|confirmad[oa]s?|calculad[oa]s?|'
    r'focad[oa]s?|fornecid[oa]s?|mencionad[oa]s?|discutid[oa]s?|'
    r'captad[oa]s?|restrit[oa]s?|reconhecid[oa]s?|preferid[oa]s?|'
    r'praticad[oa]s?|estabelecid[oa]s?|omitid[oa]s?|'
    r'absorvid[oa]s?|'
    # Adjectives
    r'essencial|fundamental|frequente(?:mente)?|'
    r'rar[oa]|inferior|superior|comum|'
    r'cumulativ[oa]|significativ[oa]|'
    r'mandatóri[oa]|obrigatóri[oa]|mandatório|'
    r'simples|possível|viável|aceitável|'
    r'mínima|mínimo|heterogêne[oa]|'
    r'genéric[oa]|insuficiente|difícil|'
    r'dose-limitante|'
    # Adverbs followed by adjective
    r'particularmente|especialmente|geralmente|tipicamente|'
    r'amplamente|predominantemente|frequentemente|'
    # "mais/menos + adj"
    r'mais |menos |'
    # Specific article+noun combinations (copula identification)
    r'o principal|a principal|o mais|a mais|'
    r'o método|o padrão|o tratamento|a dose|a terapia|'
    r'o único|a única|o exame|o fator|o dado|a ferramenta|'
    r'o radiotracador|o radiofármaco|o componente|a toxicidade|'
    r'um proxy|uma técnica|'
    r'um alfa-emissor|um beta-emissor|um emissor|'
    r'um mimético|um comparador|'
    r'um componente|um fator|uma fonte|uma limitação|uma barreira|'
    r'um radioligante|uma armadilha|um análogo|uma glicoproteína|'
    r'um fator limitante|'
    # Preposition + number
    r'de \d'
    r')\b',
    re.IGNORECASE
)

PP_RE = re.compile(r'\b\w+(?:ad[oa]s?|id[oa]s?)\b')
VERB_RE = re.compile(r'\b(?:é|são|foi|foram|será|serão|sendo|ser)\b')

e_count = 0
result_chars = []
i = 0
while i < len(text) - 3:
    if text[i:i+3] == ' e ' or text[i:i+3] == ' E ':
        rest = text[i+3:]
        m = TARGET_RE.match(rest)
        if m:
            # Look back up to 80 chars, stop at sentence boundary (. or ;)
            start = max(0, i - 80)
            ctx = text[start:i]
            last_boundary = max(ctx.rfind('. '), ctx.rfind('; '))
            if last_boundary >= 0:
                ctx = ctx[last_boundary:]
            # Check for existing verb in context (if clause already has a verb, this "e" is conjunction)
            has_verb = VERB_RE.search(ctx)
            # Check the immediately preceding word for adj/participle suffixes
            words_before = ctx.split()
            last_word = words_before[-1].rstrip('.,;:)').lower() if words_before else ''
            has_adj_suffix = last_word.endswith(('ável', 'ível', 'ente', 'ante'))

            if has_verb or (PP_RE.search(ctx) and not last_word.endswith(('ção', 'são', 'ão', 'mento', 'dade', 'gia', 'cia', 'cia', 'eiro', 'eira'))) or has_adj_suffix:
                result_chars.append(text[i:i+3])  # Keep as "e"
            else:
                e_char = 'É' if text[i+1] == 'E' else 'é'
                result_chars.append(' ' + e_char + ' ')
                e_count += 1
            i += 3
            continue
    result_chars.append(text[i])
    i += 1
result_chars.append(text[i:])
text = ''.join(result_chars)
print(f"Phase 5: Fixed {e_count} 'e' to 'e-accent' (verb ser)")

# ─── PHASE 6: Specific remaining "e" -> "e-accent" fixes ───
# Cases where Phase 5 context check was too conservative or TARGET_RE didn't match
SPECIFIC_E_FIXES = [
    # Phase 5 false negatives: nouns falsely matched as participles
    ("aminoácidos) e iniciada", "aminoácidos) é iniciada"),
    ("aminoácidos e iniciada", "aminoácidos é iniciada"),
    ("submandibulares) e iniciado", "submandibulares) é iniciado"),
    ("antes) e recomendada", "antes) é recomendada"),
    ("aminoácidos e realizada", "aminoácidos é realizada"),
    ("liberação e realizada", "liberação é realizada"),
    ("fisiológica) e iniciada", "fisiológica) é iniciada"),
    # "e o/a" copula (identification) — specific contexts where Phase 5 might miss
    ("radiofármaco padrão e o 177Lu-DOTATATE", "radiofármaco padrão é o 177Lu-DOTATATE"),
    ("177Lu) e o único radiofármaco", "177Lu) é o único radiofármaco"),
    ("FDA 2020) e o radiotracador mais", "FDA 2020) é o radiotracador mais"),
    ("Lu-177) e o radiofármaco aprovado", "Lu-177) é o radiofármaco aprovado"),
    ("O 177Lu-PSMA-I&T e um radioligante", "O 177Lu-PSMA-I&T é um radioligante"),
    ("este e o contexto clínico", "este é o contexto clínico"),
    ("PSMA e uma glicoproteína", "PSMA é uma glicoproteína"),
    ("223Ra e um alfa-emissor", "223Ra é um alfa-emissor"),
    ("223Ra e um mimético", "223Ra é um mimético"),
    ("Metastron) e um beta-emissor", "Metastron) é um beta-emissor"),
    ("GE Healthcare) e um beta-emissor", "GE Healthcare) é um beta-emissor"),
    ("GE Healthcare) e um análogo", "GE Healthcare) é um análogo"),
    ("Lantheus) e um beta-emissor", "Lantheus) é um beta-emissor"),
    ("Bayer) e um mimético", "Bayer) é um mimético"),
    ("Bayer) e um alfa-emissor", "Bayer) é um alfa-emissor"),
    ("A MIBG e um análogo", "A MIBG é um análogo"),
    ("iodo-131) e um análogo", "iodo-131) é um análogo"),
    ("que e captado pelo", "que é captado pelo"),
    ("131I e um emissor beta", "131I é um emissor beta"),
    ("SPECT/CT e um componente", "SPECT/CT é um componente"),
    ("radiofármacos terapêuticos e um fator", "radiofármacos terapêuticos é um fator"),
    ("pós-terapia e um componente", "pós-terapia é um componente"),
    # "e de X" copula (description with value)
    ("comercial e fornecida em dose", "comercial é fornecida em dose"),
    ("177Lu e de 6,65", "177Lu é de 6,65"),
    ("aceitável e de 95%", "aceitável é de 95%"),
    ("administrada e de 100-200 MBq", "administrada é de 100-200 MBq"),
    ("captação padrão e de 60 minutos", "captação padrão é de 60 minutos"),
    ("aprovada e de 7,4 GBq", "aprovada é de 7,4 GBq"),
    # "e + adjective" copula (predication)
    ("que e área de intensa", "que é área de intensa"),
    ("mielotoxicidade e cumulativa", "mielotoxicidade é cumulativa"),
    ("mielotoxicidade e dose-limitante", "mielotoxicidade é dose-limitante"),
    ("renal e mandatório", "renal é mandatório"),
    ("da aquisição e mandatória", "da aquisição é mandatória"),
    ("PSMA ao PET e a principal limitação", "PSMA ao PET é a principal limitação"),
    ("limitação intrínseca e a dependência", "limitação intrínseca é a dependência"),
    ("18F-FDG PET/CT e o exame de escolha", "18F-FDG PET/CT é o exame de escolha"),
    ("uncinado pancreático e uma armadilha", "uncinado pancreático é uma armadilha"),
    ("do paciente e simples comparado", "do paciente é simples comparado"),
    ("208 keV) e fornecido por reatores", "208 keV) é fornecido por reatores"),
    ("para 223Ra e restrita", "para 223Ra é restrita"),
    ("O 223Ra e restrito", "O 223Ra é restrito"),
    ("com 153Sm e possível", "com 153Sm é possível"),
    ("89Sr raramente e viável", "89Sr raramente é viável"),
    ("eixo curto e aceitável", "eixo curto é aceitável"),
    ("estendido não e viável", "estendido não é viável"),
    ("em 12 semanas e marcador", "em 12 semanas é marcador"),
    ("não e rotina (223Ra", "não é rotina (223Ra"),
    ("A RSO e uma técnica", "A RSO é uma técnica"),
    ("a RSO e amplamente praticada", "a RSO é amplamente praticada"),
    ("disponibilidade e mais limitada", "disponibilidade é mais limitada"),
    ("mas e indicador de técnica", "mas é indicador de técnica"),
    ("RSO e preferida sobre", "RSO é preferida sobre"),
    ("90Y-Citrato e amplamente disponível", "90Y-Citrato é amplamente disponível"),
    ("intra-articular e mais desafiador", "intra-articular é mais desafiador"),
    ("completo não e viável", "completo não é viável"),
    ("dose absorvida e calculada", "dose absorvida é calculada"),
    ("(até 30-40%) e uma limitação", "(até 30-40%) é uma limitação"),
    ("dose-resposta tumoral e mais bem", "dose-resposta tumoral é mais bem"),
    ("clínica ainda não e rotina", "clínica ainda não é rotina"),
    ("pós-terapia e reconhecida como", "pós-terapia é reconhecida como"),
    ("dosimetria e a ferramenta", "dosimetria é a ferramenta"),
    ("investimento mínimo e viável em", "investimento mínimo é viável em"),
    ("de relatório e genérico", "de relatório é genérico"),
    ("recomendada, e frequentemente omitida", "recomendada, é frequentemente omitida"),
    ("padronizado e uma barreira", "padronizado é uma barreira"),
    ("(HIS/RIS) ainda e insuficiente", "(HIS/RIS) ainda é insuficiente"),
    ("mielotoxicidade e a toxicidade dose-limitante", "mielotoxicidade é a toxicidade dose-limitante"),
    ("a medula e o fator limitante", "a medula é o fator limitante"),
    ("O sangue e um proxy", "O sangue é um proxy"),
    ("de corpo inteiro e mais simples", "de corpo inteiro é mais simples"),
    ("sanguínea e significativa (CV 20-40%)", "sanguínea é significativa (CV 20-40%)"),
    ("farmacocinética sanguinea e significativa", "farmacocinética sanguinea é significativa"),
    ("pós-dose e o dado de entrada", "pós-dose é o dado de entrada"),
    ("para 177Lu) e significativamente inferior", "para 177Lu) é significativamente inferior"),
    ("177Lu-PSMA-617 e uma fonte conhecida", "177Lu-PSMA-617 é uma fonte conhecida"),
    ("a dosimetria não e exigida", "a dosimetria não é exigida"),
    ("autorização e mais genérica", "autorização é mais genérica"),
    ("do paciente pós-terapia e um componente crítico", "do paciente pós-terapia é um componente crítico"),
    ("no paciente e predominantemente intratumoral", "no paciente é predominantemente intratumoral"),
    ("de alta energia e o principal determinante", "de alta energia é o principal determinante"),
    ("compliance domiciliar e difícil", "compliance domiciliar é difícil"),
    ("inter-paciente e significativa", "inter-paciente é significativa"),
    # "e CONTRAINDICADA" cases
    ("esta combinação e CONTRAINDICADA", "esta combinação é CONTRAINDICADA"),
    # "cabazitaxel e um comparador"
    ("cabazitaxel e um comparador", "cabazitaxel é um comparador"),
    # "e captado" (passive)
    ("gastrointestinal e captado pelos", "gastrointestinal é captado pelos"),
    # Additional false negatives from various lines
    ("farmacocinética individual (até 30-40%) e uma limitação intrínseca", "farmacocinética individual (até 30-40%) é uma limitação intrínseca"),
    ("farmacocinética inter-paciente e significativa", "farmacocinética inter-paciente é significativa"),
    # Compound that gave origin
    ("linker AHEX; e o composto que deu", "linker AHEX; é o composto que deu"),
    # Phase 5 false negative: "personalizada" falsely matched as participle
    ("personalizada e mencionada", "personalizada é mencionada"),
    # More Phase 5 false negatives
    ("inter-ciclo na farmacocinética individual (até 30-40%) e uma limitação", "inter-ciclo na farmacocinética individual (até 30-40%) é uma limitação"),
]
e6_count = 0
for old, new in SPECIFIC_E_FIXES:
    cnt = text.count(old)
    if cnt > 0:
        text = text.replace(old, new)
        e6_count += cnt
print(f"Phase 6: Fixed {e6_count} specific remaining 'e' cases")

# ─── PHASE 7: Fix "esta" -> "esta-accent" (verb estar) ───
# "esta" as demonstrative pronoun (this) precedes nouns: "esta combinação"
# "está" as verb (is) precedes adjectives, adverbs, gerunds, participles
ESTA_FIXES = [
    # "não esta " -> "não está " (negation + verb estar)
    ("não esta ", "não está "),
    ("Não esta ", "Não está "),
    # "ainda esta " -> "ainda está " (adverb + verb estar)
    ("ainda esta ", "ainda está "),
    # "que esta " before adjective/adverb/participle
    ("que esta disponível", "que está disponível"),
    # Specific patterns from the text
    ("quantitativo esta disponível", "quantitativo está disponível"),
    ("PSMA-RLT esta menos", "PSMA-RLT está menos"),
    ("ainda esta sendo", "ainda está sendo"),
]
e7_count = 0
for old, new in ESTA_FIXES:
    cnt = text.count(old)
    if cnt > 0:
        text = text.replace(old, new)
        e7_count += cnt
print(f"Phase 7: Fixed {e7_count} 'esta' to 'esta-accent' (verb estar)")

# ─── PHASE 8: Fix "estao" -> "estao-accent" (verb estar, 3rd person plural) ───
# "estão" is always the verb (no demonstrative pronoun form exists for "estao")
text = re.sub(r'\bestao\b', 'estão', text)
text = re.sub(r'\bEstao\b', 'Estão', text)
e8_count = len(re.findall(r'\bestão\b', text))  # Count for info
print(f"Phase 8: Ensured all 'estao' -> 'estao-accent'")

# ─── Write result ───
acc = len(re.findall(r'[àáâãéêíóôõúçÀÁÂÃÉÊÍÓÔÕÚÇ]', text))
print(f"Accented chars: {acc}")
print(f"File size: {len(text)} chars")

with open(target, 'w', encoding='utf-8') as f:
    f.write(text)

print("Accent fix applied.")
