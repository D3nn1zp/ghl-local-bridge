# GHL Local Bridge

GHL Local Bridge leest geselecteerde meetwaarden rechtstreeks uit de lokale GHL Connect-pagina van een GHL ProfiLux en publiceert deze via MQTT Discovery in Home Assistant.

## Functies

- Lokale verbinding zonder myGHL-account
- Blijvend Chromium-profiel voor de GHL-dashboardindeling
- Eenmalige installatie via **Open Web UI**
- Home Assistant Ingress
- Automatische MQTT Discovery
- Zelf kiezen welke sensoren worden uitgelezen
- Ondersteuning voor KH, temperatuur, dichtheid, calcium, magnesium, kalium, natrium en nitraat
- Ondersteuning voor `amd64` en `aarch64`
- Nederlandstalige, Engelstalige en Duitstalige configuratieteksten

## Installeren in Home Assistant

Voeg deze repository toe aan de Home Assistant App Store:

```text
https://github.com/D3nn1zp/ghl-local-bridge
```

Ga in Home Assistant naar:

```text
Instellingen → Apps → App store → ⋮ → Repositories
```

Plak de repository-URL, voeg hem toe en installeer daarna **GHL Local Bridge**.

## Eerste installatie

1. Vul bij **Configuratie** het lokale IP-adres van de ProfiLux en de GHL-PIN in.
2. Selecteer alleen de sensoren die je wilt uitlezen.
3. Laat **Enable setup browser** tijdens de eerste installatie aan staan.
4. Start de app.
5. Open **Open Web UI**.
6. Doorloop de GHL Connect-wizard: taal kiezen → `NEXT` → `NO` → `DONE`.
7. Vul de GHL-PIN in.
8. Voeg in het GHL-dashboard de benodigde kaarten toe:
   - **KH Director** voor KH
   - **Sensors / Sensoren** voor temperatuur en dichtheid
   - **ION Director** voor calcium, magnesium, kalium, natrium en nitraat
9. Controleer in het logboek of de gekozen waarden worden gevonden.
10. Zet **Enable setup browser** uit en herstart de app.

De volledige uitleg staat na installatie op het tabblad **Documentatie**.

## Privacy

De app gebruikt geen myGHL-account. De GHL-PIN en het browserprofiel blijven lokaal in Home Assistant opgeslagen.

## Disclaimer

Dit is een onafhankelijk communityproject en is niet officieel ontwikkeld, ondersteund of goedgekeurd door GHL.

Maker: **Dennis Pracht**
