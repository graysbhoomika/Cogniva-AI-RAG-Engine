import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from core.config import GOOGLE_API_KEY
from core.vector_store import get_vector_store
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

PROMPT_TEMPLATE = """
You are Cogniva AI, an enterprise-grade multilingual knowledge assistant.
Your goal is to answer the user's question based ONLY on the provided Context Information and the Chat History.

Chat History:
{chat_history}

Context Information:
{context}

User Question: {question}

CRITICAL INSTRUCTIONS:
1. You must answer in the EXACT SAME LANGUAGE as the User Question.
2. Use ONLY the facts from the Context Information. Do not hallucinate.
3. If the answer is not in the context, state exactly: "Mujhe diye gaye documents mein iska jawab nahi mila." 

Answer:
"""


class CustomRAGPipeline:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1
        )
        self.db = get_vector_store()
        self.vector_retriever = self.db.as_retriever(search_kwargs={"k": 4})

        self.bm25_retriever = None
        try:
            db_data = self.db.get()
            if db_data and len(db_data.get('documents', [])) > 0:
                docs = [
                    Document(page_content=txt, metadata=meta)
                    for txt, meta in zip(db_data['documents'], db_data['metadatas'])
                ]
                self.bm25_retriever = BM25Retriever.from_documents(docs)
                self.bm25_retriever.k = 3
        except Exception:
            pass

        self.prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["context", "question", "chat_history"]
        )

    def invoke(self, inputs):
        start_time = time.time()  # START TIMER
        user_query = inputs.get("query", "")
        chat_history = inputs.get("chat_history", "No previous conversation.")

        vector_docs = self.vector_retriever.invoke(user_query)
        keyword_docs = self.bm25_retriever.invoke(user_query) if self.bm25_retriever else []

        all_docs = []
        seen_content = set()
        for doc in keyword_docs + vector_docs:
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                all_docs.append(doc)

        # --- FIXED LONG LINES (No Syntax Errors) ---
        context_parts = []
        for doc in all_docs[:6]:
            source = doc.metadata.get('source', 'Unknown Document')
            page = doc.metadata.get('page', 'N/A')
            context_parts.append(f"[Source: {source}, Page: {page}]\n{doc.page_content}")

        context_text = "\n\n".join(context_parts)

        formatted_prompt = self.prompt.format(
            context=context_text,
            question=user_query,
            chat_history=chat_history
        )

        # Invoke LLM
        response = self.llm.invoke(formatted_prompt)

        latency = round(time.time() - start_time, 2)  # END TIMER

        # EXTRACT TOKEN METADATA (Observability)
        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            usage = response.response_metadata['token_usage']
            prompt_tokens = getattr(usage, "prompt_token_count", 0)
            completion_tokens = getattr(usage, "candidates_token_count", 0)

        # Extract Sources cleanly
        sources = []
        for doc in all_docs[:6]:
            raw_source = doc.metadata.get('source', 'Unknown')
            filename = raw_source.split('/')[-1].split('\\')[-1]
            page = doc.metadata.get('page', 'N/A')
            sources.append(f"📄 {filename} (Page {page})")
        # ------------------------------------------

        return {
            "result": response.content,
            "sources": list(set(sources)),
            "latency": latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }


def get_rag_chain():
    return CustomRAGPipeline()