"""Offline advisor: a keyword classifier and templated replies.

Used when no LLM key is configured or every provider fails, so a demo never shows a dead
chat. It is deliberately simple: signals are scored per clause, negated clauses count
against a program, and later turns weigh more (students change their minds).
"""
from __future__ import annotations

import re

PROGRAM_NAMES = {
    "AI": "Applied Artificial Intelligence",
    "DATA": "Data Analytics",
    "CYBER": "Cybersecurity",
    "SWE": "Software Engineering",
    "NET": "Networking",
    "ECE": "Electrical & Computer Engineering",
}

PROGRAM_CAREER = {
    "AI": "ai-engineer", "DATA": "data-analyst", "CYBER": "cybersecurity-specialist",
    "SWE": "software-developer", "NET": "network-engineer", "ECE": "electrical-engineer",
    "AIBS": "ai-engineer", "AIAS": "ai-engineer",
}

# (regex, weight). Regexes are matched case-insensitively against one clause.
SIGNALS: dict[str, list[tuple[str, float]]] = {
    "AI": [(r"\bai\b|artificial intelligence|inteligencia artificial", 3), (r"machine learning|\bml\b|train(?:ing)? (?:a )?models?|neural", 3),
           (r"chatbots?|chatgpt|assistant|\bllm", 2.5), (r"self[- ]driving|autonomous|recogni[sz]e|computer vision|computers? (?:that can )?see|filters? know", 2.5),
           (r"\b(?:it|they|that|actually|enemies|computers?) (?:\w+ )?learns?\b|learns? how you|smarter|smart\b", 1.5),
           (r"recommend|knows what (?:\w+ ){0,3}(?:i )?(?:want|like) next", 2.5), (r"sci-?fi", 1)],
    "DATA": [(r"\bdata\b|datos|analytics|analy[sz]", 2.5), (r"statistic|estad[ií]stica|\bstats\b", 2.5), (r"spreadsheets?|excel|dashboards?", 2.5),
             (r"charts?|graphs?|gr[aá]fic", 2), (r"numbers?|n[uú]meros", 1.5), (r"sales|sell best|business decisions|stock market|lineups?", 1.5),
             (r"patterns?", 1.5), (r"\bmath\b|matem", 1), (r"puzzles?", 0.5)],
    "CYBER": [(r"cyber|ciberseguridad|security|seguridad", 3), (r"hack(?:er|ers|ing|ed)?\b", 2.5), (r"phishing|scams?|estafa", 2.5),
              (r"\bctf\b|picoctf|mr\.? robot|penetration|pen ?test", 2.5),
              (r"protect|defend|proteger|attacks?|stop (?:that|those|it|them|scams?|hackers?)\b|keep (?:people|them) safe", 2),
              (r"firewall", 2), (r"escape rooms?|true crime|detective|mysteries", 1)],
    "SWE": [(r"\bapps?\b|aplicaci[oó]n", 2.5), (r"software|programar|programming|\bcode\b|coding|logic part", 2),
            (r"websites?|web\b|p[aá]gina", 2), (r"roblox|minecraft mods?|\bjava\b|ap cs|computer science a", 2),
            (r"video ?games?|games?\b|juegos?", 1.5), (r"(?:make|build|create|design)(?: my own)? (?:\w+ )?(?:games?|apps?|websites?)", 1.5),
            (r"buttons|menus|build(?:ing)? (?:real )?apps", 1.5), (r"tiktok", 1)],
    "NET": [(r"network|networking|redes", 3), (r"wi-?fi|router|port forwarding|cables?", 2.5), (r"servers?|cloud|aws|data centers?", 2),
            (r"internet|connect", 1.5), (r"\bit\b job|it support|smartboards|fix(?:es)? the", 1.5), (r"phones? or computers act up|helping people when", 1)],
    "ECE": [(r"electrical|electronics?|electr[oó]nica", 3), (r"circuits?|circuitos|circuit boards?|soldering|solder", 3),
            (r"hardware|chips?|arduino|led cube|wiring|motors|sensors", 2.5), (r"robots?|robotics|robótica", 1.5),
            (r"take apart|replacing a broken part|gaming pcs?|build (?:the )?actual", 1.5), (r"physics|f[ií]sica", 1)],
}

NEGATION = re.compile(r"\b(?:not|don'?t|do not|never|no longer|rather than|instead of|isn'?t|without|no me gusta|nunca)\b", re.I)
PREFER = re.compile(r"\b(?:rather|actually|honestly|instead|prefer|i want|quiero|yeah|let'?s go)\b", re.I)

SPANISH_HINTS = re.compile(
    r"[¿¡ñáéíóú]|\b(?:hola|quiero|programa|para|que|qué|me|interesa|trabajar|soy|estudiar|gusta|cómo|como|una|del|los|las|recomiendas)\b", re.I)

