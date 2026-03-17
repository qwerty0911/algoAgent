from langchain.tools import tool
from typing import List,Any,Dict
import requests

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

    return tag_rating_dict