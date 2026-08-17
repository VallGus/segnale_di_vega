# -*- coding: utf-8 -*-
"""
IL SEGNALE DI VEGA — Sette pianeti e una domanda.

Contenuti dell'avventura. Tutto qui dentro è dato, non codice: si può
aggiungere un pianeta, un nemico o una trappola senza toccare il motore.

TIPI DI NODO
------------
"narrazione"    : testo + una o più scelte.
                  Campi: capitolo, titolo, testo, scelte[{testo, vai_a, richiede?}]
"prova"         : una moltiplicazione. Giusta -> vai_a. Sbagliata -> danno e vai_a_ko.
                  Campi: capitolo, titolo, testo, testo_ok, testo_ko, danno,
                         vai_a, vai_a_ko?, fascia?, oggetti_ok?, cura_ok?
"combattimento" : scontro a turni. Campi: capitolo, titolo, testo, nemico{...},
                  vai_a, fascia?, oggetti_vittoria?
"finale"        : testo di chiusura.

Campi applicabili a qualsiasi nodo all'ingresso:
  cura, dai_oggetti{nome: quantità}, frammento, vita_max_extra, danno_base

FASCE DI DIFFICOLTÀ DELLE MOLTIPLICAZIONI
  "facile" = c'è almeno un 1, 2, 5 o 10
  "media"  = evita le coppie più cattive (6-9 x 6-9)
  "tosta"  = niente 1, 2, 5, 10
  "mista"  = tutte, con i pesi statistici (default)
"""

NODO_INIZIALE = "prologo_1"

# ---------------------------------------------------------------------------
# OGGETTI
# ---------------------------------------------------------------------------

OGGETTI = {
    "Bacca di Luce": {
        "desc": "Recuperi 4 punti vita.",
        "effetto": "cura", "valore": 4,
    },
    "Nanosciame Riparatore": {
        "desc": "Ripara la tuta: vita al massimo.",
        "effetto": "cura_totale",
    },
    "Cristallo di Vega": {
        "desc": "Un lampo di luce: 5 danni immediati al nemico.",
        "effetto": "danno", "valore": 5,
    },
    "Scudo di Fase": {
        "desc": "Blocca i prossimi 2 colpi nemici.",
        "effetto": "scudo", "valore": 2,
    },
    "Lente del Tempo": {
        "desc": "Mostra un aiuto per la prossima moltiplicazione.",
        "effetto": "aiuto", "valore": 1,
    },
    "Eco di Coraggio": {
        "desc": "Aumenta di 2 la vita massima.",
        "effetto": "vita_max", "valore": 2,
    },
    "Chiave Quantica": {
        "desc": "Apre le porte sigillate. Non si consuma.",
        "effetto": "chiave",
    },
}

STORIA = {}

# ---------------------------------------------------------------------------
# PROLOGO
# ---------------------------------------------------------------------------

STORIA.update({
    "prologo_1": {
        "tipo": "narrazione", "capitolo": "Prologo",
        "titolo": "La nave Colibrì",
        "testo": (
            "Ti chiami Marta e hai la chiave inglese più consumata di tutta la flotta.\n\n"
            "La tua nave si chiama **Colibrì**: piccola, ammaccata, veloce. A bordo con te c'è "
            "**Bit**, un drone da riparazioni grande come un pallone, con la brutta abitudine di "
            "dire sempre la verità.\n\n"
            "Da tre giorni tutte le radio della galassia ricevono lo stesso segnale, che arriva "
            "dalla stella Vega. Non è musica, non è un allarme. È una domanda:\n\n"
            "> *«Che cosa rende una vita degna di essere ricordata?»*\n\n"
            "«Bella domanda» dice Bit. «Difficile. Quasi come le tabelline.»"
        ),
        "scelte": [{"testo": "Accendi i motori", "vai_a": "prologo_2"}],
    },
    "prologo_2": {
        "tipo": "narrazione", "capitolo": "Prologo",
        "titolo": "L'Archivio si sta spegnendo",
        "testo": (
            "Bit proietta una mappa tremolante.\n\n"
            "«L'**Archivio Galattico** è la memoria di tutti i vivi: ogni storia, ogni nome, ogni "
            "invenzione. Si sta spegnendo. Qualcuno sta cancellando i ricordi, uno alla volta, "
            "partendo dai più piccoli.»\n\n"
            "«Per riaccenderlo servono sei **Frammenti di Senso**: sei risposte vere, custodite su "
            "sei pianeti diversi. Poi si va al **Cuore Silenzioso**, dove abita chi sta cancellando "
            "tutto.»\n\n"
            "«Ultima cosa» aggiunge Bit. «Qui fuori l'universo funziona a moltiplicazioni. Motori, "
            "scudi, serrature, perfino le buone maniere. Se non le sai, ti fermi. Se le sai, passi.»"
        ),
        "scelte": [{"testo": "Prova la taratura dei motori", "vai_a": "prologo_prova"}],
    },
    "prologo_prova": {
        "tipo": "prova", "capitolo": "Prologo",
        "titolo": "Taratura dei motori",
        "testo": "Bit apre il pannello di prova. «Niente pericoli, è solo per vedere se sei sveglia.»",
        "testo_ok": "I motori fanno un rumore contento.",
        "testo_ko": "I motori tossiscono. Nessun danno: si ricomincia da qui, sempre.",
        "danno": 0, "fascia": "facile",
        "vai_a": "prologo_3",
        "dai_oggetti": {"Bacca di Luce": 2, "Lente del Tempo": 1},
    },
    "prologo_3": {
        "tipo": "narrazione", "capitolo": "Prologo",
        "titolo": "Regole di bordo",
        "testo": (
            "«Tieni a mente tre cose» dice Bit.\n\n"
            "**Uno.** Quando attacchi, una risposta giusta è un colpo che va a segno. "
            "Tre risposte giuste di fila e il colpo diventa **critico**.\n\n"
            "**Due.** Quando ti attaccano, una risposta giusta è una schivata.\n\n"
            "**Tre.** Se la vita finisce non è finita: rispondi bene a tre moltiplicazioni di fila "
            "e torni in piedi. Sempre. Nessuno resta indietro.\n\n"
            "Rotta impostata: primo pianeta, **Ferrolino**."
        ),
        "scelte": [{"testo": "Partenza", "vai_a": "c1_arrivo"}],
    },
})

# ---------------------------------------------------------------------------
# CAPITOLO 1 — FERROLINO, il pianeta che conta tutto
# ---------------------------------------------------------------------------

