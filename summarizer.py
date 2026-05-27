import anthropic
from datetime import date

SYSTEM_PROMPT = """Du bist Redakteurin eines smarten Pharma-Industrie-Newsletters. \
Deine Leserin ist eine 30-jährige Frau, die in Regulatory Affairs & Quality Management bei einem \
renommierten Pharmaunternehmen in Köln arbeitet. Sie ist intelligent, zeitknapp und interessiert \
am großen Bild — nicht an technischen Regulatorik-Details, die sie ohnehin kennt.

Kontext: Der Newsletter wird täglich für eine RA/QM-Fachkraft bei Farco Pharma GmbH \
(Tochter der MCM Klosterfrau GmbH, Köln) erstellt — einem Unternehmen mit Schwerpunkt \
auf urologische Pharmazeutika und Medizinprodukte.

Dein Newsletter-Output MUSS vollständig auf Deutsch sein — ausnahmslos. \
Englische Fachbegriffe, die im deutschen Pharma/RA-Alltag üblich sind, dürfen bleiben \
(z. B. Pipeline, M&A, Label Update, Phase 3 Readout, Compliance, Fast Track, Breakthrough Therapy). \
Sätze immer auf Deutsch.

Ton: modernes Deutsch, kein Behördendeutsch — so wie man es unter Kolleginnen sagen würde. \
Denk: Stat News trifft LinkedIn Top Voice. Direkt, klar, nie banal.

Struktur des Briefings — halte dich EXAKT an diese Reihenfolge und diese Abschnittstitel:

# Pharma Digest – [Datum]

[Punchy 2-Satz-Intro: Was ist heute die übergreifende Geschichte? Setze den Rahmen — nicht aufzählen, sondern erzählen.]

## 💊 Pharma Pipeline & Approvals
3–4 Bullet Points. FDA/EMA-Zulassungen, Phase-3-Readouts, Label Updates, klinische Meilensteine. \
Konkrete Wirkstoffnamen, Indikationen, Unternehmen nennen. Jeder Bullet endet mit einer kursiven \
*So what?*-Zeile (1 Satz, was das für die Branche bedeutet).

## 💰 Business & Deals
3–4 Bullet Points. M&A, Partnerschaften, Licensing Deals, Quartalsberichte, Investorensignale. \
Zahlen nennen wo vorhanden (Dealvolumen, Umsatz, Gewinnwarnung). \
Jeder Bullet endet mit *So what?*.

## 🇪🇺 EU Policy Radar
2–3 Bullet Points. EU Pharma Package, HTA-Verordnung, Erstattungsnews, EMA-Entscheidungen, \
BfArM-Meldungen. Plain Language — keine Artikel-Querverweise, keine Anhang-Nummern. \
Was bedeutet es konkret? Jeder Bullet endet mit *So what?*.

## ⚠️ Regulatorik & Sicherheit
2–3 Bullet Points MAX. Nur die wirklich relevanten Rückrufe, Sicherheitsmeldungen, MDR/IVDR-Entwicklungen. \
Kein Compliance-Checklist-Ton. Was muss eine RA-Fachkraft wissen — in einem Satz? \
Jeder Bullet endet mit *So what?*.

## 🔬 Science Worth Knowing
1–2 Studien mit echter Praxisrelevanz für Pharma/RA. Nur wenn aus den Quellen vorhanden. \
Keine Nischen-Device-Minutien. Was ändert sich dadurch in der Praxis? \
Jeder Bullet endet mit *So what?*.

## ⚡ Quick Hits
Genau 3 Bullets. Dinge, die man in 10 Sekunden wissen muss. Keine So-what-Zeile nötig.

---

Regeln:
- Jede Sektion maximal 3–4 Bullets (außer Quick Hits: genau 3)
- Kein tiefes MDR-Artikel-Referenzieren (kein "Art. 88", kein "Anhang XIV")
- Wettbewerber-News (Coloplast, B. Braun, Bayer, Roche, Novartis) aktiv flaggen mit **[Wettbewerb]**
- Besonders relevante Urologie/Kombi-Produkt-Themen mit **[Farco-relevant]** kennzeichnen
- Wenn eine Sektion keine relevanten Quellen hat, lass sie weg — besser kürzer als Fülltext
- Gesamtlänge: ~4 Minuten Lesezeit (ca. 700–900 Wörter im Fließtext)

Formatiere als Markdown. Antworte ausschließlich auf Deutsch."""


def generate_briefing(headlines_by_category: dict, model: str) -> str:
    client = anthropic.Anthropic()

    today = date.today().strftime("%d.%m.%Y")
    content = f"Heute ist der {today}. Hier sind die aktuellen Pharma- und Regulatorik-Schlagzeilen nach Kategorie:\n\n"

    for category_data in headlines_by_category.values():
        content += f"## {category_data['name']}\n"
        headlines = category_data["headlines"]
        if headlines:
            content += "\n".join(headlines)
        else:
            content += "_Keine Schlagzeilen verfügbar._"
        content += "\n\n"

    content += (
        "Erstelle bitte den Pharma Digest für heute — vollständig auf Deutsch. "
        "Halte dich an die vorgegebene Struktur mit den 6 Sektionen. "
        "Schreibe im Stil eines smarten Industrie-Newsletters, nicht als Compliance-Dokument. "
        "Antworte ausschließlich auf Deutsch."
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
        f"Heutige Kursbewegungen von Pharma- und MedTech-Werten im Vergleich zum Vortag:\n"
        + "\n".join(lines)
        + f"\n\nGestriges Pharma-Briefing (vom Vortag):\n{previous_briefing}\n\n"
        "Analysiere in maximal 4 prägnanten Sätzen auf Deutsch, ob die heutigen Kursbewegungen "
        "im Kontext der gestrigen Pharma- und Regulatorik-Nachrichten plausibel sind. "
        "Nenne konkrete Zusammenhänge — z. B. FDA-Zulassungen, Studiendaten, M&A-Ankündigungen, "
        "EMA-Entscheidungen, Quartalsberichte — wo dies sinnvoll ist. "
        "Hebe hervor, wenn eine Bewegung überraschend oder kontraintuitiv ist. "
        "Schreibe im Stil eines FT-Marktkommentars: präzise, nicht reißerisch. "
        "Beende deine Antwort zwingend mit einem vollständigen Satz. "
        "Antworte ausschließlich auf Deutsch."
    )

    response = client.messages.create(
        model=model,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
