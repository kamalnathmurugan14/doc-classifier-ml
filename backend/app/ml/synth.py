"""Synthetic dataset generator: template-based fake documents so you can practise with zero real data."""

import random
from pathlib import Path

NAMES = [
    "Asha Patel",
    "John Miller",
    "Priya Nair",
    "Carlos Gomez",
    "Mei Chen",
    "Omar Haddad",
    "Lena Fischer",
    "Ravi Kumar",
]
COMPANIES = [
    "Acme Corp",
    "Globex Ltd",
    "Initech",
    "Umbrella Inc",
    "Stark Industries",
    "Wayne Enterprises",
    "Hooli",
    "Soylent Co",
]
ITEMS = [
    "consulting hours",
    "software license",
    "hardware maintenance",
    "cloud hosting",
    "training session",
    "support plan",
]
SKILLS = [
    "Python",
    "SQL",
    "React",
    "project management",
    "machine learning",
    "Docker",
    "communication",
    "data analysis",
]
TOPICS = ["sales", "customer churn", "security audit", "supply chain", "hiring", "marketing spend"]
OTHER = [
    "Dear {n}, I hope you are well. Let's catch up for lunch next week and talk about the holiday plans.",
    "Recipe: mix two cups of flour with three eggs, bake for thirty minutes and serve warm.",
    "Meeting notes: discussed the office move, the new coffee machine and parking arrangements.",
    "Travel itinerary: flight on Monday, hotel near the beach, museum visit on Tuesday afternoon.",
]
CLASSES = ["Invoice", "Contract", "Resume", "Report", "Other"]


def _money(r: random.Random) -> str:
    return f"${r.randint(50, 9000):,}.{r.randint(0, 99):02d}"


def _date(r: random.Random) -> str:
    return f"{r.randint(2023, 2026)}-{r.randint(1, 12):02d}-{r.randint(1, 28):02d}"


def make_doc(cls: str, r: random.Random) -> str:
    n, c = r.choice(NAMES), r.choice(COMPANIES)
    if cls == "Invoice":
        lines = [f"INVOICE #INV-{r.randint(1000, 9999)}", f"Bill to: {c}", f"Date: {_date(r)}"]
        lines += [f"{r.randint(1, 20)} x {r.choice(ITEMS)} ........ {_money(r)}" for _ in range(r.randint(2, 4))]
        lines += [
            f"Subtotal: {_money(r)}",
            f"Tax: {_money(r)}",
            f"Total due: {_money(r)}",
            f"Payment due by {_date(r)}. Please remit to {c}.",
        ]
    elif cls == "Contract":
        lines = [
            f"SERVICE AGREEMENT between {c} and {n}",
            f"This agreement is effective {_date(r)} (the Effective Date).",
            f"The parties agree that {c} shall provide {r.choice(ITEMS)}. Term and termination: either party may terminate with 30 days notice.",
            "Governing law: the courts of the agreed jurisdiction. Confidential information must not be disclosed.",
            f"Renewal: this contract renews every {r.randint(1, 3)} year(s). Signed: {n} / {c}",
        ]
    elif cls == "Resume":
        lines = [
            f"{n} - Resume",
            f"Objective: seeking a role as a {r.choice(['developer', 'analyst', 'manager', 'designer'])}.",
            f"Work Experience: {r.randint(2010, 2018)} - {r.randint(2019, 2024)} at {c}, delivered projects using {r.choice(SKILLS)}.",
            f"Skills: {', '.join(r.sample(SKILLS, 4))}",
            f"Education: B.Sc. {r.randint(2005, 2015)}. References available on request.",
        ]
    elif cls == "Report":
        lines = [
            f"Quarterly Report: {r.choice(TOPICS)}",
            "Executive summary: results are summarised below.",
            f"Methodology: we analysed data from {r.randint(3, 12)} regions over {r.randint(2, 4)} quarters.",
            f"Findings: {r.choice(TOPICS)} changed by {r.randint(2, 40)}%. Analysis shows a clear trend.",
            "Recommendations: invest further and monitor monthly. Conclusion: continue the plan.",
        ]
    else:
        lines = [r.choice(OTHER).format(n=n) for _ in range(r.randint(2, 3))] + [
            f"Ref {r.randint(1000, 9999)}"
        ]  # unique ref avoids exact duplicates
    return "\n".join(lines)


def generate(root: Path, per_class: int, seed: int = 7, noise: float = 0.1) -> list[tuple[str, str]]:
    """Write per_class docs per category into root/_synthetic/<class>/ ; returns [(rel_path, class)].

    `noise` swaps a fraction of lines with lines from other classes so the task is not trivially perfect.
    """
    r = random.Random(seed)
    out: list[tuple[str, str]] = []
    for cls in CLASSES:
        folder = root / "_synthetic" / cls.lower()
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(per_class):
            lines = make_doc(cls, r).split("\n")
            for k in range(len(lines)):
                if r.random() < noise:
                    lines[k] = r.choice(make_doc(r.choice(CLASSES), r).split("\n"))
            p = folder / f"{cls.lower()}_{i + 1:03d}.txt"
            p.write_text("\n".join(lines), encoding="utf-8")
            out.append((p.relative_to(root).as_posix(), cls))
    return out
