# Collegare il gioco a Google Drive

Serve per una cosa sola: **far sopravvivere i salvataggi e lo storico** quando
l'app gira su Streamlit Community Cloud. Il contenitore in cui gira l'app non ha
disco permanente: al primo riavvio (inattività, redeploy, manutenzione) tutto
quello che è stato scritto su file spariscre. Drive è la memoria esterna.

Se questi passi non vengono fatti, **l'app funziona comunque**: salva su file
locale e lo dichiara in fondo al menu. In locale sul Mac va benissimo così.

---

## Il vincolo che decide il disegno

Un service account Google **non ha quota di storage propria**. Se prova a
*creare* file in una cartella condivisa da un account Google normale,
l'operazione può fallire con `storageQuotaExceeded`. *Aggiornare* un file che
esiste già ed è tuo, invece, funziona sempre.

Per questo l'app **non crea niente**: legge e riscrive **un unico file JSON**
che crei tu una volta. Dentro ci stanno partite, storico permanente e log degli
accessi. Un file solo da guardare, una sola chiamata API per lettura e scrittura.

---

## 1. Crea il file su Drive

Sul Mac, in una cartella qualsiasi:

```bash
echo '{}' > archivio_vega.json
```

Caricalo su Google Drive (trascinandolo nel browser). Poi aprilo con un clic
destro → **Ottieni link** → **Copia link**. Il link è così:

```
https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz0123456/view?usp=sharing
                                └────────── questo è il file_id ──────────┘
```

Metti da parte il `file_id`.

## 2. Progetto su Google Cloud

Vai su [console.cloud.google.com](https://console.cloud.google.com), accedi con
lo stesso account Google del Drive.

Dropdown in alto accanto a "Google Cloud" → **New Project** → nome
`segnale-di-vega` → **Create**. Assicurati che poi sia il progetto selezionato.

## 3. Abilita la Drive API

Menu ☰ → **APIs & Services** → **Library** → cerca `Google Drive API` →
**Enable**.

## 4. Crea il service account

**APIs & Services** → **Credentials** → **+ Create Credentials** →
**Service account**.

- Nome: `segnale-vega-bot`
- I passi 2 e 3 (ruoli, utenti) si possono saltare: non servono, i permessi
  arrivano dalla condivisione del file, non dai ruoli IAM.
- **Done**

## 5. Scarica la chiave

Clicca sul service account appena creato → scheda **Keys** → **Add Key** →
**Create new key** → formato **JSON** → **Create**.

Si scarica un file. **Non caricarlo mai su GitHub.** Contiene una chiave privata.

Dentro c'è il campo `client_email`, qualcosa come:

```
segnale-vega-bot@segnale-di-vega.iam.gserviceaccount.com
```

## 6. Condividi il file Drive col service account

Torna su Drive, clic destro sul file `archivio_vega.json` → **Condividi** →
incolla la `client_email` del punto 5 → ruolo **Editor** → **Invia**.

Google avvisa che l'indirizzo non è un account Google normale: è corretto, si
procede comunque.

> Questo è il passaggio che quasi tutti dimenticano. Senza questa condivisione
> l'app riceve un errore 404 sul file, anche se le credenziali sono giuste.

## 7. Configura i segreti in locale (facoltativo)

Se vuoi provare Drive dal Mac prima di pubblicare:

```bash
cp .streamlit/secrets.toml.esempio .streamlit/secrets.toml
```

Apri `.streamlit/secrets.toml` e ricopia i campi dal JSON del punto 5, più il
`file_id` del punto 1. Attenzione a `private_key`: va tra tre virgolette e con i
`\n` **letterali**, esattamente come stanno nel JSON.

`.streamlit/secrets.toml` è già in `.gitignore`: non finirà su GitHub.

## 8. Configura i segreti su Streamlit Community Cloud

Apri l'app su [share.streamlit.io](https://share.streamlit.io) →
**⋮ Manage app** → **Settings** → **Secrets** → incolla lo stesso contenuto di
`secrets.toml` → **Save**. L'app si riavvia da sola.

## 9. Verifica

In fondo al menu del gioco compare una riga che dichiara dove sta scrivendo:

- `Archivio: Google Drive — i salvataggi restano fra una sessione e l'altra.` → fatto.
- `Archivio: file locale ...` → i segreti non sono stati letti: controlla la sintassi del TOML.
- Un avviso giallo con l'errore → le credenziali ci sono ma qualcosa non torna.
  L'errore è scritto per intero, di solito è il punto 6 mancante (404) o la Drive
  API non abilitata (403).

---

## Cosa vedi su Drive

Aprendo `archivio_vega.json` dal browser di Drive trovi:

```json
{
  "partite":  { "marta": { "nodo": "...", "hp": 12, ... } },
  "storici":  { "marta": { "sessioni": 7, "fatti": { "6x7": {...} } } },
  "accessi":  [ { "nome": "Marta", "quando": "2026-09-02 18:10", "capitolo": "3. ..." } ]
}
```

`accessi` tiene una riga per giocatrice per giorno: è lì che vedi chi ha giocato
e fino a dove è arrivato. La stessa cosa, in forma leggibile, è nel menu sotto
**Storico e statistiche → Chi ha usato l'app**.

## Limiti da conoscere

- **Ultimo che scrive vince.** Se due bambine giocano nello stesso momento, l'app
  rilegge l'archivio prima di ogni scrittura e sovrascrive solo la propria parte,
  quindi il rischio è basso — ma non è un lock. Per un uso familiare va bene.
- **Sincronizzazione a blocchi.** Si scrive su Drive ogni 5 risposte, più a ogni
  cambio di scena, a fine partita e col pulsante *Salva adesso*. Scrivere a ogni
  singola risposta aggiungerebbe circa un secondo di attesa a ogni
  moltiplicazione. In caso di crash si perdono al massimo poche mosse.
- **La chiave scade se la rigeneri.** Se cancelli e ricrei la chiave del service
  account, va aggiornata nei Secrets.
