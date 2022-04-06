# coding:utf-8
"""
  Time : 2022/4/3 5:55
  Author : vincent
  FileName: HosPrescriptionService
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2022/4/3 5:55
"""
import logging
import time

import requests
from sqlalchemy import and_
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import SQLAlchemyError

from lib.public.handle import get_config, Envelope, response_base64_decode, md5_creat_password, request_base64_encode
from lib.public.zhenzismsclient import ZhenziSmsClient
from management.models import get_session, Consignee, Address, Prescription, PresDetails

logger_timer = logging.getLogger('PrescriptionPushSyetem.uploadTimer')


def find_un_write_pres_consignee():
    """查询处方地址关联表 consignee 获取已关联地址但未写入中间表的信息列表吗 is_write_mid=0 """
    uw_records = []
    session = get_session('local')[1]
    uw_records_query = session.query(Consignee.pres_num, Consignee.addr_id, Address.provinces, Address.city,
                                     Address.zone, Address.addr_detail, Address.consignee, Address.con_tel,
                                     Consignee.send_goods_time, Address.is_hos_addr, Consignee.is_write_mid).filter(
        and_(Consignee.addr_id == Address.addr_id, Consignee.is_write_mid == 0))
    uw_records_query_sql = str(uw_records_query.statement.compile(dialect=mysql.dialect(),
                                                                  compile_kwargs={"literal_binds": True}))
    logger_timer.info('- ==> executing:%s' % uw_records_query_sql)
    uw_records_lists = uw_records_query.all()
    logger_timer.info("- ==> Parameters:")
    logger_timer.info("- <==  Columns: pres_num , addr_id , provinces , city , zone , addr_detail , "
                      "consignee , con_tel , send_goods_time , is_hos_addr , is_write_mid")
    for record in uw_records_lists:
        logger_timer.info("- <==  Row: {}".format(record))
        uw_records.append(dict(zip(record.keys(), record)))
    return uw_records


