# -*- coding: utf-8 -*-
"""
IL SEGNALE DI VEGA — interfaccia Streamlit.

Avvio:  streamlit run app.py

Interfaccia volutamente essenziale: testo, vita, una casella per il numero.
Niente animazioni, niente colori inutili: l'attenzione deve stare sulle tabelline.

Salvataggi e statistiche di lungo periodo vivono in un unico documento JSON
(vedi archivio.py): su Google Drive quando l'app e' pubblicata, su disco quando
gira in locale.
"""

import random

import streamlit as st

import archivio as A
import motore as M
import storia as S
import storico as ST

# Ogni quante risposte si scrive davvero sull'archivio. Scrivere a ogni risposta
# su Drive aggiungerebbe circa un secondo di attesa a ogni moltiplicazione: la
# partita vive in memoria e si sincronizza a blocchi, piu' i momenti importanti.
RISPOSTE_PER_SINCRONIA = 5

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
      .griglia {font-family: monospace; font-size: 1.05rem; line-height: 1.5;}
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
    st.session_state.setdefault("storico", None)
    st.session_state.setdefault("da_sincronizzare", 0)
    st.session_state.setdefault("domande_sessione", 0)
    st.session_state.setdefault("vista_storico", False)


def autosalva(forza: bool = False):
    """
    Sincronizza l'archivio se e' passato abbastanza tempo o se il momento e'
    importante (cambio di scena, oggetto trovato, uscita dal gioco).
    """
    if not st.session_state.stato:
        return
    st.session_state.da_sincronizzare += 1
    if not forza and st.session_state.da_sincronizzare < RISPOSTE_PER_SINCRONIA:
        return
    M.salva(
        st.session_state.stato,
        st.session_state.slot,
        st.session_state.storico,
        st.session_state.domande_sessione,
    )
    st.session_state.da_sincronizzare = 0


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
    slot = st.text_input(
        "Nome del salvataggio", value=M.pulisci_slot(nome),
        help="Le statistiche di lungo periodo sono legate a questo nome: "
             "usa sempre lo stesso per la stessa persona.",
    )
    if st.button("Comincia", type="primary"):
        storico_esistente = M.carica_storico(slot)
        ST.apri_sessione(storico_esistente)
        st.session_state.stato = M.nuovo_stato(nome, storico_esistente)
        st.session_state.storico = storico_esistente
        st.session_state.slot = slot
        st.session_state.domande_sessione = 0
        st.session_state.da_sincronizzare = 0
        autosalva(forza=True)
        st.rerun()

    salvataggi = M.elenco_salvataggi()
    if salvataggi:
        st.subheader("Continua una partita")
        for voce in salvataggi:
            colonne = st.columns([4, 2])
            etichetta = "COMPLETATA · " if voce["finita"] else ""
            colonne[0].write(
                f"**{voce['nome']}** ({voce['slot']}) — {etichetta}{voce['capitolo']} · "
                f"{voce['frammenti']}/6 frammenti · salvato {voce['salvato']}"
            )
            if colonne[1].button("Continua", key=f"carica_{voce['slot']}"):
                stato = M.carica(voce["slot"])
                if stato is None:
                    st.error("Salvataggio non trovato nell'archivio.")
                else:
                    storico_partita = M.carica_storico(voce["slot"])
                    ST.apri_sessione(storico_partita)
                    st.session_state.stato = stato
                    st.session_state.storico = storico_partita
                    st.session_state.slot = voce["slot"]
                    st.session_state.domande_sessione = 0
                    st.session_state.da_sincronizzare = 0
                    st.rerun()

    st.divider()
    colonne = st.columns(2)
    if colonne[0].button("Modalità allenamento (senza storia)"):
        st.session_state.allenamento = {
            "slot": st.session_state.slot,
            "ok": 0, "ko": 0, "statistiche": {}, "ultima_chiave": None,
            "aiuto_attivo": False, "domanda": None, "da_sincronizzare": 0,
        }
        st.rerun()
    if colonne[1].button("Storico e statistiche"):
        st.session_state.vista_storico = not st.session_state.vista_storico
        st.rerun()

    if st.session_state.vista_storico:
        pannello_storico_globale()

    stato_archivio()