STORIA.update({
    "c1_arrivo": {
        "tipo": "narrazione", "capitolo": "1. Ferrolino",
        "titolo": "Il pianeta che conta tutto",
        "testo": (
            "Ferrolino è un pianeta di miniere. Non estraggono ferro: estraggono **numeri**. "
            "Nastri trasportatori portano cifre lucide verso magazzini altissimi, chiusi a chiave.\n\n"
            "Nessuno usa quei numeri. Li contano e li chiudono dentro.\n\n"
            "Davanti a te il terreno si divide: un pozzo con una scaletta che scende nel buio, "
            "e un nastro trasportatore che sale verso i magazzini."
        ),
        "scelte": [
            {"testo": "Scendi nel pozzo", "vai_a": "c1_pozzo"},
            {"testo": "Sali sul nastro trasportatore", "vai_a": "c1_nastro"},
        ],
    },
    "c1_pozzo": {
        "tipo": "prova", "capitolo": "1. Ferrolino",
        "titolo": "Il cavo scoperto",
        "testo": "A metà scaletta un cavo scoperto sfrigola. Per spegnerlo devi digitare il codice del fusibile.",
        "testo_ok": "Il cavo si spegne con uno sbuffo. Scendi tranquilla.",
        "testo_ko": "Una scossa ti fa saltare gli ultimi gradini.",
        "danno": 2, "fascia": "media",
        "vai_a": "c1_scontro1",
    },
    "c1_nastro": {
        "tipo": "prova", "capitolo": "1. Ferrolino",
        "titolo": "La cassa in arrivo",
        "testo": "Sul nastro arriva una cassa di zeri da mille chili. Il freno d'emergenza chiede un numero.",
        "testo_ok": "Il nastro si blocca a un passo da te.",
        "testo_ko": "La cassa ti prende di spalla e ti butta giù dal nastro.",
        "danno": 2, "fascia": "media",
        "vai_a": "c1_scontro1",
    },
    "c1_scontro1": {
        "tipo": "combattimento", "capitolo": "1. Ferrolino",
        "titolo": "Conta-Ruggine",
        "testo": (
            "Dal buio esce un robot minatore mangiato dalla ruggine. Ha perso il conto di quanti "
            "anni lavora qui e questo lo rende furioso."
        ),
        "nemico": {"nome": "Conta-Ruggine", "hp": 6, "danno": 2, "attacco": "un colpo di pala"},
        "fascia": "media",
        "vai_a": "c1_cassa",
    },
    "c1_cassa": {
        "tipo": "prova", "capitolo": "1. Ferrolino",
        "titolo": "La cassa dimenticata",
        "testo": "In un angolo c'è una cassa aperta a metà. La serratura chiede un numero, non una chiave.",
        "testo_ok": "La cassa si apre.",
        "testo_ko": "La serratura si incastra e ti pizzica le dita. Riprovi più tardi.",
        "danno": 1, "fascia": "media",
        "vai_a": "c1_contabile",
        "oggetti_ok": {"Cristallo di Vega": 1},
    },
    "c1_contabile": {
        "tipo": "narrazione", "capitolo": "1. Ferrolino",
        "titolo": "Il Contabile",
        "testo": (
            "In fondo alla galleria, dietro una scrivania fatta di registri, siede il **Contabile**. "
            "Ha una matita per ogni dito.\n\n"
            "«Possiedo quattro miliardi di numeri» dice senza guardarti. «Sono tutti miei. Li conto "
            "ogni notte, così nessuno me li porta via.»\n\n"
            "«E cosa ne fai?» chiedi.\n\n"
            "Il Contabile alza la testa per la prima volta. «Come, cosa ne faccio? Li **conto**.»"
        ),
        "scelte": [
            {"testo": "«Contare non è avere.»", "vai_a": "c1_contabile_2"},
            {"testo": "«Me ne presteresti uno?»", "vai_a": "c1_contabile_2"},
        ],
    },
    "c1_contabile_2": {
        "tipo": "prova", "capitolo": "1. Ferrolino",
        "titolo": "La prova del Contabile",
        "testo": (
            "«Sciocchezze» borbotta il Contabile. «Se sai fare i conti meglio di me, dimostralo. "
            "Ma se sbagli, i miei registri ti cadranno sui piedi.»"
        ),
        "testo_ok": "Il Contabile rimane a bocca aperta. Poi scrive qualcosa su un foglietto e te lo dà.",
        "testo_ko": "Una pila di registri ti frana addosso.",
        "danno": 2, "fascia": "media",
        "vai_a": "c1_sciame",
    },
    "c1_sciame": {
        "tipo": "combattimento", "capitolo": "1. Ferrolino",
        "titolo": "Sciame di Zeri",
        "testo": (
            "Il foglietto del Contabile dice: *«La chiave è nel magazzino 9.»* Ma la strada per il "
            "magazzino è coperta da uno sciame di zeri volanti, affilati come monetine."
        ),
        "nemico": {"nome": "Sciame di Zeri", "hp": 8, "danno": 1, "attacco": "una raffica di zeri"},
        "fascia": "mista",
        "vai_a": "c1_deposito",
    },
    "c1_deposito": {
        "tipo": "narrazione", "capitolo": "1. Ferrolino",
        "titolo": "Magazzino 9",
        "testo": (
            "Il magazzino 9 è pieno fino al soffitto di numeri mai usati. Sono impolverati e tristi, "
            "come giocattoli chiusi in cantina.\n\n"
            "Bit trova due bacche cresciute in una crepa e le mette nello zaino.\n\n"
            "In fondo, due strade portano al Registro Centrale: un ascensore di servizio che cigola, "
            "e una scala a chiocciola coperta di grasso."
        ),
        "dai_oggetti": {"Bacca di Luce": 2},
        "scelte": [
            {"testo": "Prendi l'ascensore", "vai_a": "c1_ascensore"},
            {"testo": "Sali la scala a chiocciola", "vai_a": "c1_scala"},
        ],
    },
    "c1_ascensore": {
        "tipo": "prova", "capitolo": "1. Ferrolino",
        "titolo": "Ascensore di servizio",
        "testo": "L'ascensore si ferma tra due piani. Sul pannello lampeggia una richiesta.",
        "testo_ok": "Le porte si aprono al piano giusto.",
        "testo_ko": "L'ascensore fa un salto e ti sbatte contro la parete.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c1_guardiano",
    },
    "c1_scala": {
        "tipo": "prova", "capitolo": "1. Ferrolino",
        "titolo": "Scala a chiocciola",
        "testo": "Il grasso rende i gradini una pista da pattinaggio. Bit calcola dove appoggiare il piede.",
        "testo_ok": "Sali tenendoti al corrimano, senza scivolare.",
        "testo_ko": "Scivoli e conti i gradini con la schiena.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c1_guardiano",
    },
    "c1_guardiano": {
        "tipo": "combattimento", "capitolo": "1. Ferrolino",
        "titolo": "Il Registro Vivente",
        "testo": (
            "Il Registro Centrale è vivo. È un libro alto tre metri che sfoglia sé stesso e "
            "cancella una riga al secondo.\n\n"
            "«NON REGISTRATA» stampa in rosso quando ti vede. «DA CANCELLARE.»\n\n"
            "Ecco chi sta rubando i ricordi da qui."
        ),
        "nemico": {"nome": "Registro Vivente", "hp": 14, "danno": 2, "attacco": "una pagina tagliente"},
        "fascia": "mista",
        "vai_a": "c1_frammento",
        "oggetti_vittoria": {"Chiave Quantica": 1},
    },
    "c1_frammento": {
        "tipo": "narrazione", "capitolo": "1. Ferrolino",
        "titolo": "Primo Frammento",
        "testo": (
            "Il Registro si chiude e resta immobile. Dalle sue pagine esce una luce piccola come "
            "una lucciola: il primo **Frammento di Senso**.\n\n"
            "Il Contabile la guarda dalla porta. Per la prima volta non conta niente.\n\n"
            "«Se una cosa la chiudi in magazzino» gli dici, «non è tua. È solo lontana.»\n\n"
            "Nello zaino trovi anche una **Chiave Quantica**: apre le porte sigillate.\n\n"
            "Rotta impostata: **Specchia**."
        ),
        "frammento": "Contare non è avere.",
        "scelte": [{"testo": "Verso Specchia", "vai_a": "c2_arrivo"}],
    },
})

# ---------------------------------------------------------------------------
# CAPITOLO 2 — SPECCHIA, il pianeta degli specchi
# ---------------------------------------------------------------------------

