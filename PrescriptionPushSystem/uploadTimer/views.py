import logging


import time

from sqlalchemy import literal
from sqlalchemy.dialects import mysql

from lib.prescription_services.HosPrescriptionService import find_un_write_pres_consignee, get_pre_lists_by_statues, \
    insert_mid_prescription, update_consignee_status, upload_prescriptions
from management.models import get_session, MZPrescriptionsView, MZDetailsView, ZYPrescriptionsView, ZYDetailsView

logger_timer = logging.getLogger('PrescriptionPushSyetem.uploadTimer')


def time_out():
    format_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    print(format_time)


def insert_mid_by_pres_consignee():
    pres_detail = []
    logger_timer.info("查询处方地址关联表,获取未写入处方中间表和明细表的处方信息:")
    pres_consignee_lists = find_un_write_pres_consignee()
    if pres_consignee_lists:
        session = get_session('per')[1]
        for pres_consignee_list in pres_consignee_lists:
            del pres_consignee_list['addr_id']
            del pres_consignee_list['is_write_mid']
            prefix = pres_consignee_list['pres_num'][:3]
            if prefix == 'MZ_':
                pres_query = session.query(MZPrescriptionsView.pres_num, MZPrescriptionsView.pres_time,
                                           MZPrescriptionsView.treat_card, MZPrescriptionsView.reg_num,
                                           MZPrescriptionsView.username.label('user_name'),
                                           MZPrescriptionsView.age, MZPrescriptionsView.gender,
                                           MZPrescriptionsView.tel, MZPrescriptionsView.is_suffering,
                                           MZPrescriptionsView.amount, MZPrescriptionsView.type,
                                           MZPrescriptionsView.is_within,
                                           (MZPrescriptionsView.is_suffering * MZPrescriptionsView.amount *
                                            MZPrescriptionsView.per_pack_num).label('suffering_num'),
                                           MZPrescriptionsView.per_pack_num, MZPrescriptionsView.per_pack_dose,
                                           MZPrescriptionsView.ji_fried, MZPrescriptionsView.special_instru,
                                           MZPrescriptionsView.hos_depart, MZPrescriptionsView.doctor,
                                           MZPrescriptionsView.remark.label('prescript_remark'),
                                           MZPrescriptionsView.medication_methods,
                                           MZPrescriptionsView.medication_instruction, literal(0).label('source')
                                           ).filter(MZPrescriptionsView.pres_num == pres_consignee_list['pres_num'])
                detail_query = session.query(MZDetailsView.pres_num, MZDetailsView.medicines,
                                             MZDetailsView.goods_num, MZDetailsView.dose, MZDetailsView.unit,
                                             MZDetailsView.dose_that, MZDetailsView.remark, MZDetailsView.m_usage,
                                             MZDetailsView.goods_norms, MZDetailsView.goods_orgin).filter(
                    MZDetailsView.pres_num == pres_consignee_list['pres_num'])
                columns = "- <==  Columns: pres_num , pres_time , treat_card , reg_num , user_name , age , gender , " \
                          "tel , is_suffering , amount , type , is_within , suffering_num , per_pack_num , " \
                          "per_pack_dose , ji_fried , special_instru , hos_depart , doctor , prescript_remark , " \
                          "medication_methods , medication_instruction , source"
            elif prefix == 'ZY_':
                pres_query = session.query(ZYPrescriptionsView.pres_num, ZYPrescriptionsView.pres_time,
                                           ZYPrescriptionsView.treat_card, ZYPrescriptionsView.reg_num,
                                           ZYPrescriptionsView.username.label('user_name'),
                                           ZYPrescriptionsView.age, ZYPrescriptionsView.gender,
                                           ZYPrescriptionsView.tel, ZYPrescriptionsView.is_suffering,
                                           ZYPrescriptionsView.amount, ZYPrescriptionsView.type,
                                           ZYPrescriptionsView.is_within,
                                           (ZYPrescriptionsView.is_suffering * ZYPrescriptionsView.amount *
                                            ZYPrescriptionsView.per_pack_num).label('suffering_num'),
                                           ZYPrescriptionsView.per_pack_num, ZYPrescriptionsView.per_pack_dose,
                                           ZYPrescriptionsView.ji_fried, ZYPrescriptionsView.special_instru,
                                           ZYPrescriptionsView.hos_depart, ZYPrescriptionsView.bed_num,
                                           ZYPrescriptionsView.hospital_num, ZYPrescriptionsView.disease_code,
                                           ZYPrescriptionsView.doctor,
                                           ZYPrescriptionsView.remark.label('prescript_remark'),
                                           ZYPrescriptionsView.medication_methods,
                                           ZYPrescriptionsView.medication_instruction, literal(1).label('source')
                                           ).filter(ZYPrescriptionsView.pres_num == pres_consignee_list['pres_num'])
                detail_query = session.query(ZYDetailsView.pres_num, ZYDetailsView.medicines,
                                             ZYDetailsView.goods_num, ZYDetailsView.dose, ZYDetailsView.unit,
                                             ZYDetailsView.dose_that, ZYDetailsView.remark, ZYDetailsView.m_usage,
                                             ZYDetailsView.goods_norms, ZYDetailsView.goods_orgin).filter(
                    ZYDetailsView.pres_num == pres_consignee_list['pres_num'])
                columns = "- <==  Columns: pres_num , pres_time , treat_card , reg_num , user_name , age , gender , " \
                          "tel , is_suffering , amount , type , is_within , suffering_num , per_pack_num , " \
                          "per_pack_dose , ji_fried , special_instru , hos_depart , bed_num , hospital_num , " \
                          "disease_code , doctor , prescript_remark , medication_methods , medication_instruction , " \
                          "source"
            pres_query_sql = str(pres_query.statement.compile(dialect=mysql.dialect(),
                                                              compile_kwargs={"literal_binds": True}))
            logger_timer.info('从视图中查询处方信息,查询处方号:{}'.format(pres_consignee_list['pres_num']))
            logger_timer.info('- ==> executing:%s' % pres_query_sql)
            pres_data = pres_query.first()
            logger_timer.info("- ==> Parameters:")
            logger_timer.info(columns)
            logger_timer.info("- <==  Row: {}".format(pres_data))
            if pres_data:
                detail_query_sql = str(detail_query.statement.compile(
                    dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
                logger_timer.info('从视图中查询处方药材详情,查询处方号:{}'.format(pres_consignee_list['pres_num']))
                detail_datas = detail_query.all()
                if detail_datas:
                    logger_timer.info('- ==> executing:%s' % detail_query_sql)
                    logger_timer.info("- ==> Parameters:")
                    logger_timer.info("- <==  Columns: pres_num , medicines , goods_num , dose , unit , dose_that , "
                                      "remark , m_usage , goods_norms , goods_orgin")
                    for detail_data in detail_datas:
                        logger_timer.info("- <==  Row: {}".format(detail_data))
                        pres_detail.append(dict(zip(detail_data.keys(), detail_data)))
                    prescription = dict(zip(pres_data.keys(), pres_data))
                    prescription.update(pres_consignee_list)
                    logger_timer.info("将要插入中间表的处方信息:{}".format(prescription))
                    logger_timer.info("将要插入中间表的处方详情:{}".format(pres_detail))
                    insert_mid_pres_res = insert_mid_prescription(prescription, pres_detail)
                    if insert_mid_pres_res['status'] == 'success':
                        logger_timer.info("处方中间表和处方明细表插入成功！{}".format(insert_mid_pres_res))
                        consignee_update_res = update_consignee_status(pres_consignee_list['pres_num'])
                        if consignee_update_res['status'] == 'success':
                            logger_timer.info('写入中间表状态更新成功！{}'.format(consignee_update_res))
                        else:
                            logger_timer.info('写入中间表状态更新失败！{}'.format(consignee_update_res))
                    else:
                        logger_timer.info("处方中间表和处方明细表写入异常！{}".format(insert_mid_pres_res))
                        message = "将处方插入中间表发生异常！"
                        # send_remind_message(pres_consignee_list['pres_num'], message)
                else:
                    message = "从医院查询处方详情为空！"
                    logger_timer.error("{} 处方号：{}".format(message, pres_consignee_list['pres_num']))
                    # send_remind_message(pres_consignee_list['pres_num'], message)
            else:
                message = "从医院查询处方为空！"
                logger_timer.error("{} 处方号：{}".format(message, pres_consignee_list['pres_num']))
                # send_remind_message(pres_consignee_list['pres_num'], message)
    else:
        return


def upload_prescription_job():
    """
    定时轮询上传处方和写入中间表
    :return:
    """
    time_out()
    logger_timer.info("上传处方定时任务开始================================")
    upload_presnum = []
    upload_failed_info = []
    upload_failed_count = 0
    prescription_lists = get_pre_lists_by_statues(0, 10000)
    if prescription_lists:
        for prescription_list in prescription_lists:
            if prescription_list['upload_status'] >= 0 and prescription_list['upload_status'] < 5:
                upload_presnum.append(prescription_list['pres_num'])
            elif prescription_list['upload_status'] >= 5:
                upload_failed_count += 1
                upload_failed_info.append(prescription_list)
        if upload_presnum:
            if upload_failed_count == 0:
                upload_prescriptions(upload_presnum)
            else:
                logger_timer.info("处方表中有 {} 张处方多次上传失败！本次定时任务不再处理.详情如下:".format(upload_failed_count))
                for info in upload_failed_info:
                    logger_timer.info("处方号:{} 上传失败次数: {}".format(info['pres_num'], info['upload_status']))
                upload_prescriptions(upload_presnum)
        else:
            logger_timer.info("处方表中有 {} 张处方多次上传失败！本次定时任务不再处理.详情如下:".format(upload_failed_count))
            for info in upload_failed_info:
                logger_timer.info("处方号:{} 上传失败次数: {}".format(info['pres_num'], info['upload_status']))
    else:
        logger_timer.info("本次无未上传处方！")
    insert_mid_by_pres_consignee()
    logger_timer.info("上传处方定时任务结束================================")
