from core.ingestion import process_and_store_documents
from core.generator import get_rag_chain
import warnings

# Langchain ke warnings ko hide karne ke liye
warnings.filterwarnings("ignore")


def run_test():
    print("--- Starting Document Ingestion ---")
    # process_and_store_documents()  # Ise comment rakha hai kyunki data already save ho chuka hai

    print("\n--- Testing the Brain ---")
    chain = get_rag_chain()

    query = "Is document mein kya bataya gaya hai thoda short mein batao?"
    print(f"User: {query}")

    response = chain.invoke({"query": query})
    print(f"\nAI Response:\n{response['result']}")


if __name__ == "__main__":
    run_test()