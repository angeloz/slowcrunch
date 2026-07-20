"""Piccola calcolatrice da terminale con quattro operazioni base."""


def somma(a, b):
    return a + b


def sottrai(a, b):
    return a - b


def moltiplica(a, b):
    return a * b


def dividi(a, b):
    if b == 0:
        raise ValueError("Non e' possibile dividere per zero.")
    return a / b


def main():
    print("Calcolatrice semplice")
    primo_numero = float(input("Inserisci il primo numero: "))
    secondo_numero = float(input("Inserisci il secondo numero: "))
    operazione = input("Scegli l'operazione (+, -, *, /): ").strip()

    operazioni = {
        "+": somma,
        "-": sottrai,
        "*": moltiplica,
        "/": dividi,
    }

    if operazione not in operazioni:
        print("Operazione non valida.")
        return

    try:
        risultato = operazioni[operazione](primo_numero, secondo_numero)
    except ValueError as errore:
        print(errore)
        return

    print(f"Risultato: {risultato}")


if __name__ == "__main__":
    main()
