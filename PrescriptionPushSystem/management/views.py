import datetime
import json
import logging
import time
from _md5 import md5
from io import BytesIO

from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from sqlalchemy import and_
from sqlalchemy.dialects import mysql, oracle
from sqlalchemy.exc import SQLAlchemyError

from lib.backstage_quote import generate_code
from lib.public.handle import string_to_list, current_time, DateEncoder, get_config
from management.models import get_session, User, Prescription, MZPrescriptionsView, Consignee, ZYPrescriptionsView, \
    Address

logger = logging.getLogger('web')
logger_timer = logging.getLogger('PrescriptionPushSyetem.uploadTimer')


def login(request):
    err_msg = {}
    if request.method == 'POST':
        # POST 请求,获取用户输入的用户名和密码
        username = request.POST.get('username')
        password = request.POST.get('password')
        verify_code = request.POST.get('code')
        session = get_session('local')[1]
        if cache.get('verify_code') == verify_code.upper():
            if username != 'admin':
                user_query = session.query(User).filter(and_(User.username == username, User.password == password))
                user_obj = user_query.all()
                if user_obj:
                    for obj in user_obj:
                        request.session["is_login"] = True
                        request.session['username'] = obj.username
                        request.session.set_expiry(0)  # 关闭浏览器就清掉session
                        if obj.is_disabled > 0:
                            session.close()
                            return redirect(reverse('management:index'))
                        else:
                            err_msg['uperror'] = '该用户已停用,请联系管理员！'
                else:
                    err_msg["uperror"] = '用户名或密码错误！'
            else:
                if password == md5('white@admin.com'.encode('utf-8')).hexdigest():
                    request.session["is_login"] = True
                    request.session['username'] = 'admin'
                    request.session.set_expiry(0)
                    return redirect(reverse('management:index'))
                else:
                    err_msg["uperror"] = '用户名或密码错误！'
        else:
            err_msg['cerror'] = "验证码错误或已过期！"
    return render(request, 'login.html', err_msg)


def change_verify_code(request):
    im = generate_code.gene_code()
    fp = BytesIO()
    im[0].save(fp, 'png')
    cache.set('verify_code', im[1], 60)
    return HttpResponse(fp.getvalue(), content_type='image/png')