# ---------------------------------------------------------------------------
# Allenamento libero — alimenta lo stesso storico del gioco
# ---------------------------------------------------------------------------

def allenamento():
    a = st.session_state.allenamento
    st.title("Allenamento")

    if st.session_state.storico is None or st.session_state.storico.get("giocatore") != M.pulisci_slot(a["slot"]):
        st.session_state.storico = M.carica_storico(a["slot"])
        ST.apri_sessione(st.session_state.storico)
        a["statistiche"] = ST.semina_statistiche(st.session_state.storico)
    storico_corrente = st.session_state.storico
    st.caption(f"Le risposte finiscono nello storico di **{a['slot']}**.")

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
        ST.registra(storico_corrente, chiave, giusto)
        a["da_sincronizzare"] += 1
        if a["da_sincronizzare"] >= RISPOSTE_PER_SINCRONIA:
            M.salva_storico(storico_corrente, a["slot"])
            a["da_sincronizzare"] = 0
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

    with st.expander("Storico permanente di questa giocatrice"):
        mostra_storico(storico_corrente)

    if st.button("Torna al menu"):
        if a["da_sincronizzare"]:
            M.salva_storico(storico_corrente, a["slot"])
        st.session_state.allenamento = None
        st.session_state.esito_all = None
        st.session_state.storico = None
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
        nodo_prima = stato["nodo"]
        st.session_state.esito = M.rispondi(stato, valore, st.session_state.storico)
        st.session_state.domande_sessione += 1
        # Cambio di scena o partita finita: momenti in cui vale la pena scrivere
        # subito, cosi' un riavvio non riporta indietro il capitolo.
        autosalva(forza=(stato["nodo"] != nodo_prima or bool(stato.get("finita"))))
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
            autosalva(forza=True)
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
# Storico permanente
# ---------------------------------------------------------------------------

def mostra_storico(storico: dict):
    """Le statistiche che restano fra le partite: cosa sa e cosa non sa ancora."""
    riepilogo = ST.riepilogo(storico)
    if not riepilogo["totale_domande"]:
        st.caption("Nessuna risposta registrata finora.")
        return

    colonne = st.columns(4)
    colonne[0].metric("Risposte totali", riepilogo["totale_domande"])
    colonne[1].metric("Precisione", f"{riepilogo['precisione_globale']:.0%}")
    colonne[2].metric("Sessioni", riepilogo["sessioni"])
    colonne[3].metric("Consolidate", f"{riepilogo['conteggi']['consolidata']}/55")

    st.caption(
        "🟢 consolidata (almeno 4 giuste di fila) · 🟡 in corso · "
        "🔴 da allenare (sotto il 60% nelle ultime 5) · ⬜ mai capitata"
    )

    righe_griglia = ["&nbsp;&nbsp;&nbsp;&nbsp;" + " ".join(f"{b:>2}" for b in range(1, 11))]
    for indice, riga_simboli in enumerate(ST.griglia(storico), start=1):
        righe_griglia.append(f"{indice:>2}&nbsp; " + " ".join(riga_simboli))
    st.markdown("<div class='griglia'>" + "<br>".join(righe_griglia) + "</div>",
                unsafe_allow_html=True)

    if riepilogo["fragili"]:
        st.write("**Da allenare** — dalla più incerta")
        st.table([
            {"moltiplicazione": r["moltiplicazione"], "tentativi": r["tentativi"],
             "sbagliate": r["sbagliate"], "precisione totale": f"{r['precisione']:.0%}",
             "ultime 5": f"{r['recente']:.0%}", "ultima volta": r["ultimo_visto"][:10]}
            for r in riepilogo["fragili"][:12]
        ])
    else:
        st.success("Nessuna moltiplicazione sotto soglia in questo momento.")

    if riepilogo["solide"]:
        st.write("**Consolidate** — " + ", ".join(
            f"{r['moltiplicazione']} ({r['serie']} di fila)" for r in riepilogo["solide"][:15]
        ))
    if riepilogo["mai_viste"]:
        st.caption(f"Mai capitate ({len(riepilogo['mai_viste'])}): "
                   + ", ".join(riepilogo["mai_viste"][:20]))

    if len(riepilogo["andamento_recente"]) > 1:
        st.write("**Andamento per giorno**")
        st.table([
            {"giorno": g["giorno"], "domande": g["domande"],
             "precisione": f"{g['precisione']:.0%}"}
            for g in reversed(riepilogo["andamento_recente"])
        ])


