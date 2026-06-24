# GHL Local Bridge 1.0.0

GHL Local Bridge leest geselecteerde waarden uit de lokale GHL Connect-pagina en publiceert deze via MQTT Discovery in Home Assistant.

## Functies

- Lokale verbinding zonder myGHL-account
- Blijvend Chromium-profiel voor de GHL-dashboardindeling
- Eenmalige instelling via **Open Web UI** en Home Assistant Ingress
- Automatische MQTT Discovery
- Zelf kiezen welke sensoren worden uitgelezen
- Automatisch verwijderen van uitgeschakelde MQTT-entiteiten
- Ondersteuning voor Nederlands, Engels en Duits

## Benodigde dashboardkaarten

- **KH Director** voor KH
- **Sensors / Sensoren** voor temperatuur en dichtheid
- **ION Director** voor calcium, magnesium, kalium, natrium en nitraat

De dashboardindeling wordt eenmalig ingesteld via **Open Web UI** en blijft opgeslagen in het blijvende Chromium-profiel onder `/data`.

Dit is een onafhankelijk communityproject en is niet officieel ontwikkeld, ondersteund of goedgekeurd door GHL.
