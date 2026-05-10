# Instalar o TheraTrials no iPhone (PWA)

> O TheraTrials Oncology agora roda como um **app instalável** no iPhone — sem App Store, sem custo, sem revisão Apple. Ele funciona offline, abre em tela cheia, tem ícone próprio na tela inicial e splash screen ao abrir.

---

## Passo a passo (iPhone / iPad)

1. Abra o **Safari** (precisa ser o Safari — Chrome iOS não suporta esta funcionalidade).
2. Acesse a URL do site (ex.: `https://seu-usuario.github.io/theratrials/` ou domínio próprio).
3. Toque no botão **Compartilhar** (ícone de quadrado com seta para cima) na barra inferior.
4. Role e toque em **Adicionar à Tela de Início**.
5. Confirme o nome (já vem como **TheraTrials**) e toque em **Adicionar**.
6. Pronto — o ícone aparece na tela inicial e abre como app nativo.

> O banner discreto que aparece no rodapé da primeira visita já ensina esse passo a passo direto na tela.

---

## O que você ganha (modo standalone iOS)

| Recurso | Como funciona |
|---|---|
| **Sem barra do Safari** | Abre em tela cheia, igual app nativo |
| **Ícone na tela inicial** | Logo TheraTrials orbital, em todos os tamanhos (180×180 retina) |
| **Splash screen** | Tela de abertura preta com logo + wordmark, dimensionada para todos os iPhones (SE até 16 Pro Max) |
| **Modo offline** | Páginas já visitadas continuam acessíveis sem internet |
| **Status bar customizada** | Barra de status preta translúcida casando com o tema graphite |
| **Atualizações automáticas** | Toast "Nova versão disponível · Atualizar" quando houver nova publicação |
| **Persistência local** | Favoritos, filtros e estado de comparação ficam salvos via `localStorage` |

---

## Requisitos técnicos para hospedagem (GitHub Pages)

A PWA exige **HTTPS**. GitHub Pages já fornece HTTPS por padrão — só conferir:

1. No repositório do site, vá em **Settings → Pages**.
2. Em **Custom domain**, marque **Enforce HTTPS** (se ainda não estiver marcado).
3. URL final: `https://<seu-usuario>.github.io/<repo>/` ou domínio próprio.

> Se quiser domínio próprio (ex.: `theratrials.com.br`), aponte um registro `CNAME` para `<seu-usuario>.github.io` e adicione o domínio em Settings → Pages → Custom domain.

---

## Arquivos PWA adicionados ao projeto

```
site/
├── manifest.json                       # Web App Manifest
├── sw.js                               # Service Worker (cache offline)
├── offline.html                        # Página de fallback offline
├── INSTALL-IOS.md                      # Este guia
├── assets/
│   ├── js/
│   │   └── pwa-install.js              # Banner de instalação + registro do SW
│   └── img/
│       ├── icons/                      # 19 ícones (favicon → icon-1024)
│       │   ├── apple-touch-icon.png
│       │   ├── icon-{72,96,128,144,152,180,192,384,512,1024}.png
│       │   ├── icon-{192,512}-maskable.png
│       │   └── favicon-{16,32,48}.png
│       └── splash/                     # 32 splash screens iOS (todos os iPhones e iPads)
│           └── splash-{w}x{h}.png
```

---

## Atualizando o app no iPhone

A PWA atualiza sozinha:

- Quando você abre o app, o service worker checa por nova versão em background.
- Se houver, aparece um toast no canto inferior direito: **"Nova versão disponível · Atualizar"**.
- Toque em **Atualizar** — o app recarrega com a versão nova.

Para forçar atualização manual sem o toast:

1. Mantenha o ícone do app pressionado na tela inicial.
2. Toque em **Excluir App** → **Remover da Tela de Início** (não apaga dados, só o atalho).
3. Reabra o site no Safari e re-instale.

---

## Limitações reais do iOS para PWA

A Apple ainda restringe algumas APIs em PWAs (em comparação com Android):

- **Push notifications** — funciona apenas no iOS 16.4+ (e exige HTTPS válido).
- **Background sync** — não suportado.
- **Web Bluetooth / NFC / WebUSB** — não suportado.
- **Acesso a câmera/microfone** — funciona, mas pede permissão a cada sessão.
- **Storage** — máximo ~50 MB no IndexedDB/CacheStorage (Apple limita PWAs); o site cabe folgadamente.

Nada disso afeta o uso clínico do TheraTrials (consulta de evidências, estudos, ferramentas).

---

## Para a App Store de verdade

Se no futuro você quiser publicar na App Store oficial:

1. **Mac com Xcode** ou um serviço de build em nuvem (Codemagic, Ionic Appflow).
2. **Conta Apple Developer** ($99/ano).
3. **Wrapper Capacitor** — empacota este mesmo site como app nativo iOS sem reescrever nada.

Posso preparar o projeto Capacitor quando você tiver Mac/conta — basta avisar.

---

## Como testar localmente antes de publicar

A PWA exige HTTPS, **mas localhost é uma exceção**: funciona em `http://localhost`.

```bash
cd site
python -m http.server 8080
```

Abra `http://localhost:8080/` no Chrome → DevTools (F12) → aba **Application**:

- **Manifest** — confere se o manifest.json carregou e os ícones aparecem.
- **Service Workers** — confere se o `sw.js` está ativo.
- **Storage → Cache Storage** — confere as 3 caches (`-pages`, `-static`, `-runtime`).
- **Lighthouse** → tab **PWA** → roda auditoria; deve ficar verde em "Installable".

---

## Suporte

- Marcos Oliveira — médico nuclear
- Email: marcosmdsoliveira@gmail.com

© 2026 TheraTrials Oncology · uso educacional
