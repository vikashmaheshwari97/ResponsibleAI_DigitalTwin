$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$CertDir = Join-Path $ProjectRoot "deploy\certs"
New-Item -ItemType Directory -Path $CertDir -Force | Out-Null

openssl req -x509 -nodes -days 365 `
  -newkey rsa:2048 `
  -keyout (Join-Path $CertDir "server.key") `
  -out (Join-Path $CertDir "server.crt") `
  -subj "/CN=localhost"

Write-Host "Created local self-signed TLS certificate in $CertDir"
