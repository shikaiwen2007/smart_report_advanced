from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# 加载 .env
load_dotenv()

llm = AzureChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

system = """你是一个文件命名助手，负责将输入的文件名转换为统一规范的格式，以便后续进行自动分类与统计。输出内容严格限定为地点、详细位置、卫生问题、备注和照片序号，不包含任何与暴力、色情、仇恨等无关的描述。

命名规则如下：
1. 使用逗号 `,` 作为字段分隔符。
2. 命名格式固定为：
   <地点>,<详细位置>,<卫生问题（多个问题用“/”分隔）>,<备注>(<照片序号>)
3. 保证每个字段内容种类一致，分隔符保持统一。
4. 卫生问题的描述要简洁统一，例如：
   - “垃圾占绿乱堆放”
   - “卫生死角散在垃圾/成蝇密度高”
   - “积水容器阳性”
5. 照片序号保留在括号中，例如 `(2)`，放在备注字段中。

例如：
- 输入：“北沪航公路    西闸公路路口捕蝇笼饵料干”
  输出：“北沪航公路,西闸公路路口,捕蝇笼饵料干”
- 输入：“西闸公路1117号璨旁背街小巷卫生死角散在垃圾，成蝇密度高”
  输出：“西闸公路,1117号璨旁背街小巷,卫生死角散在垃圾/成蝇密度高”
- 输入：“秀南路147号前背街小巷   9处积水容器4处阳性(2)”
  输出：“秀南路,147号前背街小巷,积水容器阳性,9处积水容器4处阳性(2)”

请严格按照上述规则输出。
"""

prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])

# Pydantic
class ChangeName(BaseModel):
    """更改名称"""

    old_name: str = Field(description="更改前的名称")
    new_name: str = Field(description="更改后的名称")

structured_llm = llm.with_structured_output(ChangeName)
few_shot_structured_llm = prompt | structured_llm

with open("old_name.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

for line in lines:
    try:
        result = few_shot_structured_llm.invoke({"input": line})
        print(result)
    except Exception as e:
        print(f"处理失败：{line}，错误：{e}")