from difflib import SequenceMatcher

from app.repositories.faq_repository import FAQRepository


class FAQService:

    def __init__(self):
        self.repository = FAQRepository()

    def get_all_faqs(self):
        return self.repository.get_all()

    def create_faq(self, data):
        return self.repository.create(data)

    def update_faq(self, faq_id, data):
        return self.repository.update(faq_id, data)

    def delete_faq(self, faq_id):
        return self.repository.delete(faq_id)

    def find_answer(self, user_question: str):

        user_question = user_question.lower().strip()

        faqs = self.repository.get_all()

        best_match = None
        best_score = 0

        for faq in faqs:

            if not faq["is_active"]:
                continue

            stored_question = faq["question"].lower().strip()

            score = SequenceMatcher(
                None,
                user_question,
                stored_question
            ).ratio()

            if user_question == stored_question:
                score = 1.0

            if score > best_score:
                best_score = score
                best_match = faq

        if best_match and best_score >= 0.65:
            return {
                "matched": True,
                "question": best_match["question"],
                "answer": best_match["answer"],
                "message": "FAQ answer found"
            }

        return {
            "matched": False,
            "question": None,
            "answer": None,
            "message": "No matching FAQ found. Please contact the admin."
        }