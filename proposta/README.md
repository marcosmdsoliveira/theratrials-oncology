# Proposta — Portal de Ensaios & Trial Matcher (protótipo)

Protótipo navegável para **apresentação comercial** a centros recrutadores de pesquisa clínica e à indústria farmacêutica. **Não está integrado ao site** (não entra no deploy do GitHub Pages).

## Como apresentar
Abra `index.html` com duplo-clique (funciona offline, sem servidor). Navegue pelas 5 telas no topo:

1. **Buscar ensaios** — a experiência do oncologista (lado da demanda): filtros por tumor, **estado/cidade**, biomarcador, patrocinador, status e **"teste fornecido"**; cards com selo do centro, "Recrutando agora", "Teste grátis" e o botão **Encaminhar paciente**. Inclui um slot **"Destaque · Patrocinado"** claramente rotulado.
2. **Página do ensaio** — destino indexável (SEO) e ponto de conversão: braços, critérios, **pré-triagem de elegibilidade** interativa, centros no mapa, contatos do PI e **formulário de encaminhamento** (mock).
3. **Perfil do centro** — vitrine do centro recrutador com todos os seus ensaios abertos e contato ("Parceiro verificado").
4. **Painel do parceiro** — dashboard de métricas (visualizações por ensaio, origem geográfica dos médicos, **leads gerados**) — *o que se vende como assinatura*.
5. **Modelo comercial** — os produtos de receita e a lógica de parceria.

## Fonte dos dados
Ensaios reais extraídos de listas de **estudos abertos** de três centros (PDFs fornecidos): **Personal Oncologia (BH)**, **Oncominas (MG)** e **Oncoclínicas (rede nacional)**. 

> ⚠️ **Dados ilustrativos para demonstração.** Nomes de ensaios, NCT, cidades e investigadores principais vêm dos materiais dos centros; contatos/telefones marcados como *ilustrativo* substituem dados de contato reais. Atribuições de patrocinador são best-effort e devem ser confirmadas antes de uso comercial. Não usar para decisão clínica.