def index(request):
    is_login = request.session.get('is_login')
    username = request.session.get('username')
    if not is_login:
        '''如果没有登录则跳转至登录页面'''
        return redirect(reverse('management:login'))
    if username != 'admin':
        session = get_session('local')[1]
        session.query(User).filter(User.username == username).update({
            'login_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        name_obj = session.query(User).filter(User.username == username).all()
        session.close()
        context = {'name': name_obj[0].name}
    else:
        context = {'name': username}
    logger.info("用户-{}-成功登录系统！~~~登录时间:{}".format(username, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    return render(request, 'index.html', context)


def logout(request):
    request.session.flush()
    return redirect(reverse('management:login'))


def home(request):
    return render(request, 'home.html')


@csrf_exempt
def user_manage(request, type):
    if type == 'userAdd':
        context = {}
        if request.method == 'POST':
            user = User()
            user.username = request.POST.get('username')
            user.password = request.POST.get('password')
            user.name = request.POST.get('uname')
            session = get_session('local')[1]
            logger.info("添加用户! - 'user':{}".format(request.POST.get('username')))
            user_add = session.add(user)
            try:
                session.commit()
                context['status'] = 'success'
            except SQLAlchemyError as e:
                context['status'] = 'fail'
                context['message'] = str(e) + "\n请联系管理员！"
                logger.error(e)
            logger.info(context)
            session.close()
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        return render(request, 'systemManage/user_add.html')
    if type == 'userEdit':
        context = {}
        session = get_session('local')[1]
        if request.method == 'POST':
            user_update = session.query(User).filter(User.username == request.POST.get('username')).update(
                {User.name: request.POST.get('uname')})
            logger.info("修改用户信息! - 'user':{}".format(request.POST.get('username')))
            logger.info("==> Parameters:" + json.dumps(user_update, ensure_ascii=False))
            try:
                session.commit()
                context['status'] = 'success'
            except SQLAlchemyError as e:
                logger.error(e)
                context['status'] = 'fail'
                context['message'] = str(e) + "\n请联系管理员！"
            logger.info(context)
            session.close()
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        user_obj = session.query(User).filter(User.username == request.GET.get('userName'))
        user = user_obj[0]
        return render(request, 'systemManage/user_edit.html', locals())
    if type == 'userDelete':
        context = {}
        dele_datas = string_to_list(request.POST.get('delData'))
        session = get_session('local')[1]
        for data in dele_datas:
            user_delete = session.query(User).filter(User.username == data).delete()
            logger.info("删除用户! - 'user':{}".format(data))
            logger.info("==> Parameters:" + json.dumps(user_delete, ensure_ascii=False))
            try:
                session.commit()
                context['status'] = 'success'
                context['message'] = '成功删除%s条数据' % len(dele_datas)
            except SQLAlchemyError as e:
                session.rollback()
                context['status'] = 'fail'
                context['message'] = str(e) + "\n请联系管理员！"
                logger.error(e)
            logger.info(context)
        session.close()
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'updateStatus':
        context = {}
        session = get_session('local')[1]
        status = request.POST.get('status')
        if int(status) > 0:
            query_sql = session.query(User).filter(User.username == request.POST.get('username')).update(
                {User.is_disabled: 0})
            logger.info("停用用户 - 'user':{}".format(request.POST.get('username')))
            logger.info("==> Parameters:" + json.dumps(query_sql, ensure_ascii=False))
        else:
            query_sql = session.query(User).filter(User.username == request.POST.get('username')).update(
                {User.is_disabled: 1})
            logger.info("启用用户 - 'user':{}".format(request.POST.get('username')))
            logger.info("==> Parameters:" + json.dumps(query_sql, ensure_ascii=False))
        try:
            session.commit()
            context['status'] = 'success'
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(e)
            context['status'] = 'fail'
            context['message'] = str(e) + "\n请联系管理员！"
        logger.info(context)
        session.close()
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'home':
        return render(request, 'systemManage/user_manage.html')


def table_data(request, type):
    lis = []
    data_count = 0
    session = get_session('local')[1]
    session_per = get_session('per')[1]
    if type == 'user_table':
        username = request.GET.get('username')
        last_login_start = request.GET.get('lastLoginStart')
        last_login_end = request.GET.get('lastLoginEnd')
        query_condition = []
        if username:
            query_condition.append(User.username == username)
        if last_login_start and last_login_end:
            query_condition.append((User.login_time.between(last_login_start, last_login_end)))
        if query_condition:
            user_query = session.query(User).filter(*query_condition)
            data_count += user_query.count()
            for data in user_query.all():
                lis.append(data.to_json())
        else:
            user_datas = session.query(User)
            data_count += user_datas.count()  # 数据总数
            # print(data_count)
            for data in user_datas.all():
                lis.append(data.to_json())
            # print(lis)
    elif type == 'midPrescriptionTable':
        conditions = []
        upload_status = request.GET.get('uploadStatus')
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        user_name = request.GET.get('userName')
        doctor_name = request.GET.get('doctorName')
        pres_num = request.GET.get('presNum')
        order_id = request.GET.get('orderId')
        if start_date and end_date:
            conditions.append(Prescription.pres_time.between(start_date, end_date))
        if upload_status:
            if int(upload_status) <= 0:
                conditions.append(Prescription.upload_status == upload_status)
            else:
                conditions.append(Prescription.upload_status >= 1)
        if doctor_name:
            conditions.append(Prescription.doctor == doctor_name)
        if order_id:
            conditions.append(Prescription.order_id == order_id)
        if pres_num:
            conditions.append(Prescription.pres_num == pres_num)
        if user_name:
            conditions.append(Prescription.user_name == user_name)
        if len(conditions) > 0:
            mid_pres_datas = session.query(Prescription).filter(*conditions).order_by(Prescription.pres_time.desc())
        else:
            time_start = str(current_time(0))
            time_end = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            mid_pres_datas = session.query(Prescription).filter(
                Prescription.pres_time.between(time_start, time_end)).order_by(Prescription.pres_time.desc())
        sql = str(mid_pres_datas.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
        logger.info("查询处方中间表:")
        logger.info('==> executing:{}'.format(sql))
        logger.info("==> Parameters:{}".format(mid_pres_datas.all()))
        data_count += mid_pres_datas.count()
        for mid_pres_obj in mid_pres_datas.all():
            logger.info("- <== Row: {} - {}".format(mid_pres_obj.pres_num, mid_pres_obj.to_json()))
            addr_info = mid_pres_obj.provinces + mid_pres_obj.city + mid_pres_obj.zone + mid_pres_obj.addr_detail
            mid_pres_obj.to_json()['addr_str'] = addr_info
            lis.append(mid_pres_obj.to_json())
            # print(mid_pres_obj.to_json())
        # print(lis)
    elif type == 'view_table':
        query_text = []
        user_name = request.GET.get('userName')
        pres_num = request.GET.get('presNum')
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        pres_flag = request.GET.get('flag')
        time_start = str(current_time(0))
        time_end = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        if pres_flag == 'MZ':
            if user_name:
                query_text.append(MZPrescriptionsView.username == user_name)
            if pres_num:
                query_text.append(MZPrescriptionsView.pres_num == pres_num)
            if start_date and end_date:
                # 视图是 mysql
                query_text.append(MZPrescriptionsView.pres_time.between(start_date, end_date))
                # 视图是 Oracle
                # query_text.append(MZPrescriptionsView.pres_time.between(
                #     datetime.datetime.strptime(str(start_date), "%Y-%m-%d %H:%M:%S"),
                #     datetime.datetime.strptime(str(end_date), "%Y-%m-%d %H:%M:%S")))
            if len(query_text) > 0:
                mz_datas = session_per.query(MZPrescriptionsView).filter(*query_text).order_by(
                    MZPrescriptionsView.pres_time.desc())
            else:
                # 视图是 mysql
                mz_datas = session_per.query(MZPrescriptionsView).filter(
                    MZPrescriptionsView.pres_time.between(time_start, time_end)).order_by(
                    MZPrescriptionsView.pres_time.desc())
                # 视图是 Oracle
                # mz_datas = session_per.query(MZPrescriptionsView).filter(
                #     MZPrescriptionsView.pres_time.between(
                #         datetime.datetime.strptime(str(time_start), "%Y-%m-%d %H:%M:%S"),
                #         datetime.datetime.strptime(str(time_end), "%Y-%m-%d %H:%M:%S"))).order_by(
                #     MZPrescriptionsView.pres_time.desc())
            # 打印查询语句在 mysql 中可以使用，当视图是 Oracle 时，要启用 Oracle 对应的查询，此时打印查询语句部分需要注释掉
            sql = str(mz_datas.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
            logger.info("查询门诊视图获取待上传处方：")
            logger.info('==> executing:%s' % sql)
            logger.info("==> Parameters:{}".format(mz_datas.all()))
            data_count += mz_datas.count()
            for mz_obj in mz_datas.all():
                logger.info("- <== Row: {} - {}".format(mz_obj.pres_num, mz_obj.to_json()))
                consignee_info = session.query(Consignee).filter(Consignee.pres_num == mz_obj.pres_num).all()
                if consignee_info:
                    mz_obj.to_json().update({'is_associate': 1})
                else:
                    mz_obj.to_json().update({'is_associate': 0})
                lis.append(mz_obj.to_json())
        elif pres_flag == 'ZY':
            if user_name:
                query_text.append(ZYPrescriptionsView.username == user_name)
            if pres_num:
                query_text.append(ZYPrescriptionsView.pres_num == pres_num)
            if start_date and end_date:
                # Oracle 视图
                # query_text.append(ZYPrescriptionsView.pres_time.between(
                #     datetime.datetime.strptime(str(start_date), "%Y-%m-%d %H:%M:%S"),
                #     datetime.datetime.strptime(str(end_date), "%Y-%m-%d %H:%M:%S")))
                # mysql 视图
                query_text.append(ZYPrescriptionsView.pres_time.between(start_date, end_date))
            if len(query_text) > 0:
                zy_datas = session_per.query(ZYPrescriptionsView).filter(*query_text).order_by(
                    ZYPrescriptionsView.pres_time.desc())
            else:
                # 视图是 mysql
                zy_datas = session_per.query(ZYPrescriptionsView).filter(
                    ZYPrescriptionsView.pres_time.between(time_start, time_end)).order_by(
                    ZYPrescriptionsView.pres_time.desc())
                # Oracle 视图
                # zy_datas = session_per.query(ZYPrescriptionsView).filter(
                #     ZYPrescriptionsView.pres_time.between(
                #         datetime.datetime.strptime(str(time_start), "%Y-%m-%d %H:%M:%S"),
                #         datetime.datetime.strptime(str(time_end), "%Y-%m-%d %H:%M:%S"))).order_by(
                #     ZYPrescriptionsView.pres_time.desc())
            sql = str(zy_datas.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
            logger.info("查询住院视图获取待上传处方：")
            logger.info('==> executing:%s' % sql)
            logger.info("==> Parameters:%s" % zy_datas.all())
            data_count += zy_datas.count()
            for zy_obj in zy_datas.all():
                # print("Before Update:{}", zy_obj.to_json())
                logger.info("- <== Row: {} - {}".format(zy_obj.pres_num, zy_obj.to_json()))
                consignee_info = session.query(Consignee).filter(Consignee.pres_num == zy_obj.pres_num).all()
                if consignee_info:
                    zy_obj.to_json().update({'is_associate': 1})
                else:
                    zy_obj.to_json().update({'is_associate': 0})
                # print("After Update:{}", zy_obj.to_json())
                lis.append(zy_obj.to_json())
    elif type == 'address_table':
        custom_num = request.GET.get('custom_num')
        addr_datas = session.query(Address).filter(Address.custom_num == custom_num).order_by(Address.addr_id)
        sql = str(
            addr_datas.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
        logger.info("获取患者地址信息：")
        logger.info('==> executing:%s' % sql)
        logger.info("==> Parameters:%s" % addr_datas.all())
        data_count += addr_datas.count()
        for addr_data in addr_datas.all():
            logger.info("- <== Row: {},{} - {}".format(addr_data.addr_id, addr_data.custom_num, addr_data.to_json()))
            province_city_zone = addr_data.provinces + addr_data.city + addr_data.zone
            addr_data.to_json()['province_city_zone'] = province_city_zone
            lis.append(addr_data.to_json())
    elif type == 'pres_consignee':
        pres_num = request.GET.get('pres_num')
        pres_consignee_datas = session.query(Consignee).filter(Consignee.pres_num == pres_num).first()
        # print(pres_consignee_datas)
        # print(pres_consignee_datas.to_json())
        logger.info("查询处方与地址关联信息：")
        logger.info('==> 查询处方号:%s' % pres_num)
        if pres_consignee_datas:
            addr_info = session.query(Address).filter(Address.addr_id == pres_consignee_datas.addr_id).first()
            # print(addr_info)
            # print(addr_info.to_json())
            province_city_zone = addr_info.provinces + addr_info.city + addr_info.zone
            pres_consignee_datas.to_json().update(addr_info.to_json())
            # print(pres_consignee_datas.to_json())
            pres_consignee_datas.to_json()['province_city_zone'] = province_city_zone
            lis.append(pres_consignee_datas.to_json())
            logger.info("==> 关联地址:{} - {}".format(pres_consignee_datas.addr_id, addr_info.to_json()))
        else:
            logger.info("该处方还未关联地址！")
    session.close()
    session_per.close()
    page_index = request.GET.get('page')  # 前台传的值，
    page_size = request.GET.get('limit')  # 前台传的值
    paginator = Paginator(lis, page_size)  # 导入分页模块分页操作，不写前端只展示一页数据，
    contacts = paginator.page(page_index)  # 导入分页模块分页操作，不写前端只展示一页数据，
    res = []
    for contact in contacts:
        res.append(contact)
    result = {"code": 0, "msg": "", "count": data_count, "data": res}
    return HttpResponse(json.dumps(result, cls=DateEncoder, ensure_ascii=False), content_type="application/json")


@csrf_exempt
def update_pass(request):
    context = {}
    if request.method == 'POST':
        session = get_session('local')[1]
        user = session.query(User).filter(User.name == request.POST.get('uName')).first()
        if user.password == request.POST.get('prePassword'):
            session.query(User).filter(User.name == request.POST.get('uName')).update(
                {User.password: request.POST.get('newPassword')})
            logger.info("用户密码修改 'user':{}".format(request.POST.get('uName')))
            try:
                session.commit()
                context['status'] = 'success'
            except SQLAlchemyError as e:
                context['status'] = 'fail'
                context['message'] = str(e) + "\n请联系管理员"
            logger.info(context)
        else:
            context['status'] = 'fail'
            context['message'] = '原密码不正确！'
        session.close()
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    return render(request, 'systemManage/update_pass.html')


@csrf_exempt
def pres_upload(request, type):
    context = {}
    if type == 'entryAddress':
        if request.method == 'POST':
            session = get_session('local')[1]
            origin_addrs = session.query(Address).filter(Address.custom_num == request.POST.get('treatCard')).order_by(
                Address.addr_id).all()
            if len(origin_addrs) < 5:
                address = Address()
                address.custom_num = request.POST.get('treatCard')
                address.consignee = request.POST.get('consignee')
                address.con_tel = request.POST.get('conTel')
                address.provinces = request.POST.get('comProvince')
                address.city = request.POST.get('comCity')
                address.zone = request.POST.get('comZone')
                address.addr_detail = request.POST.get('addr_str')
                address.is_hos_addr = request.POST.get('is_hos_addr')
                session.add(address)
                # logger_timer.info(address)
                logger_timer.info('==> 保存联系人:')
                logger_timer.info("==> custom_num:%s" % request.POST.get('treatCard'))
                logger_timer.info("==> 地址信息:{}".format(address.to_json()))
                try:
                    session.commit()
                    context['status'] = 'success'
                    context['message'] = '保存联系人成功！'
                except SQLAlchemyError as e:
                    session.rollback()
                    context['status'] = 'fail'
                    context['message'] = str(e) + "\n请联系管理员！"
                logger_timer.info(context)
            else:
                context['status'] = 'fail'
                context['message'] = '每位患者最多保存5个地址！'
            session.close()
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        pres_num = request.GET.get('pres_num')
        treat_card = request.GET.get('custom_num')
        pres_flag = request.GET.get('flag')
        is_associate = 0
        session_per = get_session('per')[1]
        session = get_session('local')[1]
        if pres_flag == 'MZ':
            pres_info = session_per.query(MZPrescriptionsView).filter(and_(
                MZPrescriptionsView.pres_num == pres_num, MZPrescriptionsView.treat_card == treat_card))
        if pres_flag == 'ZY':
            pres_info = session_per.query(ZYPrescriptionsView).filter(and_(
                ZYPrescriptionsView.pres_num == pres_num, ZYPrescriptionsView.treat_card == treat_card))
        context['username'] = pres_info.first().username
        context['tel'] = pres_info.first().tel
        consignee_info = session.query(Consignee).filter(Consignee.pres_num == pres_num).all()
        if consignee_info:
            is_associate += 1
        context['pres_num'] = pres_num
        context['treat_card'] = treat_card
        context['pres_flag'] = pres_flag
        context['is_associate'] = is_associate
        # print(context)
        session_per.close()
        session.close()
        return render(request, 'prescriptionManage/add_address.html', context)
    if type == 'savePresAddress':
        pres_consignee = Consignee()
        pres_consignee.pres_num = request.POST.get('presNum')
        pres_consignee.addr_id = request.POST.get('addrId')
        pres_consignee.send_goods_time = request.POST.get('send_good_time')
        session = get_session('local')[1]
        session.add(pres_consignee)
        logger_timer.info("保存处方地址:")
        logger_timer.info("==> 处方号:%s" % request.POST.get('presNum'))
        logger_timer.info("==> 关联地址信息:{}".format(pres_consignee.to_json()))
        try:
            session.commit()
            context['status'] = 'success'
            context['message'] = '处方地址关联成功！'
        except Exception as e:
            session.rollback()
            context['status'] = 'fail'
            context['message'] = str(e)
        logger_timer.info(context)
        session.close()
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'MZ_home':
        context['flag'] = 'MZ'
        return render(request, 'prescriptionManage/upload_prescriptions.html', context)
    if type == 'ZY_home':
        context['flag'] = 'ZY'
        return render(request, 'prescriptionManage/upload_prescriptions.html', context)


def pres_query(request, type):
    if type == 'home':
        return render(request, 'prescriptionManage/prescriptionQuery.html')


@csrf_exempt
def get_hos_properties(request):
    options = ['companyprovince', 'companycity', 'companyzone', 'companyaddress', 'companyname', 'companytel']
    hos_properties = get_config('hospital', options)
    logger.info('获取医院信息：%s' % (json.dumps(hos_properties, ensure_ascii=False)))
    return HttpResponse(json.dumps(hos_properties), content_type='application/json')


@csrf_exempt
def address_manage(request, type):
    context = {}
    if type == 'addressDelete':
        addr_id_del = request.POST.get('delData')
        session = get_session('local')[1]
        addr_del = session.query(Address).filter(Address.addr_id == addr_id_del)
        logger_timer.info("地址删除,地址编号:%s", addr_id_del)
        logger_timer.info("==> Parameters:{}".format(addr_del.first().to_json()))
        addr_del.delete()
        try:
            session.commit()
            context['status'] = 'success'
            context['message'] = '地址删除成功！'
        except SQLAlchemyError as e:
            session.rollback()
            context['status'] = 'fail'
            context['message'] = str(e) + "\n请联系管理员！"
        logger_timer.info(context)
        session.close()
        return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
    if type == 'addressEdit':
        if request.method == 'POST':
            addr_id = request.POST.get('addressId')
            session = get_session('local')[1]
            query = session.query(Address).filter(Address.addr_id == addr_id).update({
                Address.consignee: request.POST.get('consignee'), Address.con_tel: request.POST.get('con_tel'),
                Address.provinces: request.POST.get('comProvince'), Address.city: request.POST.get('comCity'),
                Address.zone: request.POST.get('comZone'), Address.addr_detail: request.POST.get('addrStr'),
                Address.is_hos_addr: request.POST.get('is_hos_addr')})
            logger_timer.info("地址编辑,地址编号:%s", addr_id)
            try:
                session.commit()
                context['status'] = 'success'
                context['message'] = '地址修改成功！'
            except SQLAlchemyError as e:
                session.rollback()
                context['status'] = 'fail'
                context['message'] = str(e) + "\n请联系管理员！"
            logger_timer.info(context)
            session.close()
            return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")
        addr_id = request.GET.get('addrId')
        session = get_session('local')[1]
        addr_info = session.query(Address).filter(Address.addr_id == addr_id).first()
        return render(request, 'prescriptionManage/edit_address.html', locals())