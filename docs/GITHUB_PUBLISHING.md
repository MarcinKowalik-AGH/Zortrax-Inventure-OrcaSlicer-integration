# Publikacja na GitHubie

## 1. Utworzenie repozytorium

Na GitHub utwórz nowe puste repozytorium, np.:

```text
zortrax-inventure-orca
```

Nie dodawaj automatycznie README, jeżeli chcesz użyć gotowego `README.md` z tej paczki.

## 2. Pierwszy commit

W katalogu repozytorium lokalnego:

```bash
git init
git add .
git commit -m "Initial Zortrax Inventure OrcaSlicer integration v1.01"
git branch -M main
git remote add origin <URL_TWOJEGO_REPOZYTORIUM>
git push -u origin main
```

## 3. Release v1.01

Po pushu utwórz tag:

```bash
git tag v1.01
git push origin v1.01
```

W GitHub Releases możesz dodać opis:

```text
v1.01
- pure-Python G-code -> classic .zcode converter for Zortrax Inventure
- single and dual Orca printer bundles
- Windows and macOS launchers
- START_PURGE uses LENGTH-only purge without retract
- start/end/clean markers for Z-Suite-like machine behavior
```

## 4. Licencja

Przed publicznym udostępnieniem dodaj rzeczywisty plik `LICENSE`, np. MIT, GPL albo inne zasady. W tej paczce dodano tylko `LICENSE_NOTICE.md`, bo źródło nie wskazywało jednoznacznej licencji.
