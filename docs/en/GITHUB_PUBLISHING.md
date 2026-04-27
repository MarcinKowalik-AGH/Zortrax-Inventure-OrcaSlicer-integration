# Publishing on GitHub

This guide shows two ways to upload this project to GitHub.

## Method 1 — GitHub website

1. Create a new empty repository, for example `zortrax-inventure-orca`.
2. Do not create an automatic README if you want to use the `README.md` from this package.
3. Unpack the ZIP package locally.
4. In the empty repository, choose **Add file → Upload files** or the **uploading an existing file** link.
5. Drag the full contents of the unpacked project directory into the browser window.
6. Commit the files directly to the `main` branch.
7. Optional: create a release named `v1.01` and attach the ZIP package.

This method is easy, but Git is better for future updates.

## Method 2 — Git command line

Create an empty repository on GitHub, then open a terminal in the unpacked project directory and run:

```bash
git init
git add .
git commit -m "Initial Zortrax Inventure OrcaSlicer integration v1.01"
git branch -M main
git remote add origin https://github.com/<your-login>/zortrax-inventure-orca.git
git push -u origin main
```

Replace `<your-login>` with your GitHub username.

Create a version tag:

```bash
git tag v1.01
git push origin v1.01
```

Suggested release text:

```text
v1.01
- pure-Python G-code -> classic .zcode converter
- OrcaSlicer profiles for Zortrax Inventure single and dual mode
- Windows and macOS post-processing launchers
- START_MACHINE, START_PURGE, SPECIAL_CLEAN, TOOLCHANGE_META, END_MACHINE markers
- START_PURGE uses LENGTH only, with no retract
```

## Suggested repository metadata

Repository name:

```text
zortrax-inventure-orca
```

Short description:

```text
OrcaSlicer profiles and pure-Python .zcode converter for Zortrax Inventure.
```

Topics:

```text
zortrax, inventure, orcaslicer, 3d-printing, zcode, python, post-processing
```

## Updating later

```bash
git status
git add .
git commit -m "Describe the change"
git push
```

For a new version:

```bash
git tag v1.02
git push origin v1.02
```
