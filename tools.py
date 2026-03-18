from langchain.tools import tool
from typing import List,Any,Dict,Literal
import requests

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
def get_goal_requirements(goal: Literal["취미", "취업", "대회"]):
    """
    유저의 목표(취미, 취업, 대회)에 따라 집중해야 할 핵심 알고리즘 태그와 
    권장 도달 티어 정보를 반환합니다.
    """
    return GOAL_REQUIREMENTS.get(goal)

@tool
def fetch_beakjoon(beakjoon_id: str)  -> Dict[str, int]:
    """algorithm tag별로 레이팅을 반환합니다."""
    url="https://solved.ac/api/v3/user/tag_ratings"
    params = {"handle":beakjoon_id}
    resp =  requests.get(url, params=params)
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