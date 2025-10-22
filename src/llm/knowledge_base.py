"""Knowledge base for DiviaMobilités information."""

from typing import List, Dict
from loguru import logger


class DiviaMobilitesKnowledgeBase:
    """Knowledge base containing DiviaMobilités information."""

    def __init__(self):
        """Initialize knowledge base."""
        self.documents = self._load_documents()

    def _load_documents(self) -> List[Dict[str, str]]:
        """Load knowledge base documents.

        Returns:
            List of documents with content and metadata
        """
        documents = [
            {
                "id": "network_overview",
                "title": "Réseau DiviaMobilités",
                "content": """
                DiviaMobilités est le réseau de transport en commun de Dijon Métropole.
                Le réseau comprend des lignes de bus, de tramway et des services de transport à la demande.
                Le réseau dessert l'ensemble de la métropole dijonnaise avec plus de 30 lignes régulières.
                Les horaires sont adaptés aux besoins des usagers avec des fréquences renforcées aux heures de pointe.
                """,
                "category": "general",
            },
            {
                "id": "tickets_pricing",
                "title": "Tarifs et Titres de Transport",
                "content": """
                TICKETS ET TARIFS:
                - Ticket à l'unité: 1,50€ (valable 1h)
                - Carnet de 10 tickets: 12€
                - Pass journée: 4€ (voyages illimités)
                - Abonnement mensuel: 35€
                - Abonnement annuel: 350€
                
                TARIFS RÉDUITS:
                - Jeunes (-26 ans): -50% sur tous les abonnements
                - Seniors (+65 ans): -30% sur les abonnements
                - Demandeurs d'emploi: tarif solidarité à 15€/mois
                
                GRATUITÉ:
                - Enfants de moins de 4 ans
                - Accompagnateurs de personnes handicapées
                """,
                "category": "tickets",
            },
            {
                "id": "ticket_purchase",
                "title": "Où Acheter ses Titres",
                "content": """
                POINTS DE VENTE:
                - Agences DiviaMobilités (centre-ville et gare)
                - Distributeurs automatiques dans les stations de tram
                - Application mobile DiviaMobilités
                - Site web diviamobilites.fr
                - Buralistes et commerces agréés
                
                RECHARGEMENT:
                - Carte rechargeable disponible (5€ de caution)
                - Rechargement en ligne, en agence ou aux distributeurs
                - Rechargement automatique possible avec prélèvement
                """,
                "category": "tickets",
            },
            {
                "id": "refunds_claims",
                "title": "Remboursements et Réclamations",
                "content": """
                REMBOURSEMENT D'ABONNEMENT:
                - Possible en cas de déménagement, changement de situation
                - Demande à faire dans les 30 jours
                - Remboursement au prorata des mois non utilisés
                - Frais de dossier: 10€
                
                RÉCLAMATIONS:
                - Formulaire en ligne sur diviamobilites.fr
                - Par courrier au service client
                - Par téléphone au 03 80 11 29 29
                - Délai de réponse: 15 jours maximum
                
                OBJETS TROUVÉS:
                - Service objets trouvés à l'agence centrale
                - Déclaration en ligne possible
                - Conservation des objets: 3 mois
                """,
                "category": "service",
            },
            {
                "id": "accessibility",
                "title": "Accessibilité",
                "content": """
                ACCESSIBILITÉ PMR:
                - Tous les tramways sont accessibles aux fauteuils roulants
                - 80% des bus sont équipés de planchers bas
                - Rampes d'accès dans toutes les stations de tram
                - Places réservées dans tous les véhicules
                
                SERVICE PAM (Personnes à Mobilité Réduite):
                - Transport à la demande pour personnes handicapées
                - Réservation 24h à l'avance
                - Tarif identique au réseau classique
                - Inscription préalable nécessaire
                """,
                "category": "accessibility",
            },
            {
                "id": "schedules_frequency",
                "title": "Horaires et Fréquences",
                "content": """
                HORAIRES DE SERVICE:
                - Premier départ: 5h00 du lundi au samedi
                - Dernier départ: 00h30 (minuit et demi)
                - Dimanche: service réduit de 7h à 21h
                
                FRÉQUENCES:
                - Tramway: toutes les 5-10 minutes en heures de pointe
                - Bus lignes principales: toutes les 10-15 minutes
                - Bus lignes secondaires: toutes les 30 minutes
                
                SERVICES SPÉCIAUX:
                - Noctibus: vendredi et samedi jusqu'à 2h du matin
                - Service renforcé lors d'événements
                """,
                "category": "schedules",
            },
            {
                "id": "mobile_app",
                "title": "Application Mobile",
                "content": """
                FONCTIONNALITÉS DE L'APP:
                - Calcul d'itinéraire en temps réel
                - Horaires de passage aux arrêts
                - Achat et validation de titres
                - Alertes trafic et perturbations
                - Géolocalisation des arrêts proches
                - Favoris et trajets récurrents
                
                DISPONIBILITÉ:
                - iOS (App Store)
                - Android (Google Play)
                - Gratuite
                """,
                "category": "digital",
            },
            {
                "id": "news_updates",
                "title": "Actualités et Travaux",
                "content": """
                INFORMATIONS TRAFIC:
                - Consultez le site web pour les perturbations en temps réel
                - Inscrivez-vous aux alertes SMS
                - Suivez @DiviaMobilites sur les réseaux sociaux
                
                TRAVAUX EN COURS:
                - Extension de la ligne de tram T2 (fin 2025)
                - Rénovation de plusieurs stations
                - Nouveaux bus électriques en déploiement
                
                NOUVEAUTÉS:
                - Nouveau système de paiement sans contact
                - Application mobile mise à jour
                - Nouvelles lignes de bus en projet
                """,
                "category": "news",
            },
            {
                "id": "contact",
                "title": "Contact et Informations",
                "content": """
                CONTACT:
                - Téléphone: 03 80 11 29 29 (du lundi au samedi, 7h-19h)
                - Email: contact@diviamobilites.fr
                - Site web: www.diviamobilites.fr
                - Réseaux sociaux: @DiviaMobilites
                
                AGENCES:
                - Agence Centre-Ville: Place Grangier
                - Agence Gare: Parvis de la Gare SNCF
                - Horaires: lundi-samedi 9h-18h
                
                URGENCES:
                - Numéro d'urgence: 03 80 11 29 00 (24h/24)
                """,
                "category": "contact",
            },
        ]

        logger.info(f"Loaded {len(documents)} knowledge base documents")
        return documents

    def get_all_documents(self) -> List[Dict[str, str]]:
        """Get all documents.

        Returns:
            List of all documents
        """
        return self.documents

    def get_documents_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get documents by category.

        Args:
            category: Category to filter by

        Returns:
            List of documents in the category
        """
        return [doc for doc in self.documents if doc["category"] == category]

    def search_documents(self, query: str) -> List[Dict[str, str]]:
        """Simple keyword search in documents.

        Args:
            query: Search query

        Returns:
            List of matching documents
        """
        query_lower = query.lower()
        results = []

        for doc in self.documents:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()

            if query_lower in content_lower or query_lower in title_lower:
                results.append(doc)

        return results
