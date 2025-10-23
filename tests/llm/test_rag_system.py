from unittest.mock import Mock, patch
import pytest

from src.llm.rag_system import DiviaMobilitesRAG
from types import SimpleNamespace


@pytest.fixture
def mock_settings():
    with patch("src.llm.rag_system.settings") as mock:
        mock.openai_api_key = "test-openai-key"
        mock.huggingface_api_key = "test-hf-key"
        mock.huggingface_model = "mistralai/Mistral-7B-Instruct-v0.2"
        mock.llm_provider = "huggingface"
        mock.processed_data_dir = Mock()
        mock.processed_data_dir.__truediv__ = Mock(return_value="/tmp/chroma_db")
        yield mock


@pytest.fixture
def sample_docs():
    Doc = SimpleNamespace
    return [Doc(page_content="Doc1 content"), Doc(page_content="Doc2 content")]


@pytest.fixture
def mock_knowledge_base():
    with patch("src.llm.rag_system.DiviaMobilitesKnowledgeBase") as mock:
        instance = mock.return_value
        instance.get_all_documents.return_value = [
            {
                "id": "test1",
                "title": "Test Document 1",
                "content": "This is test content about DiviaMobilités.",
                "category": "general",
            }
        ]
        yield instance


@pytest.fixture
def mock_all_rag_dependencies(mock_settings, mock_knowledge_base):
    """Mock all RAG dependencies."""
    with (
        patch("src.llm.rag_system.ChatOpenAI") as mock_openai,
        patch("src.llm.rag_system.OpenAIEmbeddings") as mock_openai_emb,
        patch("src.llm.rag_system.HuggingFaceEndpoint") as mock_hf,
        patch("src.llm.rag_system.Chroma") as mock_chroma,
        patch("src.llm.rag_system.RecursiveCharacterTextSplitter"),
    ):
        # Mock LLMs
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="Test response")
        mock_openai.return_value = mock_llm
        mock_hf.return_value = mock_llm

        # Mock embeddings
        mock_openai_emb.return_value = Mock()

        # Mock vectorstore
        mock_vs = Mock()
        mock_vs.as_retriever.return_value = Mock()
        mock_chroma.from_documents.return_value = mock_vs

        yield {
            "openai": mock_openai,
            "hf": mock_hf,
            "chroma": mock_chroma,
            "vectorstore": mock_vs,
        }


class TestRAGSystemInit:
    def test_init_with_openai_provider(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG(llm_provider="openai")

        assert rag.llm_provider == "openai"
        assert rag.kb is not None
        assert rag.session_id is not None
        assert rag.chain is not None

    def test_init_with_huggingface_provider(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG(llm_provider="huggingface")

        assert rag.llm_provider == "huggingface"

    def test_init_without_any_key_fails(self, mock_settings, mock_knowledge_base):
        mock_settings.openai_api_key = ""
        mock_settings.huggingface_api_key = ""

        rag = DiviaMobilitesRAG(llm_provider="openai")

        assert rag.chain is None

    def test_init_creates_session_id(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()

        assert rag.session_id is not None
        assert isinstance(rag.session_id, str)
        assert len(rag.session_id) > 0

    def test_init_creates_empty_store(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()

        assert rag.store is not None
        assert isinstance(rag.store, dict)
        assert len(rag.store) == 0


class TestCreateLLM:
    def test_create_openai_llm(self, mock_all_rag_dependencies):
        DiviaMobilitesRAG(llm_provider="openai")

        mock_all_rag_dependencies["openai"].assert_called_once()
        call_kwargs = mock_all_rag_dependencies["openai"].call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.7

    def test_create_huggingface_llm(self, mock_settings, mock_all_rag_dependencies):
        DiviaMobilitesRAG(llm_provider="huggingface")

        mock_all_rag_dependencies["hf"].assert_called_once()
        call_kwargs = mock_all_rag_dependencies["hf"].call_args[1]
        assert call_kwargs["repo_id"] == mock_settings.huggingface_model
        assert call_kwargs["temperature"] == 0.7


class TestAsk:
    def test_ask_returns_answer(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()

        # Mock the chain
        mock_chain = Mock()
        mock_chain.invoke.return_value = {
            "answer": "Test answer",
            "context": "Test context",
        }
        rag.chain = mock_chain

        result = rag.ask("What are the bus schedules?")

        assert "answer" in result
        assert result["answer"] == "Test answer"
        assert "sources" in result
        assert "provider" in result

    def test_ask_without_initialized_chain(self, mock_settings, mock_knowledge_base):
        mock_settings.openai_api_key = ""
        mock_settings.huggingface_api_key = ""

        rag = DiviaMobilitesRAG()
        result = rag.ask("Test question")

        assert "answer" in result
        assert "pas disponible" in result["answer"].lower()
        assert "sources" in result
        assert len(result["sources"]) == 0

    def test_ask_with_custom_session_id(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()

        mock_chain = Mock()
        mock_chain.invoke.return_value = {
            "answer": "Test answer",
            "context": "Test context",
        }
        rag.chain = mock_chain

        custom_session = "custom-session-123"
        rag.ask("Test question", session_id=custom_session)

        # Vérifier que le session_id a été passé
        call_config = mock_chain.invoke.call_args[1]["config"]
        assert call_config["configurable"]["session_id"] == custom_session

    def test_ask_handles_exception(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()

        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("Test error")
        rag.chain = mock_chain

        result = rag.ask("Test question")

        assert "answer" in result
        assert "erreur" in result["answer"].lower()
        assert "Test error" in result["answer"]


class TestGetSessionHistory:
    def test_get_session_history_creates_new(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()
        session_id = "test-session"

        history = rag._get_session_history(session_id)

        assert session_id in rag.store
        assert history is not None

    def test_get_session_history_returns_existing(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()
        session_id = "test-session"

        history1 = rag._get_session_history(session_id)
        history2 = rag._get_session_history(session_id)

        assert history1 is history2


class TestResetConversation:
    def test_reset_conversation_clears_history(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()
        session_id = "test-session"

        history = rag._get_session_history(session_id)
        history.add_user_message("Test message")

        rag.reset_conversation(session_id)

        assert len(rag.store[session_id].messages) == 0

    def test_reset_conversation_with_default_session(self, mock_all_rag_dependencies):
        """Test reset_conversation avec la session par défaut."""
        rag = DiviaMobilitesRAG()

        history = rag._get_session_history(rag.session_id)
        history.add_user_message("Test message")

        rag.reset_conversation()

        assert len(rag.store[rag.session_id].messages) == 0

    def test_reset_nonexistent_session(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()

        rag.reset_conversation("nonexistent-session")


class TestCreateNewSession:
    def test_create_new_session_returns_id(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()
        new_session_id = rag.create_new_session()

        assert new_session_id is not None
        assert isinstance(new_session_id, str)
        assert len(new_session_id) > 0

    def test_create_new_session_updates_current(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()
        old_session_id = rag.session_id
        new_session_id = rag.create_new_session()

        assert new_session_id != old_session_id
        assert rag.session_id == new_session_id

    def test_create_multiple_sessions(self, mock_all_rag_dependencies):
        rag = DiviaMobilitesRAG()
        session_ids = [rag.create_new_session() for _ in range(5)]

        assert len(session_ids) == len(set(session_ids))
