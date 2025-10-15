<#
PowerShell helper to initialize git, create GitHub repo via gh CLI (if available), and push code.
Usage: .\publish.ps1 -RepoName my-repo -Visibility public
#>
param(
    [string]$RepoName = "blue-enigma-ai",
    [string]$Visibility = "private",
    [string]$RepoUrl = ""
)

# ensure git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..."
    git init
}

Write-Host 'Adding files and committing...'
git add .
git commit -m 'Initial commit - Blue Enigma hybrid AI system'

# try to use gh if available
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
    Write-Host "Creating repo via gh CLI..."
    if ($RepoUrl -ne "") {
        Write-Host "Using provided remote URL: $RepoUrl"
        git remote add origin $RepoUrl
        git branch -M main
        git push -u origin main
    } else {
        gh repo create "$RepoName" --$Visibility --confirm
        git branch -M main
        git push -u origin main
    }
} else {
    if ($RepoUrl -ne "") {
        Write-Host "Adding remote and pushing to provided RepoUrl: $RepoUrl"
        git remote add origin $RepoUrl
        git branch -M main
        git push -u origin main
    } else {
    Write-Host 'gh CLI not found. Please create a repo on GitHub and run the following commands:'
    Write-Host "git remote add origin https://github.com/<your-username>/$RepoName.git"
    Write-Host 'git branch -M main'
    Write-Host 'git push -u origin main'
    }
}
