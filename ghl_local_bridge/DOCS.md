# GHL Local Bridge – handleiding

GHL Local Bridge leest geselecteerde meetwaarden rechtstreeks uit de lokale GHL Connect-pagina van je ProfiLux en publiceert deze via MQTT Discovery in Home Assistant.

De verbinding blijft lokaal. Voor het uitlezen is geen myGHL-account nodig.

## Ondersteunde meetwaarden

Je kiest zelf welke sensoren je wilt gebruiken:

- KH
- Temperatuur
- Dichtheid zee
- Calcium
- Magnesium
- Kalium
- Natrium
- Nitraat

Alleen ingeschakelde sensoren worden gezocht en als MQTT-entiteit in Home Assistant aangemaakt.

## Benodigdheden

Voor een goede werking heb je nodig:

- Home Assistant OS met ondersteuning voor apps/add-ons
- De Mosquitto broker-app in Home Assistant
- Een GHL ProfiLux die lokaal bereikbaar is
- Het lokale IP-adres van de ProfiLux
- De PIN-code van de ProfiLux
- Minimaal één geselecteerde sensor

## Welke kaart hoort bij welke sensor?

| Sensor | Benodigde kaart in GHL Connect |
|---|---|
| KH | KH Director |
| Temperatuur | Sensors / Sensoren |
| Dichtheid zee | Sensors / Sensoren |
| Calcium | ION Director |
| Magnesium | ION Director |
| Kalium | ION Director |
| Natrium | ION Director |
| Nitraat | ION Director |

Je hoeft alleen de kaarten toe te voegen die horen bij de sensoren die je in de configuratie hebt aangezet.

# Eerste installatie

## Stap 1 – Configuratie invullen

Open **GHL Local Bridge** en ga naar **Configuratie**.

Vul hier het volgende in:

### Lokaal GHL-adres

Vul het lokale IP-adres van je ProfiLux in, bijvoorbeeld:

```text
http://192.168.1.100
```

Gebruik het lokale adres van de ProfiLux, niet het adres van Home Assistant en niet de myGHL-website.

### GHL-PIN

Vul de PIN-code in waarmee je lokaal verbinding maakt met de ProfiLux.

### Uitleesinterval

Kies hoe vaak de waarden moeten worden bijgewerkt. Bijvoorbeeld:

```text
15 minuten
```

### Sensoren selecteren

Zet alleen de sensoren aan die je daadwerkelijk hebt en in Home Assistant wilt gebruiken.

Voorbeelden:

- Heb je alleen een KH Director? Zet dan alleen **KH** aan.
- Heb je een KH Director en temperatuurprobe? Zet dan **KH** en **Temperatuur** aan.
- Heb je een ION Director maar geen dichtheidssensor? Zet dan de gewenste ION-waarden aan en laat **Dichtheid zee** uit.

### Instelbrowser inschakelen

Laat **Enable setup browser / Instelbrowser inschakelen** tijdens de eerste installatie aan staan.

Sla daarna de configuratie op.

## Stap 2 – App starten

Ga terug naar het tabblad **Info** en klik op **Starten**.

Wacht tot de app volledig is gestart.

## Stap 3 – Open Web UI openen

Klik op:

```text
Open Web UI
```

Hiermee open je de blijvende Chromium-browser van GHL Local Bridge.

Deze browser heeft een eigen, blijvend profiel. De dashboardindeling die je hier instelt, blijft daardoor bewaard na een herstart.

## Stap 4 – GHL Connect voor de eerste keer instellen

Bij een nieuw browserprofiel verschijnt eerst de GHL-installatiewizard.

Doorloop de wizard als volgt:

1. Kies de gewenste taal.
2. Klik op **NEXT**.
3. Bij de vraag of je wilt verbinden met myGHL kies je **NO**.
4. Klik op **DONE**.
5. Vul de GHL-PIN in wanneer het PIN-venster verschijnt.
6. Klik op **OK**.

Daarna opent het GHL-dashboard.

## Stap 5 – De juiste dashboardkaarten toevoegen

Klik rechtsboven in GHL Connect op het potlood om het dashboard te bewerken.

Voeg alleen de kaarten toe die nodig zijn voor de sensoren die je hebt geselecteerd:

- **KH Director** voor KH
- **Sensors / Sensoren** voor temperatuur en dichtheid
- **ION Director** voor calcium, magnesium, kalium, natrium en nitraat

Verwijder eventueel overbodige standaardkaarten zoals Tijd, Onderhoud of Voederpauze. Dit is niet verplicht, maar maakt het dashboard overzichtelijker.

