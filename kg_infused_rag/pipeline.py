from __future__ import annotations

from .interfaces import EntityLinkerGateway
from .module1_spreading_activation import SpreadingActivationRetriever
from .module2_query_expansion import KGQueryExpander
from .module3_generation import FactEnhancedGenerator
from .types import GeneratedNote


class KGInfusedRAGPipeline:
    """
    End-to-end orchestrator for:
      1) Spreading Activation retrieval
      2) KG-based Query Expansion
      3) Fact-enhanced note generation
    """

    def __init__(
        self,
        module1: SpreadingActivationRetriever,
        module2: KGQueryExpander,
        module3: FactEnhancedGenerator,
        entity_linker: EntityLinkerGateway,
    ) -> None:
        self.module1 = module1
        self.module2 = module2
        self.module3 = module3
        self.entity_linker = entity_linker

    def run(self, question: str) -> GeneratedNote:
        seed_qids = self.entity_linker.link(question)
        triples = self.module1.run(question, seed_qids)
        expanded = self.module2.run(question, triples)
        return self.module3.run(question, expanded)

