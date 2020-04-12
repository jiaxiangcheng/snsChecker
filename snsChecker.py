# webdriver
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ohter useful libraries
from io import StringIO
from bs4 import BeautifulSoup
from time import sleep
import requests
import pycurl
import subprocess
import csv
import pickle   # cookies
from threading import Thread
from datetime import datetime
import sys, os

# for machineID and userID
import getpass
import socket

# to use mongoDB
from pymongo import MongoClient

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def create_proxyauth_extension(threadID, proxy_host, proxy_port,proxy_username, proxy_password,scheme='http', plugin_path=None):
    """Proxy Auth Extension

    args:
        proxy_host (str): domain or ip address, ie proxy.domain.com
        proxy_port (int): port
        proxy_username (str): auth username
        proxy_password (str): auth password
    kwargs:
        scheme (str): proxy scheme, default http
        plugin_path (str): absolute path of the extension       

    return str -> plugin_path
    """
    import string
    import zipfile

    if getattr(sys, 'frozen', False):
        proxyPath = "proxy" + threadID + ".zip" #proxy file name"
    else:
        proxyPath = "proxy" + threadID + ".zip"

    if plugin_path is None:
        plugin_path = proxyPath

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
    """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "${scheme}",
                host: "${host}",
                port: parseInt(${port})
              },
              bypassList: ["foobar.com"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "${username}",
                password: "${password}"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path

def getPage(url):
    try:
        buffer = StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEFUNCTION, buffer.write)
        c.perform()
        c.close()
        html = buffer.getvalue()
        return BeautifulSoup(html, "html.parser")
    except KeyboardInterrupt:
        exit()
    except:
        return None

def capthaByPass(driver, threadID):
    API_KEY = 'ed46d20463af59005b4236ff493a2cac'  # Your 2captcha API KEY
    site_key = '6LfBixYUAAAAABhdHynFUIMA_sa4s-XsJvnjtgB0'  # site-key, read the 2captcha docs on how to get this
    url = 'https://www.sneakersnstuff.com/en'  # url which want to BP
    captchaSolverDelay = 5

    s = requests.Session()
    # here we post site key to 2captcha to get captcha ID (and we parse it here too)
    captcha_id = s.post("http://2captcha.com/in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}".format(API_KEY, site_key, url)).text.split('|')[1]
    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Captcha id for page " + url + " ---> " + captcha_id)
    # then we parse gresponse from 2captcha response
    recaptcha_answer = s.get(
        "http://2captcha.com/res.php?key={}&action=get&id={}".format(API_KEY, captcha_id)).text
    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "THREAD " + threadID + " ----> " + "Start to solving the captcha" + bcolors.ENDC)
    
    while 'CAPCHA_NOT_READY' in recaptcha_answer:
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "CAPCHA_NOT_READY, waiting for " + str(captchaSolverDelay) + " seconds" )
        sleep(captchaSolverDelay)
        recaptcha_answer = s.get(
            "http://2captcha.com/res.php?key={}&action=get&id={}".format(API_KEY, captcha_id)).text
    recaptcha_answer = recaptcha_answer.split('|')[1]
    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Recaptcha answer id for captcha ID: " + captcha_id + " ---> " + recaptcha_answer)
    js = "document.getElementById('g-recaptcha-response').textContent = " + '"' + recaptcha_answer + '"'
    driver.execute_script(js)
    js = "document.getElementById('recaptcha_submit').click()"
    driver.execute_script(js)

    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKGREEN + "THREAD " + threadID + " ----> " + "Captcha solved :)" + bcolors.ENDC)
    return 

def searchOrder(driver, account, password, threadID, productName):
    waitTimeout = 20

    # log in
    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Start to login")
    WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.CLASS_NAME, "account")))
    driver.find_element_by_class_name("account").click()
    WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.ID, "emailInput")))
    WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.ID, "passwordInput")))
    emialField = driver.find_element_by_id("emailInput")
    passwordField = driver.find_element_by_id("passwordInput")

    # filling email
    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Filling email address")
    emialField.send_keys(account)
    sleep(1)
    passwordField.send_keys("")
    if len(driver.find_elements_by_id("error-emailInput")) > 0 :
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Wrong email address")
        return False, None

    # filling password
    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Filling password")
    passwordField.send_keys(password)
    sleep(1)

    # click the login btn
    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Login")
    WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.CLASS_NAME, "auth__btn")))
    driver.find_element_by_class_name("auth__btn").click()
    sleep(1)
    if len(driver.find_elements_by_class_name("error-message")) > 0:
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Email or password is incorrect")
        return False, None
    sleep(2)

    html = driver.page_source
    html = BeautifulSoup(html, "html.parser")

    # search for any history order
    if html.find(id = "order-history-trigger") is not None:
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Find history order!")
        WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.ID, "order-history-trigger")))
        driver.find_element_by_id("order-history-trigger").click()
        sleep(1)
        historyOrders = driver.find_elements_by_class_name("order-history-table__tr")
        # search the corret history order
        if len(historyOrders) > 0:
            for order in historyOrders:
                order.click()
                sleep(1)
                modalBodyHtml = BeautifulSoup(driver.page_source, "html.parser")
                modalDialogHtml = modalBodyHtml.find(class_ = "modal-dialog--order")
                modalContentHtml = modalDialogHtml.find(class_ = "modal-content")
                modalBodyHtml = modalContentHtml.find(class_ = "modal-body")
                modalOrderBody = modalBodyHtml.findAll("tr")
                found = False
                if len(modalOrderBody) > 0:
                    for row in modalOrderBody:
                        if productName.lower() in row.getText().lower():
                            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKGREEN + "THREAD " + threadID + " ----> " + "Item Found!" + bcolors.ENDC)
                            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE +  "THREAD " + threadID + " ----> " + "Redirecting to tracking page" + bcolors.ENDC)
                            windowBefore = driver.window_handles[0]
                            WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Track")))
                            driver.find_element_by_partial_link_text("Track").click()
                            sleep(1)
                            windowAfter = driver.window_handles[1]
                            found = True
                            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Getting the tracking number")
                            trackingNumber = getTrackingID(driver, windowBefore, windowAfter, account)
                            driver.close()
                            driver.switch_to.window(windowBefore)
                            sleep(1)
                            driver.find_elements_by_class_name("modal-btn-close")[1].click()
                            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Sign out")
                            WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Sign")))
                            driver.find_element_by_partial_link_text("Sign").click()
                            return True, trackingNumber
                    if not found:
                        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.FAIL + "THREAD " + threadID + " ----> " + "Didn't find product containing " + productName + bcolors.ENDC)
                        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Checking the next order")
    else:
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.FAIL + "THREAD " + threadID + " ----> " + "Didn't find any history order!" + bcolors.ENDC)
        # sign out
        WebDriverWait(driver, waitTimeout).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Sign")))
        driver.find_element_by_partial_link_text("Sign").click()
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Sign out")
        return False, None

def getTrackingID(driver, windowBefore, windowAfter, account):
    driver.switch_to.window(windowAfter)
    sleep(1)
    trackingNumbers = str(driver.current_url)
    auxPosition = trackingNumbers.rfind("/")
    trackingNumbers = trackingNumbers[:auxPosition]
    auxPosition = trackingNumbers.rfind("=") + 1
    trackingNumbers = trackingNumbers[auxPosition:]

    if getattr(sys, 'frozen', False):
        filePath = sys._MEIPASS + "/trackingNumbers.csv"
    else:
        filePath = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/trackingNumbers.csv"

    with open(filePath, "a+") as fd:
        fd.write(trackingNumbers + "," + account+ "\n")
    return trackingNumbers

def readCSV(filePath, type):
    data = []
    with open(filePath) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        count = 0
        for row in csv_reader:
            # row[0] -> column 0
            if row != "":
                if ":" not in row[0]:
                    if type == "accounts":
                        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.FAIL + "Wrong format in the accounts file." + bcolors.ENDC)
                    else: 
                        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.FAIL + "Wrong format in the proxies file." + bcolors.ENDC)
                    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Terminating the script and try again!" + bcolors.ENDC)
                    sys.exit()
                splited = str(row[0]).split(":")
                if type == "accounts":
                    email = splited[0]
                    password = splited[1]
                    data.append({"email": email, "password": password})
                else:
                    domain = splited[0]
                    port = splited[1]
                    username = splited[2]
                    password = splited[3]
                    data.append({"domain": domain, "port": port, "username": username, "password": password})
                count += 1
    if type == "accounts":
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "Processed " + str(count) + " accounts.")
    else:
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "Processed " + str(count) + " proxies.")
    return data



def task(threadID, options, url, accounts, productName, proxy):
    if getattr(sys, 'frozen', False):
        driverPath = sys._MEIPASS + "/chromedriver"
    else:
        driverPath = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/chromedriver"

    if options !=  "LOCALHOST":
        driver = webdriver.Chrome(executable_path = driverPath, options=options) 
    else:
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "THREAD " + threadID + " ----> " + "running on local host" + bcolors.ENDC)
        driver = webdriver.Chrome(executable_path = driverPath) 
    driver.get(url)
    sleep(1)

    if "access denied" in driver.title.lower():
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.FAIL + "THREAD " + threadID + " ----> " + "Acess denied" + bcolors.ENDC)
        driver.close()
    else:
        # check if proxy is valid or not
        if len(driver.find_elements_by_id("main-frame-error")) > 0:
            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.FAIL + "THREAD " + threadID + " ----> " + "Proxy error" + bcolors.ENDC)
            driver.close()
        else:
            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKGREEN + "THREAD " + threadID + " ----> " + "running on " + proxy + bcolors.ENDC)
            if "machine" in driver.title.lower():
                capthaByPass(driver, threadID)
            else:
                if "1999" in driver.title:
                    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "THREAD " + threadID + " ----> " + "No captcha needed" + bcolors.ENDC)

            for account in accounts:
                print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.HEADER + "------------------------------------------------------------------------------------------------------------" + bcolors.ENDC)
                print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.HEADER + "THREAD " + threadID + " ----> " + "Searching on: " + str(account) + bcolors.ENDC)
                print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.HEADER + "------------------------------------------------------------------------------------------------------------" + bcolors.ENDC)
                
                [found, trackingNumber] = searchOrder(driver, account["email"], account["password"], threadID, productName)
                sleep(1)

                if found:
                    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKGREEN + "THREAD " + threadID + " ----> " + "Saving tracking number: " + trackingNumber + " for the account: " + account["email"] + bcolors.ENDC)
                else:
                    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + threadID + " ----> " + "Repeat the process for next acount")
            
            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKGREEN + "THREAD " + threadID + " ----> " + "Finished all searching" + bcolors.ENDC)
            driver.close()

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def getLocalIdentifies():
    return getpass.getuser(), socket.gethostname()

def sendActivationkey(licenses, availableKeys, key):
    localKey = key
    endLoop = False

    validKeys = availableKeys.find()
    keys = []
    for item in validKeys:
        keys.append(item["key"])

    while not endLoop:
        # check if key is valid
        if localKey in keys:
            # activate only if not exists
            [userId, machineId] = getLocalIdentifies()
            if not licenses.count_documents({"userId": userId, "machineId": machineId, "key": localKey}) > 0:
                id = licenses.count_documents({})
                license = {"_id": id, "userId": userId, "machineId": machineId, "key": localKey}
                licenses.insert_one(license)
                print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKGREEN + "Key registered successful! Restart the script please." + bcolors.ENDC)
                endLoop = True
            else:
                print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.WARNING + "Key already registered on other device! Try another one:" + bcolors.ENDC)
                localKey = input()
        else:
            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.WARNING + "Invalid key!" + bcolors.ENDC)
            localKey = input()

def alreadyRegistered(licenses):
    [userId, machineId] = getLocalIdentifies()
    if licenses.count_documents({"userId": userId, "machineId": machineId}) > 0:
        return True
    else:
        return False

def printLogo():
    print("""\

    __  __                     __  __               __                   
   / / / /__  __ ____   ___   / / / /__  __ ____   / /_ ___   _____ _____
  / /_/ // / / // __ \ / _ \ / /_/ // / / // __ \ / __// _ \ / ___// ___/
 / __  // /_/ // /_/ //  __// __  // /_/ // / / // /_ /  __// /   (__  ) 
