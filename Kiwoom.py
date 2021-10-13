import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3
from log.log_class import *

TR_REQ_TIME_INTERVAL = 0.2


class Kiwoom(QAxWidget):
    '''
    * Produced By ParkDangDang
    '''
    '''
    # 초기화 / 생성자 함수.
    '''
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.logging = Logging()
        self.condition = {}
        self.condtion_detail = {}

    '''
    # kiwoom instance 생성
    '''
    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    '''
    # 키움증권 서버로부터 발생한 이벤트(signal)와 이를 처리할 메서드(slot)를 연결.
    '''
    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        self.OnReceiveMsg.connect(self.msg_slot)

        ## 조건검색식 관련 추가
        self.OnReceiveConditionVer.connect(self.receiveConditionVer)
        self.OnReceiveTrCondition.connect(self.receiveTrCondition)
        self.OnReceiveRealCondition.connect(self.receiveRealCondition)

    '''
    # Connect
    '''
    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    '''
    # Connect
    '''
    def _event_connect(self, err_code):
        if err_code == 0:
            print("Connected")
        else:
            print("Disconnected")

        self.login_event_loop.exit()

    '''
    # 송수신 메세지 get
    '''
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        self.logging.logger.debug("스크린: %s, 요청이름: %s, tr코드: %s --- %s" % (sScrNo, sRQName, sTrCode, msg))

    '''
    # Code List 함수.
    '''
    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    '''
    # 종목명 조회 함수.
    '''
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    '''
    # Connect State 함수.
    '''
    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    '''
    # Login 정보.
    '''
    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    '''
    # Input Setting.
    '''
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    '''
    # 데이터 요청
    '''
    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    '''
    # 데이터 수신
    '''
    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    '''
    # 반복 함수 ->> opt10081 내부에서 쓰이는 함수.
    '''
    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    '''
    # 주문 요청.
    '''
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    '''
    # 체결잔고 데이터.
    '''
    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    '''
    # Server 구분
    '''
    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    '''
    # 체결 데이터 출력
    '''
    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(gubun)
        print(self.get_chejan_data(9203))
        print(self.get_chejan_data(302))
        print(self.get_chejan_data(900))
        print(self.get_chejan_data(901))

    '''
    # 실시간 데이터 수신.
    '''
    def _receive_tr_data(self, screen_no, rqname, trcode, recode_name, next, unused1, unused2, unused3, unused4):
        if next == 2:
            self.remained_data = True
        else:
            self.remained_data = False

        # 일자’, ‘시가’, ‘고가’, ‘저가’, ‘현재가’, ‘거래량’
        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    '''
    # Format 변환
    '''
    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '' or strip_data == '.00':
            strip_data = '0'

        try:
            format_data = format(int(strip_data), ',d')
        except:
            format_data = format(float(strip_data))
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if data.startswith('.'):
            strip_data = '0' + strip_data
        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    '''
    # 예수금
    '''
    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    '''
    # 실시간 데이터 조회 내부 함수.
    '''
    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def _opw00018(self, rqname, trcode):
        # Single Data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))

        total_earning_rate = Kiwoom.change_format(total_earning_rate)

        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate)
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # Multi Data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append(
                [name, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate])

    '''
    # 조건식을 로드한다.
    '''
    def getConditionLoad(self):
        print("[getConditionLoad]")
        ret = self.dynamicCall("GetConditionLoad()")

        if not ret:
            self.logging.logger.debug("조건식이 없습니다")
            print("조건식이 없습니다")

        self.conditionLoop = QEventLoop()
        self.conditionLoop.exec_()

    def getConditionNameList(self):
        print("[getConditionNameList]")
        '''
        return: dict - {인덱스:조건명, 인덱스:조건명, ...}
        '''

        # 수신된 사용자 조건검색식 리스트를 받아옴 (ex. 인덱스^조건명;)
        data = self.dynamicCall("GetConditionNameList()")

        if data == "":
            print("getConditionNameList(): 사용자 조건식이 없습니다.")

        conditionList = data.split(";")
        del conditionList[-1]

        conditionDict = {}

        for condition in conditionList:
            key, value = condition.split("^")
            conditionDict[int(key)] = value

        return conditionDict

    '''
    # 사용자 조건검색식 수신 함수
    '''

    def receiveConditionVer(self, receive, msg):

        try:
            if not receive:
                return

            self.condition = self.getConditionNameList()
            print("### 조건식 개수 ::: " + len(self.condition))

            for key in self.condition.keys():
                print("조건식: ", key, ": ", self.condition[key])

        except Exception as e:
            print(e)

        finally:
            self.conditionLoop.exit()

    '''
    # 조건검색 초기 조회시 반환되는 값을 받는 함수
    # sScrNo : 화면번호
    # strCodeList : 종목코드 리스트 (ex:039490;005930;036570;…;)
    # strConditionName: 조건식 이름
    # nIndex: 조건명 인덱스
    # nNext : 연속조회 여부(0:연속조회없음, 2:연속조회 있음)
    '''

    def receiveTrCondition(self, screenNo, codes, conditionName, conditionIndex, inquiry):

        try:
            if codes == "":
                return
            code_list = codes.split(";")
            del code_list[-1]
            print("종목개수 : ", len(code_list))

            for code in code_list:
                self.logging.logger.debug("{} {}\n".format(code, self.get_master_code_name(code)))
                self.condtion_detail[code] = self.get_master_code_name(code)

        finally:
            self.conditionLoop.exit()

    '''
    # 실시간 종목 조건검색 요청시 발생되는 이벤트
    :param code             : string - 종목코드
    :param event            : string - 이벤트종류("I": 종목편입, "D": 종목이탈)
    :param conditionName    : string - 조건식 이름
    :param conditionIndex   : string - 조건식 인덱스(여기서만 인덱스가 string 타입으로 전달됨)
    '''

    def receiveRealCondition(self, code, event, conditionName, conditionIndex):
        print("[receive_real_condition]")

        logDateTime = datetime.today().strftime("%Y-%m-%d %H:%M:%S")  # 화면에 노출할 날짜를 만듬 (YYYY-mm-dd HH:MM:SS 형태)
        codeName = self.dynamicCall("GetMasterCodeName(QString)", [code]).strip()  # 종목 코드로 종목 이름을 가져옴

        if str(event) == "I":  # 편입 종목이라면
            # 트레이딩 화면 내역에 로그를 남김
            self.logging.logger.debug(str(logDateTime) + " 편입 신호 : " + str(code) + ", " + str(codeName))

        elif str(event) == "D":  # 이탈 종목이라면
            self.logging.logger.debug(str(logDateTime) + " 이탈 신호 : " + str(code) + ", " + str(codeName))
    """
    종목 조건검색 요청 메서드

    이 메서드로 얻고자 하는 것은 해당 조건에 맞는 종목코드이다.
    해당 종목에 대한 상세정보는 setRealReg() 메서드로 요청할 수 있다.
    요청이 실패하는 경우는, 해당 조건식이 없거나, 조건명과 인덱스가 맞지 않거나, 조회 횟수를 초과하는 경우 발생한다.

    조건검색에 대한 결과는
    1회성 조회의 경우, receiveTrCondition() 이벤트로 결과값이 전달되며
    실시간 조회의 경우, receiveTrCondition()과 receiveRealCondition() 이벤트로 결과값이 전달된다.

    :param screenNo: string
    :param conditionName: string - 조건식 이름
    :param conditionIndex: int - 조건식 인덱스
    :param isRealTime: int - 조건검색 조회구분(0: 1회성 조회, 1: 실시간 조회)
    """
    def sendCondition(self, screenNo, conditionName, conditionIndex, isRealTime):
        req = self.dynamicCall("SendCondition(QString, QString, int, int",screenNo, conditionName, conditionIndex, isRealTime)
        self.logging.logger.debug(str(conditionName) + " 실행 ")

        # if not req:
        #     print("sendCondition(): 조건검색 요청 실패")


        # self.receiveTrCondition()
        self.conditionLoop = QEventLoop()
        self.conditionLoop.exec_()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    kiwoom.reset_opw00018_output()
    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]

    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
    kiwoom.getConditionLoad()

    # print(kiwoom.opw00018_output['single'])
    # print(kiwoom.opw00018_output['multi'])
