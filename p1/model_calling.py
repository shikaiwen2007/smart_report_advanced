from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os

# 加载 .env
load_dotenv()

print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

llm = AzureChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

response = llm.invoke("Hello, world!")
print(response.content)