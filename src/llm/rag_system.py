"""RAG system for DiviaMobilités chatbot with multi-LLM support."""

from typing import Dict, Optional, Any
from uuid import uuid4

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from loguru import logger

from .knowledge_base import DiviaMobilitesKnowledgeBase
from src.config import get_settings
from src.utils.metrics import llm_requests_total, llm_request_duration

settings = get_settings()


class DiviaMobilitesRAG:
    """RAG system for DiviaMobilités information with multi-LLM support."""

    def __init__(self, llm_provider: Optional[str] = None):
        """Initialize RAG system.

        Args:
            llm_provider: LLM provider to use ('openai' or 'huggingface')
                         If None, uses settings.llm_provider
        """
        self.llm_provider = llm_provider or settings.llm_provider
        logger.info(f"LLM Provider selected: {self.llm_provider}")

        if self.llm_provider == "openai" and not settings.openai_api_key:
            logger.warning("No OpenAI API key provided. RAG system will not work.")
            self.chain = None
            return
        elif self.llm_provider == "huggingface" and not settings.huggingface_api_key:
            logger.warning("No HuggingFace API key provided. RAG system will not work.")
            self.chain = None
            return

        self.kb = DiviaMobilitesKnowledgeBase()
        self.vectorstore = None
        self.chain = None
        self.store: Dict[str, ChatMessageHistory] = {}
        self.session_id = str(uuid4())
        logger.info(f"Session ID created: {self.session_id}")

        self._initialize_rag()

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session."""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def _create_llm(self):
        """Create LLM instance based on provider configuration."""
        if self.llm_provider == "openai":
            logger.info("Using OpenAI LLM (gpt-4o-mini)")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                openai_api_key=settings.openai_api_key,
            )
        elif self.llm_provider == "huggingface":
            logger.info(f"Using HuggingFace LLM ({settings.huggingface_model})")
            llm = HuggingFaceEndpoint(
                repo_id=settings.huggingface_model,
                huggingfacehub_api_token=settings.huggingface_api_key,
                temperature=0.7,
                max_new_tokens=512,
            )
            return ChatHuggingFace(llm=llm)
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def _initialize_rag(self) -> None:
        """Initialize RAG components using pure LCEL."""
        try:
            logger.info(f"Initializing RAG system with {self.llm_provider} provider")

            # Create documents from knowledge base
            documents = []
            for doc in self.kb.get_all_documents():
                documents.append(
                    Document(
                        page_content=doc["content"],
                        metadata={
                            "title": doc["title"],
                            "category": doc["category"],
                            "id": doc["id"],
                        },
                    )
                )

            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500, chunk_overlap=50
            )
            splits = text_splitter.split_documents(documents)

            logger.info(f"Created {len(splits)} document chunks")

            if self.llm_provider == "openai":
                embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
            else:
                from langchain_huggingface import HuggingFaceEmbeddings

                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )

            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory=str(settings.processed_data_dir / "chroma_db"),
            )

            # Create LLM
            llm = self._create_llm()

            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

            # Step 1: Contextualize question with chat history
            contextualize_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Étant donné un historique de conversation et la dernière question de l'utilisateur "
                        "qui pourrait faire référence au contexte de l'historique, formulez une question "
                        "autonome qui peut être comprise sans l'historique. NE répondez PAS à la question, "
                        "reformulez-la simplement si nécessaire, sinon retournez-la telle quelle.",
                    ),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # Step 2: Answer question with context
            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Vous êtes un assistant pour répondre aux questions sur DiviaMobilités, "
                        "le réseau de transport en commun de Dijon. "
                        "Utilisez les éléments de contexte suivants pour répondre à la question. "
                        "Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas. "
                        "Utilisez trois phrases maximum et gardez la réponse concise.\n\n"
                        "Contexte: {context}",
                    ),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # Build the chain with LCEL
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            def contextualize_question(inputs: Dict[str, Any]) -> str:
                """Reformulate question based on chat history."""
                if not inputs.get("chat_history"):
                    return inputs["input"]

                chain = contextualize_prompt | llm | StrOutputParser()
                return chain.invoke(inputs)

            # Create the RAG chain
            rag_chain = (
                RunnablePassthrough.assign(
                    standalone_question=RunnableLambda(contextualize_question)
                )
                | RunnablePassthrough.assign(
                    context=lambda x: format_docs(
                        retriever.invoke(x["standalone_question"])
                    )
                )
                | RunnablePassthrough.assign(answer=qa_prompt | llm | StrOutputParser())
            )

            # Add message history management
            self.chain = RunnableWithMessageHistory(
                rag_chain,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )

            logger.info("RAG system initialized successfully with pure LCEL")

        except Exception as e:
            logger.error(f"Error initializing RAG system: {e}")
            self.chain = None

    def ask(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Ask a question to the RAG system."""
        if not self.chain:
            llm_requests_total.labels(status="error").inc()
            logger.error("Chain not initialized")
            return {
                "answer": f"Désolé, le système d'assistance n'est pas disponible. Veuillez vérifier la configuration de l'API {self.llm_provider.upper()}.",
                "sources": [],
            }

        sid = session_id or self.session_id

        try:
            with llm_request_duration.time():
                result = self.chain.invoke(
                    {"input": question}, config={"configurable": {"session_id": sid}}
                )

            llm_requests_total.labels(status="success").inc()

            # Extract source information from context
            sources = []
            if "context" in result:
                # Parse context to extract source documents
                context_text = result["context"]
                # Note: In pure LCEL, we format docs as text, so we can't easily extract metadata
                # For now, we'll just indicate that sources were used
                sources.append(
                    {
                        "title": "Base de connaissances DiviaMobilités",
                        "category": "general",
                        "content": context_text[:200] + "..."
                        if len(context_text) > 200
                        else context_text,
                    }
                )

            return {
                "answer": result["answer"],
                "sources": sources,
                "provider": self.llm_provider,
            }

        except Exception as e:
            logger.error(f"Error processing question: {e}")
            logger.error(f"Error message: {str(e)}")
            llm_requests_total.labels(status="error").inc()
            return {
                "answer": f"Désolé, une erreur s'est produite: {str(e)}",
                "sources": [],
                "provider": self.llm_provider,
            }

    def reset_conversation(self, session_id: Optional[str] = None) -> None:
        """Reset conversation memory for a session."""
        sid = session_id or self.session_id
        if sid in self.store:
            self.store[sid].clear()
            logger.info(f"Conversation memory cleared for session {sid}")

    def create_new_session(self) -> str:
        """Create a new conversation session."""
        new_session_id = str(uuid4())
        self.session_id = new_session_id
        logger.info(f"Created new session: {new_session_id}")
        return new_session_id