Sla de dashboardindeling daarna op.

## Stap 6 – Controleren of de waarden worden gevonden

Ga terug naar GHL Local Bridge en open het tabblad **Logboek**.

Een succesvolle uitlezing ziet er ongeveer zo uit:

```text
Gevonden waarden: kh=8.0, temperature=26.7, density=1.0226, calcium=400, magnesium=1173, potassium=360, sodium=9596, nitrate=6
Waarden via MQTT naar Home Assistant verzonden.
```

Alleen de sensoren die je hebt geselecteerd, hoeven in deze regel aanwezig te zijn.

## Stap 7 – Instelbrowser uitschakelen

Wanneer alle gekozen waarden correct worden gevonden:

1. Ga naar **Configuratie**.
2. Zet **Enable setup browser / Instelbrowser inschakelen** uit.
3. Sla de configuratie op.
4. Ga terug naar **Info**.
5. Klik op **Herstarten**.

Na de herstart blijft het opgeslagen Chromium-profiel behouden, maar de instelbrowser hoeft niet meer zichtbaar te blijven draaien.

GHL Local Bridge haalt de gekozen waarden daarna automatisch op volgens het ingestelde uitleesinterval.

# Sensoren later wijzigen

Wil je later een sensor toevoegen of verwijderen?

1. Ga naar **Configuratie**.
2. Pas de sensorselectie aan.
3. Zet de instelbrowser tijdelijk weer aan wanneer je een extra GHL-kaart moet toevoegen.
4. Sla de configuratie op en herstart de app.
5. Open zo nodig **Open Web UI**.
6. Voeg de benodigde kaart toe aan het GHL-dashboard.
7. Controleer het logboek.
8. Zet de instelbrowser daarna weer uit en herstart de app.

Wanneer je een sensor uitschakelt, verwijdert GHL Local Bridge de bijbehorende MQTT Discovery-entiteit automatisch uit Home Assistant.

# Waar verschijnen de sensoren?

Na een succesvolle uitlezing verschijnen de sensoren onder de MQTT-integratie in Home Assistant.

Ga naar:

```text
Instellingen → Apparaten & diensten → MQTT
```

Daar verschijnt een apparaat met de naam die je bij **Home Assistant device name** hebt ingesteld, bijvoorbeeld:

```text
GHL Aquarium
```

# Aanbevolen instellingen

Zet op het tabblad **Info** deze opties aan:

- **Starten bij opstarten**
- **Watchdog**

Hierdoor start de bridge automatisch mee en wordt hij opnieuw gestart wanneer hij onverwacht stopt.

# Problemen oplossen

## De app blijft melden dat sensoren ontbreken

Controleer het volgende:

- Staat de sensor aan in de configuratie?
- Is de bijbehorende kaart toegevoegd in de Web UI?
- Staat de waarde zichtbaar op het GHL-dashboard?
- Is de PIN correct ingevuld?
- Is het lokale IP-adres van de ProfiLux correct?

Let op: de dashboardindeling van je gewone browser wordt niet automatisch overgenomen. Je moet de kaarten toevoegen in de browser die je via **Open Web UI** opent.

## Open Web UI opent niet

Controleer of **Enable setup browser / Instelbrowser inschakelen** aan staat en herstart daarna de app.

## De verkeerde waarden blijven in Home Assistant staan

Sla de configuratie opnieuw op en herstart de app. Uitgeschakelde sensoren worden daarna uit MQTT Discovery verwijderd.

## De waarden worden niet direct bijgewerkt

De bridge gebruikt het ingestelde uitleesinterval. Bij een interval van 15 minuten kan het dus maximaal 15 minuten duren voordat een nieuwe waarde verschijnt.

Je kunt de app handmatig herstarten om direct een nieuwe uitlezing te laten uitvoeren.

## De ProfiLux heeft een ander IP-adres gekregen

Pas het adres aan onder **Configuratie → Lokaal GHL-adres** en herstart de app.

# Privacy en beveiliging

- De meetwaarden worden lokaal uitgelezen.
- Er is geen myGHL-account nodig.
- De GHL-PIN wordt alleen lokaal binnen de app gebruikt.
- MQTT gebruikt de interne MQTT-service van Home Assistant.
- De Web UI loopt via Home Assistant Ingress en gebruikt de bestaande Home Assistant-aanmelding.

# Belangrijk

GHL Local Bridge is een onafhankelijk communityproject en is niet officieel ontwikkeld, ondersteund of goedgekeurd door GHL.
