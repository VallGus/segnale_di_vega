# -*- coding: utf-8 -*-
"""
IL SEGNALE DI VEGA — interfaccia Streamlit.

Avvio:  streamlit run app.py

Interfaccia volutamente essenziale: testo, vita, una casella per il numero.
Niente animazioni, niente colori inutili: l'attenzione deve stare sulle tabelline.
"""

import random

import streamlit as st

import motore as M
import storia as S

st.set_page_config(page_title="Il Segnale di Vega", page_icon="*", layout="centered")

st.markdown(
    """
    <style>
      .block-container {max-width: 780px; padding-top: 1.5rem;}
      .stMarkdown p, .stMarkdown li {font-size: 1.12rem; line-height: 1.65;}
      .stMarkdown blockquote {font-size: 1.12rem;}
      div[data-testid="stMetricValue"] {font-size: 1.4rem;}
      .barra {font-family: monospace; font-size: 1.25rem; letter-spacing: 1px;}
      .domanda {font-size: 2.6rem; font-weight: 700; text-align: center;
                padding: 0.4rem 0 0.2rem 0;}
      .esito-ok {font-size: 1.15rem; padding: 0.5rem 0;}
      .esito-ko {font-size: 1.15rem; padding: 0.5rem 0;}
      .stButton button {font-size: 1.05rem; padding: 0.5rem 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

INCORAGGIAMENTI = [
    "Adesso lo sai. Avanti.",
    "Succede. Si riprova.",
    "Un errore è un'informazione, non un difetto.",
    "Bit dice: «Nessun problema, ho visto di peggio.»",
    "Quasi. Guarda il trucco qui sotto.",
]
COMPLIMENTI = ["Perfetto!", "Esatto!", "Preciso.", "Colpo secco!", "Così si fa."]


# ---------------------------------------------------------------------------
# Stato della sessione
# ---------------------------------------------------------------------------

def init():
    st.session_state.setdefault("stato", None)
    st.session_state.setdefault("slot", "marta")
    st.session_state.setdefault("esito", None)
    st.session_state.setdefault("allenamento", None)


def autosalva():
    if st.session_state.stato:
        M.salva(st.session_state.stato, st.session_state.slot)


# ---------------------------------------------------------------------------
# Menu iniziale
# ---------------------------------------------------------------------------

def menu():
    st.title("IL SEGNALE DI VEGA")
    st.caption("Sette pianeti e una domanda — un'avventura a moltiplicazioni")

    st.markdown(
        "Un'avventura spaziale in cui si combatte, si schiva, si aprono porte e si usano "
        "oggetti magici **rispondendo a moltiplicazioni da 1x1 a 10x10**.\n\n"
        "Se la vita finisce, non si perde la partita: si torna in piedi con tre risposte "
        "giuste di fila."
    )

    st.subheader("Nuova avventura")
    nome = st.text_input("Come ti chiami?", value="Marta")
    slot = st.text_input("Nome del salvataggio", value=nome.lower() or "partita")
    if st.button("Comincia", type="primary"):
        st.session_state.stato = M.nuovo_stato(nome)
        st.session_state.slot = slot
        autosalva()
        st.rerun()

    salvataggi = M.elenco_salvataggi()
    if salvataggi:
        st.subheader("Continua una partita")
        for voce in salvataggi:
            colonne = st.columns([4, 2])
            colonne[0].write(
                f"**{voce['slot']}** — {voce['capitolo']} · "
                f"{voce['frammenti']}/6 frammenti · salvato {voce['salvato']}"
            )
            if colonne[1].button("Continua", key=f"carica_{voce['slot']}"):
                st.session_state.stato = M.carica(voce["slot"])
                st.session_state.slot = voce["slot"]
                st.rerun()

    st.divider()
    if st.button("Modalità allenamento (senza storia)"):
        st.session_state.allenamento = {"ok": 0, "ko": 0, "statistiche": {}, "ultima_chiave": None,
                                        "aiuto_attivo": False, "domanda": None}
        st.rerun()


# ---------------------------------------------------------------------------
# Allenamento libero
# ---------------------------------------------------------------------------

def allenamento():
    st.title("Allenamento")
    a = st.session_state.allenamento
    if a["domanda"] is None:
        a["domanda"] = M.crea_domanda(a, "prova")
    d = a["domanda"]

    st.markdown(f"<div class='domanda'>{d['a']} x {d['b']} = ?</div>", unsafe_allow_html=True)
    indice = a["ok"] + a["ko"]
    with st.form(f"all_{indice}", clear_on_submit=True):
        risposta = st.text_input("Risultato", key=f"ris_all_{indice}")
        inviato = st.form_submit_button("Rispondi", type="primary")
    if inviato:
        try:
            valore = int(risposta.strip())
        except (ValueError, AttributeError):
            st.warning("Scrivi un numero.")
            return
        giusto = valore == d["a"] * d["b"]
        chiave = M.chiave(d["a"], d["b"])
        dati = a["statistiche"].setdefault(chiave, {"ok": 0, "ko": 0})
        dati["ok" if giusto else "ko"] += 1
        a["ok" if giusto else "ko"] += 1
        a["ultima_chiave"] = chiave
        st.session_state.esito_all = (giusto, d["a"], d["b"])
        a["domanda"] = None
        st.rerun()

    if st.session_state.get("esito_all"):
        giusto, a1, b1 = st.session_state.esito_all
        if giusto:
            st.success(f"{random.choice(COMPLIMENTI)}  {a1}x{b1} = {a1 * b1}")
        else:
            st.error(f"{a1}x{b1} fa {a1 * b1}. {M.suggerimento(a1, b1)}")

    st.session_state.esito_all = None
    st.caption(f"Giuste: {a['ok']} · Sbagliate: {a['ko']}")
    if st.button("Torna al menu"):
        st.session_state.allenamento = None
        st.session_state.esito_all = None
        st.rerun()


# ---------------------------------------------------------------------------
# Barra della vita
# ---------------------------------------------------------------------------

def barra_vita(stato):
    pieni = stato["hp"]
    vuoti = stato["hp_max"] - pieni
    barra = "#" * pieni + "." * vuoti
    st.markdown(
        f"<div class='barra'>VITA [{barra}] {stato['hp']}/{stato['hp_max']}</div>",
        unsafe_allow_html=True,
    )


def intestazione(stato):
    nodo = S.STORIA[stato["nodo"]]
    colonne = st.columns([3, 2])
    colonne[0].caption(f"Capitolo: {nodo.get('capitolo', '-')}")
    colonne[1].caption(f"Frammenti: {len(stato['frammenti'])}/6"
                       + (f" · Scudo: {stato['scudo']}" if stato["scudo"] else ""))
    barra_vita(stato)
    if stato["combattimento"]:
        nemico = stato["combattimento"]
        pieni = nemico["hp"]
        vuoti = nemico["hp_max"] - pieni
        st.markdown(
            f"<div class='barra'>{nemico['nome'].upper()} [{'#' * pieni + '.' * vuoti}] "
            f"{nemico['hp']}/{nemico['hp_max']}</div>",
            unsafe_allow_html=True,
        )
    st.divider()


# ---------------------------------------------------------------------------
# Feedback dell'ultima risposta
# ---------------------------------------------------------------------------

def mostra_esito():
    esito = st.session_state.esito
    if not esito or "giusto" not in esito:
        st.session_state.esito = None
        return
    if esito["giusto"]:
        testo = f"**{random.choice(COMPLIMENTI)}** {esito['domanda']} = {esito['risposta_esatta']}"
        if esito.get("critico"):
            testo += "  —  **COLPO CRITICO!**"
        st.success(testo)
    else:
        st.error(
            f"**{esito['domanda']} fa {esito['risposta_esatta']}.** "
            f"{random.choice(INCORAGGIAMENTI)}\n\n{esito['suggerimento']}"
        )
    st.session_state.esito = None


# ---------------------------------------------------------------------------
# Domanda
# ---------------------------------------------------------------------------

ETICHETTE = {
    "attacco": "Attacchi! Rispondi per colpire",
    "difesa": "Attenta! Rispondi per schivare",
    "prova": "Rispondi per riuscire",
    "oggetto": "Rispondi per attivare l'oggetto",
    "rianimazione": "Rianimazione: tre risposte giuste di fila",
}


def mostra_domanda(stato):
    domanda = stato["domanda"]
    st.write(f"**{ETICHETTE.get(domanda['contesto'], 'Rispondi')}**")
    if domanda["contesto"] == "rianimazione":
        st.info(f"Serie: {stato['morte']['serie']}/{M.RISPOSTE_PER_RIANIMARSI}")
    st.markdown(
        f"<div class='domanda'>{domanda['a']} x {domanda['b']} = ?</div>",
        unsafe_allow_html=True,
    )
    if domanda.get("aiuto"):
        st.info("Lente del Tempo: " + M.suggerimento(domanda["a"], domanda["b"]))

    indice = stato["totale_ok"] + stato["totale_ko"]
    with st.form(f"domanda_{indice}", clear_on_submit=True):
        risposta = st.text_input("Il tuo risultato", key=f"risp_{indice}",
                                 placeholder="scrivi il numero e premi Invio")
        inviato = st.form_submit_button("Rispondi", type="primary")
    if inviato:
        try:
            valore = int(risposta.strip())
        except (ValueError, AttributeError):
            st.warning("Serve un numero: scrivi solo cifre.")
            return
        st.session_state.esito = M.rispondi(stato, valore)
        autosalva()
        st.rerun()


# ---------------------------------------------------------------------------
# Scelte
# ---------------------------------------------------------------------------

def mostra_scelte(stato):
    nodo = S.STORIA[stato["nodo"]]
    for indice, scelta in enumerate(nodo.get("scelte", [])):
        richiesto = scelta.get("richiede")
        if richiesto and stato["oggetti"].get(richiesto, 0) <= 0:
            st.button(f"{scelta['testo']}  (serve: {richiesto})", key=f"sc_{indice}", disabled=True)
            continue
        if st.button(scelta["testo"], key=f"sc_{indice}", type="primary" if indice == 0 else "secondary"):
            M.scegli(stato, scelta["vai_a"])
            autosalva()
            st.rerun()


# ---------------------------------------------------------------------------
# Zaino
# ---------------------------------------------------------------------------

def mostra_zaino(stato):
    usabili = {n: q for n, q in stato["oggetti"].items()
               if q > 0 and S.OGGETTI[n]["effetto"] != "chiave"}
    passivi = [n for n, q in stato["oggetti"].items()
               if q > 0 and S.OGGETTI[n]["effetto"] == "chiave"]
    if not usabili and not passivi:
        return
    st.divider()
    st.write("**Zaino**")
    if not M.puo_usare_oggetti(stato):
        st.caption("Gli oggetti si usano nel tuo turno, non mentre schivi.")
    for nome, quanti in usabili.items():
        colonne = st.columns([5, 2])
        colonne[0].write(f"{nome} x{quanti} — {S.OGGETTI[nome]['desc']}")
        if colonne[1].button("Usa", key=f"usa_{nome}", disabled=not M.puo_usare_oggetti(stato)):
            M.prepara_uso_oggetto(stato, nome)
            autosalva()
            st.rerun()
    for nome in passivi:
        st.caption(f"{nome} — {S.OGGETTI[nome]['desc']}")


# ---------------------------------------------------------------------------
# Pannelli in fondo
# ---------------------------------------------------------------------------

def pannelli(stato):
    st.divider()
    with st.expander("Diario di bordo"):
        for riga in reversed(stato["diario"][-15:]):
            st.text(riga)

    with st.expander("Frammenti raccolti"):
        if not stato["frammenti"]:
            st.write("Ancora nessuno.")
        for frammento in stato["frammenti"]:
            st.write(f"- *{frammento}*")

    with st.expander("Per i grandi: come stanno andando le tabelline"):
        riepilogo = M.riepilogo_statistiche(stato)
        st.write(f"Domande totali: **{riepilogo['totale_domande']}** · "
                 f"precisione: **{riepilogo['precisione_globale']:.0%}** · "
                 f"rianimazioni: **{stato['morti']}**")
        if riepilogo["da_allenare"]:
            st.write("Da allenare (le più incerte):")
            st.table([
                {"moltiplicazione": r["moltiplicazione"], "tentativi": r["tentativi"],
                 "giuste": r["giuste"], "sbagliate": r["sbagliate"],
                 "precisione": f"{r['precisione']:.0%}"}
                for r in riepilogo["da_allenare"]
            ])
        else:
            st.caption("Servono un po' più di domande per dire qualcosa di sensato.")


def barra_laterale(stato):
    with st.sidebar:
        st.write(f"**{stato['nome']}**")
        st.caption(f"Salvataggio: {st.session_state.slot}")
        st.caption("Il gioco si salva da solo a ogni mossa.")
        if st.button("Salva adesso"):
            percorso = M.salva(stato, st.session_state.slot)
            st.success(f"Salvato in {percorso.name}")
        if st.button("Torna al menu"):
            autosalva()
            st.session_state.stato = None
            st.session_state.esito = None
            st.rerun()


# ---------------------------------------------------------------------------
# Vista di gioco
# ---------------------------------------------------------------------------

def gioco():
    stato = st.session_state.stato
    nodo = S.STORIA[stato["nodo"]]
    barra_laterale(stato)
    intestazione(stato)

    st.subheader(nodo.get("titolo", ""))
    st.markdown(nodo.get("testo", ""))

    mostra_esito()

    if nodo["tipo"] == "finale":
        st.balloons()
        st.success("Avventura completata.")
        pannelli(stato)
        return

    if stato["morte"]:
        st.warning("La tuta è in riserva. Bit ha attivato il rianimatore: "
                   "tre risposte giuste di fila e si riparte.")
        mostra_domanda(stato)
    elif stato["domanda"]:
        mostra_domanda(stato)
    else:
        mostra_scelte(stato)

    mostra_zaino(stato)
    pannelli(stato)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

init()
if st.session_state.allenamento is not None:
    allenamento()
elif st.session_state.stato is None:
    menu()
else:
    gioco()
