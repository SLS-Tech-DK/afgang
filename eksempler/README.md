# Eksempler — kundeskabeloner + acceptance-test

Realistiske eksempel-input pr. produkt. Kunder kan bruge dem som skabelon for
deres egne uploads. Filerne genereres af `gen_samples.py`, som SAMTIDIG kører
hver eksempelfil gennem den rigtige motor som end-to-end acceptance-test.

## Filer
- ordre-eksempel.csv — ordredata (salg/indkøb/lager/kunde/butik)
- lager-eksempel.csv — lagerbeholdning + kostpris
- produktkatalog-eksempel.csv — produkttekst-optimering
- reviews-eksempel.csv — review-analyse
- annoncer-eksempel.csv — annonce-spild
- soegelog-eksempel.csv — søgeords-gap
- landingsside-eksempel.txt — landingsside-analyse
- *.json — strukturerede input (konkurrent, AI-synlighed, prisovervågning, nævner-AI-alarm)
- event-onepager.html — printbar pitch-side til netværks-events
- gen_samples.py — genererer eksemplerne + acceptance-test af alle 14 motorer

## Kør acceptance-test
Kræver motor-modulerne i PYTHONPATH (fra produktmapperne). Alle 14 motorer skal
give gyldigt output på eksempeldata.
