# Finance Cruscotto

App Streamlit ricavata dai sette notebook dell'autore. Integra 30 titoli e le sezioni IG, mm e za. Non richiede Colab, montaggio Drive o esecuzione di notebook.

## Avvio

Usare Python 3.12. Installare `pip install -r requirements.txt`, poi avviare `streamlit run app.py`.

## Pubblicazione

Caricare i file della cartella in un repository GitHub e selezionare `app.py` come file principale su Streamlit Community Cloud. Non includere dati personali o credenziali. Nessuna pubblicazione è stata effettuata durante la creazione del progetto.

## Numerazione e modifica dei titoli

La colonna `N.` identifica la posizione del titolo nell’anagrafica, anche nelle viste filtrate e nel CSV. I numeri vengono ricalcolati dopo aggiunte e cancellazioni.

Attivare **Modifica anagrafica** nella barra laterale: la tabella consente di cambiare ISIN, nome, banca, valuta e ticker Yahoo. Per aggiungere una voce usare la riga vuota in fondo; per cancellare una o più voci scegliere **Titoli da eliminare** sotto la tabella e premere **Elimina titoli selezionati**. Il pulsante salva subito la cancellazione e le altre modifiche della tabella. Premere **Salva anagrafica** per applicare le modifiche. Occorrono banca, nome, valuta e almeno un ISIN o un ticker. Gli ISIN vengono normalizzati in maiuscolo e controllati nel formato; il controllo non certifica l’identità o la disponibilità dello strumento.

Il salvataggio sostituisce atomicamente `titoli.json` sul server e azzera il report precedente. Quando cambia un ISIN, il vecchio link viene rimosso e il ticker precedente viene cancellato, salvo che sia stato sostituito nello stesso intervento. Questo evita il recupero dei prezzi della vecchia classe. Dopo il salvataggio tornare alla vista principale e aggiornare le quotazioni.

Nella barra laterale, **Salva JSON sul PC** esporta l’ultima versione salvata: se la tabella contiene modifiche, premere prima **Salva anagrafica**. Per ripristinare un backup, scegliere **Carica JSON dal PC** e premere **Applica JSON caricato**. Il file viene validato prima di sostituire tutta l’anagrafica sul server; un file non valido lascia intatti i dati esistenti. Il caricamento elimina il report precedente e le modifiche non salvate nell’editor. Il JSON contiene l’anagrafica, senza le quotazioni, e resta compatibile con `titoli.json`.

Su Streamlit Community Cloud o altri hosting con disco temporaneo, le modifiche locali possono andare perse al riavvio o al deploy: conservare il JSON sul PC per ricaricarlo, oppure aggiornare il file nel repository per renderle permanenti tra i deploy. L’anagrafica del server è condivisa tra gli utenti. L’editor non pubblica modifiche su GitHub.

## Comportamento

Il pulsante Aggiorna prova prima l'eventuale ticker Yahoo configurato, poi ricerca il fondo per ISIN su Yahoo e FT Markets, per tutte le banche. Per mm e IG, Morningstar resta l'ultimo tentativo quando Yahoo e FT non restituiscono uno storico. La banca non limita più l'accesso alla ricerca per ISIN Yahoo/FT. La disponibilità dei fornitori e la correttezza dei ticker/classi devono essere verificate dal server di destinazione: il ticker configurato non è automaticamente confrontato con l'ISIN. Le date delle quotazioni sono visibili. Il riferimento di inizio anno è l'ultimo prezzo disponibile entro il 1 gennaio, senza utilizzare prezzi successivi alla data richiesta. Non vengono applicate le modifiche manuali dimostrative del notebook originario.

Le quantità sono convenzionalmente uno. Non vengono mostrate somme patrimoniali: prezzi con valute o convenzioni diverse non rappresentano un portafoglio confrontabile. La variazione è sul prezzo, senza cedole/distribuzioni. La media per banca è aritmetica e riguarda solo titoli con dati disponibili.

I titoli senza storico o ticker utilizzabile restano N/D. Il riquadro **Motivi dei dati mancanti** mostra gli identificativi malformati e i tentativi senza risultati. Un ISIN deve avere 12 caratteri; questo controllo non ne certifica l'identità. Le voci riconosciute come obbligazioni o certificati dal link Borsa Italiana, oppure dal campo opzionale `type` (`bond` o `certificate`), non vengono inviate ai servizi per fondi: serve un ticker Yahoo verificato o una fonte dedicata. I link sono conservati per controllo manuale; lo scraping generico del notebook è stato escluso perché potrebbe riconoscere numeri che non sono prezzi. Non sono stati inventati prezzi.

Nelle tabelle di consultazione ogni ISIN è cliccabile e apre la pagina informativa configurata nell'anagrafica (Borsa Italiana per i titoli quotati disponibili, FT Markets per i fondi). Il CSV conserva invece l'ISIN puro. Le schede restano ordinate `Tutti`, `IG`, `mm`, `za`; nel grafico complessivo i titoli sono disposti per banca nell'ordine `za`, `mm`, `IG`.

## Verifiche

Il progetto include controlli sulla normalizzazione dello storico, sulle date e sui dati mancanti. Le quotazioni live e il deployment Streamlit devono essere verificati nell'ambiente di destinazione.

Verifica effettuata: avvio con Streamlit AppTest, 25 titoli presenti e nessuna eccezione iniziale. Una richiesta reale Yahoo ha restituito un limite di richieste (HTTP 429); nessuna quotazione aggiornata è stata confermata.

## Verifica del 3 ottobre 2026
Corretto il parametro session di mstarpy: richiede una MorningstarSession, non una requests.Session generica. La prova reale su Pictet Security fallisce ora all’avvio di Chrome richiesto da mstarpy. Yahoo restituisce HTTP 429. Nessuna quotazione è stata recuperata; il deploy Streamlit non è verificato.

## Aggiornamento za del 31 ottobre 2026

La sezione za contiene i 12 fondi con nomi e ISIN forniti dall'autore. Le sezioni IG e mm restano invariate. Tutte le viste, i grafici e il CSV usano la stessa anagrafica `titoli.json`. Gli ISIN sono visibili anche prima del recupero delle quotazioni. I ticker Yahoo precedenti di za sono rimossi: non sono stati verificati per le classi indicate. Il recupero di za avviene per ISIN tramite Yahoo e FT; in caso di indisponibilità i valori restano N/D.

## Metodo Untitled64 (31 ottobre 2026)

`fund_sources.py` riprende Yahoo Search e lo storico FT dal notebook Untitled64. Le date sono dinamiche, la valuta FT segue l’anagrafica, e za non avvia più mstarpy/Chrome. Sei test superati; prova live: 11 quotazioni za su 12, BGF World Tech LU0376438312 N/D, come nell’esecuzione salvata di Untitled64.

`Finance_Cruscotto.ipynb` scarica gli stessi moduli e la stessa anagrafica da questo repository. Non esegue più i vecchi notebook concatenati che interrompevano l’avvio. Produce una lista di osservazione senza quantità patrimoniali; i file quantità originali rimangono separati. I vecchi output sono rimossi per evitare di confonderli con nuove quotazioni.