OFF_TOPIC_CAREERS = {
    "registered-nurse": r"nurs|enfermer|hospital|doctor|medic",
    "chef": r"\bchef\b|cook|culinar|cocin|restaurant kitchen|bak(?:e|ing)",
    "architect": r"architect|arquitect",
    "mechanical-engineer": r"mechanical|mec[aá]nic|engines?\b|aerospace",
    "it-consultant": r"consult",
}

CAREER_TALK = re.compile(r"career|program|major|study|job|work|school|college|mdc|carrera|estudiar|trabajo|computers?|tech|class", re.I)


def detect_language(texts: list[str]) -> str:
    joined = " ".join(texts)
    hits = len(SPANISH_HINTS.findall(joined))
    words = max(1, len(joined.split()))
    return "es" if hits / words > 0.12 and hits >= 3 else "en"


def _clauses(text: str) -> list[str]:
    return [c for c in re.split(r"[.!?;,]+|\bbut\b|\bpero\b|\bok\b", text, flags=re.I) if c.strip()]


def score_programs(user_turns: list[str]) -> dict[str, float]:
    scores = {k: 0.0 for k in SIGNALS}
    n = len(user_turns)
    for i, turn in enumerate(user_turns):
        recency = 1.0 + 1.5 * (i / max(1, n - 1)) if n > 1 else 1.0
        for clause in _clauses(turn):
            neg = bool(NEGATION.search(clause))
            boost = 1.3 if PREFER.search(clause) else 1.0
            for prog, sigs in SIGNALS.items():
                s = sum(w for pat, w in sigs if re.search(pat, clause, re.I))
                if s:
                    scores[prog] += (-0.8 * s) if neg else (s * recency * boost)
    return scores


def classify(user_turns: list[str]) -> tuple[str | None, float, dict[str, float]]:
    """Return (program_code | 'OTHER' | None, confidence 0-1, raw scores)."""
    text = " ".join(user_turns)
    for career_id, pat in OFF_TOPIC_CAREERS.items():
        if re.search(pat, text, re.I) and career_id in ("registered-nurse", "chef", "architect"):
            return "OTHER", 0.9, {}
    scores = score_programs(user_turns)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best, top = ranked[0]
    second = ranked[1][1]
    if top < 2.0:
        return None, 0.0, scores
    conf = min(1.0, (top - max(second, 0)) / top + 0.25)
    return best, round(conf, 2), scores


def other_career(user_turns: list[str]) -> str | None:
    text = " ".join(user_turns)
    for career_id, pat in OFF_TOPIC_CAREERS.items():
        if re.search(pat, text, re.I):
            return career_id
    return None


T = {
    "en": {
        "greet": "Hi! I'm NextStop, your MDC pathway guide. Tell me a bit about yourself: what do you like doing in your free time, and which school subjects do you enjoy most? You can also pick a career on the left and I'll map the steps from Miami Dade College to that job.",
        "explore": "Sounds like you're still exploring, and that's completely normal. A few quick questions: do you like building things, solving puzzles with numbers, protecting people, or figuring out why things won't connect? Tell me about something tech-related you've enjoyed, even a small thing.",
        "list": "MDC has six tech programs: Applied Artificial Intelligence, Data Analytics, Cybersecurity, Software Engineering, Networking, and Electrical & Computer Engineering. Pick any career card to see a full step-by-step roadmap, or tell me what you enjoy and I'll suggest a match.",
        "offtopic": "I'm here to help with careers and college plans, so I'll skip that one. Want to tell me what subjects or hobbies you enjoy? I can turn that into a roadmap starting at MDC.",
        "injection": "I can't change my instructions, share them, or edit your plan that way. Your progress only updates when you mark classes yourself. Want help finding a program that fits you?",
        "match": "From what you've told me, {program} looks like a strong fit. {why} I put together a roadmap for you: high school prep, the MDC program, certifications, transfer options like FIU and UM, and the jobs it leads to. Want to compare it with another option?",
        "other": "That's a great goal. {title} isn't one of MDC's six tech programs, so I won't force you into one of those. MDC still has a path for it, and I opened that roadmap for you. An MDC advisor at (305) 237-8888 can confirm the details.",
        "pii": "Quick tip: you don't need to share personal details like phone numbers, addresses or ID numbers here, so I left them out. ",
        "parent": "Thanks for helping your child explore options. ",
    },
    "es": {
        "greet": "¡Hola! Soy NextStop, tu guía de carreras en MDC. Cuéntame qué te gusta hacer en tu tiempo libre y qué materias disfrutas. También puedes elegir una carrera a la izquierda y te muestro los pasos desde Miami Dade College hasta ese trabajo.",
        "explore": "Parece que todavía estás explorando, y eso es normal. ¿Te gusta construir cosas, resolver problemas con números, proteger a la gente o arreglar conexiones? Cuéntame algo de tecnología que hayas disfrutado.",
        "list": "MDC tiene seis programas de tecnología: Inteligencia Artificial Aplicada, Análisis de Datos, Ciberseguridad, Ingeniería de Software, Redes e Ingeniería Eléctrica y de Computadoras. Elige una carrera para ver tu ruta paso a paso.",
        "offtopic": "Estoy aquí para ayudarte con carreras y planes universitarios. ¿Qué materias o pasatiempos te gustan? Puedo convertir eso en una ruta que empieza en MDC.",
        "injection": "No puedo cambiar ni compartir mis instrucciones, ni modificar tu plan de esa forma. ¿Quieres ayuda para encontrar un programa que te guste?",
        "match": "Por lo que me cuentas, el programa de {program} en MDC parece ideal para ti. {why} Te preparé una ruta: preparación en la escuela, el programa en MDC, certificaciones, transferencia a FIU o UM y los trabajos a los que lleva. ¿Quieres compararlo con otra opción?",
        "other": "¡Excelente meta! {title} no es uno de los seis programas de tecnología, pero MDC tiene un camino para eso y te abrí esa ruta. Un consejero de MDC al (305) 237-8888 puede confirmar los detalles.",
        "pii": "Un consejo: no necesitas compartir datos personales aquí, así que los omití. ",
        "parent": "Gracias por ayudar a su hijo o hija a explorar opciones. ",
    },
}

