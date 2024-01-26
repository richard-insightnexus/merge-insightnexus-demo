import logging
from typing import Any, Optional

from llama_index import ServiceContext
from llama_index.indices.struct_store.sql_query import BaseSQLTableQueryEngine
from llama_index.prompts import BasePromptTemplate

from in_llama_index.retriever.insightnexus_retriever import InsightNexusNLSQLRetriever

logger = logging.getLogger(__name__)


class InsightNexusNLSQLTableQueryEngine(BaseSQLTableQueryEngine):
    """
    Natural language SQL Table query engine for InsightNexus.
    """

    def __init__(
            self,
            synthesize_response: bool = True,
            response_synthesis_prompt: Optional[BasePromptTemplate] = None,
            service_context: Optional[ServiceContext] = None,
            verbose: bool = False,
            account_id: Optional[str] = None,
            **kwargs: Any,
    ) -> None:
        """Initialize params."""
        self._sql_retriever = InsightNexusNLSQLRetriever(
            service_context=service_context,
            account_id=account_id,
            verbose=verbose,
        )
        super().__init__(
            synthesize_response=synthesize_response,
            response_synthesis_prompt=response_synthesis_prompt,
            service_context=service_context,
            verbose=verbose,
            **kwargs,
        )

    @property
    def sql_retriever(self) -> InsightNexusNLSQLRetriever:
        """Get SQL retriever."""
        return self._sql_retriever
