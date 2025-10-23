from src.llm.knowledge_base import DiviaMobilitesKnowledgeBase


class TestKnowledgeBaseInit:
    def test_init_loads_documents(self):
        kb = DiviaMobilitesKnowledgeBase()

        assert kb.documents is not None
        assert len(kb.documents) > 0
        assert isinstance(kb.documents, list)

    def test_documents_have_required_fields(self):
        kb = DiviaMobilitesKnowledgeBase()

        required_fields = ["id", "title", "content", "category"]
        for doc in kb.documents:
            for field in required_fields:
                assert field in doc
                assert doc[field] is not None
                assert len(str(doc[field])) > 0


class TestGetAllDocuments:
    def test_get_all_documents_returns_list(self):
        kb = DiviaMobilitesKnowledgeBase()
        docs = kb.get_all_documents()

        assert isinstance(docs, list)
        assert len(docs) > 0

    def test_get_all_documents_returns_same_as_init(self):
        kb = DiviaMobilitesKnowledgeBase()
        docs = kb.get_all_documents()

        assert docs == kb.documents

    def test_documents_contain_expected_categories(self):
        kb = DiviaMobilitesKnowledgeBase()
        docs = kb.get_all_documents()

        categories = {doc["category"] for doc in docs}
        expected_categories = {
            "general",
            "tickets",
            "service",
            "accessibility",
            "schedules",
            "digital",
            "news",
            "contact",
        }

        assert expected_categories.issubset(categories)


class TestGetDocumentsByCategory:
    def test_get_documents_by_category_tickets(self):
        kb = DiviaMobilitesKnowledgeBase()
        docs = kb.get_documents_by_category("tickets")

        assert len(docs) > 0
        for doc in docs:
            assert doc["category"] == "tickets"

    def test_get_documents_by_category_general(self):
        kb = DiviaMobilitesKnowledgeBase()
        docs = kb.get_documents_by_category("general")

        assert len(docs) > 0
        for doc in docs:
            assert doc["category"] == "general"

    def test_get_documents_by_category_nonexistent(self):
        kb = DiviaMobilitesKnowledgeBase()
        docs = kb.get_documents_by_category("nonexistent_category")

        assert len(docs) == 0
        assert isinstance(docs, list)

    def test_get_documents_by_category_empty_string(self):
        kb = DiviaMobilitesKnowledgeBase()
        docs = kb.get_documents_by_category("")

        assert len(docs) == 0

    def test_all_categories_have_documents(self):
        kb = DiviaMobilitesKnowledgeBase()
        all_docs = kb.get_all_documents()
        categories = {doc["category"] for doc in all_docs}

        for category in categories:
            docs = kb.get_documents_by_category(category)
            assert len(docs) > 0


class TestSearchDocuments:
    def test_search_documents_by_content(self):
        kb = DiviaMobilitesKnowledgeBase()
        results = kb.search_documents("tramway")

        assert len(results) > 0
        for doc in results:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            assert "tramway" in content_lower or "tramway" in title_lower

    def test_search_documents_by_title(self):
        kb = DiviaMobilitesKnowledgeBase()
        results = kb.search_documents("tarifs")

        assert len(results) > 0
        found_in_title = any("tarifs" in doc["title"].lower() for doc in results)
        assert found_in_title

    def test_search_documents_case_insensitive(self):
        kb = DiviaMobilitesKnowledgeBase()
        results_lower = kb.search_documents("divia")
        results_upper = kb.search_documents("DIVIA")
        results_mixed = kb.search_documents("DiViA")

        assert len(results_lower) == len(results_upper)
        assert len(results_lower) == len(results_mixed)

    def test_search_documents_no_results(self):
        kb = DiviaMobilitesKnowledgeBase()
        results = kb.search_documents("xyzabc123nonexistent")

        assert len(results) == 0
        assert isinstance(results, list)

    def test_search_documents_empty_query(self):
        kb = DiviaMobilitesKnowledgeBase()
        results = kb.search_documents("")

        assert len(results) == len(kb.get_all_documents())

    def test_search_documents_partial_match(self):
        kb = DiviaMobilitesKnowledgeBase()
        results = kb.search_documents("bus")

        assert len(results) > 0
        for doc in results:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            assert "bus" in content_lower or "bus" in title_lower

    def test_search_documents_multiple_keywords(self):
        kb = DiviaMobilitesKnowledgeBase()
        results_ticket = kb.search_documents("ticket")
        results_tarif = kb.search_documents("tarif")

        assert len(results_ticket) > 0
        assert len(results_tarif) > 0
