"""SQL Retriever."""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from in_llama_index.prompts.sql_prompts import BASE_POSTGRES_PROMPT_TMPL, BASE_POSTGRES_PROMPT
from llama_index.callbacks.base import CallbackManager
from llama_index.core.base_retriever import BaseRetriever
from llama_index.indices.struct_store.sql_retriever import DefaultSQLParser
from llama_index.llms.utils import LLMType
from llama_index.prompts import BasePromptTemplate
from llama_index.prompts.mixin import PromptMixin
from llama_index.schema import NodeWithScore, QueryBundle, QueryType, TextNode
from llama_index.service_context import ServiceContext

logger = logging.getLogger(__name__)


class InsightNexusSQLRetriever(BaseRetriever):
    """SQL Retriever.

    Retrieves from InsightNexus' data steward via raw SQL statements.

    Args:
        in_base_url: InsightNexus' base URL
        return_raw (bool): Whether to return raw results or format results.
            Defaults to True.

    """

    def __init__(
            self,
            in_base_url: Optional[str] = None,
            in_sql_path: Optional[str] = None,
            callback_manager: Optional[CallbackManager] = None,
            account_id: Optional[str] = None,
            return_raw: bool = True,
            **kwargs: Any,
    ) -> None:
        """Initialize params."""
        if in_base_url is None:
            in_base_url = os.environ.get("INSIGHTNEXUS_BASE_URL")
        if in_base_url is None:
            raise ValueError(
                "INSIGHTNEXUS_BASE_URL is must be set as an environment variable. Try something like http://localhost:8081 for example.")
        self.in_data_base_url = in_base_url

        if in_sql_path is None:
            in_sql_path = os.environ.get("INSIGHTNEXUS_SQL_PATH")
        if in_sql_path is None:
            in_sql_path = "/sql-translation"

        if account_id is None:
            raise ValueError(
                "account_id must be set"
            )
        self._account_id = account_id
        self._return_raw = return_raw
        self._in_sql_path = in_sql_path

        super().__init__(callback_manager)

    def _format_node_results(
            self, results: List[List[Any]], col_keys: List[str]
    ) -> List[NodeWithScore]:
        """Format node results."""
        nodes = []
        for result in results:
            metadata = dict(zip(col_keys, result))
            text_node = TextNode(
                text="",
                metadata=metadata,
            )
            nodes.append(NodeWithScore(node=text_node))
        return nodes

    def retrieve_with_metadata(
            self, str_or_query_bundle: QueryType
    ) -> Tuple[List[NodeWithScore], Dict]:
        """Retrieve with metadata."""
        if isinstance(str_or_query_bundle, QueryBundle):
            query_bundle = str_or_query_bundle.query_str
        else:
            query_bundle = str_or_query_bundle

        raw_response_str, metadata = self.execute_sql(query_bundle)

        if self._return_raw:
            return [NodeWithScore(node=TextNode(text=raw_response_str))], metadata
        else:
            # return formatted
            results = metadata["result"]
            col_keys = metadata["col_keys"]
            return self._format_node_results(results, col_keys), metadata

    async def aretrieve_with_metadata(
            self, str_or_query_bundle: QueryType
    ) -> Tuple[List[NodeWithScore], Dict]:
        return self.retrieve_with_metadata(str_or_query_bundle)

    def execute_sql(self, query_str: str) -> Any:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }

        session = requests.Session()
        response = session.post(
            self.in_data_base_url.strip("/") + self._in_sql_path,
            headers=headers,
            json={"rawQuery": query_str, "accountId": self._account_id},
        )
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: {response.text}"
            )

        jsonResponse = response.json()
        records = jsonResponse["records"]
        fields = jsonResponse["fields"]
        col_keys = []
        result = []
        for record in records:
            row = tuple(record)
            result.append(row)
        for field in fields:
            col_keys.append(field["name"])

        return str(result), {
            "results": result,
            "col_keys": col_keys
        }

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query."""
        retrieved_nodes, _ = self.retrieve_with_metadata(query_bundle)
        return retrieved_nodes


class InsightNexusNLSQLRetriever(BaseRetriever, PromptMixin):
    """Text-to-SQL Retriever.

        Retrieves via text.

        Args:
            in_base_url: Base URL for InsightNexus.
            in_sql_generator_path: InsightNexus LLM path for sql generation. (Optional)
            service_context (ServiceContext): Service context. Defaults to None.
            return_raw (bool): Whether to return plain-text dump of SQL results, or parsed into Nodes.
            handle_sql_errors (bool): Whether to handle SQL errors. Defaults to True.
            llm (Optional[LLM]): Language model to use.

        """

    def __init__(
            self,
            llm: Optional[LLMType] = "default",
            in_base_url: Optional[str] = None,
            in_sql_generator_path: Optional[str] = None,
            in_table_schema_path: Optional[str] = None,
            service_context: Optional[ServiceContext] = None,
            return_raw: bool = True,
            handle_sql_errors: bool = True,
            verbose: bool = False,
            account_id: Optional[str] = None,
            callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        """Initialize params."""
        self._sql_retriever = InsightNexusSQLRetriever(return_raw=return_raw, account_id=account_id)
        self._service_context = service_context or ServiceContext.from_defaults(llm=llm)
        self._text_to_sql_prompt = BASE_POSTGRES_PROMPT
        self._sql_generator_path = in_sql_generator_path
        self._handle_sql_errors = handle_sql_errors
        self._verbose = verbose
        self._sql_parser = DefaultSQLParser()

        if account_id is None:
            raise ValueError("account_id must be set")
        self._account_id = account_id

        if in_base_url is None:
            in_base_url = os.environ.get("INSIGHTNEXUS_BASE_URL")
        if in_base_url is None:
            raise ValueError(
                "INSIGHTNEXUS_BASE_URL is must be set as an environment variable. Try something like "
                "http://localhost:8081 for example.")
        self.in_data_base_url = in_base_url

        if in_sql_generator_path is None:
            in_sql_generator_path = os.environ.get("INSIGHTNEXUS_SQL_GENERATOR_PATH")
        self._sql_generator_path = in_sql_generator_path

        if in_table_schema_path is None:
            in_table_schema_path = os.environ.get("INSIGHTNEXUS_TABLE_CONTEXT_PATH")
        if in_table_schema_path is None:
            in_table_schema_path = "/sql/schema"
        self._table_schema_path = in_table_schema_path
        super().__init__(callback_manager)

    def retrieve_with_metadata(
            self, str_or_query_bundle: QueryType
    ) -> Tuple[List[NodeWithScore], Dict]:
        """Retrieve with metadata."""
        if isinstance(str_or_query_bundle, str):
            query_bundle = QueryBundle(str_or_query_bundle)
        else:
            query_bundle = str_or_query_bundle
        table_desc_str = self._get_table_context(query_bundle)
        logger.info(f"> Table desc str: {table_desc_str}")
        if self._verbose:
            print(f"> Table desc str: {table_desc_str}")

        if self._sql_generator_path is not None:
            response_str = self._get_insightnexus_sql_query(
                self._text_to_sql_prompt,
                question=query_bundle.query_str,
                schema=table_desc_str
            )
        else:
            response_str = self._service_context.llm.predict(
                self._text_to_sql_prompt,
                question=query_bundle.query_str,
                schema=table_desc_str,
            )

        sql_query_str = self._sql_parser.parse_response_to_sql(
            response_str, query_bundle
        )
        # assume that it's a valid SQL query
        logger.debug(f"> Predicted SQL query: {sql_query_str}")
        if self._verbose:
            print(f"> Predicted SQL query: {sql_query_str}")

        try:
            retrieved_nodes, metadata = self._sql_retriever.retrieve_with_metadata(
                sql_query_str
            )
        except BaseException as e:
            # if handle_sql_errors is True, then return error message
            if self._handle_sql_errors:
                err_node = TextNode(text=f"Error: {e!s}")
                retrieved_nodes = [NodeWithScore(node=err_node)]
                metadata = {}
            else:
                raise

        return retrieved_nodes, {"sql_query": sql_query_str, **metadata}

    async def aretrieve_with_metadata(
            self, str_or_query_bundle: QueryType
    ) -> Tuple[List[NodeWithScore], Dict]:
        """Async retrieve with metadata."""
        if isinstance(str_or_query_bundle, str):
            query_bundle = QueryBundle(str_or_query_bundle)
        else:
            query_bundle = str_or_query_bundle
        table_desc_str = self._get_table_context(query_bundle)
        logger.info(f"> Table desc str: {table_desc_str}")

        if self._sql_generator_path is not None:
            response_str = self._get_insightnexus_sql_query(
                self._text_to_sql_prompt,
                question=query_bundle.query_str,
                schema=table_desc_str
            )
        else:
            response_str = await self._service_context.llm.apredict(
                self._text_to_sql_prompt,
                question=query_bundle.query_str,
                schema=table_desc_str,
            )

        sql_query_str = self._sql_parser.parse_response_to_sql(
            response_str, query_bundle
        )
        # assume that it's a valid SQL query
        logger.debug(f"> Predicted SQL query: {sql_query_str}")

        try:
            (
                retrieved_nodes,
                metadata,
            ) = await self._sql_retriever.aretrieve_with_metadata(sql_query_str)
        except BaseException as e:
            # if handle_sql_errors is True, then return error message
            if self._handle_sql_errors:
                err_node = TextNode(text=f"Error: {e!s}")
                retrieved_nodes = [NodeWithScore(node=err_node)]
                metadata = {}
            else:
                raise
        return retrieved_nodes, {"sql_query": sql_query_str, **metadata}

    def _get_insightnexus_sql_query(self, prompt: BasePromptTemplate, **prompt_args: Any) -> str:
        formatted_prompt = prompt.format(**prompt_args)
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }

        session = requests.Session()
        response = session.post(
            self.in_data_base_url.strip("/") + self._sql_generator_path,
            headers=headers,
            json={"prompt": formatted_prompt},
        )
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: {response.text}"
            )

        return response.json()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query."""
        retrieved_nodes, _ = self.retrieve_with_metadata(query_bundle)
        return retrieved_nodes

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Async retrieve nodes given query."""
        retrieved_nodes, _ = await self.aretrieve_with_metadata(query_bundle)
        return retrieved_nodes

    def _get_table_context(self, query_bundle: QueryBundle) -> str:
        """Get Table Context

        Get all necessary schema information as well as any additional context
        from the InsightNexus endpoint.
        """

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }

        session = requests.Session()
        response = session.post(
            self.in_data_base_url.strip("/") + self._table_schema_path,
            headers=headers,
            json={"account_id": self._account_id, "question": query_bundle.query_str},
        )
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: {response.text}"
            )

        return response.json()["schema"]
