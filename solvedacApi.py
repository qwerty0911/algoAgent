import httpx
from fastapi import FastAPI, Depends, HTTPException, status

app = FastAPI()


# solved.ac API 기본 주소
SOLVED_AC_API_URL = "https://solved.ac/api/v3"

#유저 정보 받아오기
@app.get("/baekjoon/user/{handle}")
async def get_solved_ac_user(handle: str):
    """
    특정 백준 핸들(아이디)의 정보를 solved.ac에서 가져옵니다.
    """
    # 1. httpx 클라이언트 생성 (비동기)
    async with httpx.AsyncClient() as client:
        try:
            # 2. solved.ac API 호출
            response = await client.get(
                f"{SOLVED_AC_API_URL}/user/show",
                params={"handle": handle},
                headers={"Content-Type": "application/json"}
            )
            
            # 3. 응답 상태 코드 확인 (200 OK가 아니면 에러 발생)
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="해당 백준 아이디를 찾을 수 없습니다.")
            
            response.raise_for_status()
            
            # 4. JSON 데이터 파싱
            data = response.json()
            
            # 5. 필요한 정보만 골라서 리턴 (예: 티어, 푼 문제 수)
            return {
                "handle": data.get("handle"),
                "tier": data.get("tier"),
                "solved_count": data.get("solvedCount"),
                "rating": data.get("rating"),
                "profile_image": data.get("profileImageUrl")
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="solved.ac API 통신 중 오류가 발생했습니다.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")


#난이도별 푼 문제수 (tag_ratings : 푼 문제의 태그)
@app.get("/baekjoon/user/{handle}/stats")
async def get_user_tag_stats(handle: str):
    """
    유저가 어떤 알고리즘 태그를 몇 문제 풀었는지 통계를 가져옵니다.
    """
    async with httpx.AsyncClient() as client:
        try:
            # 1. 태그별 통계 API 호출
            response = await client.get(
                f"{SOLVED_AC_API_URL}/user/problem_stats",
                params={"handle": handle}
            )
            response.raise_for_status()
            stats_data = response.json() # 리스트 형태 [{}, {}, ...]

            # 2. 데이터 가공 (태그명과 푼 문제 수만 추출)
            # stats_data는 각 태그 객체들의 리스트입니다.
            refined_stats = []
            for item in stats_data:
                tag = item.get("tag")
                if not tag: # tag 객체가 없으면 스킵
                    continue
                
                # displayNames 리스트가 있고, 최소 하나 이상의 원소가 있는지 확인
                display_names = tag.get("displayNames", [])
                display_name = display_names[0].get("name") if display_names else tag.get("key")

                refined_stats.append({
                    "tag_name": tag.get("key"),
                    "display_name": display_name,
                    "solved_count": item.get("solved", 0),
                    "exp": item.get("exp", 0)
                })

            # 3. 많이 푼 순서대로 정렬 (내림차순)
            refined_stats.sort(key=lambda x: x["solved_count"], reverse=True)

            return {
                "handle": handle,
                "top_tags": refined_stats[:10]  # 상위 10개 태그만 반환
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))