def get_pre_lists_by_statues(start_status, end_status):
    """
    在中间表中根据处方状态查询需要上传的处方
    :param start_status:
    :param end_status:
    :return:
    """
    pres_lists = []
    session = get_session('local')[1]
    pre_lists_query = session.query(Prescription.pres_num, Prescription.upload_status).filter(
        Prescription.upload_status.between(start_status, end_status))
    sql = str(pre_lists_query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
    logger_timer.info('- ==> executing:%s' % sql)
    query_lists = pre_lists_query.all()
    logger_timer.info("- ==> Parameters:%s" % query_lists)
    logger_timer.info("- <==  Columns: pres_num , upload_status")
    for pres_obj in query_lists:
        logger_timer.info("- <==  Row: {} , {}".format(pres_obj.pres_num, pres_obj.upload_status))
        pres_lists.append(dict(zip(pres_obj.keys(), pres_obj)))
    return pres_lists


def upload_prescriptions(pre_lists):
    """
    上传处方至智慧药房，成功后把中间表的upload_status置为-1，否则该值+1
    :param pre_lists: 需要上传的处方号列表
    :return:
    """
    logger_timer.info("开始批量上传 %s 个处方" % (len(pre_lists)))
    for pres_num in pre_lists:
        request_sb = build_upload_prescription_req(pres_num)
        url = get_config('interface', 'orderUrl')
        logger_timer.info("调用康美接口saveOrderInfoToCharacterSet Begin, 请求url：%s, 请求体：%s" % (url, request_sb))
        # 使用 requests 向 webservice 接口发送报文数据保存订单
        request_body = get_request_body(request_sb)
        response = requests.post(url, request_body)
        logging.info('response envelope:%s' % response.text)
        env = Envelope(response.text)
        xml_data = response_base64_decode(env.get_context('return'))
        logger_timer.info("调用康美接口saveOrderInfoToCharacterSet End, 接口返回：%s", xml_data)
        xml = Envelope(xml_data)
        if (xml.get_context("resultCode") == '0') or (xml.get_context("resultCode") == '22'):
            order_id = xml.get_context("orderid")
            description = xml.get_context('message')
            logger_timer.info("处方上传成功！处方号：{} -- 对应订单号：{}".format(pres_num, order_id))
            update_prescription_statues(pres_num, order_id=order_id, describe=description)
        else:
            logger_timer.info("处方上传失败！处方号为：%s", pres_num)
            if xml.get_context("resultCode") == '500':
                reason = xml.get_context('description')
            else:
                reason = xml.get_context('message')
            update_prescription_statues(pres_num, describe=reason)
            send_remind_message(pres_num, reason)


def build_upload_prescription_req(pres):
    """
    组装请求报文
    :param pres: 处方号
    :return:
    """
    key = int(time.time() * 1000)
    sign = md5_creat_password("saveOrderInfo" + str(key) + get_config('hospital', 'companyPass'))
    pres_info, pres_details = find_prescription_details(pres)
    content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    content += "<orderInfo>"
    content += "<head>"
    content += "<company_num>" + get_config('hospital', 'companyNum') + "</company_num>"
    content += "<key>" + str(key) + "</key>"
    content += "<sign>" + sign + "</sign>"
    content += "</head>"
    content += "<data>"
    content += "<order_time>" + pres_info.pres_time + "</order_time>"
    content += "<treat_card>" + pres_info.treat_card + "</treat_card>"
    content += "<reg_num>" + pres_info.reg_num + "</reg_num>"
    content += "<addr_str>" + pres_info.provinces + "," + pres_info.city + "," + pres_info.zone + "," + \
               pres_info.addr_detail + "</addr_str>"
    content += "<consignee>" + pres_info.consignee + "</consignee>"
    content += "<con_tel>" + pres_info.con_tel + "</con_tel>"
    content += "<send_goods_time>" + (pres_info.send_goods_time if pres_info.send_goods_time else ''
                                      ) + "</send_goods_time>"
    content += "<is_hos_addr>" + str(pres_info.is_hos_addr) + "</is_hos_addr>"
    content += "<prescript>"
    content += "<pdetail>"
    content += "<user_name>" + pres_info.user_name + "</user_name>"
    content += "<doctor>" + pres_info.doctor + "</doctor>"
    content += "<age>" + str(pres_info.age) + "</age>"
    content += "<gender>" + str(pres_info.gender) + "</gender>"
    content += "<tel>" + pres_info.tel + "</tel>"
    content += "<is_suffering>" + str(pres_info.is_suffering) + "</is_suffering>"
    content += "<amount>" + str(pres_info.amount) + "</amount>"
    content += "<suffering_num>" + str(pres_info.suffering_num) + "</suffering_num>"
    content += "<ji_fried>" + str(pres_info.ji_fried) + "</ji_fried>"
    content += "<per_pack_num>" + str(pres_info.per_pack_num) + "</per_pack_num>"
    content += "<per_pack_dose>" + (str(pres_info.per_pack_dose) if pres_info.per_pack_dose else '200'
                                    ) + "</per_pack_dose>"
    content += "<type>" + str(pres_info.type) + "</type>"
    content += "<other_pres_num>" + pres_info.other_pres_num + "</other_pres_num>"
    content += "<special_instru>" + pres_info.special_instru + "</special_instru>"
    content += "<is_within>" + str(pres_info.is_within) + "</is_within>"
    content += "<bed_num>" + (str(pres_info.bed_num) if pres_info.bed_num else '') + "</bed_num>"
    content += "<hos_depart>" + (pres_info.hos_depart if pres_info.hos_depart else '') + "</hos_depart>"
    content += "<hospital_num>" + (pres_info.hospital_num if pres_info.hospital_num else '') + "</hospital_num>"
    content += "<disease_code>" + (pres_info.disease_code if pres_info.disease_code else '') + "</disease_code>"
    content += "<prescript_remark>" + (pres_info.prescript_remark if pres_info.prescript_remark else ''
                                       ) + "</prescript_remark>"
    content += "<medication_methods>" + (pres_info.medication_methods if pres_info.medication_methods else '') + \
               "</medication_methods>"
    content += "<medication_instruction>" + \
               (pres_info.medication_instruction if pres_info.medication_instruction else ''
                ) + "</medication_instruction>"
    content += "<is_hos>" + ('2' if pres_info.source == 1 else '1') + "</is_hos>"
    content += "<medici_xq>"
    for pres_det in pres_details:
        content += "<xq>"
        content += "<medicines>" + pres_det.medicines + "</medicines>"
        content += "<dose>" + pres_det.dose + "</dose>"
        content += "<unit>" + pres_det.unit + "</unit>"
        content += "<goods_num>" + pres_det.goods_num + "</goods_num>"
        content += "<dose_that>" + (pres_det.dose_that if pres_det.dose_that else '') + "</dose_that>"
        content += "<remark>" + (pres_det.remark if pres_det.remark else '') + "</remark>"
        content += "<m_usage>" + (pres_det.m_usage if pres_det.m_usage else '') + "</m_usage>"
        content += "<goods_norms>" + (pres_det.goods_norms if pres_det.goods_norms else '') + "</goods_norms>"
        content += "<goods_orgin>" + (pres_det.goods_orgin if pres_det.goods_orgin else '') + "</goods_orgin>"
        content += "</xq>"
    content += "</medici_xq>"
    content += "</pdetail>"
    content += "</prescript>"
    content += "</data>"
    content += "</orderInfo>"
    return content


def find_prescription_details(pres):
    session = get_session('local')[1]
    logger_timer.info("从中间表查询处方详情：")
    pres_detail_query = session.query(Prescription).filter(Prescription.pres_num == pres)
    pres_detail_sql = str(pres_detail_query.statement.compile(
        dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
    logger_timer.info('- ==> executing:%s' % pres_detail_sql)
    pres_detail_res = pres_detail_query.first()
    logger_timer.info("- ==> Parameters:%s" % pres_detail_res)
    logger_timer.info("- <==  Columns: {}".format(pres_detail_res.keys()))
    logger_timer.info("- <==  Row: {}".format(pres_detail_res.to_json()))
    logger_timer.info("从中间表查询处方药品详情：")
    pres_drug_detail_query = session.query(PresDetails).filter(PresDetails.pres_num == pres)
    drug_detail_sql = str(pres_drug_detail_query.statement.compile(
        dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
    logger_timer.info('- ==> executing:%s' % drug_detail_sql)
    drug_detail_res = pres_drug_detail_query.all()
    logger_timer.info("- ==> Parameters:%s" % drug_detail_res)
    for i in range(len(drug_detail_res)):
        if i == 0:
            logger_timer.info("- <==  Columns: {}".format(drug_detail_res[i].keys()))
            logger_timer.info("- <==  Row: {}".format(drug_detail_res[i].to_json()))
        else:
            logger_timer.info("- <==  Row: {}".format(drug_detail_res[i].to_json()))
    session.close()
    return pres_detail_res, drug_detail_res


def get_request_body(content):
    """
    对请求报文进行 Base64
    :param content:
    :return:
    """
    sb = "<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"  >"
    sb += "<soap:Body>"
    sb += "<ns1:saveOrderInfoToCharacterSet xmlns:ns1=\"http://factory.service.cxf.kangmei.com/\">"
    sb += "<request>"
    sb += request_base64_encode(content)
    sb += "</request>"
    sb += "<characterSet>UTF-8</characterSet>"
    sb += "</ns1:saveOrderInfoToCharacterSet>"
    sb += "</soap:Body>"
    sb += "</soap:Envelope>"
    return sb


def update_prescription_statues(pres_num, order_id='', describe=''):
    """
    更新处方上传状态 成功 -1 失败 +1
    :param pres_num:
    :param order_id:
    :param describe:
    :return:
    """
    session = get_session('local')[1]
    if order_id:
        session.query(Prescription).filter(Prescription.pres_num == pres_num).update({
            Prescription.upload_status: '-1', Prescription.order_id: order_id, Prescription.description: describe,
            Prescription.upload_time: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))})
    else:
        session.query(Prescription).filter(Prescription.pres_num == pres_num).update({
            Prescription.upload_status: Prescription.upload_status + 1, Prescription.description: describe})
    try:
        session.commit()
        logger_timer.info("处方号：%s 上传状态更新成功！" % pres_num)
    except SQLAlchemyError as e:
        session.rollback()
        logger_timer.info('处方号： %s 上传状态更新失败！' % pres_num)
        logger_timer.error(str(e))
    session.close()


def insert_mid_prescription(prescription):
    message = {}
    session = get_session('local')[1]
    logger_timer.info("插入中间表==>处方表：")
    prescription_info = Prescription(
        pres_num=prescription['pres_num'], pres_time=prescription['pres_time'], treat_card=prescription['treat_card'],
        reg_num=prescription['reg_num'], provinces=prescription['provinces'], city=prescription['city'],
        zone=prescription['zone'], addr_detail=prescription['addr_detail'], consignee=prescription['consignee'],
        con_tel=prescription['con_tel'], send_goods_time=prescription['send_goods_time'],
        user_name=prescription['user_name'], age=prescription['age'], gender=prescription['gender'],
        tel=prescription['tel'], is_suffering=prescription['is_suffering'], amount=prescription['amount'],
        suffering_num=prescription['suffering_num'], ji_fried=prescription['ji_fried'],
        per_pack_num=prescription['per_pack_num'], per_pack_dose=prescription['per_pack_dose'], type=prescription['type'],
        is_within=prescription['is_within'], other_pres_num=prescription.get('other_pres_num', prescription['pres_num']),
        special_instru=prescription['special_instru'], bed_num=prescription.get('bed_num'),
        hos_depart=prescription.get('hos_depart'), hospital_num=prescription.get('hospital_num'),
        disease_code=prescription.get('disease_code'), doctor=prescription['doctor'],
        prescript_remark=prescription['prescript_remark'], is_hos_addr=prescription['is_hos_addr'],
        medication_methods=prescription['medication_methods'],
        medication_instruction=prescription['medication_instruction'], source=prescription['source']
    )
    session.add(prescription_info)
    try:
        session.commit()
        message['status'] = 'success'
        logger_timer.info("处方成功插入中间表！{}".format(message))
    except SQLAlchemyError as e:
        session.rollback()
        message['status'] = 'fail'
        logger_timer.info("处方插入中间表失败！{}".format(message))
        logger_timer.error(str(e))
    session.close()
    return message


def insert_mid_prescription_detail(pres_details):
    message = {}
    pres_detail_lists = []
    session = get_session('local')[1]
    logger_timer.info("插入中间表==>处方明细表：")
    for pres_detail in pres_details:
        detail_info = PresDetails(
            pres_num=pres_detail['pres_num'], goods_num=pres_detail['goods_num'], medicines=pres_detail['medicines'],
            dose=pres_detail['dose'], unit=pres_detail['unit'], m_usage=pres_detail['m_usage'],
            goods_norms=pres_detail['goods_norms'], goods_orgin=pres_detail['goods_orgin'], remark=pres_detail['remark'],
            dose_that=pres_detail['dose_that'], unit_price=pres_detail.get('unit_price'),
            MedPerDay=pres_detail.get('MedPerDay'), MedPerDos=pres_detail.get('MedPerDos')
        )
        pres_detail_lists.append(detail_info)
    session.add_all(pres_detail_lists)
    try:
        session.commit()
        message['status'] = 'success'
        logger_timer.info("处方详情成功插入中间处方明细表！{}".format(message))
    except SQLAlchemyError as e:
        session.rollback()
        message['status'] = 'fail'
        logger_timer.info("处方详情插入中间处方明细表失败！{}".format(message))
        logger_timer.error(str(e))
    session.close()
    return message


def update_consignee_status(pres_num):
    message = {}
    session = get_session('local')[1]
    logger_timer.info("更新中间表写入状态：")
    is_write_mid_update = session.query(Consignee).filter(Consignee.pres_num == pres_num).update({'is_write_mid': 1})
    logger_timer.info("==> Parameters:影响行：%s" % is_write_mid_update)
    try:
        session.commit()
        message['status'] = 'success'
        logger_timer.info('写入中间表状态更新成功！{}'.format(message))
    except SQLAlchemyError as e:
        session.rollback()
        message['status'] = 'fail'
        logger_timer.info('写入中间表状态更新失败！{}'.format(message))
        logging.error(str(e))
    session.close()
    return message


def send_remind_message(pres_num, message):
    options = ['appID', 'appSecret', 'messageServiceUrl', 'emergencyContact']
    msg_info = get_config('message', options)
    logger_timer.info("msg_info:%s" % msg_info)
    hos_name = get_config('hospital', 'companyName')
    msg_client = ZhenziSmsClient(msg_info['messageServiceUrl'], msg_info['appID'], msg_info['appSecret'])
    params = {}
    for tel in msg_info['emergencyContact'].split(','):
        logger_timer.info("发送提醒信息 -{}- {} 处方号:{} . 到 {}".format(hos_name, message, pres_num, tel))
        params['number'] = tel
        params['templateId'] = '8589'
        params['templateParams'] = ['vincent', hos_name, pres_num, message]
        result = msg_client.send(params)
        logger_timer.info("结果：%s" % result)
