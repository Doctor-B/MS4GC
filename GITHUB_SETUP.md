# How to publish MS4GC on GitHub

This guide assumes that you already have a GitHub account.

## Option A: Upload through the GitHub web interface

1. Create a new repository on GitHub.
2. Repository name: `MS4GC`.
3. Do **not** add a README, license, or `.gitignore` on GitHub because these files already exist in this folder.
4. Open the new empty repository in your browser.
5. Choose **uploading an existing file**.
6. Drag all files and folders from this local `MS4GC` directory into the upload area.
7. Commit the uploaded files.

This is the easiest way if you do not want to use Git locally.

## Option B: Use Git on the command line

Open a terminal in the `MS4GC` folder and run:

```bash
git init
git add .
git commit -m "Initial commit: add MS4GC 1.04"
git branch -M main
git remote add origin https://github.com/YOUR-GITHUB-NAME/MS4GC.git
git push -u origin main
```

Replace `YOUR-GITHUB-NAME` with your actual GitHub username.

## Option C: Use GitHub CLI

If you have the GitHub CLI installed:

```bash
gh auth login
gh repo create MS4GC --public --source=. --remote=origin --push
```

Use `--private` instead of `--public` if the repository should not be public.

## Recommended first release

After uploading, create a GitHub release:

- Tag: `v1.04`
- Title: `MS4GC 1.04`
- Description: summarize language support, header-free point-pair output, and edge positioning.

## Before publishing

Run the tests once:

```bash
python -m unittest discover -s tests
```

Also verify the main examples:

```bash
python MS4GC.py 0011010
python MS4GC.py -clock 0.48 0.51 2
python MS4GC.py -language de -show
```