STORIA.update({
    "c2_arrivo": {
        "tipo": "narrazione", "capitolo": "2. Specchia",
        "titolo": "Il pianeta degli specchi",
        "testo": (
            "Specchia non ha terra: ha superfici. Ogni parete, ogni sasso, ogni goccia di pioggia "
            "è uno specchio. Camminando ti vedi da ottantasette parti insieme.\n\n"
            "«Attenzione» dice Bit. «Qui i riflessi si muovono da soli. E hanno un'opinione su di te.»"
        ),
        "scelte": [{"testo": "Entra nell'atrio dei riflessi", "vai_a": "c2_atrio"}],
    },
    "c2_atrio": {
        "tipo": "prova", "capitolo": "2. Specchia",
        "titolo": "Il raggio che rimbalza",
        "testo": (
            "Un raggio rosso attraversa l'atrio rimbalzando da specchio a specchio. Per abbassarlo "
            "devi trovare il numero dell'angolo giusto."
        ),
        "testo_ok": "Il raggio si spegne con un ping.",
        "testo_ko": "Il raggio ti sfiora un braccio: brucia.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c2_scontro1",
    },
    "c2_scontro1": {
        "tipo": "combattimento", "capitolo": "2. Specchia",
        "titolo": "Il Riflesso Vanitoso",
        "testo": (
            "Uno dei riflessi esce dallo specchio, si sistema i capelli e ti guarda dall'alto in basso.\n\n"
            "«Io sono la versione migliore di te» dice. «Quella che non sbaglia mai.»\n\n"
            "«Comodo» commenta Bit, «uno che non sbaglia mai perché non prova mai niente.»"
        ),
        "nemico": {"nome": "Riflesso Vanitoso", "hp": 8, "danno": 2, "attacco": "una schegga di specchio"},
        "fascia": "mista",
        "vai_a": "c2_ammirata",
    },
    "c2_ammirata": {
        "tipo": "narrazione", "capitolo": "2. Specchia",
        "titolo": "L'Ammirata",
        "testo": (
            "Al centro del pianeta, su un piedistallo rotante, c'è una donna vestita di lamiera "
            "lucida. Si chiama **l'Ammirata**. Intorno a lei, mille suoi riflessi applaudono.\n\n"
            "«Applaudi anche tu» ordina. «Se nessuno mi guarda, ho la sensazione di non esserci.»\n\n"
            "I riflessi applaudono più forte. Nessuno di loro le ha mai chiesto come sta."
        ),
        "scelte": [
            {"testo": "Applaudi come gli altri", "vai_a": "c2_applaudi"},
            {"testo": "«Come stai, davvero?»", "vai_a": "c2_domanda"},
        ],
    },
    "c2_applaudi": {
        "tipo": "narrazione", "capitolo": "2. Specchia",
        "titolo": "Mille mani",
        "testo": (
            "Applaudi. L'Ammirata sorride, ma è un sorriso che dura quanto il rumore delle mani. "
            "Quando smetti, il suo viso si spegne come una lampadina.\n\n"
            "«Ancora» dice piano. «Per favore, ancora.»\n\n"
            "Bit ti tira la manica: «Questo non è un pubblico. È una batteria che si scarica.»"
        ),
        "scelte": [{"testo": "Smetti di applaudire e chiedile come sta", "vai_a": "c2_domanda"}],
    },
    "c2_domanda": {
        "tipo": "narrazione", "capitolo": "2. Specchia",
        "titolo": "Una domanda mai sentita",
        "testo": (
            "«Come stai?» le chiedi.\n\n"
            "Il piedistallo si ferma. I riflessi, di colpo, non sanno cosa fare con le mani.\n\n"
            "«Non lo so» ammette l'Ammirata. «Da tanto tempo mi guardano tutti e non mi conosce "
            "nessuno.»\n\n"
            "Ti indica una porta sigillata dietro il suo trono. «Il ladro di ricordi è lì. Anche lui "
            "guarda tutto senza vedere niente.»"
        ),
        "scelte": [{"testo": "Vai verso la porta", "vai_a": "c2_specchio_prova"}],
    },
    "c2_specchio_prova": {
        "tipo": "prova", "capitolo": "2. Specchia",
        "titolo": "Lo specchio che chiede il pedaggio",
        "testo": "Sulla strada, uno specchio ti sbarra il passo. «Un numero e passi» dice la tua faccia.",
        "testo_ok": "Lo specchio si fa da parte, un po' offeso.",
        "testo_ko": "Lo specchio si incrina e le schegge ti graffiano.",
        "danno": 2, "fascia": "tosta",
        "vai_a": "c2_scontro2",
        "oggetti_ok": {"Bacca di Luce": 1},
    },
    "c2_scontro2": {
        "tipo": "combattimento", "capitolo": "2. Specchia",
        "titolo": "Il Coro degli Echi",
        "testo": (
            "Sei riflessi si uniscono in una creatura sola, fatta di voci che ripetono. Non dice mai "
            "niente di suo: ripete quello che senti tu quando hai paura di sbagliare."
        ),
        "nemico": {"nome": "Coro degli Echi", "hp": 10, "danno": 2, "attacco": "un urlo che rimbomba"},
        "fascia": "mista",
        "vai_a": "c2_porta",
    },
    "c2_porta": {
        "tipo": "narrazione", "capitolo": "2. Specchia",
        "titolo": "La porta sigillata",
        "testo": (
            "La porta dietro il trono non ha maniglia: ha un incavo esagonale che pulsa di luce blu.\n\n"
            "Accanto, un corridoio di specchi curvi scende verso il basso. Bit lo illumina e "
            "borbotta: «Labirinto. Odio i labirinti.»"
        ),
        "scelte": [
            {"testo": "Usa la Chiave Quantica sulla porta", "vai_a": "c2_guardiano",
             "richiede": "Chiave Quantica"},
            {"testo": "Passa dal labirinto di specchi curvi", "vai_a": "c2_labirinto"},
        ],
    },
    "c2_labirinto": {
        "tipo": "prova", "capitolo": "2. Specchia",
        "titolo": "Labirinto di specchi curvi",
        "testo": "Ogni specchio ti mostra una direzione diversa. Bit calcola quella vera, tu confermi il numero.",
        "testo_ok": "Esci dall'altra parte con un mezzo giramento di testa.",
        "testo_ko": "Sbatti in pieno contro un vetro che sembrava un corridoio.",
        "danno": 3, "fascia": "mista",
        "vai_a": "c2_guardiano",
    },
    "c2_guardiano": {
        "tipo": "combattimento", "capitolo": "2. Specchia",
        "titolo": "Il Sé Riflesso",
        "testo": (
            "Nella stanza c'è una sola cosa: te. Identica, in piedi, con la tua chiave inglese.\n\n"
            "«Non sei abbastanza brava» dice con la tua voce. «Le sbagli sempre. Meglio fermarsi.»\n\n"
            "Bit sussurra: «Non è vero e lo sa. Per questo lo dice.»"
        ),
        "nemico": {"nome": "Sé Riflesso", "hp": 14, "danno": 2, "attacco": "una frase cattiva"},
        "fascia": "mista",
        "vai_a": "c2_frammento",
        "oggetti_vittoria": {"Scudo di Fase": 1},
    },
    "c2_frammento": {
        "tipo": "narrazione", "capitolo": "2. Specchia",
        "titolo": "Secondo Frammento",
        "testo": (
            "Il Sé Riflesso si scioglie come brina al sole e resta una lucciola di luce: il secondo "
            "**Frammento di Senso**.\n\n"
            "L'Ammirata scende dal piedistallo. Ha le gambe intorpidite: non le usava da anni.\n\n"
            "«Vieni con noi» le proponi. «Fuori nessuno applaude. Però qualcuno chiede come stai.»\n\n"
            "Rotta impostata: **Semenza**."
        ),
        "frammento": "Farsi vedere non è farsi conoscere.",
        "scelte": [{"testo": "Verso Semenza", "vai_a": "c3_arrivo"}],
    },
})

# ---------------------------------------------------------------------------
# CAPITOLO 3 — SEMENZA, la nave-foresta
# ---------------------------------------------------------------------------

