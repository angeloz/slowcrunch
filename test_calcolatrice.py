import unittest

from calcolatrice import dividi, moltiplica, somma, sottrai


class CalcolatriceTest(unittest.TestCase):
    def test_somma(self):
        self.assertEqual(somma(2, 3), 5)

    def test_sottrazione(self):
        self.assertEqual(sottrai(10, 4), 6)

    def test_moltiplicazione(self):
        self.assertEqual(moltiplica(6, 7), 42)

    def test_divisione(self):
        self.assertEqual(dividi(8, 2), 4)

    def test_divisione_per_zero(self):
        with self.assertRaises(ValueError):
            dividi(5, 0)


if __name__ == "__main__":
    unittest.main()
