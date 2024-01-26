# InsightNexus Merge Demo

This is a demo of InsightNexus' dataprocessor that integrates with Merge's Support Ticketing and LlamaIndex. It's set to run with OpenAI's API for ease. 
## Notable Features

- Prompt Injection protection
- Multi-tenant data protection
- Data ingestion enrichment
- Retrieval enrichment
- Much better out of the box performance when compared to base LlamaIndex
## Installation

Set your OPENAI_API_KEY and MERGE_API_KEY in the `.env` file

```bash
  ...
  POSTGRES_DDL_AUTO=none
  POSTGRES_URL=jdbc:postgresql://db:5432/insightnexus
  OPENAI_API_KEY=
  MERGE_API_KEY=
```

Start the docker containers:
```bash
docker-compose up
```

And you'll have a local testable version ready to go. There are a couple of endpoints that will be interesting to developers using Merge. Base URL by default is http://localhost:8081

POST /merge/endpoint (Creates a merge endpoint to be synced periodically and incrementally)
```
{
    "accountId": "MERGE_LINKED_ACCOUNT_ID_HERE",
    "accountToken": "MERGE_LINKED_ACCOUNT_TOKEN_HERE"
}
```

POST /merge/sync (Creates a fresh sync of a merge endpoint. This deletes all previous data and performs a fresh sync)
```
{
    "categoryName":"ticketing",
    "accountId":"MERGE_LINKED_ACCOUNT_ID_HERE"
}
```
</details>


If you'd like to see it in action, you can view and run `test.py` by first installing the requirements:
```bash
pip install -r requirements.txt
python test.py
```

## Examples from Zendesk Test Account + Merge

Question: `Give me tickets related to technical issues`

Pure LlamaIndex:
```
** Response: ** 
assistant: I'm sorry, but there are currently no tickets related to technical issues. 
```
InsightNexus:
```
** Response: ** 

assistant: Here are some tickets related to technical issues: 

  

1. Ticket ID: c4c23b32-5b91-4d95-8015-3feefdaa1a00 

   - Description: The customer is having trouble setting up a new product and is seeking help. 

   - Status: OPEN 

   - Priority: NORMAL 

   - Link: [Ticket Link](https://insightnexus.zendesk.com/agent/tickets/1) 

  

2. Ticket ID: 445d7e0a-cb21-422d-96be-19e9d5eabaff 

   - Description: The customer wants to use the blurred background feature but doesn't know how to turn it on. 

   - Status: OPEN 

   - Priority: None 

   - Link: [Ticket Link](https://insightnexus.zendesk.com/agent/tickets/11) 
...
```

----------
----------
Question: `How many of my customers are asking about onboarding issues?`

Pure LlamaIndex:
```
** Response: ** 
assistant: None of your customers are asking about onboarding issues. 
```

InsightNexus:
```
** Response: ** 
assistant: There are 3 customers who have asked about onboarding issues. 
```