/_/ /_/ \__, // .___/ \___//_/ /_/ \__,_//_/ /_/ \__/ \___//_/   /____/  
       /____//_/                                                         
                                                                                               
    """)

def main():
    
    printLogo()

    # Files path
    if getattr(sys, 'frozen', False):
        accountsPath = sys._MEIPASS + "/accounts.csv"
        proxiesPath = sys._MEIPASS + "/proxies.csv"
    else:
        accountsPath = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/accounts.csv"
        proxiesPath = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/proxies.csv"

    ##########################
    # Connect to DB          #
    ##########################

    mongoClient = MongoClient('mongodb+srv://admin:admin@cluster0-ojxmr.mongodb.net/test?retryWrites=true&w=majority')
    db = mongoClient.sns
    licenses = db.licenses
    availableKeys = db.availableKeys

    if not alreadyRegistered(licenses):
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Please input your activation key:" + bcolors.ENDC)
        key = input()
        sendActivationkey(licenses, availableKeys, key)
    else:
        ##########################
        # read input from user   #
        ##########################
        isInt = False
        numBrowsers = 1
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Choose the number of browsers to open:" + bcolors.ENDC)
        while not isInt:
            numBrowsers = input()
            if RepresentsInt(numBrowsers):
                numBrowsers = int(numBrowsers)
                isInt = True
            else:
                print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.WARNING + "Please enter a correct integer number!" + bcolors.ENDC)

        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "The name of the product:" + bcolors.ENDC)
        productName = input()
        url = "https://www.sneakersnstuff.com/en"
        
        print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Use localhost? True or False." + bcolors.ENDC)
        localHost = input()
        if localHost.lower() == "false":
            localHost = False
        elif localHost.lower() == "true":
            localHost = True

        # options.headless = True
        # options.add_argument("--window-size=%s" % WINDOW_SIZE)

        # read data from local files
        accounts = readCSV(accountsPath, "accounts")
        if not localHost:
            proxies = readCSV(proxiesPath, "proxies")
        accountsPerBrowser = int(len(accounts)) // int(numBrowsers)
        oneMore = False

        if int(len(accounts)) % int(numBrowsers) != 0:
            oneMore = True

        # check browser numbers
        if numBrowsers > len(accounts):
            sys.exit(bcolors.WARNING + "Number of browsers should less or equal to number of accounts!" + bcolors.ENDC)
        
        my_threads = []
        iterator = 0
        usedProxiesCount = 0
        for n in range(numBrowsers):
            currentProxy = ""
            if not localHost:
                # check proxies numbers, if not enough proxies then reuse them
                if usedProxiesCount <= len(proxies) - 1:
                    currentProxy = proxies[usedProxiesCount]['domain'] + ":" + proxies[usedProxiesCount]['port'] + ":" + proxies[usedProxiesCount]['username'] + ":" + proxies[usedProxiesCount]['password']
                    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Setting proxy for browser " + str(n) + bcolors.ENDC)
                    # set proxy for each browser
                    options = Options()
                    proxyauth_plugin_path = create_proxyauth_extension(
                        threadID=str(n),
                        proxy_host=proxies[usedProxiesCount]["domain"],
                        proxy_port=proxies[usedProxiesCount]["port"], 
                        proxy_username=proxies[usedProxiesCount]["username"],
                        proxy_password=proxies[usedProxiesCount]["password"]
                        )
                    options.add_extension(proxyauth_plugin_path)
                    usedProxiesCount += 1
                else:
                    print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Reusing proxies for browser " + str(n) + bcolors.ENDC)
                    sys.exit()
                    usedProxiesCount = 0
            else:
                options = "LOCALHOST"

            chunks = []
            if oneMore:
                oneMore = False
                chunks.append(accounts[len(accounts) - 1])
            for j in range(accountsPerBrowser):
                chunks.append(accounts[iterator + j])
            # print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + "THREAD " + str(n) + " ----> " + str(chunks))
            t = Thread(target=task, args=(str(n), options, url, chunks, productName, currentProxy))
            t.start()
            my_threads.append(t)
            iterator += accountsPerBrowser

        # all thread should wait here to finish
        for t in my_threads:
            t.join()

        # show the result file
        if getattr(sys, 'frozen', False):
            filePath = sys._MEIPASS + "/trackingNumbers.csv"
        else:
            filePath = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/trackingNumbers.csv"

        if os.path.exists(filePath):
            with open(filePath, "a+") as fd:
                fd.write("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"]\n")
            
            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Script ended, found some tracking number. Opening the file" + bcolors.ENDC)
            subprocess.call(['open', filePath])
        else:
            print("["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"] - " + bcolors.OKBLUE + "Script ended, no tracking number found" + bcolors.ENDC)

if __name__ == '__main__':
    main()


"""
There are many options here, to name a few:

If class alone is unique, you can use

driver.find_element_by_css_selector(".button_main").click()
If class + value combo is unique, you can use:

driver.find_element_by_css_selector(".button_main[value='something']").click()
You can also use xpath:

driver.find_element_by_xpath("//input[@type='submit' and @value='something']").click()
If none of those work (i.e. they are not identifying button uniquely), look at the elements above the button (for example <form) and provide the xpath in format:

driver.find_element_by_xpath("//unique_parent//input[@type="submit" and @value='something']").click()
"""