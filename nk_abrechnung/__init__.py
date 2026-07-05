"""NK-Abrechnungsprogramm – Teinacher Str. 4, 75387 Neubulach.

Nebenkosten- und Eigentümer-Abrechnung für ein Zweifamilienhaus mit
Wärmepumpe, getrennter Zähler-Erfassung (WP-Strom, Haushaltsstrom UV,
Wärmemengenzähler, Kalt- und Warmwasser) und mehreren Mietperioden.

Die Ergebnisse werden vollständig aus den Roh-Zählerständen und den
Kostenparametern berechnet (siehe ``engine``) und reproduzieren die im
Projekt dokumentierten Abrechnungssummen.
"""

from .config import OBJEKT

__all__ = ["OBJEKT"]
__version__ = "1.0.0"
