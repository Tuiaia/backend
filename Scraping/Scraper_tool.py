from BoraInvestir import BoraInvestir
from Forbes import Forbes
import schedule
import time

if '__main__' == __name__:
    print("Começando os Scraping, esperando o horario programado")
    schedule.every().day.at("00:00:00").do(BoraInvestir().run)
    schedule.every().day.at("00:30:00").do(Forbes().run)
    while True:
        schedule.run_pending()
        time.sleep(1)
