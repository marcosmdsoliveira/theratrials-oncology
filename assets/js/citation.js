/* ============================================================
   Citação do card do Database (Vancouver · AMA · ABNT · texto simples)

   Fonte única: `card.citation`, a publicação REPRESENTADA pelo card
   (a que sustenta os dados exibidos), já normalizada a partir do
   snapshot PubMed pelo pipeline do Database v2. Nada é buscado na rede.

   Regras:
   • autoria só de `citation.authors` / `collective_name`. `sponsor`
     (PI) NUNCA entra na citação: investigador principal não é o
     primeiro autor da publicação;
   • sem `citation` estruturada: o `ref` do card vai literal, sem
     autor extraído ou inventado;
   • sem publicação (estudo registrado/em andamento): referência do
     registro (NCT), sem autor;
   • card em revisão editorial ou evidence_collection: sem citação
     principal escolhida por máquina;
   • metadado ausente é omitido, nunca inventado.
   ============================================================ */
(function (root) {
  'use strict';
  var TT = root.TheraTrials = root.TheraTrials || {};

  function limpo(t) { return String(t == null ? '' : t).trim(); }
  function semPonto(t) { return limpo(t).replace(/[.\s]+$/, ''); }
  function ponto(t) { t = semPonto(t); return t ? t + '.' : ''; }

  function nomeVancouver(a) {
    return [a.family, a.given_initials, a.suffix].filter(Boolean).join(' ');
  }
  function nomeAbnt(a) {
    var fam = a.family.toUpperCase() + (a.suffix ? ' ' + (/^jr\.?$/i.test(a.suffix) ? 'JUNIOR' : a.suffix.toUpperCase()) : '');
    var ini = (a.given_initials || '').split('').map(function (c) { return c + '.'; }).join(' ');
    return ini ? fam + ', ' + ini : fam;
  }

  function autores(c, fmt) {
    var lista = c.authors || [];
    var total = Math.max(c.authors_total || 0, lista.length);
    if (!lista.length) return c.collective_name ? semPonto(c.collective_name) : '';
    if (fmt === 'abnt') {
      if (total > 3) return nomeAbnt(lista[0]) + ' et al';
      return lista.map(nomeAbnt).join('; ');
    }
    if (fmt === 'ama') {
      if (total > 6) return lista.slice(0, 3).map(nomeVancouver).join(', ') + ', et al';
      return lista.map(nomeVancouver).join(', ');
    }
    if (fmt === 'plain') return nomeVancouver(lista[0]) + (total > 1 ? ', et al' : '');
    // vancouver: até 6 autores; acima disso, os 6 primeiros + et al.
    return lista.slice(0, 6).map(nomeVancouver).join(', ') + (total > 6 ? ', et al' : '');
  }

  // "2016;17(3):378-388" — só o que existe
  function fonteNumerica(c) {
    var s = String(c.year || '');
    if (c.volume) s += ';' + c.volume;
    if (c.issue) s += (c.volume ? '' : ';') + '(' + c.issue + ')';
    if (c.pages || c.article_number) s += ':' + (c.pages || c.article_number);
    return s;
  }

  function estruturada(c, fmt) {
    var au = autores(c, fmt);
    var tit = ponto(c.title);
    var doi = c.doi ? 'doi:' + c.doi : '';
    if (fmt === 'abnt') {
      var partes = [];
      // NBR 6023 admite o título do periódico abreviado (ISO 4); o título completo do PubMed vem na forma NLM
      var per = semPonto(c.journal_abbrev || c.journal);
      if (per) partes.push(per);
      if (c.volume) partes.push('v. ' + c.volume);
      if (c.issue) partes.push('n. ' + c.issue);
      if (c.pages) partes.push('p. ' + c.pages);
      else if (c.article_number) partes.push('art. ' + c.article_number);
      if (c.year) partes.push(String(c.year));
      return [ponto(au), tit, partes.length ? partes.join(', ') + '.' : '',
              c.doi ? 'DOI: ' + c.doi + '.' : '', c.pmid ? 'PMID: ' + c.pmid + '.' : '']
        .filter(Boolean).join(' ');
    }
    var jor = semPonto(c.journal_abbrev || c.journal);
    if (fmt === 'plain') {
      return [au ? au + '.' : '', tit, (jor ? jor + ' ' : '') + fonteNumerica(c) + '.',
              doi ? doi + '.' : '', c.pmid ? 'PMID: ' + c.pmid + '.' : ''].filter(Boolean).join(' ');
    }
    // vancouver e ama: Autores. Título. Periódico. Ano;Vol(Num):Pág. doi. PMID.
    return [au ? au + '.' : '', tit, jor ? jor + '.' : '', fonteNumerica(c) + '.',
            doi ? doi + '.' : '', c.pmid ? 'PMID: ' + c.pmid + '.' : ''].filter(Boolean).join(' ');
  }

  function pmidDoCard(s) {
    var m = String(s.pubmed_url || '').match(/pubmed\.ncbi\.nlm\.nih\.gov\/(\d+)/);
    return m ? m[1] : '';
  }
  function nctDoCard(s) {
    var m = String(s.nct || '').match(/NCT\d{8}/);
    return m ? m[0] : '';
  }
  function titulo(s) {
    return limpo(s.acron || String(s.estudo || '').split('\n')[0].split('(')[0]);
  }

  /** Que tipo de citação o card admite. */
  function kind(s) {
    if (!s) return 'none';
    if (/^Em revisão/i.test(limpo(s.status))) return 'withheld';
    if (s.citation && s.record_type !== 'evidence_collection') return 'structured';
    if (pmidDoCard(s) || /^(Publicado|Apresentado|Aprovado)/i.test(limpo(s.status))) return 'reference';
    return 'registry';
  }

  function format(s, fmt) {
    fmt = fmt || 'vancouver';
    var k = kind(s);
    if (k === 'none') return '';
    if (k === 'withheld') return 'Referência em revisão editorial.';
    if (k === 'structured') return estruturada(s.citation, fmt);
    var nct = nctDoCard(s);
    if (k === 'reference') {
      // `ref` literal: é a referência editorial do card; nenhum autor é extraído dele nem do sponsor.
      // O PMID do card NÃO é anexado: sem citação estruturada, a ligação ref ↔ PMID não foi validada
      // (pode ser justamente o conflito que bloqueou a citação).
      return [ponto(s.ref || titulo(s)), nct ? '[' + nct + ']' : ''].filter(Boolean).join(' ');
    }
    // registry: estudo sem publicação indexada — identifica o estudo, sem autor
    var reg = nct ? 'ClinicalTrials.gov: ' + nct + '.' : '';
    var link = s.nct_url && /^https?:\/\//.test(s.nct_url) ? 'Disponível em: ' + s.nct_url + '.' : '';
    return [ponto(titulo(s)), reg, 'Estudo sem publicação indexada.', link].filter(Boolean).join(' ');
  }

  TT.citation = { format: format, kind: kind };
  if (typeof module !== 'undefined' && module.exports) module.exports = TT.citation;
})(typeof window !== 'undefined' ? window : globalThis);
