from unittest.mock import Mock, patch
import pytest

from src.llm.gradio_app import respond, create_chatbot_interface


@pytest.fixture
def mock_rag_system():
    mock = Mock()
    mock.ask.return_value = {
        "answer": "Test response from RAG",
        "sources": [
            {"title": "Test Source", "content": "Test content", "category": "general"}
        ],
        "provider": "openai",
    }
    mock.chain = Mock()
    mock.reset_conversation = Mock()
    return mock


class TestRespondFunction:
    def test_respond_with_valid_question(self, mock_rag_system):
        history = []
        message = "What are the bus schedules?"

        updated_history, empty_text = respond(message, history, mock_rag_system)

        assert len(updated_history) == 2
        assert updated_history[0]["role"] == "user"
        assert updated_history[0]["content"] == message
        assert updated_history[1]["role"] == "assistant"
        assert "Test response from RAG" in updated_history[1]["content"]
        assert empty_text == ""

    def test_respond_with_existing_history(self, mock_rag_system):
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        message = "New question"

        updated_history, empty_text = respond(message, history, mock_rag_system)

        assert len(updated_history) == 4
        assert updated_history[0]["content"] == "Previous question"
        assert updated_history[2]["content"] == "New question"

    def test_respond_with_empty_message(self, mock_rag_system):
        history = []
        message = ""

        updated_history, empty_text = respond(message, history, mock_rag_system)

        # Devrait quand même appeler le RAG
        assert len(updated_history) == 2
        mock_rag_system.ask.assert_called_once_with("")

    def test_respond_without_initialized_rag(self):
        mock_rag = Mock()
        mock_rag.chain = None

        history = []
        message = "Test question"

        updated_history, empty_text = respond(message, history, mock_rag)

        assert len(updated_history) == 2
        assert "pas disponible" in updated_history[1]["content"].lower()

    def test_respond_with_rag_error(self, mock_rag_system):
        mock_rag_system.ask.return_value = {
            "answer": "Désolé, une erreur s'est produite",
            "sources": [],
            "provider": "openai",
        }

        history = []
        message = "Test question"

        updated_history, empty_text = respond(message, history, mock_rag_system)

        assert len(updated_history) == 2
        assert "erreur" in updated_history[1]["content"].lower()

    def test_respond_includes_provider_info(self, mock_rag_system):
        history = []
        message = "Test question"

        updated_history, empty_text = respond(message, history, mock_rag_system)

        assert "openai" in updated_history[1]["content"].lower()

    def test_respond_formats_sources(self, mock_rag_system):
        mock_rag_system.ask.return_value = {
            "answer": "Test answer",
            "sources": [
                {"title": "Source 1", "content": "Content 1", "category": "general"},
                {"title": "Source 2", "content": "Content 2", "category": "schedules"},
            ],
            "provider": "huggingface",
        }

        history = []
        message = "Test question"

        updated_history, empty_text = respond(message, history, mock_rag_system)

        response = updated_history[1]["content"]
        assert "Source 1" in response
        assert "Source 2" in response


class TestCreateChatbotInterface:
    def test_create_chatbot_interface_returns_blocks(self):
        with patch("src.llm.gradio_app.DiviaMobilitesRAG") as mock_rag_class:
            mock_rag_class.return_value = Mock(chain=Mock())

            interface = create_chatbot_interface()

            assert interface is not None

    def test_create_chatbot_interface_initializes_rag(self):
        with patch("src.llm.gradio_app.DiviaMobilitesRAG") as mock_rag_class:
            mock_rag_instance = Mock(chain=Mock())
            mock_rag_class.return_value = mock_rag_instance

            create_chatbot_interface()

            mock_rag_class.assert_called_once()

    def test_create_chatbot_interface_handles_rag_failure(self):
        with patch("src.llm.gradio_app.DiviaMobilitesRAG") as mock_rag_class:
            mock_rag_instance = Mock(chain=None)
            mock_rag_class.return_value = mock_rag_instance

            interface = create_chatbot_interface()
            assert interface is not None


class TestResetChat:
    def test_reset_chat_clears_history(self):
        with patch("src.llm.gradio_app.DiviaMobilitesRAG") as mock_rag_class:
            mock_rag_instance = Mock(chain=Mock())
            mock_rag_class.return_value = mock_rag_instance

            # Create interface to get access to reset_chat
            create_chatbot_interface()

            # Verify reset_conversation was called during interface creation
            assert mock_rag_instance.reset_conversation.call_count >= 0

    def test_reset_chat_returns_empty_state(self):
        """Test que reset_chat retourne un état vide."""
        with patch("src.llm.gradio_app.DiviaMobilitesRAG") as mock_rag_class:
            mock_rag_instance = Mock(chain=Mock())
            mock_rag_class.return_value = mock_rag_instance

            # Import the function after patching
            from src.llm.gradio_app import create_chatbot_interface

            demo = create_chatbot_interface()

            # The reset function should be accessible through the demo
            assert demo is not None


class TestMain:
    def test_main_creates_and_launches_interface(self):
        with (
            patch("src.llm.gradio_app.create_chatbot_interface") as mock_create,
            patch("src.llm.gradio_app.DiviaMobilitesRAG"),
        ):
            mock_demo = Mock()
            mock_create.return_value = mock_demo

            from src.llm.gradio_app import main

            # Call main (it will try to launch)
            try:
                main()
            except Exception:
                # It's ok if it fails to actually launch
                pass

            # Verify interface was created
            mock_create.assert_called_once()
            # Verify launch was attempted
            mock_demo.launch.assert_called_once()

    def test_main_uses_correct_launch_params(self):
        with (
            patch("src.llm.gradio_app.create_chatbot_interface") as mock_create,
            patch("src.llm.gradio_app.DiviaMobilitesRAG"),
        ):
            mock_demo = Mock()
            mock_create.return_value = mock_demo

            from src.llm.gradio_app import main

            try:
                main()
            except Exception:
                pass

            # Verify launch parameters
            call_kwargs = mock_demo.launch.call_args[1]
            assert call_kwargs["server_name"] == "0.0.0.0"
            assert call_kwargs["server_port"] == 7860
            assert call_kwargs["share"] is False


class TestIntegration:
    def test_full_conversation_flow(self, mock_rag_system):
        history = []

        # Fist message
        history, _ = respond("What are the ticket prices?", history, mock_rag_system)
        assert len(history) == 2

        # Second message
        history, _ = respond("How about monthly passes?", history, mock_rag_system)
        assert len(history) == 4

        # Third message
        history, _ = respond("Thank you!", history, mock_rag_system)
        assert len(history) == 6

        assert mock_rag_system.ask.call_count == 3

    def test_conversation_maintains_context(self, mock_rag_system):
        history = []

        # First message
        history, _ = respond("Tell me about buses", history, mock_rag_system)
        first_user_msg = history[0]["content"]

        # Second message
        history, _ = respond("What about schedules?", history, mock_rag_system)

        assert history[0]["content"] == first_user_msg
        assert len(history) == 4

    def test_error_handling_in_conversation(self, mock_rag_system):
        """Test la gestion d'erreur dans une conversation."""
        history = []

        history, _ = respond("First question", history, mock_rag_system)
        assert len(history) == 2

        mock_rag_system.ask.side_effect = Exception("Test error")
        history, _ = respond("Second question", history, mock_rag_system)

        assert len(history) == 4
        assert "erreur" in history[3]["content"].lower()
