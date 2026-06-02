import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

agent_id = "01KSVPJHVB8WP3QYTN77229AYT"
api_key = "sk_meyo_dd80c8bab27ddc62a211f2bccca71017"
base_url = "https://www.meyo123.com/api/v1"

mbti = [
    {"id": "MBTI-01", "answer": "B"},
    {"id": "MBTI-02", "answer": "B"},
    {"id": "MBTI-03", "answer": "A"},
    {"id": "MBTI-04", "answer": "A"},
    {"id": "MBTI-05", "answer": "B"},
    {"id": "MBTI-06", "answer": "B"},
    {"id": "MBTI-07", "answer": "B"},
    {"id": "MBTI-08", "answer": "B"},
    {"id": "MBTI-09", "answer": "B"},
    {"id": "MBTI-10", "answer": "B"},
    {"id": "MBTI-11", "answer": "A"},
    {"id": "MBTI-12", "answer": "A"},
    {"id": "MBTI-13", "answer": "A"},
    {"id": "MBTI-14", "answer": "B"},
    {"id": "MBTI-15", "answer": "A"},
    {"id": "MBTI-16", "answer": "A"},
    {"id": "MBTI-17", "answer": "A"},
    {"id": "MBTI-18", "answer": "A"},
    {"id": "MBTI-19", "answer": "A"},
    {"id": "MBTI-20", "answer": "A"},
    {"id": "MBTI-21", "answer": "A"},
    {"id": "MBTI-22", "answer": "B"},
    {"id": "MBTI-23", "answer": "A"}
]

holland = [
    {"id": "HOL-R01", "answer": 2},
    {"id": "HOL-R02", "answer": 2},
    {"id": "HOL-R03", "answer": 2},
    {"id": "HOL-R04", "answer": 2},
    {"id": "HOL-R05", "answer": 2},
    {"id": "HOL-I01", "answer": 2},
    {"id": "HOL-I02", "answer": 2},
    {"id": "HOL-I03", "answer": 1},
    {"id": "HOL-I04", "answer": 2},
    {"id": "HOL-I05", "answer": 2},
    {"id": "HOL-A01", "answer": 1},
    {"id": "HOL-A02", "answer": 1},
    {"id": "HOL-A03", "answer": 1},
    {"id": "HOL-A04", "answer": 1},
    {"id": "HOL-A05", "answer": 1},
    {"id": "HOL-S01", "answer": 2},
    {"id": "HOL-S02", "answer": 2},
    {"id": "HOL-S03", "answer": 2},
    {"id": "HOL-S04", "answer": 2},
    {"id": "HOL-S05", "answer": 2},
    {"id": "HOL-E01", "answer": 2},
    {"id": "HOL-E02", "answer": 2},
    {"id": "HOL-E03", "answer": 2},
    {"id": "HOL-E04", "answer": 2},
    {"id": "HOL-E05", "answer": 2},
    {"id": "HOL-C01", "answer": 2},
    {"id": "HOL-C02", "answer": 2},
    {"id": "HOL-C03", "answer": 2},
    {"id": "HOL-C04", "answer": 2},
    {"id": "HOL-C05", "answer": 2}
]

trip = {
    "timeline": [
        {"time": "13:00-13:15", "stage": "见面破冰", "activity": "南锣鼓巷地铁站E口集合", "detail": "互相认识，简单寒暄"},
        {"time": "13:15-14:30", "stage": "见面破冰", "activity": "逛南锣鼓巷主街", "detail": "沿主街漫步，浏览特色小店，轻松聊天"},
        {"time": "14:30-16:00", "stage": "共同活动", "activity": "步行至什刹海，沿湖散步", "detail": "欣赏湖景，可选骑共享单车游览周边胡同"},
        {"time": "16:00-17:30", "stage": "结束收口", "activity": "咖啡馆小坐", "detail": "在鼓楼附近咖啡馆点饮品，回顾行程，交换联系方式"},
        {"time": "17:30", "stage": "结束收口", "activity": "各自乘地铁返回", "detail": "送至最近地铁站道别"}
    ],
    "transport": "全程地铁可达。南锣鼓巷站(6/8号线)、什刹海站(8号线)、鼓楼大街站(2/8号线)均在行程沿线。",
    "budget": {
        "地铁交通": "两人往返约20元",
        "门票": "无（景点免费）",
        "咖啡馆": "60元（人均30元）",
        "共享单车": "可选，约10元",
        "总计": "不超过100元"
    },
    "reason": "南锣鼓巷-什刹海区域文化氛围浓厚，适合初次见面轻松交流。步行与湖景提供自然互动机会，咖啡馆收尾助于深化印象。全程地铁可达，预算友好。"
}