def pannello_storico_globale():
    """Vista dal menu: tutte le giocatrici, chi ha usato l'app e quando."""
    st.divider()
    st.subheader("Storico e statistiche")
    giocatori = M.elenco_giocatori()
    if not giocatori:
        st.caption("Ancora nessuna partita registrata.")
    else:
        scelto = st.selectbox("Giocatrice", giocatori)
        mostra_storico(M.carica_storico(scelto))

    accessi = A.leggi().get("accessi", [])
    if accessi:
        with st.expander("Chi ha usato l'app"):
            st.table([
                {"giocatrice": v.get("nome", v.get("slot")), "quando": v.get("quando", "?"),
                 "capitolo": v.get("capitolo", "?"), "frammenti": v.get("frammenti", 0),
                 "risposte in partita": v.get("domande_totali", 0)}
                for v in reversed(accessi[-40:])
            ])

    if st.button("Chiudi lo storico"):
        st.session_state.vista_storico = False
        st.rerun()


def stato_archivio():
    """Dove stanno finendo i dati: informazione onesta, non decorativa."""
    st.divider()
    if A.modalita() == "drive":
        st.caption("Archivio: Google Drive — i salvataggi restano fra una sessione e l'altra.")
    else:
        st.caption("Archivio: file locale `salvataggi/archivio_vega.json`. "
                   "Su Streamlit Cloud senza credenziali Drive i dati si perdono al riavvio.")
    if A.ultimo_errore():
        st.warning(f"Ultimo problema con l'archivio → {A.ultimo_errore()}")


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
        etichette = ["Questa partita", "Storico completo"]
        scelta = st.radio("Cosa guardare", etichette, horizontal=True,
                          label_visibility="collapsed")
        if scelta == etichette[0]:
            riepilogo = M.riepilogo_statistiche(stato)
            st.write(f"Domande in questa partita: **{riepilogo['totale_domande']}** · "
                     f"precisione: **{riepilogo['precisione_globale']:.0%}** · "
                     f"rianimazioni: **{stato['morti']}**")
            if riepilogo["da_allenare"]:
                st.table([
                    {"moltiplicazione": r["moltiplicazione"], "tentativi": r["tentativi"],
                     "giuste": r["giuste"], "sbagliate": r["sbagliate"],
                     "precisione": f"{r['precisione']:.0%}"}
                    for r in riepilogo["da_allenare"]
                ])
            else:
                st.caption("Servono un po' più di domande per dire qualcosa di sensato.")
        else:
            if st.session_state.storico:
                mostra_storico(st.session_state.storico)
            else:
                st.caption("Storico non caricato.")


def barra_laterale(stato):
    with st.sidebar:
        st.write(f"**{stato['nome']}**")
        st.caption(f"Salvataggio: {st.session_state.slot}")
        in_attesa = st.session_state.da_sincronizzare
        if in_attesa:
            st.caption(f"{in_attesa} mosse non ancora sincronizzate "
                       f"(si salva ogni {RISPOSTE_PER_SINCRONIA}).")
        else:
            st.caption("Tutto sincronizzato.")
        if st.button("Salva adesso"):
            if M.salva(stato, st.session_state.slot, st.session_state.storico,
                       st.session_state.domande_sessione):
                st.session_state.da_sincronizzare = 0
                st.success("Salvato nell'archivio.")
            else:
                st.error(f"Salvataggio non riuscito → {A.ultimo_errore()}")
        if st.button("Torna al menu"):
            autosalva(forza=True)
            st.session_state.stato = None
            st.session_state.storico = None
            st.session_state.esito = None
            st.rerun()
        st.divider()
        st.caption("Archivio: " + ("Google Drive" if A.modalita() == "drive" else "file locale"))
        if A.ultimo_errore():
            st.warning(A.ultimo_errore())


# ---------------------------------------------------------------------------
# Vista di gioco
# ---------------------------------------------------------------------------

def gioco():
    stato = st.session_state.stato
    if st.session_state.storico is None:
        st.session_state.storico = M.carica_storico(st.session_state.slot)
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
