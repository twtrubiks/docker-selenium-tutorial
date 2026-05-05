# docker-selenium-tutorial

[Youtube Tutorial - docker-selenium-tutorial 教學 Python](https://youtu.be/pXOFmK0eVDk)

## 說明

以前在使用 selenium 時, 都需要先抓對應的 driver, 然後再開始使用,

如果電腦比較差, 跑起來又會比較慢, 而且也蠻吃電腦資源的, 所以今天

要來介紹 server 版本的 selenium 概念, 就是 docker-selenium, repo 如下

[https://github.com/SeleniumHQ/docker-selenium](https://github.com/SeleniumHQ/docker-selenium)

這樣子就可以把它執行在 server, 也不吃自己本機電腦的資源,

重點是大家還可以一起使用 :thumbsup:

> 本篇範例使用的 image tag 為 `4.43.0-20260404` (對應 Selenium 4.43),
> 上游版本更新很快, 直接用 `latest` 也可以, 但鎖版本比較好 reproduce.

## 介紹

- [Standalone (單機模式)](#standalone)
- [Headless mode](#headless-mode)
- [Video recording (錄影)](#video-recording)
- [Hub and Nodes (含 Edge)](#hub-and-nodes)
- [Dynamic Grid (每個 session 一個全新容器)](#dynamic-grid)

### Standalone

先來看一個例子 [docker-compose-standalone-firefox.yml](docker-compose-standalone-firefox.yml)

```yml
services:
  firefox:
    image: selenium/standalone-firefox:4.43.0-20260404
    shm_size: 2gb
    ports:
      - "4444:4444"
      - "7900:7900"
    # environment:
    #   - SE_VNC_NO_PASSWORD=1
    #   - SE_VNC_VIEW_ONLY=1
```

```cmd
docker compose -f docker-compose-standalone-firefox.yml up
```

進入 firefox 容器可以看到 driver 已經安裝好了.

```cmd
>> ls -al /opt
drwxr-xr-x 1 seluser seluser    4096 Apr 13 08:58 bin
-rwxr-xr-x 1 ubuntu  ubuntu  6132584 Feb 24  2025 geckodriver-v0.36.0
drwxrwxr-x 1 seluser root       4096 Apr 13 08:28 selenium
```

反之進入 chrome 容器可以也看到 driver 已經安裝,

可參考 [docker-compose-standalone-chrome.yml](docker-compose-standalone-chrome.yml).

接著可以進入 [http://localhost:4444/](http://localhost:4444/ui), 查看 Selenium Grid

![alt tag](https://i.imgur.com/UOZxSCg.png)

接下來就是透過 python 連線, 安裝 selenium

```cmd
pip install selenium
```

程式碼可參考 [demo.py](demo.py)

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Selenium 4 之後 endpoint 用根路徑即可 (/wd/hub 仍向下相容)
browser = webdriver.Remote(
    command_executor="http://localhost:4444",
    options=webdriver.ChromeOptions(),
)

browser.get("https://www.google.com")
print(browser.title)
WebDriverWait(browser, 10).until(
    EC.presence_of_element_located((By.NAME, "q"))
)
browser.save_screenshot("screenshot.png")
browser.quit()
```

如果我們想看執行過程, 可以開以下連結

[http://localhost:7900/?autoconnect=1&resize=scale&password=secret](http://localhost:7900/?autoconnect=1&resize=scale&password=secret)

![alt tag](https://i.imgur.com/BuA8XhA.png)

預設密碼是 `secret`, 不想要密碼可以設 `SE_VNC_NO_PASSWORD=1`,
不想被人控制可以設 `SE_VNC_VIEW_ONLY=1`.

```yml
environment:
  - SE_VNC_NO_PASSWORD=1
  - SE_VNC_VIEW_ONLY=1
```

詳細請參考 [Debugging](https://github.com/SeleniumHQ/docker-selenium#debugging).

### Headless mode

跑在沒有螢幕的 Linux server 上, 兩種選擇:

1. **保留 Xvfb (預設)** - 容器內建虛擬 framebuffer, 瀏覽器以為自己有螢幕,
   還可以開 `7900` 用 noVNC 即時看畫面 debug, 推薦在開發階段用.
2. **純 headless** - 把 `SE_START_XVFB` 設為 `false`, 同時程式裡傳
   `--headless` 給瀏覽器, 最省資源, 適合 CI.

```yml
environment:
  - SE_START_XVFB=false
```

```python
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
```

> 在容器內若想穩定, 上游建議仍保留 Xvfb (`SE_START_XVFB=true`), 詳見上游 README.

### Video recording

支援 `SE_VIDEO_FILE_NAME=auto` 自動以 session id 命名,
這樣多個 session 平行跑就不會互相覆蓋.

[docker-compose-video.yml](docker-compose-video.yml)

```yml
services:
  chrome_standalone:
    image: selenium/standalone-chrome:4.43.0-20260404
    shm_size: 2gb
    ports:
      - "4444:4444"
      - "7900:7900"
    environment:
      - SE_NODE_GRID_URL=http://chrome_standalone:4444

  chrome_video:
    image: selenium/video:ffmpeg-8.1-20260404
    volumes:
      - ./videos:/videos
    depends_on:
      - chrome_standalone
    environment:
      - DISPLAY_CONTAINER_NAME=chrome_standalone
      - SE_NODE_GRID_URL=http://chrome_standalone:4444
      - SE_VIDEO_FILE_NAME=auto
```

影片就會紀錄到 `./videos/` 資料夾, 把整段操作完整錄下來.

如果想讓檔名直接帶測試名稱, 在程式裡加上 capability:

```python
options.set_capability("se:name", "checkout-flow-test")
```

搭配 `SE_VIDEO_FILE_NAME=auto`, 就會錄出 `checkout-flow-test_<sessionId>.mp4`.

#### 常見的坑

**1. `./videos/` 沒寫入權限, mp4 沒落地**

video 容器內是用 `seluser` (uid 1200, gid 1201) 在跑 ffmpeg, 但 `./videos/` 如果是
host 上由 root (或其他使用者) 建立的, 會因為權限不足寫不進去, 結果跑完一場測試資料夾還是空的.

修法 (推薦, 最乾淨): 把 host 目錄改成 seluser 可寫

```bash
sudo chown -R 1200:1201 ./videos/
```

(selenium image 的 seluser uid=1200, gid=1201, 見
[Base/Dockerfile](https://github.com/SeleniumHQ/docker-selenium/blob/trunk/Base/Dockerfile))

### Hub and Nodes

除了 Standalone 之外, 還有 Hub + Nodes 模式, 一個 hub 派工給多個 node,
這次範例直接把三大瀏覽器 (Chrome / Firefox / Edge) 都接上去.

[docker-compose-v3.yml](docker-compose-v3.yml)

```yml
services:
  chrome:
    image: selenium/node-chrome:4.43.0-20260404
    shm_size: 2gb
    depends_on: [selenium-hub]
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_GRID_URL=http://selenium-hub:4444

  edge:
    image: selenium/node-edge:4.43.0-20260404
    shm_size: 2gb
    depends_on: [selenium-hub]
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_GRID_URL=http://selenium-hub:4444

  firefox:
    image: selenium/node-firefox:4.43.0-20260404
    shm_size: 2gb
    depends_on: [selenium-hub]
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_NODE_GRID_URL=http://selenium-hub:4444

  selenium-hub:
    image: selenium/hub:4.43.0-20260404
    container_name: selenium-hub
    ports:
      - "4442:4442"
      - "4443:4443"
      - "4444:4444"
```

這樣子就可以選擇要用哪個瀏覽器測試了.

```python
options = webdriver.EdgeOptions()  # 想用哪個瀏覽器就換哪個 Options
browser = webdriver.Remote(command_executor="http://localhost:4444", options=options)
```

這邊有兩個地方稍微說明:

- 假如你的 session 沒有正確 quit, 你會發現你沒辦法再連上去, 除非等到
  [session-timeout](https://github.com/SeleniumHQ/docker-selenium#grid-url-and-session-timeout)
  或是重啟容器.
- 此模式沒有對外開 7900, 但你可以從 Grid UI 的 session 列表點 **camera 圖示**
  看 live view (前提是 node 有設 `SE_NODE_GRID_URL`).

![alt tag](https://i.imgur.com/uUsvEJE.png)

### Dynamic Grid

Selenium 4 加入的玩法 - 每次有測試請求進來, hub 才即時 `docker run` 一個全新的
瀏覽器容器來跑, 跑完馬上銷毀. 好處:

- 每個 session 100% 隔離, 不會互相污染 cookie / cache.
- 不用預先養一堆 idle 的 node, 省資源.
- 適合 CI 大量平行測試, 或當作給 AI agent 用的 sandbox.

[docker-compose-dynamic-grid.yml](docker-compose-dynamic-grid.yml)

```yml
services:
  node-docker:
    image: selenium/node-docker:4.43.0-20260404
    volumes:
      - ./assets:/opt/selenium/assets
      - ./NodeDocker/config.toml:/opt/selenium/docker.toml
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on: [selenium-hub]
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub

  selenium-hub:
    image: selenium/hub:4.43.0-20260404
    container_name: selenium-hub
    ports:
      - "4442:4442"
      - "4443:4443"
      - "4444:4444"
```

[NodeDocker/config.toml](NodeDocker/config.toml) 是把 capability 對應到要開哪個 image:

```toml
[docker]
configs = [
  "selenium/standalone-chrome:4.43.0-20260404",  '{"browserName": "chrome", "platformName": "linux"}',
  "selenium/standalone-firefox:4.43.0-20260404", '{"browserName": "firefox", "platformName": "linux"}',
  "selenium/standalone-edge:4.43.0-20260404",    '{"browserName": "MicrosoftEdge", "platformName": "linux"}',
]
# node-docker image 內建 socat 會把 docker.sock 轉成 TCP 2375,
# 4.43 內部改用 JDK HttpClient 不支援 unix:// scheme, 所以走 http://127.0.0.1:2375.
url = "http://127.0.0.1:2375"
# video-image = "selenium/video:ffmpeg-8.1-20260404"  # 解開可幫每個 session 自動開錄影容器
```

#### 啟動方式

**1. (建議) 預先 pull 三個瀏覽器 image**

```bash
docker pull selenium/standalone-chrome:4.43.0-20260404
docker pull selenium/standalone-firefox:4.43.0-20260404
docker pull selenium/standalone-edge:4.43.0-20260404
```

不 pull 也可以動, 但第一次跑測試時 hub 會卡幾十秒邊下載 image 邊開 session,
容易誤判成 timeout.

**2. 啟動 grid**

```bash
docker compose -f docker-compose-dynamic-grid.yml up
```

啟動後 `docker ps` 應該只看到 2 個容器: `selenium-hub` + `node-docker`.
**不會有瀏覽器容器** — 那是收到請求才會即時開出來, 跑完馬上銷毀.

**3. 跑測試**

測試端程式碼**完全不用改**, 一樣連 `http://localhost:4444`,
hub 會在背景幫你開新容器, 結束後自動清掉. 這時再去 `docker ps` 就會看到
中間多了一個 `selenium/standalone-chrome` (或對應瀏覽器) 的容器,
session 一結束它就消失.

#### 常見的坑

**1. `FileNotFoundException: /opt/selenium/assets/<sessionId>/selenium-server.log`**

session 結束時 node-docker 要把容器 log 落地到 `./assets/<sessionId>/` 但寫不進去.
原因是 `./assets` 是 docker 第一次啟動時自動建立的, owner 是 **root**, 而容器內
是用 `seluser` (uid 1200, 見 [Base/Dockerfile](https://github.com/SeleniumHQ/docker-selenium/blob/trunk/Base/Dockerfile)) 在跑.

修法:

```bash
sudo chown -R 1200:1201 ./assets
```

(這個錯誤其實**不影響測試結果**, 只是 log 沒落地)

## 小結論

我覺得這個東西可以用來測試或開發應該都沒有什麼問題,

終於不用再擔心 chrome 版本和 driver 不符合了 :smile:

新版又多了 Dynamic Grid 和影片自動命名上傳.

## Donation

文章都是我自己研究內化後原創，如果有幫助到您，也想鼓勵我的話，歡迎請我喝一杯咖啡 :laughing:

綠界科技 ECPAY ( 不需註冊會員 )

![alt tag](https://payment.ecpay.com.tw/Upload/QRCode/201906/QRCode_672351b8-5ab3-42dd-9c7c-c24c3e6a10a0.png)

[贊助者付款](http://bit.ly/2F7Jrha)

歐付寶 ( 需註冊會員 )

![alt tag](https://i.imgur.com/LRct9xa.png)

[贊助者付款](https://payment.opay.tw/Broadcaster/Donate/9E47FDEF85ABE383A0F5FC6A218606F8)

## 贊助名單

[贊助名單](https://github.com/twtrubiks/Thank-you-for-donate)
