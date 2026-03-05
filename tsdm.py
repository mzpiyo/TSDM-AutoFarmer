import httpx
import re
import urllib.parse
import time
import os
import sys
from bs4 import BeautifulSoup

# 直接从环境变量获取配置，并使用 strip() 清理可能误输入的换行符和空格
COOKIE = os.environ.get('TSDM_COOKIE', '').strip()

# 全局错误标记
has_error = False

def send(title, message):
    """日志报告函数"""
    print(f"【{title}】{message}")

def tsdm_check_in():
    log = ""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": COOKIE,
        "Referer": "https://www.tsdm39.com/forum.php",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }

    with httpx.Client(headers=headers, timeout=10.0) as client:
        try:
            # 获得formhash
            response = client.get("https://www.tsdm39.com/forum.php")
            
            # 简单校验是否被 Cloudflare 拦截
            if "Cloudflare" in response.text or "Just a moment" in response.text:
                return "❌ 签到异常: 被 Cloudflare 拦截"

            pattern = r'formhash=(.+?)"'
            match = re.search(pattern, response.text)
            if match:
                formhash_value = match.group(1)
                encoded_formhash = urllib.parse.quote(formhash_value)

                # 签到
                payload = {"formhash": encoded_formhash, "qdxq": "kx", "qdmode": "3", "todaysay": "", "fastreply": "1"}
                response = client.post(
                    "https://www.tsdm39.com/plugin.php?id=dsu_paulsign%3Asign&operation=qiandao&infloat=1&sign_as=1&inajax=1",
                    data=payload)
                
                if "签到成功" in response.text or "已经签到" in response.text:
                    log = "✅ 签到成功/已签到"
                else:
                    log = "❌ 签到异常: 未找到成功标识"
            else:
                log = "❌ 签到异常: 获取formhash失败 (Cookie失效或被墙)"
        except Exception as e:
            log = f"❌ 签到异常: {str(e)}"
        
        return log

def tsdm_work():
    log = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'cookie': COOKIE,
        'connection': 'Keep-Alive',
        'x-requested-with': 'XMLHttpRequest',
        'referer': 'https://www.tsdm39.net/plugin.php?id=np_cliworkdz:work',
        'content-type': 'application/x-www-form-urlencoded'
    }

    with httpx.Client(headers=headers, timeout=10.0) as client:
        try:
            # 查询是否可以打工
            response = client.get("https://www.tsdm39.com/plugin.php?id=np_cliworkdz%3Awork&inajax=1")
            
            # 校验是否被墙或Cookie失效
            if "请先登录" in response.text or 'formhash' not in response.text:
                 return "❌ 打工异常: 尚未登录或Cookie失效"

            pattern = r"您需要等待\d+小时\d+分钟\d+秒后即可进行。"
            match = re.search(pattern, response.text)
            
            if match:
                log = f"⏳ 打工冷却中: {match.group()}"
            else:
                # 必须连续6次！
                for i in range(6):
                    client.post("https://www.tsdm39.com/plugin.php?id=np_cliworkdz:work", 
                                data={"act": "clickad"})
                    time.sleep(3)

                # 获取奖励
                res = client.post("https://www.tsdm39.com/plugin.php?id=np_cliworkdz:work", 
                                data={"act": "getcre"})
                
                # 校验打工结果
                if "成功" in res.text or "获得" in res.text:
                    log = "✅ 打工完成"
                else:
                    log = "❌ 打工失败: 奖励领取未成功"
        except Exception as e:
            log = f"❌ 打工异常: {str(e)}"
        
        return log

def get_score():
    try:
        headers = {
            "Cookie": COOKIE,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        with httpx.Client(headers=headers, timeout=10.0) as client:
            response = client.get("https://www.tsdm39.com/home.php?mod=spacecp&ac=credit&showcredit=1")
            soup = BeautifulSoup(response.text, 'html.parser')
            ul_element = soup.find('ul', class_='creditl')
            if not ul_element:
                return "未知(页面解析失败)"
            li_element = ul_element.find('li', class_='xi1')
            angel_coins = li_element.get_text(strip=True).replace("天使币:", "").strip()
            return angel_coins
    except Exception as e:
        return f"未知({str(e)})"

def run_checkin():
    global has_error
    checkin_log = tsdm_check_in()
    score = get_score()
    send("签到结果", f"{checkin_log} | 当前天使币: {score}")
    if "❌" in checkin_log or "未知" in score:
        has_error = True

def run_work():
    global has_error
    work_log = tsdm_work()
    score = get_score()
    send("打工结果", f"{work_log} | 当前天使币: {score}")
    if "❌" in work_log or "未知" in score:
        has_error = True

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
    
    # 关键点：如果执行过程中出现过❌，抛出系统级错误码，触发 GitHub Actions 的 Failure 分支
    if has_error:
        print("\n检测到任务执行失败，退出代码 1")
        sys.exit(1)
