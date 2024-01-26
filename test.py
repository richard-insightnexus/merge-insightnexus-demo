import os
import openai
import llama_index
from dotenv import load_dotenv
from llama_index import ServiceContext
from llama_index.llms import OpenAI

from in_llama_index.indices.struct_store.insightnexus_sql_query import InsightNexusNLSQLTableQueryEngine

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

llm = OpenAI(temperature=0, model="gpt-4")

service_context = ServiceContext.from_defaults(llm=llm)

merge_linked_account_id = input("Enter Merge LinkedAccount ID: ")
query = input("Enter your question: ")

in_query_engine = InsightNexusNLSQLTableQueryEngine(account_id=merge_linked_account_id)
in_response = in_query_engine.query(query)

print("** RESPONSE **")
print(in_response)


