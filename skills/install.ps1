param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,

    [string[]]$Skills = @(),

    [switch]$List,

    [switch]$All
)

$SkillDir = Split-Path -Parent $PSCommandPath
$ManifestPath = Join-Path -Path $SkillDir -ChildPath "skills.json"

if ($List) {
    $manifest = Get-Content -Path $ManifestPath -Raw | ConvertFrom-Json
    Write-Host "`n=== Skills disponibles ===" -ForegroundColor Cyan
    $manifest.categories | ForEach-Object {
        Write-Host "`n[$($_.category)]" -ForegroundColor Yellow
        $_.skills | ForEach-Object {
            Write-Host "  $($_.name) - $($_.description)" -ForegroundColor White
        }
    }
    return
}

function Get-Target {
    $targets = @(
        (Join-Path -Path $target -ChildPath ".opencode\skills"),
        (Join-Path -Path $target -ChildPath ".claude\skills"),
        (Join-Path -Path $target -ChildPath ".agents\skills")
    )
    $existing = $targets | Where-Object { Test-Path -LiteralPath $_ }
    if ($existing) {
        return $existing | Select-Object -First 1
    }
    $chosen = $targets[0]
    New-Item -ItemType Directory -Path $chosen -Force | Out-Null
    return $chosen
}

$TargetDir = Get-Target

if ($All -or $Skills.Count -eq 0) {
    $Skills = Get-ChildItem -Directory -Path $SkillDir | Where-Object { $_.Name -ne "node_modules" } | ForEach-Object { $_.Name }
}

$Skills | ForEach-Object {
    $skill = $_
    $src = Join-Path -Path $SkillDir -ChildPath $skill
    $dst = Join-Path -Path $TargetDir -ChildPath $skill
    if (Test-Path -LiteralPath $src) {
        if (Test-Path -LiteralPath $dst) {
            Write-Host "  Actualizando: $skill" -ForegroundColor Yellow
        } else {
            Write-Host "  Instalando: $skill" -ForegroundColor Green
        }
        Copy-Item -Path "$src\*" -Destination $dst -Recurse -Force
    } else {
        Write-Warning "Skill no encontrado: $skill"
    }
}

Write-Host "`nSkills instalados en: $TargetDir" -ForegroundColor Cyan
Write-Host "Usa 'opencode' en el proyecto para cargarlos automaticamente.`n" -ForegroundColor Cyan
