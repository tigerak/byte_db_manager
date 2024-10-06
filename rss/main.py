import os
import re
import sys
BASE_DIR = '/home/data_ai/Project'
sys.path.append(BASE_DIR)
from datetime import datetime
from time import sleep
import json
import requests
import xml.etree.ElementTree as ET
import traceback
# modules
from config import *
from save_function import Save_function


class RSS_update():
    def __init__(self, save_function):
        try:
            with open(LAST_RSS_PATH, 'r', encoding='utf-8') as json_file:
                self.rss_list = json.load(json_file)
        except:
            self.rss_list = []

        self.new_list = []
        
        self.save_function = save_function

    # 산업과 마켓+ RSS를 순회
    def category_rotation(self):
        try:
            for rss_url in YTN_RSS:
                response = requests.get(rss_url)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    self.channel_rotation(root)
                else:
                    logging.error(f"Failed to fetch RSS feed: {rss_url}, Status Code: {response.status_code}")
        except Exception as e:
            logging.error("An error occurred in category_rotation(): %s", str(e))
            # 슬랙 알림 전송
            error_title = "Category Rotation에서 에러 발생"
            error_message = str(e)
            traceback_info = traceback.format_exc()
            send_slack_notification(error_title, error_message, traceback_info)
            # 예외를 재발생시켜 메인 루프에서 처리할 수 있게 함
            raise
                
        # 순회를 마친 모든 데이터의 article_date를 datetime 형식으로 변환하고 정렬
        sorted_data = sorted(self.new_list, key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)
        
        # function/data/last_rss.json과 일치하지 않으면 
        matching = sorted(self.rss_list, key=lambda x: sorted(x['input_url'])) \
            == sorted(sorted_data, key=lambda x: sorted(x['input_url']))
        # 일치하지 않는 새 데이터들을 save_function.py로 보내고 
        if not matching:
            print('새 데이터 추가')
            different_data = [item for item in sorted_data if item['input_url'] not in {d['input_url'] for d in self.rss_list}]
            print(different_data)
            self.save_function.prepare_article(different_data)
            # function/data/last_rss.json을 마지막 목록으로 갱신
            with open(LAST_RSS_PATH, 'w', encoding='utf-8') as json_file:
                json.dump(sorted_data, json_file, ensure_ascii=False, indent=4)
            
        # print(f"데이터가 DB에 저장되었습니다.{self.chromadb.get_most_recent_items()}")

    # 채널 순회. 각 1개.
    def channel_rotation(self, root):
        for channel in root.findall('channel'):
            self.item_rotation(channel)

    # 아이템 순회. 각 30개.
    def item_rotation(self, channel):
        email_pattern = re.compile(r'.+@yna\.co\.kr$')
        # 아이템 파싱.
        for item in channel.findall('item'):
            # print(f"{ET.tostring(item, encoding='unicode')}")
            input_url = item.find('link').text if item.find('link') is not None else 'No url'
            title = item.find('title').text if item.find('title') is not None else 'No title'
            
            article = item.find('description').text if item.find('description') is not None else 'No description'
            
            ### !!!!! 기사가 '' 인 속보에서 계속 문제를 일으킴 !!!!! ###
            try:
                # 머릿말 제거
                article_parts = article.split('=연합뉴스)', 1)
                if len(article_parts) > 1:
                    article = article_parts[1]
                # 각 줄을 분리합니다.
                lines = article.split('\n')
                # 기자명 제거
                first_sentence_parts= lines[0].split(' = ', 1)
                if len(first_sentence_parts) > 1:
                    lines[0] = first_sentence_parts[-1]
                # 뒤에서부터 순차적으로 검사합니다.
                while lines:
                    last_line = lines[-1].strip()  # 마지막 줄을 가져옵니다.
                    # (끝) 또는 특정 이메일 패턴이 있는지 확인합니다.
                    if last_line == "(끝)" or email_pattern.match(last_line):
                        lines.pop()  # 해당 줄을 삭제합니다.
                    else:
                        break  # 패턴이 없는 줄을 만나면 중지합니다.
                # 필터링된 줄들을 다시 합칩니다.
                cleaned_article = '\n'.join(lines)
            except:
                cleaned_article = title
            
            ### !!!!! 날짜에서도 무슨 문제를 일으킴 !!!!! ###
            # pubDate를 원하는 형식으로 변환
            pub_date_raw = item.find('pubDate').text if item.find('pubDate') is not None else 'No date'
            try:
                # 문자열을 datetime 객체로 변환
                ### !!!!! 여기서 또 무슨 짓을 한걸까 !!!!! ###
                pub_date_parsed = datetime.strptime(pub_date_raw, '%a, %d %b %Y %H:%M:%S %z')
                # 원하는 형식으로 다시 문자열로 변환
                article_date = pub_date_parsed.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                article_date = 'Invalid date format'

            temp_dict = {
                'input_url': input_url,
                'article_date': article_date,
                'title': title,
                'article': cleaned_article,
            }
            self.new_list.append(temp_dict)


