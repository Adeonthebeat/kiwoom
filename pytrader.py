import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import pandas


from Kiwoom import *
from log.log_class import *

form_class = uic.loadUiType("pytrader.ui")[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.trade_stocks_done = False

        self.kiwoom = Kiwoom()
        self.kiwoom.commConnect()

        self.logging = Logging()

        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        self.timer2 = QTimer(self)
        self.timer2.start(1000 * 10)
        self.timer2.timeout.connect(self.timeout2)

        account_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")

        self.logging.logger.debug("### accounts ### " + accounts)

        accounts_list = accounts.split(';')[0:account_num]
        self.comboBox.addItems(accounts_list)

        self.lineEdit.textChanged.connect(self.code_changed)
        self.pushButton.clicked.connect(self.send_order)
        self.pushButton_2.clicked.connect(self.check_balance)
        self.pushButton_cond.clicked.connect(self.start_cond)
        self.pushButton_4.clicked.connect(self.all_buy)

        self.load_condition_list()

    '''
    # 트레이딩
    '''
    def trade_stocks(self, tradeTc, list):

        self.logging.logger.debug("### trade Stock ###")

        # hoga_lookup = {'지정가': "00", '시장가': "03"}

        # account
        account = self.comboBox.currentText()
        self.logging.logger.debug("### account :::: " + account + " ###")
        self.logging.logger.debug("### tradeTc :::: " + tradeTc + " ###")

        print("### list :::: ", list)

        if tradeTc == "매수":
            for code in list:
                self.kiwoom.send_order("reqBuy001", "0101", account, 1, code, 10, 0, "03", "")

    '''
    # 자동 주문 리스트 - 사용 X

    def load_buy_sell_list(self):
        # -*- coding: utf-8 -*-
        f = open("buy_list.txt", 'rt', encoding='cp949')
        buy_list = f.readlines()
        f.close()

        # -*- coding: utf-8 -*-
        f = open("sell_list.txt", 'rt', encoding='cp949')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_4.setRowCount(row_count)

        # buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rsplit())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(len(buy_list) + j, i, item)

        self.tableWidget_4.resizeRowsToContents()
    '''

    '''
    # Code Changed.
    '''

    def code_changed(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    '''
    # 주문 요청.
    '''

    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()

        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price,
                               hoga_lookup[hoga], "")

    '''
    # 서버 연결 상태 확인.
    '''

    def timeout(self):
        market_start_time = QTime(9, 0, 0)
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.trade_stocks_done is False:
            # self.trade_stocks()
            self.trade_stocks_done = True

        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    '''
    # 타임 체크
    '''

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

    '''
    # 잔고 체크
    '''

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw00001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)
        self.tableWidget.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()

    def load_condition_list(self):
        print("pytrader.py [load_condition_list]")

        cond_list = []

        try:
            # 조건식 실행
            # getConditionLoad 가 정상 실행되면 kiwoom.condition에 조건식 목록이 들어간다.
            self.kiwoom.getConditionLoad()

            dic = self.kiwoom.condition

            for key in dic.keys():
                cond_list.append("{};{}".format(key, dic[key]))
            self.cbCdtNm.addItems(cond_list)

        except Exception as e:
            print(e)

    '''
    # 조건식 조회
    '''

    def start_cond(self):
        conditionIndex = self.cbCdtNm.currentText().split(';')[0]
        conditionName = self.cbCdtNm.currentText().split(';')[1]
        self.kiwoom.sendCondition("01111", conditionName, int(conditionIndex), 0)

        list = []
        dic = self.kiwoom.condtion_detail

        for key in dic.keys():
            list.append("{};{}".format(key, dic[key]))
        self.tableWidget_4.setRowCount(len(list))

        for i in range(len(list)):
            data = list[i].split(';')
            for j in range(len(data)):
                item = QTableWidgetItem(data[j])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_4.setItem(i, j, item)

        return list

    def all_buy(self):

        list = []
        dic = self.kiwoom.condtion_detail

        for key in dic.keys():
            list.append(key)

        self.trade_stocks("매수", list)

        return list


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
