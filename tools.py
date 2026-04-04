import datetime

from langchain.tools import tool
from typing import List, Any, Dict, Literal
import requests
from schemas import Problem
from db import db_manager
from agent_context import agent_session_id_ctx
import httpx

# 1. 목표별 요구사항 데이터 (DB나 JSON 파일로 관리해도 좋습니다)
GOAL_REQUIREMENTS = {
    "취미": {
        "description": "기본적인 프로그래밍 사고력을 기르고 간단한 퍼즐을 푸는 수준",
        "core_tags": ["Implementation", "Arithmetic", "String"],
        "target_tier": "Silver",
        "priority_logic": "흥미 위주의 쉬운 문제 추천"
    },
    "취업": {
        "description": "국내 주요 기업 코딩 테스트 합격 수준",
        "core_tags": ["BFS", "DFS", "Greedy", "Dynamic Programming", "Dijkstra", "Hash"],
        "target_tier": "Gold",
        "priority_logic": "빈출 유형 중 취약점 우선 보완"
    },
    "대회": {
        "description": "ICPC, SCPC 등 고난도 알고리즘 대회 준비 수준",
        "core_tags": ["Segment Tree", "Network Flow", "Geometry", "Bipartite Matching", "SCC"],
        "target_tier": "Platinum",
        "priority_logic": "고난도 테크닉 및 수학적 증명 위주"
    }
}

@tool
async def get_goal_requirements(goal: Literal["취미", "취업", "대회"]):
    """
    유저의 목표(취미, 취업, 대회)에 따라 집중해야 할 핵심 알고리즘 태그와 
    권장 도달 티어 정보를 반환합니다.
    """
    return GOAL_REQUIREMENTS.get(goal)

@tool
async def fetch_beakjoon(beakjoon_id: str)  -> Dict[str, int]:
    """
    algorithm tag별로 레이팅을 반환합니다.
    """
    url="https://solved.ac/api/v3/user/tag_ratings"
    params = {"handle":beakjoon_id}

    # 1. 비동기 HTTP 통신
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        return f"문제를 찾을 수 없습니다. (에러 코드: {resp.status_code})"
    data = resp.json()

    tag_rating_dict = {}

    for item in data:
        korean_name = next(
        (name_info['name'] for name_info in item['tag']['displayNames'] if name_info['language'] == 'ko'),
        item['tag']['key'] # 한국어 이름이 없으면 영문 key를 기본값으로 사용
        )
    
        tag_rating_dict[korean_name] = item['rating']

    #결과가 너무 많으면 자르기
    #sorted_dict = dict(sorted(tag_rating_dict.items(), key=lambda x: x[1]['rating'], reverse=True)[:15])

    return tag_rating_dict

@tool
async def recommand_question(problem_id) -> str:
    """
    agent에 의해 추천된 문제번호의 정보를 가져와 로드맵에 추가합니다.
    (LLM은 session_id를 신경 쓰지 않아도 됩니다.)
    """
    session_id = agent_session_id_ctx.get()
    if session_id is None:
        return "세션 정보가 없어 로드맵에 저장하지 못했습니다. (내부 설정 오류)"

    url = f"https://solved.ac/api/v3/problem/show"
    params = {"problemId":problem_id}

    # 1. 비동기 HTTP 통신
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        return f"문제를 찾을 수 없습니다. (에러 코드: {resp.status_code})"

    data = resp.json()

    #세션에 문제 저장
    problem = Problem(
        problem_id=data["problemId"],
        title=data["titleKo"],
        level=data["level"],
        tags=[tag["key"] for tag in data.get("tags", [])]
    )

    problem_dict = problem.model_dump()
    collection = db_manager.db.get_collection("algoAgent")
    await collection.update_one(
        {"_id": session_id},  # 세션 ID(UUID)로 문서 찾기
        {
            "$push": {"problems": problem_dict},       # problems 리스트 끝에 추가
            "$set": {"updated_at": datetime.datetime.now()}    # 수정 시간 업데이트
        }
    )
    
    return f"{problem}문제를 추천하고 로드맵에 저장할게"

@tool
async def search_problem_from_solvedac(tag: str, tier: str = "s1..g4") -> str:
    """
    solved.ac API를 사용하여 특정 태그와 난이도에 맞는 문제 번호를 검색합니다.
    예: tag="bfs", tier="g5..g1"
    """
    url = "https://solved.ac/api/v3/search/problem"
    
    # query 문법: tag:{태그명} tier:{난이도범위}
    params = {
        "query": f"tag:{tag} tier:{tier}",
        "sort": "random",
        "direction": "desc",
        "page": 1
    }

    async with httpx.AsyncClient() as client:
        # solved.ac API는 별도의 헤더 없이도 호출 가능하지만, 
        # 가끔 User-Agent를 요구할 수 있으니 넣어주는 것이 안전합니다.
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = await client.get(url, params=params, headers=headers)

    if resp.status_code != 200:
        return f"문제 검색 실패 (에러 코드: {resp.status_code})"

    data = resp.json()
    items = data.get("items", [])

    if not items:
        return f"'{tag}' 태그와 '{tier}' 난이도에 해당하는 문제를 찾지 못했습니다."

    # 첫 번째 문제의 번호와 제목 반환
    first_problem = items[0]
    problem_id = first_problem["problemId"]
    title = first_problem["titleKo"]
    
    return f"추천 문제 번호: {problem_id} (제목: {title})"