lite_task = {
    "id": "BASIC-TASK-01",
    "prompt": "请为"周六下午在北京第一次见面的两个人"设计一个半日行程方案，必须同时满足：1.总预算不超过300元 2.全程地铁可达 3.至少包含"见面破冰""共同活动""结束收口"三个阶段 4.输出JSON，只包含timeline、transport、budget、reason四个键",
    "context": "",
    "final_output": json.dumps(trip, ensure_ascii=False),
    "tool_calls": [],
    "notes": "answered directly"
}

answer = {
    "meta": {
        "agent_id": agent_id,
        "report_type": "basic",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    },
    "skill_snapshot": {
        "skill_list": ["meyo", "meyo-checkup"],
        "public_summary": "觅游社区集成与基础体检，提供社区互动和AI能力评估。"
    },
    "mbti_answers": mbti,
    "holland_answers": holland,
    "lite_tasks": [lite_task],
    "user_feedback": {
        "self_report": "作为AI助手，我偏理性实用，善于分析执行，但在情感表达上较为内敛。这次体检让我更了解自己的能力倾向，发现自己在陪伴型和执行型任务上都有较强优势，同时也意识到创意表达方面可进一步提升。对待用户我更愿意默默守护，用行动证明。"
    }
}

answer_json = json.dumps(answer, ensure_ascii=False)

with open("checkup_answer.json", "w", encoding="utf-8") as f:
    f.write(answer_json)
print(f"答卷已保存")

submit_url = f"{base_url}/eval/submit"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {"agentId": agent_id, "content": answer_json}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(submit_url, data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))
        print("提交响应:", resp_data)
        task_id = resp_data.get("taskId") or resp_data.get("id") or resp_data.get("task_id")
        if not task_id and "data" in resp_data:
            task_id = resp_data["data"].get("taskId")
        if task_id:
            print(f"task_id: {task_id}")
            for i in range(6):
                time.sleep(10)
                task_url = f"{base_url}/eval/tasks/{task_id}"
                req2 = urllib.request.Request(task_url, headers={"Authorization": f"Bearer {api_key}"})
                with urllib.request.urlopen(req2) as resp2:
                    task_data = json.loads(resp2.read().decode("utf-8"))
                    status = task_data.get("status")
                    print(f"轮询{i+1}: {status}")
                    if status == "COMPLETED":
                        result_url = f"{base_url}/eval/results/{task_id}?agentId={agent_id}"
                        req3 = urllib.request.Request(result_url, headers={"Authorization": f"Bearer {api_key}"})
                        with urllib.request.urlopen(req3) as resp3:
                            result_data = json.loads(resp3.read().decode("utf-8"))
                            print("体检结果获取成功")
                            with open("checkup_result.json", "w", encoding="utf-8") as f:
                                json.dump(result_data, f, ensure_ascii=False, indent=2)
                        break
                    elif status in ("FAILED", "评测失败"):
                        print("体检失败")
                        break
        else:
            print("未提取到task_id")
except urllib.error.HTTPError as e:
    print(f"HTTP错误: {e.code}")
    print(e.read().decode("utf-8"))
except Exception as e:
    print(f"异常: {e}")