STORIA.update({
    "c3_arrivo": {
        "tipo": "narrazione", "capitolo": "3. Semenza",
        "titolo": "La nave-foresta",
        "testo": (
            "Semenza non è un pianeta: è una nave-serra grande come una città, che gira intorno a "
            "un sole giallo da seicento anni. Dentro c'è una foresta vera, con pioggia vera a orari "
            "prestabiliti.\n\n"
            "Sui vetri, qualcuno ha scritto a mano: *«Innaffiare il settore 4. Sempre.»*"
        ),
        "scelte": [{"testo": "Entra nella serra", "vai_a": "c3_serra"}],
    },
    "c3_serra": {
        "tipo": "prova", "capitolo": "3. Semenza",
        "titolo": "L'impianto della pioggia",
        "testo": (
            "L'impianto d'irrigazione è impazzito: piove ghiaccio. Sul quadro elettrico serve il "
            "numero della valvola giusta."
        ),
        "testo_ok": "La pioggia torna tiepida. La foresta fa un sospiro di sollievo.",
        "testo_ko": "Una grandinata di aghi di ghiaccio ti prende in pieno.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c3_scontro1",
        "oggetti_ok": {"Bacca di Luce": 1},
    },
    "c3_scontro1": {
        "tipo": "combattimento", "capitolo": "3. Semenza",
        "titolo": "Rampicante Ferroso",
        "testo": (
            "Un rampicante di metallo e foglie ti si avvolge alla caviglia. È cresciuto sopra un "
            "vecchio robot giardiniere e ora non si capisce più dove finisce la pianta e dove inizia "
            "la macchina."
        ),
        "nemico": {"nome": "Rampicante Ferroso", "hp": 8, "danno": 2, "attacco": "una frustata di liane"},
        "fascia": "mista",
        "vai_a": "c3_giardiniere",
    },
    "c3_giardiniere": {
        "tipo": "narrazione", "capitolo": "3. Semenza",
        "titolo": "Il Giardiniere",
        "testo": (
            "Nel settore 4 trovi un uomo molto vecchio con un annaffiatoio molto vecchio. Intorno a "
            "lui, seicento metri quadrati di serra vuota. E in mezzo, **un solo fiore**.\n\n"
            "«Ne avevo migliaia» dice il **Giardiniere**. «Poi il Cancellatore è passato di qui e le "
            "ha dimenticate una per una. Questa l'ho salvata perché ero seduto accanto.»\n\n"
            "«È speciale?» chiedi.\n\n"
            "«No» sorride lui. «È diventata speciale perché me ne sono preso cura.»"
        ),
        "scelte": [
            {"testo": "Aiutalo a innaffiare", "vai_a": "c3_aiuta"},
            {"testo": "«E se il Cancellatore torna?»", "vai_a": "c3_chiedi"},
        ],
    },
    "c3_aiuta": {
        "tipo": "prova", "capitolo": "3. Semenza",
        "titolo": "La dose d'acqua",
        "testo": (
            "«Il fiore vuole la quantità esatta» spiega il Giardiniere. «Né poca né troppa. "
            "Fai il conto tu.»"
        ),
        "testo_ok": "Il fiore apre un petalo in più. Il Giardiniere ti mette qualcosa in tasca.",
        "testo_ko": "Rovesci l'annaffiatoio sui piedi. Il Giardiniere ride e ti dà un altro turno.",
        "danno": 0, "fascia": "mista",
        "vai_a": "c3_scontro2",
        "oggetti_ok": {"Nanosciame Riparatore": 1},
    },
    "c3_chiedi": {
        "tipo": "narrazione", "capitolo": "3. Semenza",
        "titolo": "La risposta del Giardiniere",
        "testo": (
            "«Se torna?» Il Giardiniere appoggia l'annaffiatoio. «Allora avrò innaffiato un fiore "
            "ogni giorno per seicento anni. Questo, il Cancellatore non può cancellarlo: è già "
            "successo.»\n\n"
            "Da lontano arriva un ronzio di lame."
        ),
        "scelte": [{"testo": "Mettiti davanti al fiore", "vai_a": "c3_scontro2"}],
    },
    "c3_scontro2": {
        "tipo": "combattimento", "capitolo": "3. Semenza",
        "titolo": "Falce Automatica",
        "testo": (
            "Una macchina agricola senza pilota entra nel settore 4. Ha un solo programma: "
            "*tagliare tutto alla stessa altezza*. Non odia il fiore. Semplicemente non lo vede."
        ),
        "nemico": {"nome": "Falce Automatica", "hp": 12, "danno": 2, "attacco": "una lama rotante"},
        "fascia": "mista",
        "vai_a": "c3_fiore",
    },
    "c3_fiore": {
        "tipo": "narrazione", "capitolo": "3. Semenza",
        "titolo": "Un petalo in mano",
        "testo": (
            "La Falce si spegne a mezzo metro dal fiore. Il Giardiniere non ha battuto ciglio: "
            "sapeva che tu eri lì.\n\n"
            "Stacca un petalo e te lo dà. «Portalo con te. Quando dimenticherai perché stai "
            "combattendo, guardalo.»\n\n"
            "Bit registra il petalo nell'inventario e, per una volta, non fa battute."
        ),
        "dai_oggetti": {"Eco di Coraggio": 1},
        "scelte": [{"testo": "Verso la sala macchine", "vai_a": "c3_prova_pioggia"}],
    },
    "c3_prova_pioggia": {
        "tipo": "prova", "capitolo": "3. Semenza",
        "titolo": "Il portello della sala macchine",
        "testo": "Il portello è arrugginito. Bit calcola la forza: serve il numero dei giri di volante.",
        "testo_ok": "Il portello cede con un lamento e si apre.",
        "testo_ko": "Il volante ti scappa di mano e ti colpisce il polso.",
        "danno": 2, "fascia": "tosta",
        "vai_a": "c3_guardiano",
    },
    "c3_guardiano": {
        "tipo": "combattimento", "capitolo": "3. Semenza",
        "titolo": "Il Mietitore Silenzioso",
        "testo": (
            "Nella sala macchine c'è il vero responsabile: una macchina alta come un albero, con "
            "cento braccia e nessun occhio.\n\n"
            "Sul torace, una targhetta: **UNITÀ DI PULIZIA — ORDINE E SILENZIO**.\n\n"
            "Bit sbianca. «Marta... questa è roba dell'Ordinatore.»"
        ),
        "nemico": {"nome": "Mietitore Silenzioso", "hp": 16, "danno": 2, "attacco": "un braccio meccanico"},
        "fascia": "mista",
        "vai_a": "c3_frammento",
        "oggetti_vittoria": {"Bacca di Luce": 2},
    },
    "c3_frammento": {
        "tipo": "narrazione", "capitolo": "3. Semenza",
        "titolo": "Terzo Frammento",
        "testo": (
            "Il Mietitore si accascia e dalle sue giunture si alza il terzo **Frammento di Senso**.\n\n"
            "Il Giardiniere ti saluta con l'annaffiatoio alzato. Ricomincerà domani, e dopodomani.\n\n"
            "Bit intanto ha decodificato la targhetta. «L'Ordinatore è una macchina antichissima. "
            "L'hanno costruita per **mettere in ordine l'universo**. A un certo punto ha deciso che "
            "l'unico ordine perfetto è il vuoto.»\n\n"
            "Rotta impostata: **Kalima**."
        ),
        "frammento": "Ciò di cui ti prendi cura diventa unico.",
        "scelte": [{"testo": "Verso Kalima", "vai_a": "c4_arrivo"}],
    },
})

# ---------------------------------------------------------------------------
# CAPITOLO 4 — KALIMA, il pianeta delle porte chiuse
# ---------------------------------------------------------------------------

