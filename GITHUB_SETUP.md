# GitHub setup for MS4GC

This guide assumes that Git is installed and that you already have a GitHub account.

## 1. Create a new GitHub repository

1. Open GitHub in your browser.
2. Click `+` → `New repository`.
3. Repository name: `MS4GC`.
4. Do **not** add a README, `.gitignore`, or license on GitHub, because these files already exist locally.
5. Click `Create repository`.

## 2. Initialize the local repository

Open PowerShell in the local `MS4GC` folder:

```powershell
git init
git add .
git commit -m "Initial commit: add MS4GC 1.05"
git branch -M main
```

## 3. Connect to GitHub

Replace `DEIN-GITHUB-NAME` with your real GitHub username:

```powershell
git remote add origin https://github.com/DEIN-GITHUB-NAME/MS4GC.git
```

If the remote already exists, use:

```powershell
git remote set-url origin https://github.com/DEIN-GITHUB-NAME/MS4GC.git
```

Check the remote URL:

```powershell
git remote -v
```

The URL should contain only one slash after `github.com`:

```text
https://github.com/DEIN-GITHUB-NAME/MS4GC.git
```

## 4. Push the repository

```powershell
git push -u origin main
```

After this, the repository should be visible at:

```text
https://github.com/DEIN-GITHUB-NAME/MS4GC
```

## 5. Normal workflow after code changes

```powershell
git status
git diff
git add .
git commit -m "Describe the change"
git push
```

Before publishing a new version, it is recommended to run the tests:

```powershell
python -m unittest discover -s tests
```
