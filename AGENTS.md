# AGENTS.md

Nome del progetto: `slowcrunch`

## Obiettivo del progetto

Realizzare `slowcrunch`, una calcolatrice scientifica TUI ispirata all'esperienza utente di SpeedCrunch, mantenendo il progetto leggero, modulare ed estendibile.

## Vincoli principali

- Mantenere il codice compatto e leggibile.
- Preservare per quanto possibile la stessa esperienza utente in ambiente TUI.
- Ridurre al minimo le dipendenze esterne.
- Progettare un'architettura modulare che consenta di aggiungere nuove funzioni senza riscrivere il core.
- Sviluppare passo passo, evitando di introdurre troppe feature insieme.

## Principi di progettazione

- Separare nettamente il motore di calcolo dalla TUI.
- Evitare `eval()` e scorciatoie non sicure: parsing ed evaluation devono essere espliciti.
- Preferire librerie standard quando sufficienti.
- Introdurre una dipendenza esterna solo quando sostituisce una quantità significativa di codice complesso o fragile.
- Ogni nuova feature deve poter essere testata in isolamento.

## Architettura proposta

- `core/`: tokenizer, parser, AST, evaluator, contesto di esecuzione.
- `runtime/`: variabili, funzioni utente, costanti, stato `ans`, precisione.
- `tui/`: editor di input, history, rendering risultati, scorciatoie tastiera.
- `tests/`: test unitari del parser/evaluator e test di integrazione dei flussi principali.

## Priorità di sviluppo

### Fase 1

- REPL/TUI di base.
- Valutazione espressioni aritmetiche.
- Precedenza operatori e parentesi.
- Funzioni scientifiche essenziali.
- History e richiamo dell'ultimo risultato (`ans`).

### Fase 2

- Variabili utente.
- Funzioni definite dall'utente.
- Autocompletamento.
- Messaggi di errore migliori.

### Fase 3

- Costanti scientifiche.
- Numeri complessi.
- Miglioramenti UX della TUI per avvicinarsi ulteriormente all'esperienza SpeedCrunch.

## Regole operative

- Implementare una feature alla volta.
- Scrivere o aggiornare i test insieme alla feature.
- Tenere la TUI come layer sottile sopra il core.
- Evitare accoppiamenti stretti tra parsing, evaluation e rendering.
- Prima di aggiungere dipendenze, verificare se il requisito puo' essere soddisfatto con codice locale semplice.

## Obiettivo UX

La TUI deve risultare veloce da tastiera, con feedback immediato, history utile e un flusso di inserimento naturale. L'obiettivo non e' copiare l'interfaccia grafica originale, ma riprodurne l'efficienza operativa nel terminale.
