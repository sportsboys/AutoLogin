from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By #按照什么方式查找，By.ID,By.CSS_SELECTOR
from selenium.webdriver.common.keys import Keys #键盘按键操作
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait #等待页面加载某些元素
from selenium.webdriver.chrome.options import Options
import time
import random


# 加启动配置 禁用日志log
chrome_options = Options()
chrome_options.add_argument('–no-sandbox')# “–no - sandbox”参数是让Chrome在root权限下跑
chrome_options.add_argument('–disable-dev-shm-usage')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_argument('--start-maximized')#最大化
chrome_options.add_argument('--incognito')#无痕隐身模式
chrome_options.add_argument("disable-cache")#禁用缓存
chrome_options.add_argument('log-level=3')
chrome_options.add_argument('disable-infobars')
chrome_options.add_argument('--headless')

url = "https://newids.seu.edu.cn/authserver/login?service=http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/*default/index.do"
dailyDone = False # 今日是否已经打卡

# 创建打卡记录log文件
def writeLog(text):
    with open('log.txt', 'a') as f:
        s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + text
        print(s)
        f.write(s + '\n')
        f.close()



def enterUserPW():
    # 创建账号密码文件，以后都不用重复输入
    # 1.1版本之后更新可以读取 chrome.exe 的位置，防止用户Chrome浏览器未安装到默认位置导致的程序无法执行
    try:
        with open("loginData.txt", mode='r', encoding='utf-8') as f:
            # 去掉换行符
            lines = f.readlines()
            user = lines[0].strip()
            pw = lines[1].strip()
            if len(lines) > 2:
                loc = lines[2].strip()
            else:
                loc = ""
            f.close()
    except FileNotFoundError:
        print("Welcome to AUTO DO THE F***ING DAILY JOB, copyright belongs to S.H.")
        with open("loginData.txt", mode='w', encoding='utf-8') as f:
            user = input('Please Enter Your Username: ')
            pw = input('Then Please Enter Your Password: ')
            loc = ""
            f.write(user + '\n')
            f.write(pw + '\n')
            f.close()

    return user, pw, loc
    

def login(user, pw, browser):
    browser.get(url)
    browser.implicitly_wait(10)
    
    # 填写用户名密码
    username = browser.find_element_by_id('username')
    password = browser.find_element_by_id('password')
    username.clear()
    password.clear()
    username.send_keys(user)
    password.send_keys(pw)

    # 点击登录
    login_button = browser.find_element_by_class_name('auth_login_btn')
    login_button.submit()

# 检查是否无text按钮
def check(text, browser):
    buttons = browser.find_elements_by_tag_name('button')
    for button in buttons:
        if button.get_attribute("textContent").find(text)>= 0:
            return True
    return False

if __name__ == "__main__":
    user, pw, browser_loc = enterUserPW()
    # 判断是否写入非默认安装位置的 Chrome 位置
    if len(browser_loc) > 10:
        chrome_options.binary_location = browser_loc
    
    localtime = time.localtime(time.time())
    set_minite = localtime.tm_min # 首次登陆的分钟时刻，代表以后每次在此分钟时刻打卡
    set_hour = localtime.tm_hour # 首次登陆的时钟时刻，代表以后每次在此时钟时刻打卡

    if set_hour > 9:
        set_hour = 7 # 如果首次登录超过上午10点，则以后默认在7点钟打卡
        first_time = True

    while True:
        try:
            # 登录打卡一次试一试
            browser = webdriver.Chrome('./chromedriver',options=chrome_options)
            print("------------------浏览器已启动----------------------")
            login(user, pw, browser)
            browser.implicitly_wait(10)
            time.sleep(10)

            # 确认是否打卡成功
            # 的确无新增按钮
            dailyDone = not check("新增", browser)
            if dailyDone is True and check("退出", browser) is True: # 今日已完成打卡
                sleep_time = (set_hour+24-time.localtime(time.time()).tm_hour)*3600 + (set_minite-time.localtime(time.time()).tm_min)*60
                writeLog("下次打卡时间：明天" + str(set_hour) + ':' + str(set_minite) + "，" + "即" + str(sleep_time) + 's后')
                browser.close()
                print("------------------浏览器已关闭----------------------")
                time.sleep(sleep_time)
            elif dailyDone is False: # 今日未完成打卡
                # 点击报平安
                buttons = browser.find_elements_by_css_selector('button')
                for button in buttons:
                    if button.get_attribute("textContent").find("新增")>= 0:
                        button.click()
                        browser.implicitly_wait(10)

                        # 输入温度37°
                        inputfileds = browser.find_elements_by_tag_name('input')
                        for i in inputfileds:
                            if i.get_attribute("placeholder").find("请输入当天晨检体温") >= 0:
                                i.click()
                                i.send_keys(str(random.randint(365,370)/10.0))

                                #确认并提交
                                buttons = browser.find_elements_by_tag_name('button')
                                for button in buttons:
                                    if button.get_attribute("textContent").find("确认并提交") >= 0:
                                        button.click()
                                        buttons = browser.find_elements_by_tag_name('button')
                                        button = buttons[-1]
                                        # 提交
                                        if button.get_attribute("textContent").find("确定") >= 0:
                                            button.click()
                                            dailyDone = True # 标记已完成打卡
                                            writeLog("打卡成功")
                                        break
                                break
                        break
                browser.close()
                print("------------------浏览器已关闭----------------------")
                time.sleep(10) # 昏睡10s 为了防止网络故障未打上卡
            else:
                browser.close()
                print("------------------网站出现故障----------------------")
                print("------------------浏览器已关闭----------------------")
                time.sleep(300) # 昏睡5min 为了防止网络故障未打上卡
        except Exception as r:
            print("未知错误 %s" %(r))