# RSS 순회를 10초마다 반복하며 로그를 남기고 매일 자정 갱신합니다.
import logging
from logging.handlers import TimedRotatingFileHandler
import schedule

def setup_logging(log_filename=None):
    # 로그 설정
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    if not log_filename:
        log_filename = os.path.join(RSS_LOG_DIR, 'rss_observation.log')

    # 로그 파일이 매일 자정에 교체되도록 설정
    handler = TimedRotatingFileHandler(
        filename=log_filename, 
        when='midnight', 
        interval=1, 
        backupCount=7
    )
    
    handler.setLevel(logging.INFO)

    # 로그 메시지 형식 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # 로거에 핸들러 추가
    logger.addHandler(handler)

    # 표준 출력과 표준 오류를 로거에 연결
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)


class StreamToLogger:
    """
    file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def generate_log_filename():
    """
    Generate a new log filename with the current date.
    """
    current_date = datetime.now().strftime("%y_%m_%d")
    log_filename = os.path.join(RSS_LOG_DIR, f'{current_date}_rss_observation.log')
    setup_logging(log_filename)
    

def main(save_function):
    generate_log_filename()

    # 로그 메시지 기록
    logging.info("RSS observation started")
    while True:
        try:
            rss = RSS_update(save_function)
            rss.category_rotation()
            print("10 초 쉼")
            del rss
            sleep(10)
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                # 프로그램 종료를 위한 예외는 다시 발생시킴
                raise
            # 에러 발생 시 Slack으로 알림 전송
            error_title = "RSS 수집 중 에러 발생"
            error_message = str(e)
            traceback_info = traceback.format_exc()
            send_slack_notification(error_title, error_message, traceback_info)
            # 로그에 에러 기록
            logging.error("An error occurred in main(): %s", str(e))
            # 필요한 경우 프로그램 종료 또는 재시작 로직 추가
            break  # 또는 continue로 변경하여 루프를 지속할 수 있습니다.

def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # 키보드 인터럽트는 기본 동작을 유지
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    # 슬랙 알림 전송
    error_title = "전역 예외 발생"
    error_message = str(exc_value)
    traceback_info = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    send_slack_notification(error_title, error_message, traceback_info)

sys.excepthook = global_exception_handler

def send_slack_notification(error_title, error_message, traceback_info):
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":warning: {error_title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"<@{SLACK_ID}> *에러 메시지:*\n```{error_message}```"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*스택 트레이스:*\n```{traceback_info}```"
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            logging.error("Failed to send Slack notification: %s", response.text)
    except Exception as e:
        logging.error("Exception occurred while sending Slack notification: %s", str(e))


# Schedule the logging initialization to run every day at midnight
schedule.every().day.at("00:00").do(generate_log_filename)

# Run the scheduled jobs
def run_scheduler():
    while True:
        schedule.run_pending()
        # Wait until just before the next whole minute to minimize delay
        sleep(60 - datetime.now().second)


# Save_function을 여기서 한번만 실행시키는 것에 주의하십시오.
if __name__ == "__main__":
    save_function = Save_function()

    # Start the scheduler in a separate thread
    import threading
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    main(save_function)