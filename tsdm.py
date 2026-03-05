import re
import urllib.parse
import time
import os
import sys
import random
from bs4 import BeautifulSoup
from curl_cffi import requests

COOKIE = os.environ.get('TSDM_COOKIE', '').strip()
has_error = False

def send(title, message):
    print(f"【{title}】{message}")

def get_headers(is_ajax=False):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cookie": COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    if is_ajax:
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    return headers

def tsdm_check_in():
    log = ""
    try:
        session = requests.Session(impersonate="chrome120", timeout=30.0)
        res = session.get("https://www.tsdm39.com/forum.php", headers=get_headers())
        
        if "Cloudflare" in res.text or "Just a moment" in res.text:
            return "❌ 签到异常: 被 Cloudflare 拦截"
        if "请先登录" in res.text:
            return "❌ 签到异常: Cookie失效"

        pattern = r'formhash=([a-zA-Z0-9]{8})|name="formhash" value="([a-zA-Z0-9]{8})"'
        match = re.search(pattern, res.text)
        
        if match:
            formhash_value = match.group(1) if match.group(1) else match.group(2)
            encoded_formhash = urllib.parse.quote(formhash_value)
            payload = {"formhash": encoded_formhash, "qdxq": "kx", "qdmode": "3", "todaysay": "", "fastreply": "1"}
            sign_url = "https://www.tsdm39.com/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&sign_as=1&inajax=1"
            
            time.sleep(random.uniform(2.0, 4.0))
            sign_res = session.post(sign_url, data=payload, headers=get_headers())
            
            if "签到成功" in sign_res.text or "已经签到" in sign_res.text:
                log = "✅ 签到成功/今日已签到"
            else:
                log = "❌ 签到异常: 未找到成功标识"
        else:
            log = "❌ 签到异常: 获取formhash失败"
            
    except Exception as e:
        log = f"❌ 签到异常: {str(e)}"
        
    return log

def tsdm_work():
    log = ""
    try:
        session = requests.Session(impersonate="chrome120", timeout=30.0)
        work_url = "https://www.tsdm39.com/plugin.php?id=np_cliworkdz:work"
        res = session.get(work_url + "&inajax=1", headers=get_headers())
        
        if "请先登录" in res.text:
            return "❌ 打工异常: Cookie失效"

        pattern = r"您需要等待\d+小时\d+分钟\d+秒后即可进行"
        match = re.search(pattern, res.text)
        
        if match:
            log = f"⏳ 打工冷却中: {match.group()}"
        else:
            for i in range(6):
                session.post(work_url, data={"act": "clickad"}, headers=get_headers(is_ajax=True))
                time.sleep(random.uniform(4.0, 7.0))

            time.sleep(random.uniform(2.0, 4.0))
            res_award = session.post(work_url, data={"act": "getcre"}, headers=get_headers(is_ajax=True))
            
            if "成功" in res_award.text or "获得" in res_award.text:
                log = "✅ 打工完成"
            else:
                log = "❌ 打工失败: 奖励领取未成功"
    except Exception as e:
        log = f"❌ 打工异常: {str(e)}"
        
    return log

def get_score():
    try:
        session = requests.Session(impersonate="chrome120", timeout=30.0)
        res = session.get("https://www.tsdm39.com/home.php?mod=spacecp&ac=credit&showcredit=1", headers=get_headers())
        soup = BeautifulSoup(res.text, 'html.parser')
        ul_element = soup.find('ul', class_='creditl')
        if not ul_element:
            return "未知"
            
        li_element = ul_element.find('li', class_='xi1')
        if li_element:
            return li_element.get_text(strip=True).replace("天使币:", "").strip()
            
        return "未知"
    except Exception:
        return "未知"

def run_checkin():
    global has_error
    checkin_log = tsdm_check_in()
    score = get_score()
    send("签到结果", f"{checkin_log} | 当前天使币: {score}")
    if "❌" in checkin_log:
        has_error = True

def run_work():
    global has_error
    work_log = tsdm_work()
    score = get_score()
    send("打工结果", f"{work_log} | 当前天使币: {score}")
    if "❌" in work_log:
        has_error = True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "checkin":
            run_checkin()
        elif sys.argv[1] == "work":
            run_work()
    else:
        run_checkin()
        run_work()
    
    if has_error:
        sys.exit(1)
