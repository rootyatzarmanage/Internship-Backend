from app.schemas.faq import FAQCreate, FAQUpdate

faq_db = [
    {
        "id": 1,
        "question": "Who is Janesh?",
        "answer": "Janesh is a developer who builds web applications, APIs, and software solutions.",
        "category": "General",
        "is_active": True
    },
    {
        "id": 2,
        "question": "What technologies does Janesh use?",
        "answer": "Python, FastAPI, Django, React, Java, Docker, and cloud technologies.",
        "category": "Skills",
        "is_active": True
    },
    {
        "id": 3,
        "question": "How can I contact Janesh?",
        "answer": "You can contact Janesh through the chat widget on this portfolio.",
        "category": "Contact",
        "is_active": True
    }
]


class FAQRepository:

    def get_all(self):
        return faq_db

    def get_by_id(self, faq_id: int):
        return next(
            (faq for faq in faq_db if faq["id"] == faq_id),
            None
        )

    def create(self, data: FAQCreate):
        faq = {
            "id": max((item["id"] for item in faq_db), default=0) + 1,
            **data.model_dump(),
            "is_active": True
        }

        faq_db.append(faq)
        return faq

    def update(self, faq_id: int, data: FAQUpdate):
        faq = self.get_by_id(faq_id)

        if not faq:
            return None

        faq.update(data.model_dump(exclude_unset=True))
        return faq

    def delete(self, faq_id: int):
        faq = self.get_by_id(faq_id)

        if not faq:
            return False

        faq_db.remove(faq)
        return True