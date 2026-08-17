# -*- coding: utf-8 -*-
"""
Prove sul nome della giocatrice.

Si lancia con:  python prova_nome.py

Il nome sta in `storia.py` come segnaposto {nome}. Questo test verifica che:
  1. nessun nome proprio sia rimasto cablato nella storia;
  2. la sostituzione funzioni su testo, titolo e scelte;
  3. un nome vuoto non produca frasi rotte;
  4. il segnaposto non arrivi mai a schermo cosi' com'e' — che e' il modo tipico
     in cui questa classe di bug si manifesta: si sostituisce in un punto e si
     dimentica l'altro.
"""

from __future__ import annotations

import os
import re

os.environ["VEGA_ARCHIVIO"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "salvataggi", "_prova_nome.json"
)

from streamlit.testing.v1 import AppTest   # noqa: E402

import archivio as A                       # noqa: E402
import motore as M                         # noqa: E402
import storia as S                         # noqa: E402

NOMI_VIETATI = ("Marta", "Irene", "Erik")
esiti: list[bool] = []


def controlla(descrizione: str, condizione: bool) -> None:
    esiti.append(bool(condizione))
    print(f"  [{'ok' if condizione else 'FALLITO'}] {descrizione}")


def testo_schermo(app) -> str:
    pezzi = ([e.value for e in app.markdown] + [e.value for e in app.caption]
             + [e.value for e in app.title] + [e.value for e in app.subheader]
             + [e.value for e in app.info] + [e.value for e in app.success]
             + [e.value for e in app.warning] + [e.value for e in app.error]
             + [b.label for b in app.button])
    return " ".join(str(p) for p in pezzi)


def main() -> None:
    print("1. Niente nomi cablati nella storia")
    testo_storia = str(S.STORIA)
    for nome in NOMI_VIETATI:
        controlla(f"«{nome}» non appare in storia.py",
                  not re.search(rf"\b{nome}\b", testo_storia))
    controlla("il segnaposto {nome} c'e'", "{nome}" in testo_storia)

    print("\n2. Sostituzione nel motore")
    stato = M.nuovo_stato("Sofia")
    testo = M.personalizza(S.STORIA[S.NODO_INIZIALE]["testo"], stato)
    controlla("il nome compare nel prologo", "Sofia" in testo)
    controlla("nessun segnaposto residuo", "{nome}" not in testo)
    titolo = M.personalizza(S.STORIA["c7_intermezzo2"]["titolo"], stato)
    controlla("il nome compare anche nei titoli", titolo == "La risposta di Sofia")

    print("\n3. Nomi limite")
    controlla("nome vuoto -> «tu»",
              "tu" in M.personalizza("Ti chiami {nome}.", {"nome": ""}))
    controlla("nome assente -> «tu»",
              "tu" in M.personalizza("Ti chiami {nome}.", {}))
    controlla("spazi ai bordi ripuliti",
              M.personalizza("{nome}!", {"nome": "  Leo  "}) == "Leo!")
    controlla("nome con accento",
              M.personalizza("{nome}", {"nome": "Niccolò"}) == "Niccolò")
    controlla("testo senza segnaposto invariato",
              M.personalizza("Nessun nome qui.", stato) == "Nessun nome qui.")

    print("\n4. A schermo, dentro l'app")
    A.percorso_locale().unlink(missing_ok=True)
    app = AppTest.from_file("app.py", default_timeout=90).run()
    app.text_input[0].set_value("Sofia")
    app.text_input[1].set_value("4826")
    app = [b for b in app.button if b.label == "Entra"][0].click().run()
    app = [b for b in app.button if b.label == "Comincia l'avventura"][0].click().run()
    controlla("nessuna eccezione", not app.exception)

    visto = testo_schermo(app)
    controlla("il prologo saluta Sofia", "Sofia" in visto)
    controlla("nessun {nome} visibile a schermo", "{nome}" not in visto)
    controlla("nessun nome di un'altra bambina",
              not any(re.search(rf"\b{n}\b", visto) for n in NOMI_VIETATI))

    print("\n5. Anche procedendo nella storia")
    for _ in range(10):
        visto = testo_schermo(app)
        if "{nome}" in visto:
            break
        if app.text_input:
            app.text_input[0].set_value("56")
            app = [b for b in app.button if b.label == "Rispondi"][0].click().run()
        else:
            scelte = [b for b in app.button
                      if b.label not in ("Salva adesso", "Metti in pausa")]
            if not scelte:
                break
            app = scelte[0].click().run()
    controlla("nessun segnaposto dopo dieci mosse", "{nome}" not in testo_schermo(app))
    controlla("nessuna eccezione lungo il percorso", not app.exception)

    falliti = esiti.count(False)
    print(f"\n{len(esiti) - falliti}/{len(esiti)} prove superate.")
    if falliti:
        raise SystemExit(1)
    print("Tutto verde.")


if __name__ == "__main__":
    main()
