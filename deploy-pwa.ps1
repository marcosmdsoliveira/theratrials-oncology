# ==============================================================================
# TheraTrials Oncology — Deploy PWA para GitHub Pages
# ==============================================================================
# Faz: limpa lock órfão, configura identidade git, cria 2 commits separados
# (1 para alterações em common.js/data.js, 1 para tudo do PWA) e dá push.
#
# Como rodar:
#   1. Abra PowerShell na pasta do site:
#      cd "C:\Users\marco\Desktop\TheraTrials Oncology\site"
#   2. (Primeira vez) permitir scripts locais nesta sessão:
#      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   3. Rodar:
#      .\deploy-pwa.ps1
# ==============================================================================

$ErrorActionPreference = 'Stop'

function Section($title) {
    Write-Host ""
    Write-Host "==> $title" -ForegroundColor Cyan
}

# Garante que estamos na pasta certa
$siteRoot = "C:\Users\marco\Desktop\TheraTrials Oncology\site"
Set-Location $siteRoot

# 1. Limpa lock órfão
Section "1/6 · Limpando lock órfão (se existir)"
if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
    Write-Host "    .git\index.lock removido" -ForegroundColor Yellow
} else {
    Write-Host "    nenhum lock encontrado · OK"
}

# 2. Identidade git (caso ainda não esteja configurada)
Section "2/6 · Conferindo identidade git"
$null = git config user.name "Marcos Oliveira"
$null = git config user.email "marcosmdsoliveira@gmail.com"
Write-Host "    user.name  = $(git config user.name)"
Write-Host "    user.email = $(git config user.email)"

# 3. Status atual
Section "3/6 · Status atual"
git status -s | Select-Object -First 25

# 4. Commit 1 — common.js + data.js
Section "4/6 · Commit 1 — atualizações em common.js + data.js"
git reset HEAD 2>$null  # zera índice por garantia
git add assets/js/common.js assets/js/data.js
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "fix(database): atualizacoes em common.js e data.js`n`n- common.js: ajustes em filtros, favoritos e exportacao CSV`n- data.js: correcoes em entradas de estudo"
} else {
    Write-Host "    nada a commitar em JS · pulando"
}

# 5. Commit 2 — feat: PWA / iOS app
Section "5/6 · Commit 2 — feat: PWA / iOS app"
# Stage tudo restante (gitignore exclui *.bak_*)
git add -A
$staged2 = git diff --cached --name-only
if ($staged2) {
    Write-Host "    Arquivos a commitar:"
    $staged2 | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
    git commit -m "feat(pwa): TheraTrials Oncology como app instalavel iOS/Android`n`n- manifest.json com 12 icones, 4 shortcuts, modo standalone`n- sw.js: cache offline (network-first HTML, cache-first assets)`n- pwa-install.js: banner Adicionar a Tela Inicial + auto-update toast`n- offline.html: pagina de fallback com lista de paginas em cache`n- 19 icones iOS (60-1024) + maskable + favicons`n- 32 splash screens (iPhone SE -> 16 Pro Max, iPad mini -> Pro 12.9)`n- meta tags PWA injetadas em 18 paginas HTML (idempotente)`n- INSTALL-IOS.md: guia de instalacao no iPhone`n- .gitignore: cobre *.bak_*"
} else {
    Write-Host "    nada a commitar · pulando"
}

# 6. Push
Section "6/6 · Push para origin/main"
git push origin main
Write-Host ""
Write-Host "DEPLOY CONCLUIDO" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "  1. Acesse https://github.com/marcosmdsoliveira/theratrials-oncology/settings/pages"
Write-Host "  2. Confira que 'Enforce HTTPS' esta marcado"
Write-Host "  3. Aguarde ~1 min para o Pages publicar"
Write-Host "  4. No iPhone, abra a URL pelo Safari e use Compartilhar -> Adicionar a Tela de Inicio"
Write-Host ""
