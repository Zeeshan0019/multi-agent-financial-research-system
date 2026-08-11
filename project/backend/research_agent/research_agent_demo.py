from typing import List, Dict, Any

MOCK_VECTOR_DB = [
    {
        "content": "Our operating margin for FY2025 came in at 19.8%, compared to 21.4% in FY2024. Margin compression occurred because of higher AI engineering wages, elevated subcontracting costs, and currency headwinds.",
        "metadata": {
            "company": "NexaCore",
            "section": "CEO Letter - Margin Compression",
            "page": 5
        }
    },
    {
        "content": "Voluntary attrition for FY2025 was 17.4%, compared to 14.9% in FY2024.",
        "metadata": {
            "company": "NexaCore",
            "section": "Corporate Overview - Attrition",
            "page": 4
        }
    }
]

class StandaloneResearchAgent:

    def __init__(self):
        self.documents = MOCK_VECTOR_DB

    def retrieve_context(self, query):

        results = []

        for doc in self.documents:

            if any(word in doc["content"].lower() for word in query.lower().split()):

                results.append(doc)

        return results

    def build_prompt(self, query, docs):

        context = ""

        for i, doc in enumerate(docs):

            meta = doc["metadata"]

            context += f"""

Document {i+1}

Company : {meta['company']}
Section : {meta['section']}
Page : {meta['page']}

Content :
{doc['content']}

"""

        return f"""
SYSTEM:
Use ONLY the context below.
Do not hallucinate.

CONTEXT:

{context}

QUESTION:
{query}

ANSWER:
"""

    def simulate_llm(self, prompt):

        if "margin" in prompt.lower():

            return "Operating margin for FY2025 was 19.8%, down from 21.4%. The decline was due to higher AI engineering wages, subcontracting costs and currency headwinds. [NexaCore | CEO Letter - Margin Compression | Page 5]"

        elif "attrition" in prompt.lower():

            return "Voluntary attrition for FY2025 was 17.4%. [NexaCore | Corporate Overview - Attrition | Page 4]"

        else:

            return "Information not found in source documents."

    def process_query(self, query):

        docs = self.retrieve_context(query)

        prompt = self.build_prompt(query, docs)

        answer = self.simulate_llm(prompt)

        return answer


agent = StandaloneResearchAgent()

print("Research Agent Loaded Successfully\n")

query = input("Enter your Question : ")

print("\n")

print(agent.process_query(query))