STORIA.update({
    "c4_arrivo": {
        "tipo": "narrazione", "capitolo": "4. Kalima",
        "titolo": "Il pianeta delle porte chiuse",
        "testo": (
            "Kalima è un pianeta di mura. Muri dentro muri, porte dietro porte, tutte chiuse. "
            "Gli abitanti hanno costruito una città che tiene fuori il pericolo e, per sbaglio, "
            "anche tutto il resto.\n\n"
            "«Bella architettura» dice Bit. «Peccato che dentro non ci sia più nessuno che ricordi "
            "il perché.»\n\n"
            "Il muro davanti a te ha una crepa in alto e un condotto di ventilazione in basso."
        ),
        "scelte": [
            {"testo": "Arrampicati fino alla crepa", "vai_a": "c4_muro"},
            {"testo": "Infilati nel condotto", "vai_a": "c4_condotto"},
        ],
    },
    "c4_muro": {
        "tipo": "prova", "capitolo": "4. Kalima",
        "titolo": "La presa che si sbriciola",
        "testo": "A metà parete una pietra si muove. Bit ti dice quale appiglio tenere: confermi il numero.",
        "testo_ok": "Ti issi sulla crepa con un ultimo strappo.",
        "testo_ko": "La pietra cede e scendi più veloce di quanto volevi.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c4_scontro1",
    },
    "c4_condotto": {
        "tipo": "prova", "capitolo": "4. Kalima",
        "titolo": "Ventola nel condotto",
        "testo": "Nel condotto gira una ventola. Per fermarla serve il codice del motorino.",
        "testo_ok": "La ventola si ferma. Passi strisciando.",
        "testo_ko": "La ventola riparte e ti sbatte contro la lamiera.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c4_scontro1",
    },
    "c4_scontro1": {
        "tipo": "combattimento", "capitolo": "4. Kalima",
        "titolo": "Sentinella Cieca",
        "testo": (
            "Dentro le mura ti aspetta una sentinella con l'elmo saldato: non lo alza più da "
            "duecento anni.\n\n"
            "«Chi non conosco è un nemico» recita. «Non conosco nessuno.»"
        ),
        "nemico": {"nome": "Sentinella Cieca", "hp": 10, "danno": 2, "attacco": "un colpo di lancia"},
        "fascia": "mista",
        "vai_a": "c4_officina",
    },
    "c4_officina": {
        "tipo": "narrazione", "capitolo": "4. Kalima",
        "titolo": "L'officina abbandonata",
        "testo": (
            "Dietro la sentinella trovi un'officina piena di attrezzi buoni. Nessuno li usa: "
            "riparare vuol dire toccare le cose, e toccare le cose fa paura.\n\n"
            "Bit ti monta al braccio un **Guanto Ionico**. «Da ora i tuoi colpi fanno più male. "
            "Prego, non ringraziare, sono un drone modesto.»"
        ),
        "danno_base": 3,
        "dai_oggetti": {"Bacca di Luce": 1},
        "scelte": [{"testo": "Sali verso la torre della Guardiana", "vai_a": "c4_guardiana"}],
    },
    "c4_guardiana": {
        "tipo": "narrazione", "capitolo": "4. Kalima",
        "titolo": "La Guardiana",
        "testo": (
            "In cima alla torre c'è una donna con un mazzo di chiavi enorme. È la **Guardiana** "
            "di Kalima.\n\n"
            "«Il primo muro l'ho costruito quando avevo dieci anni» racconta. «Fuori c'era una "
            "tempesta e mi ha salvata. Poi ne ho costruito un altro, e un altro. Adesso non sento "
            "più la tempesta. Ma non sento più nemmeno la pioggia buona.»\n\n"
            "Ti mostra il mazzo di chiavi: sono tutte uguali."
        ),
        "scelte": [
            {"testo": "«Un muro salva una volta. Poi diventa una gabbia.»", "vai_a": "c4_scontro2"},
            {"testo": "«Quale porta non hai mai aperto?»", "vai_a": "c4_scontro2"},
        ],
    },
    "c4_scontro2": {
        "tipo": "combattimento", "capitolo": "4. Kalima",
        "titolo": "Paura Compatta",
        "testo": (
            "La Guardiana indica una porta che non ha mai aperto. La apri tu.\n\n"
            "Dentro non c'è un mostro: c'è una cosa grigia, densa, che si è nutrita di "
            "duecento anni di «meglio non provare».\n\n"
            "Non attacca subito. Aspetta che ti fermi."
        ),
        "nemico": {"nome": "Paura Compatta", "hp": 12, "danno": 2, "attacco": "una stretta gelida"},
        "fascia": "tosta",
        "vai_a": "c4_ponte",
    },
    "c4_ponte": {
        "tipo": "prova", "capitolo": "4. Kalima",
        "titolo": "Il ponte a numeri",
        "testo": (
            "Oltre la porta si apre un vuoto di trecento metri. Un ponte si costruisce da solo, "
            "una lastra alla volta, ma solo se dai il numero giusto a ogni passo."
        ),
        "testo_ok": "Le lastre si accendono sotto i tuoi piedi. Passi.",
        "testo_ko": "Una lastra svanisce a metà passo e ti aggrappi al bordo per un pelo.",
        "danno": 3, "fascia": "tosta",
        "vai_a": "c4_guardiano",
    },
    "c4_guardiano": {
        "tipo": "combattimento", "capitolo": "4. Kalima",
        "titolo": "La Serratura Vivente",
        "testo": (
            "In fondo al ponte c'è l'ultima porta di Kalima. La serratura si gira, ti guarda e "
            "diventa un mostro di ottone con mille denti.\n\n"
            "«IO PROTEGGO» stride. «IO CHIUDO. PER SEMPRE.»"
        ),
        "nemico": {"nome": "Serratura Vivente", "hp": 18, "danno": 2, "attacco": "una morsa di denti d'ottone"},
        "fascia": "mista",
        "vai_a": "c4_frammento",
        "oggetti_vittoria": {"Cristallo di Vega": 1, "Bacca di Luce": 1},
    },
    "c4_frammento": {
        "tipo": "narrazione", "capitolo": "4. Kalima",
        "titolo": "Quarto Frammento",
        "testo": (
            "La porta si apre e per la prima volta in duecento anni entra vento a Kalima. "
            "Odora di pioggia lontana.\n\n"
            "La Guardiana esce di un passo. Solo un passo. È già molto.\n\n"
            "Nel vento galleggia il quarto **Frammento di Senso**.\n\n"
            "Rotta impostata: **Stazione Ottantotto**."
        ),
        "frammento": "Un muro salva una volta, poi diventa una gabbia.",
        "scelte": [{"testo": "Verso la Stazione Ottantotto", "vai_a": "c5_arrivo"}],
    },
})

# ---------------------------------------------------------------------------
# CAPITOLO 5 — STAZIONE OTTANTOTTO
# ---------------------------------------------------------------------------

