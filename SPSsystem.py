import schedule
import time
import datetime

def main():
    now = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
    print(now, flush=True)

if __name__ == "__main__":
    main()
    # 1分毎に実行
    schedule.every(1).minutes.do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)