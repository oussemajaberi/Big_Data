# Recupere l'URL Jupyter (avec token) du conteneur spark-jupyter et la copie dans le presse-papiers.
$line = docker exec spark-jupyter jupyter server list 2>$null | Select-String "http://"
if (-not $line) {
    Write-Error "Aucun serveur Jupyter trouve. Le conteneur spark-jupyter tourne-t-il ? (docker ps)"
    exit 1
}

$token = ($line -replace '.*token=([a-f0-9]+).*', '$1')
$url = "http://localhost:8888/?token=$token"

Write-Output $url
Set-Clipboard -Value $url
Write-Output "(URL copiee dans le presse-papiers)"