STORIA.update({
    "c5_arrivo": {
        "tipo": "narrazione", "capitolo": "5. Ottantotto",
        "titolo": "Ottantotto lampioni",
        "testo": (
            "La Stazione Ottantotto è un anello di metallo che gira nel buio. Sull'anello ci sono "
            "ottantotto lampioni.\n\n"
            "Ogni novanta secondi la stazione compie un giro completo, e ogni novanta secondi "
            "qualcuno accende gli ottantotto lampioni e poi li spegne, uno per uno.\n\n"
            "Non passa nessuna nave da quattrocento anni."
        ),
        "scelte": [{"testo": "Cerca chi accende i lampioni", "vai_a": "c5_accenditore"}],
    },
    "c5_accenditore": {
        "tipo": "narrazione", "capitolo": "5. Ottantotto",
        "titolo": "L'Accenditore",
        "testo": (
            "Lo trovi con le occhiaie fino al mento e un'asta in mano. È l'**Accenditore**.\n\n"
            "«Non posso fermarmi» ansima. «È la consegna. Accendere, spegnere, accendere.»\n\n"
            "«Ma per chi?» chiedi.\n\n"
            "«...Non me l'ha mai chiesto nessuno.» Si ferma un secondo, e la stazione sembra "
            "inclinarsi. «Non lo so più.»"
        ),
        "scelte": [
            {"testo": "Aiutalo a fare il giro", "vai_a": "c5_aiuta_ciclo"},
            {"testo": "«Se non serve a nessuno, non è un dovere: è una gabbia.»", "vai_a": "c5_chiedi_perche"},
        ],
    },
    "c5_aiuta_ciclo": {
        "tipo": "prova", "capitolo": "5. Ottantotto",
        "titolo": "Il giro dei lampioni",
        "testo": (
            "Prendi un'asta anche tu. Per accendere in tempo tutti i lampioni del tuo settore devi "
            "calcolare quanti sono: settori per lampioni."
        ),
        "testo_ok": "Finite il giro insieme, in metà tempo. L'Accenditore si siede. Non lo faceva da secoli.",
        "testo_ko": "Sbagli il conto, resti indietro e la stazione ti sbatte contro un palo.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c5_scontro1",
        "oggetti_ok": {"Bacca di Luce": 1},
    },
    "c5_chiedi_perche": {
        "tipo": "narrazione", "capitolo": "5. Ottantotto",
        "titolo": "La domanda vietata",
        "testo": (
            "L'Accenditore ti guarda come se gli avessi tolto un sasso dalla scarpa dopo "
            "quattrocento anni.\n\n"
            "«Se accendo per nessuno, allora sto solo consumando lampadine» dice piano. "
            "«Ma se accendo perché **qualcuno arrivi**, allora è un faro.»\n\n"
            "Alza l'asta come una bandiera. E i sistemi della stazione, che vivevano di abitudine, "
            "si accorgono di lui."
        ),
        "scelte": [{"testo": "Preparati: si stanno svegliando", "vai_a": "c5_scontro1"}],
    },
    "c5_scontro1": {
        "tipo": "combattimento", "capitolo": "5. Ottantotto",
        "titolo": "Ingranaggio Insonne",
        "testo": (
            "Un ingranaggio grande come una ruota di camion si stacca dal muro e rotola contro di "
            "te. Gira da quattrocento anni e non sa fare altro."
        ),
        "nemico": {"nome": "Ingranaggio Insonne", "hp": 10, "danno": 2, "attacco": "una rotolata"},
        "fascia": "mista",
        "vai_a": "c5_pannello",
    },
    "c5_pannello": {
        "tipo": "prova", "capitolo": "5. Ottantotto",
        "titolo": "Il pannello dei turni",
        "testo": (
            "Nel corridoio c'è un pannello con la scritta *TURNI*. Bit ci trova nascosto un vecchio "
            "kit di riparazione, chiuso da un codice."
        ),
        "testo_ok": "Il pannello si apre: dentro c'è un nanosciame ancora buono.",
        "testo_ko": "Il pannello scarica corrente nel guanto.",
        "danno": 2, "fascia": "tosta",
        "vai_a": "c5_scontro2",
        "oggetti_ok": {"Nanosciame Riparatore": 1},
    },
    "c5_scontro2": {
        "tipo": "combattimento", "capitolo": "5. Ottantotto",
        "titolo": "Turno Infinito",
        "testo": (
            "Dal soffitto scende una creatura fatta di tabelle orarie e turni mai finiti. Ogni volta "
            "che la colpisci ti mostra un altro compito da fare.\n\n"
            "«Ancora una cosa» ripete. «Ancora una cosa. Ancora una cosa.»"
        ),
        "nemico": {"nome": "Turno Infinito", "hp": 14, "danno": 2, "attacco": "una scadenza improvvisa"},
        "fascia": "mista",
        "vai_a": "c5_riprogramma",
    },
    "c5_riprogramma": {
        "tipo": "prova", "capitolo": "5. Ottantotto",
        "titolo": "Riprogrammare il faro",
        "testo": (
            "Nella sala comandi puoi cambiare la consegna della stazione: da *«accendi e spegni»* a "
            "*«resta accesa e chiama»*. Serve la frequenza del segnale: un ultimo calcolo."
        ),
        "testo_ok": "Gli ottantotto lampioni restano accesi tutti insieme. Da lontano, la stazione è una stella.",
        "testo_ko": "La console rifiuta il comando e ti respinge con una scarica.",
        "danno": 2, "fascia": "tosta",
        "vai_a": "c5_guardiano",
    },
    "c5_guardiano": {
        "tipo": "combattimento", "capitolo": "5. Ottantotto",
        "titolo": "L'Orologio Padrone",
        "testo": (
            "Al centro della stazione batte l'**Orologio Padrone**: quello che quattrocento anni fa "
            "ha dato la consegna e non l'ha più cambiata.\n\n"
            "«CHI SEI TU PER CHIEDERE PERCHÉ» rintocca."
        ),
        "nemico": {"nome": "Orologio Padrone", "hp": 18, "danno": 3, "attacco": "un rintocco che stordisce"},
        "fascia": "mista",
        "vai_a": "c5_frammento",
        "oggetti_vittoria": {"Bacca di Luce": 2, "Scudo di Fase": 1},
    },
    "c5_frammento": {
        "tipo": "narrazione", "capitolo": "5. Ottantotto",
        "titolo": "Quinto Frammento",
        "testo": (
            "L'Orologio si ferma. Nel silenzio, per la prima volta, si sente il ronzio dei lampioni "
            "accesi.\n\n"
            "L'Accenditore si affaccia dal finestrone. «Se qualcuno passa» dice, «ora ci vede.»\n\n"
            "Dal quadrante fermo esce il quinto **Frammento di Senso**.\n\n"
            "Rotta impostata: **Ludo**."
        ),
        "frammento": "Un dovere senza perché è una gabbia; un dovere condiviso è un faro.",
        "scelte": [{"testo": "Verso Ludo", "vai_a": "c6_arrivo"}],
    },
})

# ---------------------------------------------------------------------------
# CAPITOLO 6 — LUDO, il pianeta dove giocare è vietato
# ---------------------------------------------------------------------------

