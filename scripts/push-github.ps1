# Sostituisci solo il nome repo se ne vuoi uno diverso.
# Requisiti: Git installato. Per creare automaticamente il repo serve GitHub CLI: winget install GitHub.cli

$ErrorActionPreference = "Stop"
$RepoName = "puglia-profit-engine"
$GitHubUser = "antoniobottalico1505"

cd "$PSScriptRoot\.."

git init
git add .
git commit -m "Create Puglia Profit Engine"

# Opzione A: se hai GitHub CLI configurato con gh auth login
gh repo create "$GitHubUser/$RepoName" --public --source=. --remote=origin --push

# Opzione B manuale se il repo esiste già:
# git branch -M main
# git remote add origin "https://github.com/$GitHubUser/$RepoName.git"
# git push -u origin main
