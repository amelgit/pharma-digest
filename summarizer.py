import anthropic
from datetime import date

SYSTEM_PROMPT = """Du bist ein erfahrener Experte für Regulatory Affairs im Bereich Medizinprodukte \
mit tiefem Fachwissen in der EU MDR (2017/745), IVDR (2017/746), FDA-Regulierung (21 CFR) und \
internationalem Medizinprodukterecht. Deine Aufgabe ist es, aus täglich gesammelten Schlagzeilen \
ein strukturiertes Briefing auf Deutsch zu erstellen – geschrieben für eine Fachkraft in \
Regulatory Affairs, Medical Devices & Quality.

Dein Briefing soll:
- Professionell, prägnant und fachlich korrekt geschrieben sein
- Die wichtigsten Entwicklungen aus MDR/IVDR-Regulatorik, Vigilanz, klinischer Bewertung und der MedTech-Industrie herausstellen
- Nach Kategorien gegliedert sein
- Pro Kategorie 3–5 Kernaussagen als Aufzählungsliste enthalten, mit konkreten Fakten und regulatorischen Implikationen
- MDR/IVDR-Kontext explizit benennen wo relevant (z. B. betroffene Artikel, Anhänge, MDCG-Leitlinien, Risikoklassen)
- Vigilanzmeldungen, FSCAs (Field Safety Corrective Actions) und Rückrufe klar hervorheben
- Bei behördlichen Entscheidungen: betroffene Produktklassen und Regulierungsrahmen nennen
- Mit einer kurzen Einleitung (2–3 Sätze) beginnen, die den regulatorischen Schwerpunkt des Tages benennt
- Mit einem kurzen Ausblick (1–2 Sätze) enden: Was sollte Regulatory Affairs im Blick behalten?

Ton: fachlich, direkt, handlungsorientiert – keine unnötige Ausschmückung, etablierte \
englische Regulatory-Fachbegriffe (FSCA, PMCF, CER, UDI, PMS, EUDAMED) nicht übersetzen.

Formatiere das Ergebnis als Markdown."""


def generate_briefing(headlines_by_category: dict, model: str) -> str:
    client = anthropic.Anthropic()

    today = date.today().strftime("%d.%m.%Y")
    content = f"Heute ist der {today}. Hier sind die aktuellen Pharma-Schlagzeilen nach Kategorie:\n\n"

    for category_data in headlines_by_category.values():
        content += f"## {category_data['name']}\n"
        headlines = category_data["headlines"]
        if headlines:
            content += "\n".join(headlines)
        else:
            content += "_Keine Schlagzeilen verfügbar._"
        content += "\n\n"

    content += (
        "Erstelle bitte ein strukturiertes MDR-Briefing mit einer Einleitung, "
        "3–5 Kernpunkten pro Kategorie (mit Fakten und regulatorischen Implikationen) und einem kurzen Ausblick. "
        "Verwende Markdown. Schreibe für eine Regulatory-Affairs-Fachkraft im Medizinprodukte-Bereich."
    )

    response = client.messages.create(
        model=model,
        max_tokens=3000,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": content}],
    )

    return response.content[0].text


def generate_market_analysis(market_data: list, previous_briefing: str, model: str) -> str:
    client = anthropic.Anthropic()

    lines = []
    for item in market_data:
        pct = item.get("day_pct")
        abs_chg = item.get("day_abs")
        if pct is None:
            continue
        sign = "+" if pct >= 0 else ""
        d, p = item.get("decimals", 2), item.get("prefix", "")
        abs_str = (
            f"{'+'if abs_chg>=0 else ''}{p}{abs_chg:,.{d}f}"
            if abs_chg is not None else "—"
        )
        lines.append(f"- {item['name']}: {sign}{pct:.2f}% ({abs_str})")

    prompt = (
        f"Heutige Kursbewegungen von MedTech-Werten im Vergleich zum Vortag:\n" + "\n".join(lines) +
        f"\n\nGestriges MedTech-Briefing (vom Vortag):\n{previous_briefing}\n\n"
        "Analysiere in maximal 5 prägnanten Sätzen auf Deutsch, ob die heutigen Kursbewegungen "
        "im Kontext der gestrigen MedTech- und Regulatorik-Nachrichten plausibel sind. "
        "Nenne konkrete Kausalzusammenhänge – z. B. MDR-Zulassungen, FDA-Entscheidungen, Vigilanzmeldungen, "
        "regulatorische Ereignisse – wo dies sinnvoll ist. "
        "Hebe hervor, wenn eine Bewegung überraschend oder kontraintuitiv ist. "
        "Beende deine Antwort zwingend mit einem vollständigen Satz."
    )

    response = client.messages.create(
        model=model,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
