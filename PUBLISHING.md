# Publiceren op GitHub

Deze map is klaar voor de openbare GitHub-repository:

```text
https://github.com/D3nn1zp/ghl-local-bridge
```

Je GitHub-gebruikersnaam is **D3nn1zp**. Je e-mailadres is niet nodig voor de repository-URL of containernaam en staat niet in dit pakket.

## 1. Maak de repository

Maak op GitHub een nieuwe openbare repository met exact deze naam:

```text
ghl-local-bridge
```

Upload daarna de volledige inhoud van deze ZIP naar de hoofdmap van de repository.

In de hoofdmap moeten onder andere deze onderdelen staan:

```text
.github/
ghl_local_bridge/
LICENSE
README.md
repository.yaml
```

## 2. Publiceer release 1.0.0

Ga naar **Releases → Create a new release** en gebruik:

```text
Tag: 1.0.0
Release title: GHL Local Bridge 1.0.0
```

Publiceer de release. De GitHub Action bouwt vervolgens automatisch images voor `amd64` en `aarch64` en maakt een multi-architecture image.

## 3. Controleer GitHub Actions

Ga naar **Actions** en wacht tot deze onderdelen groen zijn:

- Initialize build
- Build amd64 image
- Build aarch64 image
- Publish multi-arch manifest

Bij een foutmelding over rechten:

```text
Settings → Actions → General → Workflow permissions
```

Selecteer **Read and write permissions** en voer de release opnieuw uit.

## 4. Maak het package openbaar

Ga na de geslaagde build naar **Packages**, open `ghl-local-bridge`, ga naar **Package settings** en zet de zichtbaarheid op **Public**.

## 5. Test installatie in Home Assistant

Voeg in Home Assistant deze repository toe:

```text
https://github.com/D3nn1zp/ghl-local-bridge
```

Installeer daarna GHL Local Bridge vanuit de App Store.

## Latere updates

Verhoog bij iedere update het versienummer in:

```text
ghl_local_bridge/config.yaml
```

Maak daarna een GitHub-release met exact hetzelfde versienummer als tag.