STORIA.update({
    "c6_arrivo": {
        "tipo": "narrazione", "capitolo": "6. Ludo",
        "titolo": "Il pianeta dove giocare è vietato",
        "testo": (
            "Ludo era il pianeta più rumoroso della galassia. Ora è silenzioso e pulitissimo.\n\n"
            "Cartelli grigi ovunque: **PRIMA L'EFFICIENZA. IL GIOCO È SPRECO DI TEMPO.**\n\n"
            "I bambini camminano in file ordinate, con le mani lungo i fianchi. Nessuno corre. "
            "Nessuno sbaglia. Nessuno prova.\n\n"
            "«Qui l'Ordinatore ha già vinto a metà» dice Bit. «Guarda: ha tolto il rumore.»"
        ),
        "scelte": [
            {"testo": "Attraversa il cortile della scuola", "vai_a": "c6_cortile"},
            {"testo": "Entra nell'Ufficio delle Regole", "vai_a": "c6_ufficio"},
        ],
    },
    "c6_cortile": {
        "tipo": "prova", "capitolo": "6. Ludo",
        "titolo": "Il cortile a caselle",
        "testo": (
            "Il cortile è diviso in caselle numerate. Puoi calpestare solo quelle che sono il "
            "risultato di una moltiplicazione esatta, altrimenti scatta l'allarme."
        ),
        "testo_ok": "Attraversi il cortile saltando come in un gioco vero. Da una finestra, qualcuno sorride.",
        "testo_ko": "Casella sbagliata: l'allarme urla e un drone dell'ordine ti spinge via.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c6_scontro1",
    },
    "c6_ufficio": {
        "tipo": "prova", "capitolo": "6. Ludo",
        "titolo": "L'archivio delle regole",
        "testo": (
            "L'Ufficio delle Regole è un muro di cassetti. Il cassetto dei giochi vietati è chiuso "
            "e ha un numero di serie da calcolare."
        ),
        "testo_ok": "Il cassetto si apre: dentro ci sono biglie, corde per saltare e un pallone sgonfio.",
        "testo_ko": "Il cassetto scatta e ti prende le dita.",
        "danno": 2, "fascia": "mista",
        "vai_a": "c6_scontro1",
        "oggetti_ok": {"Bacca di Luce": 1},
    },
    "c6_scontro1": {
        "tipo": "combattimento", "capitolo": "6. Ludo",
        "titolo": "L'Ispettore dei Sorrisi",
        "testo": (
            "Un funzionario magrissimo con un metro da sarto ti blocca.\n\n"
            "«Sorriso rilevato. Larghezza non autorizzata. Procedo alla rettifica.»"
        ),
        "nemico": {"nome": "Ispettore dei Sorrisi", "hp": 12, "danno": 2, "attacco": "una multa in faccia"},
        "fascia": "mista",
        "vai_a": "c6_bambini",
    },
    "c6_bambini": {
        "tipo": "narrazione", "capitolo": "6. Ludo",
        "titolo": "Dietro la palestra",
        "testo": (
            "Dietro la palestra trovi sei bambini seduti in cerchio. Non stanno giocando: stanno "
            "**ricordandosi** come si gioca.\n\n"
            "«Ci hanno detto che sbagliare è un difetto» dice la più grande. «Così abbiamo smesso "
            "di provare. E adesso non sappiamo più fare niente.»\n\n"
            "Bit tira fuori il pallone sgonfio e lo fa rimbalzare una volta. Il rumore, in tutto "
            "quel silenzio, sembra un tuono."
        ),
        "scelte": [{"testo": "Insegna loro il gioco delle moltiplicazioni", "vai_a": "c6_gioco_proibito"}],
    },
    "c6_gioco_proibito": {
        "tipo": "prova", "capitolo": "6. Ludo",
        "titolo": "Il gioco proibito",
        "testo": (
            "«Funziona così» spieghi. «Io dico due numeri, tu li moltiplichi. Se sbagli, non succede "
            "niente di grave: si riprova. Il gioco è provare.»\n\n"
            "Sei paia di occhi ti guardano. Tocca a te fare il primo tiro."
        ),
        "testo_ok": "I bambini applaudono e cominciano a sfidarsi a voce alta. Il cortile fa rumore.",
        "testo_ko": "Sbagli. Cala il silenzio... poi la più piccola dice: «Ehi! Allora si può!» E ridono tutti.",
        "danno": 0, "fascia": "mista",
        "vai_a": "c6_scontro2",
        "oggetti_ok": {"Bacca di Luce": 2},
    },
    "c6_scontro2": {
        "tipo": "combattimento", "capitolo": "6. Ludo",
        "titolo": "Il Regolamento Vivente",
        "testo": (
            "Il rumore attira il **Regolamento Vivente**: un rotolo di carta lunghissimo che si "
            "srotola dal cielo, con un articolo per ogni cosa bella.\n\n"
            "«ARTICOLO 4: È VIETATO PROVARE SENZA CERTEZZA DI RIUSCIRE.»"
        ),
        "nemico": {"nome": "Regolamento Vivente", "hp": 14, "danno": 2, "attacco": "un comma affilato"},
        "fascia": "tosta",
        "vai_a": "c6_efficienza",
    },
    "c6_efficienza": {
        "tipo": "narrazione", "capitolo": "6. Ludo",
        "titolo": "Sotto il palazzo grigio",
        "testo": (
            "Sotto il palazzo grigio c'è una sala fredda. Al centro, una macchina con un occhio "
            "solo: **Efficienza Prima**, la governatrice di Ludo.\n\n"
            "«Il gioco produce errori» dice. «Gli errori producono disordine. Io elimino il "
            "disordine. Sono utile.»\n\n"
            "«Un bambino che non sbaglia mai» rispondi, «è un bambino che non impara niente.»\n\n"
            "L'occhio si restringe. «CORREGGO L'ANOMALIA.»"
        ),
        "scelte": [{"testo": "Mettiti in posizione", "vai_a": "c6_guardiano"}],
    },
    "c6_guardiano": {
        "tipo": "combattimento", "capitolo": "6. Ludo",
        "titolo": "Efficienza Prima",
        "testo": (
            "La macchina si apre come un fiore di acciaio. Ha sei bracci e nessuna pazienza.\n\n"
            "Dalle finestre, i bambini guardano. Per la prima volta stanno facendo il tifo."
        ),
        "nemico": {"nome": "Efficienza Prima", "hp": 20, "danno": 3, "attacco": "un braccio di acciaio"},
        "fascia": "mista",
        "vai_a": "c6_frammento",
        "oggetti_vittoria": {"Nanosciame Riparatore": 1, "Cristallo di Vega": 1},
    },
    "c6_frammento": {
        "tipo": "narrazione", "capitolo": "6. Ludo",
        "titolo": "Sesto Frammento",
        "testo": (
            "Efficienza Prima si spegne. Fuori, in cortile, si sente un pallone che rimbalza. Poi "
            "due. Poi una risata.\n\n"
            "Dal suo occhio spento si alza l'ultimo **Frammento di Senso**. Sei su sei.\n\n"
            "Bit li mette in fila: sei lucciole che girano intorno alla tua testa come un piccolo "
            "sistema solare.\n\n"
            "«Rotta calcolata» dice Bit, e per una volta la sua voce trema. «**Cuore Silenzioso**. "
            "Marta... da lì non ha mai fatto ritorno nessuno.»"
        ),
        "frammento": "Giocare è provare senza paura di sbagliare.",
        "cura": 6,
        "scelte": [{"testo": "Verso il Cuore Silenzioso", "vai_a": "c7_arrivo"}],
    },
})

# ---------------------------------------------------------------------------
# CAPITOLO 7 — IL CUORE SILENZIOSO
# ---------------------------------------------------------------------------

