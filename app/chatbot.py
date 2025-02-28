from typing import Dict
from .knowledge_base import CDPKnowledgeBase

class CDPChatbot:
    def __init__(self):
        self.knowledge_base = CDPKnowledgeBase()
        
    def answer_question(self, question: str) -> Dict:
        """Process user question and generate response"""
        try:
            response = self.knowledge_base.search(question)
            return {
                'answer': response['content'],
                'title': response['title'],
                'relevant_docs': []
            }
        except Exception as e:
            return {
                'answer': 'Sorry, I encountered an error. Please try again.',
                'title': 'Error',
                'relevant_docs': []
            }