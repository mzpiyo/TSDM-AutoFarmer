import httpx
import re
import time
import os
import sys

COOKIE = os.environ.get('TSDM_COOKIE', '')

def send(title, message):
    print(f"【{title}】{message}")

def get_common_headers(referer="https://www.tsdm39.com/forum.php"):
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Cookie": COOKIE,
        "Referer": referer
    }

def extract_formhash(html_text):
    pattern = r'(?:formhash=|name="formhash"\s+value="|var\s+formhash\s*=\s*[\'"])([a-zA-Z0-9]{8})'
    match = re.search(pattern, html_text)
    return match.group(1) if match else None

def tsdm_check_in():
    headers = get_common_headers()
    with httpx.Client(headers=headers, follow_redirects=True, timeout=15) as client:
        try:
            response = client.get("https://www.tsdm39.com/forum.php")
            formhash_value = extract_formhash(response.text)
            
            if not formhash_value:
                return "❌ 签到异常: 获取formhash失败 (HTML结构可能已大变或Cookie失效)"

            payload = {
                "formhash": formhash_value, 
                "qdxq": "kx", 
                "qdmode": "3", 
                "todaysay": "", 
                "fastreply": "1"
            }
            
            url_params = {
                "id": "dsu_paulsign:sign",
                "operation": "qiandao",
                "infloat": "1",
                "sign_as": "1",
                "inajax": "1"
            }
            
            response = client.post(
                "https://www.tsdm39.com/plugin.php",
                params=url_params,
                data=payload
            )
            
            if "签到成功" in response.text or "恭喜你签到成功" in response.text:
                return "✅ 签到成功"
            elif "您今日已经签到" in response.text:
                return "✅ 今日已签到"
            else:
                return f"❌ 签到异常: 未知响应 (截取: {response.text[:50]})"
                
        except Exception as e:
            return f"❌ 签到异常: {str(e)}"

def tsdm_work():
    headers = get_common_headers("https://www.tsdm39.com/plugin.php?id=np_cliworkdz:work")
    headers["X-Requested-With"] = "XMLHttpRequest"
    
    work_params = {"id": "np_cliworkdz:work"}
    
    with httpx.Client(headers=headers, follow_redirects=True, timeout=15) as client:
        try:
            response = client.get("https://www.tsdm39.com/plugin.php", params=work_params)
            
            cooldown_match = re.search(r"等待.*?(\d+)小时.*?(\d+)分钟", response.text)
            if cooldown_match:
                return f"⏳ 打工冷却中: {cooldown_match.group()}"
            
            for i in range(6):
                client.post(
                    "https://www.tsdm39.com/plugin.php",
                    params=work_params,
                    data={"act": "clickad"}
                )
                time.sleep(3)

            response = client.post(
                "https://www.tsdm39.com/plugin.php",
                params=work_params,
                data={"act": "getcre"}
            )
            
            if "您已经成功领取了奖励" in response.text or "打工成功" in response.text:
                return "✅ 打工完成"
            elif "必须与上一次间隔" in response.text or "已经打过工" in response.text:
                return "✅ 今日已打工"
            else:
                return f"❌ 打工异常: 未知响应 (截取: {response.text[:50]})"
                
        except Exception as e:
            return f"❌ 打工异常: {str(e)}"

def get_score():
    headers = get_common_headers("https://www.tsdm39.com/home.php?mod=spacecp&ac=credit")
    with httpx.Client(headers=headers, follow_redirects=True, timeout=15) as client:
        try:
            response = client.get(
                "https://www.tsdm39.com/home.php", 
                params={"mod": "spacecp", "ac": "credit", "showcredit": "1"}
            )
            match = re.search(r'天使币[：:]\s*(\d+)', response.text)
            if match:
                return match.group(1)
            return "未匹配到天使币"
        except Exception as e:
            return f"获取失败({str(e)})"

def run_checkin():
    checkin_log = tsdm_check_in()
    score = get_score()
    send("签到完成", f"{checkin_log} | 当前天使币: {score}")

def run_work():
    work_log = tsdm_work()
    score = get_score()
    send("打工完成", f"{work_log} | 当前天使币: {score}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "checkin":
            run_checkin()
        elif sys.argv[1] == "work":
            run_work()
        else:
            print("Invalid command. Use 'checkin' or 'work'")
    else:
        run_checkin()
        run_work()