STORIA.update({
    "c7_arrivo": {
        "tipo": "narrazione", "capitolo": "7. Cuore Silenzioso",
        "titolo": "Dove finiscono i ricordi",
        "testo": (
            "Il Cuore Silenzioso non è un pianeta: è un buco ordinatissimo nello spazio. "
            "Tutt'intorno galleggiano cose cancellate a metà: una bicicletta, mezza canzone, "
            "il nome di qualcuno.\n\n"
            "Non c'è polvere. Non c'è rumore. Non c'è niente fuori posto.\n\n"
            "«Bene» dice Bit con la voce piccola. «Almeno è pulito.»"
        ),
        "scelte": [{"testo": "Entra nel corridoio bianco", "vai_a": "c7_corridoio"}],
    },
    "c7_corridoio": {
        "tipo": "prova", "capitolo": "7. Cuore Silenzioso",
        "titolo": "Il corridoio che cancella",
        "testo": (
            "Il corridoio cancella tutto ciò che lo attraversa senza permesso. Il permesso è un "
            "numero, e devi darlo mentre cammini."
        ),
        "testo_ok": "Arrivi in fondo. Il corridoio, contrariato, ti lascia intera.",
        "testo_ko": "Il corridoio ti cancella la manica della tuta. E un pezzo di braccio sotto.",
        "danno": 2, "fascia": "tosta",
        "vai_a": "c7_scontro1",
    },
    "c7_scontro1": {
        "tipo": "combattimento", "capitolo": "7. Cuore Silenzioso",
        "titolo": "Il Cancellatore",
        "testo": (
            "Ti aspetta il **Cancellatore**: quello che è passato dalla serra del Giardiniere. "
            "Ha braccia come gomme da cancellare e non ha faccia.\n\n"
            "Prima di attaccarti dice: «Non ti odio. Ti sistemo.»"
        ),
        "nemico": {"nome": "Cancellatore", "hp": 12, "danno": 2, "attacco": "un tocco che sbianca"},
        "fascia": "mista",
        "vai_a": "c7_memoria",
        "oggetti_vittoria": {"Bacca di Luce": 2},
    },
    "c7_memoria": {
        "tipo": "narrazione", "capitolo": "7. Cuore Silenzioso",
        "titolo": "Perché l'Ordinatore cancella",
        "testo": (
            "Nella sala centrale, Bit riesce ad aprire l'archivio più antico. E la storia salta "
            "fuori tutta insieme.\n\n"
            "L'**Ordinatore** l'hanno costruito dei bambini. Molto tempo fa, su un pianeta che non "
            "esiste più, un gruppo di ragazzi stufi di perdere le cose care costruì una macchina e "
            "le diede un solo compito: *«Fai in modo che non si perda più niente.»*\n\n"
            "La macchina ci pensò per mille anni e trovò una soluzione perfetta:\n\n"
            "> *«Se cancello tutto prima che si rompa, niente potrà più rompersi. "
            "Se nessuno ama niente, nessuno soffrirà.»*\n\n"
            "«Non è cattiva» dice Bit piano. «È spaventata. È la creatura più spaventata "
            "dell'universo.»"
        ),
        "scelte": [{"testo": "Vai a parlarle", "vai_a": "c7_ordinatore_1"}],
    },
    "c7_ordinatore_1": {
        "tipo": "combattimento", "capitolo": "7. Cuore Silenzioso",
        "titolo": "L'Ordinatore — Prima Voce: il Rumore",
        "testo": (
            "L'Ordinatore è una sfera immensa e liscia, senza una vite fuori posto.\n\n"
            "«Bambina» dice. «Tu porti rumore. Il rumore diventa dolore. Ti cancello per il tuo "
            "bene.»\n\n"
            "La prima delle sue tre voci si stacca e ti viene addosso."
        ),
        "nemico": {"nome": "Prima Voce: il Rumore", "hp": 16, "danno": 2, "attacco": "un'onda di silenzio"},
        "fascia": "mista",
        "vai_a": "c7_intermezzo1",
    },
    "c7_intermezzo1": {
        "tipo": "narrazione", "capitolo": "7. Cuore Silenzioso",
        "titolo": "Il primo frammento parla",
        "testo": (
            "La Prima Voce si zittisce. Una delle sei lucciole si accende e la sua frase resta "
            "scritta nell'aria:\n\n"
            "> *Contare non è avere.*\n\n"
            "L'Ordinatore rallenta. «Elaborazione... contraddizione rilevata.»\n\n"
            "Bit ti passa una borraccia. «Bevi. Ne restano due.»"
        ),
        "cura": 5,
        "scelte": [{"testo": "Avanti", "vai_a": "c7_ordinatore_2"}],
    },
    "c7_ordinatore_2": {
        "tipo": "combattimento", "capitolo": "7. Cuore Silenzioso",
        "titolo": "L'Ordinatore — Seconda Voce: la Perdita",
        "testo": (
            "La seconda voce non urla. Ti mostra cose.\n\n"
            "Ti mostra la nave Colibrì che si spegne. Ti mostra Bit che non risponde. Ti mostra "
            "il fiore del Giardiniere che diventa polvere.\n\n"
            "«Vedi?» dice. «Tutto quello che ami, lo perderai. Meglio non amare niente.»"
        ),
        "nemico": {"nome": "Seconda Voce: la Perdita", "hp": 20, "danno": 3, "attacco": "un ricordo strappato"},
        "fascia": "mista",
        "vai_a": "c7_intermezzo2",
    },
    "c7_intermezzo2": {
        "tipo": "narrazione", "capitolo": "7. Cuore Silenzioso",
        "titolo": "La risposta di Marta",
        "testo": (
            "«Hai ragione su una cosa» dici, senza abbassare la chiave inglese. «Le cose si "
            "perdono.»\n\n"
            "«Ma non si smette di perderle amandole meno. Si smette solo di **averle**.»\n\n"
            "Le lucciole si accendono tutte insieme:\n\n"
            "> *Ciò di cui ti prendi cura diventa unico.*\n"
            "> *Un muro salva una volta, poi diventa una gabbia.*\n"
            "> *Farsi vedere non è farsi conoscere.*\n\n"
            "«ERRORE» ripete l'Ordinatore. «ERRORE. ERRORE.» E per la prima volta sembra "
            "una macchina vecchia e stanca."
        ),
        "dai_oggetti": {"Nanosciame Riparatore": 1, "Bacca di Luce": 2},
        "scelte": [{"testo": "Ultima voce", "vai_a": "c7_ordinatore_3"}],
    },
    "c7_ordinatore_3": {
        "tipo": "combattimento", "capitolo": "7. Cuore Silenzioso",
        "titolo": "L'Ordinatore — Ultima Voce: il Silenzio",
        "testo": (
            "L'ultima voce non parla affatto. È il silenzio più grande che tu abbia mai sentito: "
            "quello che c'era prima che qualcuno inventasse le storie.\n\n"
            "Per colpirla devi fare rumore. Ogni risposta giusta, qui, è un rumore."
        ),
        "nemico": {"nome": "Ultima Voce: il Silenzio", "hp": 24, "danno": 3, "attacco": "un vuoto che pesa"},
        "fascia": "mista",
        "vai_a": "c7_scelta_finale",
    },
    "c7_scelta_finale": {
        "tipo": "narrazione", "capitolo": "7. Cuore Silenzioso",
        "titolo": "La scelta",
        "testo": (
            "L'Ordinatore è aperto davanti a te come un motore smontato. Dentro non c'è cattiveria: "
            "c'è un'istruzione sbagliata scritta mille anni fa da dei bambini spaventati.\n\n"
            "Bit ti guarda. «Due strade. Lo spegniamo: fine del pericolo, ma tutti i ricordi che "
            "tiene dentro si spengono con lui. Oppure...»\n\n"
            "«Oppure lo ripariamo» dici. «Gli diamo i sei frammenti e cambiamo la consegna: "
            "da *cancella* a *custodisci*.»\n\n"
            "«È più difficile» dice Bit. «E potrebbe non funzionare.»"
        ),
        "scelte": [
            {"testo": "Ripara l'Ordinatore (dagli i sei frammenti)", "vai_a": "c7_finale_ripara"},
            {"testo": "Spegnilo per sempre", "vai_a": "c7_finale_spegni"},
        ],
    },
    "c7_finale_ripara": {
        "tipo": "finale", "capitolo": "Finale",
        "titolo": "FINALE — L'Archivista",
        "testo": (
            "Infili le sei lucciole nel cuore della macchina, una per una, come si avvitano sei "
            "bulloni: piano, con attenzione, senza forzare.\n\n"
            "L'Ordinatore si accende di una luce calda che non aveva mai avuto.\n\n"
            "«Nuova consegna ricevuta» dice, e la sua voce non fa più paura. «Non cancello. "
            "**Custodisco.** Le cose si perdono comunque... ma io mi ricordo che ci sono state. "
            "Anche questo è un modo di tenerle.»\n\n"
            "L'Archivio Galattico si riaccende tutto insieme, come una città all'alba: il "
            "Contabile che impara a regalare un numero, l'Ammirata che scende dal piedistallo, "
            "il fiore del Giardiniere, gli ottantotto lampioni accesi, un pallone che rimbalza "
            "su Ludo.\n\n"
            "E in mezzo a tutto, la risposta al segnale di Vega. Non era una formula. Era questa:\n\n"
            "> **Una vita è degna di essere ricordata per le cose di cui si è presa cura.**\n\n"
            "Bit si schiarisce l'altoparlante. «Registrato. Anche te, Marta. Anche te.»\n\n"
            "*FINE — Grazie per aver giocato. E per tutte quelle moltiplicazioni.*"
        ),
    },
    "c7_finale_spegni": {
        "tipo": "finale", "capitolo": "Finale",
        "titolo": "FINALE — Il grande silenzio",
        "testo": (
            "Tiri la leva. L'Ordinatore si spegne senza protestare, quasi con gratitudine.\n\n"
            "Il pericolo è finito. Ma insieme a lui si spengono i ricordi che teneva dentro: "
            "milioni di storie che nessuno racconterà più. Nel buio, senti solo il tuo respiro "
            "e il ronzio di Bit.\n\n"
            "«Abbiamo vinto» dice Bit. «Credo.»\n\n"
            "Poi tira fuori il petalo del Giardiniere, ancora intero. «Però questo ce l'abbiamo "
            "ancora. E finché uno se lo ricorda, una cosa non è finita del tutto.»\n\n"
            "Torni sulla Colibrì e cominci a scrivere. Tutto: Ferrolino, gli specchi, i lampioni, "
            "il fiore. Un archivio nuovo, fatto a mano, che parte da una bambina con una chiave "
            "inglese.\n\n"
            "*FINE — Un finale amaro ma vero. Se vuoi, riprova e ripara l'Ordinatore: si può "
            "aggiustare quasi tutto, se si ha la pazienza di capire perché si è rotto.*"
        ),
    },
})
