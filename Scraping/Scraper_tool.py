from BoraInvestir import BoraInvestir
from Forbes import Forbes
import time
import schedule

if '__main__' == __name__:
    schedule.every(2).hours.do(Forbes().run())
    schedule.every(2).hours.do(BoraInvestir().run())
    while True:
        schedule.run_pending()
        time.sleep(1)