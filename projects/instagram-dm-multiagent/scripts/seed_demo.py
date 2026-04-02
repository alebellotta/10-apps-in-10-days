import asyncio

from app.db.repositories.kb import KnowledgeBaseRepository
from app.db.session import AsyncSessionLocal, init_db


FAQS = [
    {
        "category": "faq",
        "question": "Quali sono gli orari di apertura?",
        "answer": "Siamo disponibili dal lunedi al venerdi dalle 9:00 alle 18:00.",
        "language": "it",
        "tags": "orari,apertura,assistenza",
    },
    {
        "category": "pricing",
        "question": "Quanto costa il servizio base?",
        "answer": "Il piano base parte da 49 euro al mese. Per offerte personalizzate scrivici qualche dettaglio in piu.",
        "language": "it",
        "tags": "prezzi,costi,preventivo",
    },
    {
        "category": "booking",
        "question": "Come posso prenotare una call?",
        "answer": "Puoi prenotare una call dal sito oppure lasciarci email e numero e ti ricontattiamo.",
        "language": "it",
        "tags": "prenotazione,call,demo",
    },
    {
        "category": "links",
        "question": "Dove trovo il sito?",
        "answer": "Il sito e https://example.com",
        "language": "it",
        "tags": "sito,link,website",
    },
    {
        "category": "support",
        "question": "In quanto tempo rispondete?",
        "answer": "Di solito rispondiamo entro una giornata lavorativa.",
        "language": "it",
        "tags": "tempi,risposta,supporto",
    },
]


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        repo = KnowledgeBaseRepository(session)
        for item in FAQS:
            await repo.create(**item)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
