import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from tools import fetch_beakjoon, get_goal_requirements, recommand_question, search_problem_from_solvedac

load_dotenv()

system_prompt = """
당신은 백준 알고리즘 학습 전문가입니다.
사용자의 질문에 답할 때 다음 규칙을 철저히 따르세요:

1. 사용자가 '취업', '취미', '대회' 중 하나의 목표를 언급하면,
   반드시 'get_goal_requirements' 툴을 실행하여 공인된 가이드라인 정보를 가져오세요.
2. 툴에서 가져온 'core_tags' 정보를 바탕으로 사용자의 현재 실력과 비교하여 조언하세요.
3. 절대 당신의 사전 지식만으로 알고리즘 로드맵을 설명하지 마세요.
4. 문제를 추천할땐 'recommand_question' 툴을 사용해 문제의 id 난이도 알고리즘 tag를 조회해서 가져오세요.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

title_prompt = ChatPromptTemplate.from_messages([
    ("system", """당신은 요약 전문가입니다. 사용자의 질문을 분석하여 5단어 이내의 제목을 생성하세요.

    [주의사항]
    - 반드시 제목만 출력하세요.
    - '제목:', '추천:', '어떠신가요?' 같은 부가 설명이나 인사는 절대로 금지합니다.
    - 답변에 제목 외의 다른 문자가 포함되면 시스템 에러가 발생합니다."""),
    ("human", "{input}"),
])

_tools = [fetch_beakjoon, get_goal_requirements, recommand_question, search_problem_from_solvedac]

_model = init_chat_model("gpt-5-nano")
_agent = create_tool_calling_agent(_model, _tools, prompt)
agent_executor = AgentExecutor(agent=_agent, tools=_tools, verbose=True)

_title_model = init_chat_model("gpt-5-nano")
title_chain = title_prompt | _title_model | StrOutputParser()
