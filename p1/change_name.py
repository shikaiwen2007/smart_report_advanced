from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional
import json

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
# human 消息：用户输入的原始文件名（{input}）。

# Pydantic
class ChangeName(BaseModel):
    """更改名称"""

    old_name: str = Field(description="更改前的名称")
    new_name: str = Field(description="更改后的名称")

structured_llm = llm.with_structured_output(ChangeName)
few_shot_structured_llm = prompt | structured_llm



# 定义结构化输出模型
class NamePair(BaseModel):
    location: str = Field(description="名称中的地点")
    sub_location: str = Field(description="名称中的具体地点")
    issue_found: list[str] = Field(description="名称中的问题")
    notes: Optional[str] = Field(default=None, description="名称中的问题备注")
    photo_number: Optional[int] = Field(default=None, description="名称中的问题数量")

# 修改 system prompt，让模型直接拆分 new_name
system_extract = """你是一个信息提取助手。
输入的内容格式为 new_name，格式如下：
<地点>,<详细位置>,<卫生问题>,<备注>(<照片序号>)

请从输入中提取信息，并严格按照以下 JSON 格式输出：
{
  "location": "...",
  "sub_location": "...",
  "issue_found": ["..."],
  "notes": "...",
  "photo_number": ...
}

示例：
- 输入："北沪航公路,西闸公路路口,捕蝇笼饵料干"
  输出：{
    "location": "北沪航公路",
    "sub_location": "西闸公路路口",
    "issue_found": ["捕蝇笼饵料干"],
    "notes": null,
    "photo_number": null
  }

- 输入："西闸公路,1117号璨旁背街小巷,卫生死角散在垃圾/成蝇密度高(2)"
  输出：{
    "location": "西闸公路",
    "sub_location": "1117号璨旁背街小巷",
    "issue_found": ["卫生死角散在垃圾", "成蝇密度高"],
    "notes": null,
    "photo_number": 2
  }

- 输入："东风新村,19号旁,积水容器阳性,多处轮胎积水(9处以上)'"
  输出：{
    "location": "东风新村",
    "sub_location": "19号旁",
    "issue_found": ["积水容器阳性", "多处轮胎积水"],
    "notes": "9处以上",
    "photo_number": null
  }
"""

prompt_extract = ChatPromptTemplate.from_messages([
    ("system", system_extract),
    ("human", "{input}")
])

structured_llm_extract = llm.with_structured_output(NamePair)
chain = prompt_extract | structured_llm_extract

results = []

with open("old_name.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

for line in lines:
    try:
        # 第一步：获取 old_name 和 new_name
        for line in lines:
            result = few_shot_structured_llm.invoke({"input": line}) # 输入：{"input": line} → human 消息。
        
        # 第二步：用 new_name 提取分类信息
        extracted = chain.invoke({"input": result.new_name})
        
        # 组装最终 JSON
        record = {
            "path": f"your/image/path/{result.old_name}.jpg",  # 你可以根据需要拼接真实路径
            "old_name": result.old_name,
            "names_pairs": extracted.model_dump()
        }
        results.append(record)

    except Exception as e:
        with open("issue_name.txt", "a", encoding="utf-8") as f:
            f.write(line + "\n")

# 保存结果到 JSON 文件
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
