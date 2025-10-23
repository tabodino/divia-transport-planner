"""Gradio interface for DiviaMobilités chatbot."""

import gradio as gr
from loguru import logger

from .rag_system import DiviaMobilitesRAG
from src.config import get_settings

settings = get_settings()


def respond(message: str, history: list, rag_system: DiviaMobilitesRAG) -> tuple:
    """Process user message and return response.

    Args:
        message: User message
        history: Chat history in messages format [{"role": "user", "content": "..."}, ...]
        rag_system: RAG system instance to use

    Returns:
        Tuple of (updated_history, empty_string_for_textbox)
    """

    # Check if RAG system is initialized
    if not rag_system or not rag_system.chain:
        logger.error("RAG system not initialized")
        error_answer = "Désolé, le système d'assistance n'est pas disponible. Veuillez vérifier la configuration."
        history = history or []
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_answer})
        return history, ""

    try:
        logger.info("Calling RAG system...")
        result = rag_system.ask(message)

        logger.debug(f"Result keys: {result.keys()}")
        answer = result["answer"]
        logger.info(f"Answer received (length: {len(answer)})")
        logger.debug(f"Answer preview: {answer[:100]}...")

        # Add provider info
        provider = result.get("provider", "unknown")
        answer += f"\n\n_Réponse générée par {provider}_"

        # Add sources if available
        if result["sources"]:
            logger.info(f"Adding {len(result['sources'])} sources to answer")
            answer += "\n\n📚 **Sources:**\n"
            for source in result["sources"][:2]:  # Limit to 2 sources
                answer += f"- {source['title']} ({source['category']})\n"

        # Update history with new messages in messages format
        history = history or []
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": answer})

        return history, ""

    except Exception as e:
        logger.error("Error in respond function")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")

        # Return error message to user in messages format
        error_answer = f"Erreur: {str(e)}"
        history = history or []
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_answer})
        return history, ""


def create_chatbot_interface():
    """Create Gradio chatbot interface."""

    # Initialize RAG system
    logger.info("Creating RAG system instance...")
    rag = DiviaMobilitesRAG()

    if not rag.chain:
        logger.error("RAG system failed to initialize")
    else:
        logger.info("RAG system initialized successfully")

    def respond_wrapper(message: str, history: list) -> tuple:
        """Wrapper to pass rag system to respond function."""
        return respond(message, history, rag)

    def reset_chat():
        """Reset chat conversation."""
        rag.reset_conversation()
        return [], ""

    # Create Gradio interface
    with gr.Blocks(
        title="DiviaMobilités Assistant",
        theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="purple"),
    ) as demo:
        gr.Markdown(
            """
            # 🚌 DiviaMobilités Assistant Intelligent
            
            Posez vos questions sur le réseau DiviaMobilités : horaires, tarifs, 
            titres de transport, remboursements, actualités, et plus encore !
            """
        )

        chatbot = gr.Chatbot(
            height=500,
            label="Conversation",
            avatar_images=(None, "🤖"),
            type="messages",
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Votre question",
                placeholder="Ex: Comment acheter un ticket ? Quels sont les tarifs ?",
                scale=4,
            )
            submit = gr.Button("Envoyer", variant="primary", scale=1)

        with gr.Row():
            clear = gr.Button("Nouvelle conversation", variant="secondary")

        gr.Markdown(
            """
            ### 💡 Exemples de questions :
            - Quels sont les tarifs des tickets ?
            - Comment obtenir un remboursement ?
            - Où acheter mes titres de transport ?
            - Quels sont les horaires du tramway ?
            - Comment contacter le service client ?
            - Y a-t-il des travaux en cours ?
            """
        )

        msg.submit(respond_wrapper, [msg, chatbot], [chatbot, msg])
        submit.click(respond_wrapper, [msg, chatbot], [chatbot, msg])
        clear.click(reset_chat, None, [chatbot, msg])

        gr.Markdown(
            """
            ---
            **Note:** Cet assistant utilise l'intelligence artificielle pour répondre à vos questions 
            basées sur les informations officielles de DiviaMobilités. Pour des informations en temps réel 
            ou des cas spécifiques, contactez le service client au 03 80 11 29 29.
            """
        )

    return demo


def main():
    """Launch Gradio app."""
    logger.info("Starting DiviaMobilités Gradio chatbot")

    demo = create_chatbot_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":  # pragma: no cover
    main()