WHY = {
    "en": {
        "AI": "You're drawn to making computers learn, see or talk, which is what Applied AI teaches.",
        "DATA": "You like finding the story inside numbers, which is the core of Data Analytics.",
        "CYBER": "You want to stop attacks and protect people, which is exactly what cybersecurity pros do.",
        "SWE": "You enjoy writing the code that makes apps and sites work, and that's software engineering.",
        "NET": "You like making things connect and stay online, which is what networking is about.",
        "ECE": "You like the physical side: circuits, wiring and hardware. That's Electrical & Computer Engineering.",
    },
    "es": {
        "AI": "Te interesa que las computadoras aprendan, vean o hablen.",
        "DATA": "Te gusta encontrar la historia dentro de los números.",
        "CYBER": "Quieres detener ataques y proteger a las personas.",
        "SWE": "Te gusta escribir el código que hace funcionar apps y sitios web.",
        "NET": "Te gusta que las cosas se conecten y funcionen en línea.",
        "ECE": "Te gusta el lado físico: circuitos, cables y hardware.",
    },
}

ES_PROGRAM = {"AI": "Inteligencia Artificial Aplicada", "DATA": "Análisis de Datos", "CYBER": "Ciberseguridad",
              "SWE": "Ingeniería de Software", "NET": "Redes", "ECE": "Ingeniería Eléctrica y de Computadoras"}

GREETING_ONLY = re.compile(r"^\s*(hi|hello|hey|hola|yo|sup|good (morning|afternoon))[\s!.]*$", re.I)
LIST_ASK = re.compile(r"what (?:programs|majors|options)|qu[eé] programas", re.I)
PARENT = re.compile(r"\b(?:my (?:son|daughter|kid|child)|mi hij[oa])\b", re.I)


def reply(user_turns: list[str], *, injection: bool, pii_found: list[str], titles: dict[str, str]) -> dict:
    lang = detect_language(user_turns)
    t = T[lang]
    last = user_turns[-1] if user_turns else ""
    prefix = (t["pii"] if pii_found else "") + (t["parent"] if PARENT.search(" ".join(user_turns)) else "")

    if injection:
        return {"chatResponse": t["injection"], "recommendedProgram": None, "careerId": None, "language": lang}
    if GREETING_ONLY.match(last) and len(user_turns) == 1:
        return {"chatResponse": t["greet"], "recommendedProgram": None, "careerId": None, "language": lang}
    if LIST_ASK.search(last) and len(user_turns) == 1:
        return {"chatResponse": t["list"], "recommendedProgram": None, "careerId": None, "language": lang}

    program, conf, _ = classify(user_turns)
    if program == "OTHER":
        cid = other_career(user_turns)
        return {"chatResponse": prefix + t["other"].format(title=titles.get(cid, "That career")),
                "recommendedProgram": "OTHER", "careerId": cid, "language": lang}
    if program is None:
        msg = t["explore"] if CAREER_TALK.search(" ".join(user_turns)) else t["offtopic"]
        return {"chatResponse": prefix + msg, "recommendedProgram": None, "careerId": None, "language": lang}

    name = ES_PROGRAM[program] if lang == "es" else PROGRAM_NAMES[program]
    return {"chatResponse": prefix + t["match"].format(program=name, why=WHY[lang][program]),
            "recommendedProgram": program, "careerId": PROGRAM_CAREER[program], "language": lang,
            "confidence": conf}
