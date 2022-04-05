# coding:utf-8
"""
  Time : 2022/4/3 2:12
  Author : vincent
  FileName: models
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2022/4/3 2:12
"""
import datetime
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Float, String, DateTime, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

from lib.public.handle import get_config

Base = declarative_base()               # 表格对象基类


class User(Base):
    """用户信息表"""
    __tablename__ = 'tb_admin'
    username = Column(String(50), nullable=False, primary_key=True, unique=True, comment='用户名')
    name = Column(String(50), nullable=True, unique=True, comment='姓名')
    password = Column(String(100), nullable=False, comment='密码')
    # register_time = Column(String(25), comment='注册时间')
    register_time = Column(DateTime, default=datetime.datetime.now, comment='注册时间')
    # auto_now_add：当对象首次被创建时,自动将该字段的值设置为当前时间.通常用于表示对象创建时间
    # auto_now：当对象被保存时, 自动将该字段的值设置为当前时间.通常用于表示 “last - modified” 时间戳
    login_time = Column(TIMESTAMP(timezone=False), comment='最近登录时间')
    is_disabled = Column(Integer, default=1, comment='是否禁用')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict


class Consignee(Base):
    """
    处方地址关联表类
    """
    __tablename__ = 'pres_consignee'
    pres_num = Column(String(50), nullable=False, primary_key=True, comment='医院处方号')
    addr_id = Column(Integer, nullable=False, comment='地址id')
    send_goods_time = Column(String(25), comment='送货时间')
    is_write_mid = Column(Integer, nullable=False, default=0, comment="是否写入中间表 0 未处理 1 已处理")

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict


class Prescription(Base):
    """
    处方表类
    """
    __tablename__ = 'mid _prescriptions'
    pres_num = Column(String(50), nullable=False, primary_key=True, comment='处方单号')
    pres_time = Column(String(25), comment='处方生成时间')
    treat_card = Column(String(50), comment='诊疗卡号')
    reg_num = Column(String(50), comment='挂单号')
    province = Column(String(10), comment='省份')
    city = Column(String(10), comment='城市')
    zone = Column(String(10), comment='区')
    addr_detail = Column(String(120), comment='收货地址')
    consignee = Column(String(20), comment='收货人')
    con_tel = Column(String(50), comment='收货人电话')
    send_goods_time = Column(String(25), comment='送货时间')
    user_name = Column(String(20), comment='患者姓名')
    age = Column(Integer, comment='患者年龄')
    gender = Column(Integer, comment='患者性别')
    tel = Column(String(50), comment='患者电话')
    is_suffering = Column(Integer, comment='是否煎煮 取值范围：0 否，1 是')
    amount = Column(Integer, comment='数量')
    suffering_num = Column(Integer, comment='煎煮剂数')
    ji_fried = Column(Integer, comment='几煎')
    per_pack_num = Column(Integer, comment='每剂几包')
    per_pack_dose = Column(Integer, comment='每包多少ml')
    type = Column(Integer, comment='处方类型 0:中药，1:西药，2:膏方，3:丸剂，5:散剂，7:免煎颗粒')
    is_within = Column(Integer, comment='服用方式 0 内服，1 外用')
    other_pres_num = Column(String(50), nullable=False, comment='医院处方号')
    special_instru = Column(String(100), comment='处方特殊说明 诊断信息')
    bed_num = Column(String(50), comment='床位号')
    hos_depart = Column(String(50), comment='医院科室')
    hospital_num = Column(String(50), comment='住院号')
    disease_code = Column(String(50), comment='病区号')
    doctor = Column(String(50), comment='医生姓名')
    prescript_remark = Column(String(120), comment='处方备注')
    upload_status = Column(Integer, default=0, comment='上传状态(成功 -1,刚生成时为0,每失败一次+1)')
    description = Column(String(100), comment='上传描述')
    upload_time = Column(TIMESTAMP(timezone=False), comment='上传时间')
    order_id = Column(String(36), comment='康美订单id')
    is_hos_addr = Column(Integer, comment='地址类型 0 未知,1送医院,2 送患者家里')
    medication_methods = Column(String(50), comment='用药方法')
    medication_instruction = Column(String(50), comment='用药指导')
    source = Column(Integer, comment='0 门诊 1 住院')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict

    def keys(self):
        """当对实例化对象使用dict(obj)的时候, 会调用这个方法,这里定义了字典的键, 其对应的值将以obj['name']的形式取,
        但是对象是不可以以这种方式取值的, 为了支持这种取值, 可以为类增加这个方法"""
        return ('addr_detail', 'age', 'amount', 'bed_num', 'city', 'con_tel', 'consignee', 'disease_code', 'doctor',
                'gender', 'hos_depart', 'hospital_num', 'is_hos_addr', 'is_suffering', 'is_within', 'ji_fried',
                'keys', 'medication_instruction', 'medication_methods', 'metadata', 'order_id', 'other_pres_num',
                'per_pack_dose', 'per_pack_num', 'pres_num', 'pres_time', 'prescript_remark', 'province',
                'reg_num', 'send_goods_time', 'source', 'special_instru', 'suffering_num', 'tel', 'treat_card',
                'type', 'upload_status', 'upload_time', 'user_name', 'zone')

    def __getitem__(self, item):
        """内置方法, 当使用obj['name']的形式的时候, 将调用这个方法, 这里返回的结果就是值"""
        return getattr(self, item)


class PresDetails(Base):
    """
    处方明细(药材)表类
    """
    __tablename__ = 'mid_prescription_details'
    pres_detail_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True, comment='处方详情id')
    pres_num = Column(String(36), nullable=False, comment='处方单号')
    goods_num = Column(String(100), nullable=False, comment='药材编号')
    medicines = Column(String(100), nullable=False, comment='药品名')
    dose = Column(String(10), comment='剂量')
    unit = Column(String(50), comment='单位')
    m_usage = Column(String(100), comment='药品特殊煎法')
    goods_norms = Column(String(100), comment='药品规格')
    goods_orgin = Column(String(100), comment='药品产地')
    remark = Column(String(100), comment='备注')
    dose_that = Column(String(100), comment='药品注意事项说明')
    unit_price = Column(Float, server_default='0.00', comment='医院药品销售单价')
    MedPerDos = Column(String(20), comment='用量(剂量)eg:2片/次(每次两片)')
    MedPerDay = Column(String(20), comment='执行频率(频次)（eg:一日3次）')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict

    def keys(self):
        return ('pres_num', 'goods_num', 'medicine', 'dose', 'unit', 'm_usage', 'goods_norms', 'goods_orgin', 'remark',
                'dose_that', 'unit_price', 'MedPerDos', 'MedPerDay')


class Address(Base):
    """
    地址 custom_addr 表类
    """
    __tablename__ = 'custom_addr'
    addr_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True, comment='地址id')
    custom_num = Column(String(50), nullable=False, comment='患者id,标识唯一患者')
    consignee = Column(String(30), comment='收货人')
    con_tel = Column(String(50), comment='收货人电话')
    province = Column(String(10), comment='省份')
    city = Column(String(10), comment='城市')
    zone = Column(String(10), comment='区县')
    addr_detail = Column(String(50), nullable=False, comment='详细地址')
    is_hos_addr = Column(Integer, comment='地址类型 0 未知,1送医院,2 送患者家里')
    auto_state = Column(Integer, default=0, comment='是否默认地址')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict


class MZPrescriptionsView(Base):
    __tablename__ = 'mz_hosp_prescriptions_view'
    # __abstract__ = True
    pres_num = Column(String(50), nullable=False, primary_key=True, comment='处方单号')
    pres_time = Column(String(25), comment='处方生成时间')
    treat_card = Column(String(50), comment='诊疗卡号')
    reg_num = Column(String(50), comment='挂单号')
    username = Column(String(20), comment='患者姓名')
    age = Column(Integer, comment='患者年龄')
    gender = Column(Integer, comment='患者性别')
    tel = Column(String(50), comment='患者电话')
    is_suffering = Column(Integer, comment='是否煎煮 取值范围：0 否，1 是')
    amount = Column(Integer, comment='数量')
    suffering_num = Column(Integer, comment='煎煮剂数')
    ji_fried = Column(Integer, comment='几煎')
    per_pack_num = Column(Integer, comment='每剂几包')
    per_pack_dose = Column(Integer, comment='每包多少ml')
    type = Column(Integer, comment='处方类型 0:中药，1:西药，2:膏方，3:丸剂，5:散剂，7:免煎颗粒')
    is_within = Column(Integer, comment='服用方式 0 内服，1 外用')
    special_instru = Column(String(100), comment='处方特殊说明 诊断信息')
    hos_depart = Column(String(50), comment='医院科室')
    hospital_num = Column(String(50), comment='住院号')
    doctor = Column(String(50), comment='医生姓名')
    remark = Column(String(120), comment='处方备注')
    medication_methods = Column(String(50), comment='用药方法')
    medication_instruction = Column(String(50), comment='用药指导')
    is_hos = Column(Integer, comment='0 门诊 1 住院')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict


class ZYPrescriptionsView(Base):
    # __abstract__ = True
    __tablename__ = 'zy_hosp_prescriptions_view'
    pres_num = Column(String(50), nullable=False, primary_key=True, comment='处方单号')
    pres_time = Column(String(25), comment='处方生成时间')
    treat_card = Column(String(50), comment='诊疗卡号')
    reg_num = Column(String(50), comment='挂单号')
    username = Column(String(20), comment='患者姓名')
    age = Column(Integer, comment='患者年龄')
    gender = Column(Integer, comment='患者性别')
    tel = Column(String(50), comment='患者电话')
    is_suffering = Column(Integer, comment='是否煎煮 取值范围：0 否，1 是')
    amount = Column(Integer, comment='数量')
    suffering_num = Column(Integer, comment='煎煮剂数')
    ji_fried = Column(Integer, comment='几煎')
    per_pack_num = Column(Integer, comment='每剂几包')
    per_pack_dose = Column(Integer, comment='每包多少ml')
    type = Column(Integer, comment='处方类型 0:中药，1:西药，2:膏方，3:丸剂，5:散剂，7:免煎颗粒')
    is_within = Column(Integer, comment='服用方式 0 内服，1 外用')
    special_instru = Column(String(100), comment='处方特殊说明 诊断信息')
    bed_num = Column(String(50), comment='床位号')
    hos_depart = Column(String(50), comment='医院科室')
    hospital_num = Column(String(50), comment='住院号')
    disease_code = Column(String(50), comment='病区号')
    doctor = Column(String(50), comment='医生姓名')
    remark = Column(String(120), comment='处方备注')
    medication_methods = Column(String(50), comment='用药方法')
    medication_instruction = Column(String(50), comment='用药指导')
    is_hos = Column(Integer, comment='0 门诊 1 住院')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict


class MZDetailsView(Base):
    __tablename__ = 'mz_details_view'
    # __abstract__ = True
    id = Column(Integer, primary_key=True)
    pres_num = Column(String(36), nullable=False, comment='处方单号')
    goods_num = Column(String(100), nullable=False, comment='药材编号')
    medicines = Column(String(100), nullable=False, comment='药品名')
    dose = Column(String(10), comment='剂量')
    unit = Column(String(50), comment='单位')
    dose_that = Column(String(100), comment='药品注意事项说明')
    m_usage = Column(String(100), comment='药品特殊煎法')
    goods_norms = Column(String(100), comment='药品规格')
    goods_orgin = Column(String(100), comment='药品产地')
    remark = Column(String(100), comment='备注')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict


class ZYDetailsView(Base):
    __tablename__ = 'zy_details_view'
    # __abstract__ = True                       # 取消注释，在初始化数据库时不会创建对应的表，初始化完毕再注释掉
    id = Column(Integer, primary_key=True)
    pres_num = Column(String(36), nullable=False, comment='处方单号')
    goods_num = Column(String(100), nullable=False, comment='药材编号')
    medicines = Column(String(100), nullable=False, comment='药品名')
    dose = Column(String(10), comment='剂量')
    unit = Column(String(50), comment='单位')
    dose_that = Column(String(100), comment='药品注意事项说明')
    m_usage = Column(String(100), comment='药品特殊煎法')
    goods_norms = Column(String(100), comment='药品规格')
    goods_orgin = Column(String(100), comment='药品产地')
    remark = Column(String(100), comment='备注')

    def to_json(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        if "keys" in dict:
            del dict['keys']
        if "metadata" in dict:
            del dict['metadata']
        return dict


# class MPrescriptionsView(models.Model):
#     __tablename__ = 'mz_hosp_prescriptions_view'
#     pres_num = models.CharField(max_length=50, primary_key=True, verbose_name='处方单号')
#     pres_time = models.CharField(max_length=25, verbose_name='处方生成时间')
#     treat_card = models.CharField(max_length=50, null=True, verbose_name='诊疗卡号')
#     reg_num = models.CharField(max_length=50, null=False, verbose_name='挂单号')
#     username = models.CharField(max_length=20, null=False, verbose_name='患者姓名')
#     age = models.IntegerField(null=False, verbose_name='患者年龄')
#     gender = models.IntegerField(null=False, verbose_name='患者性别 0 女，1 男，2 未知(病人没有登记性别的情况下)')
#     tel = models.CharField(max_length=50, null=False, verbose_name='患者电话')
#     is_suffering = models.IntegerField(null=False, verbose_name='是否煎煮 取值范围：0 否，1 是')
#     amount = models.IntegerField(null=False, verbose_name='剂数(付数)')
#     suffering_num = models.IntegerField(null=False, verbose_name='煎煮袋数')
#     ji_fried = models.IntegerField(verbose_name='几煎')
#     per_pack_num = models.IntegerField(verbose_name='每剂几包')
#     per_pack_dose = models.IntegerField(verbose_name='每包多少ml')
#     type = models.IntegerField(verbose_name='处方类型 0:中药，1:西药，2:膏方，3:丸剂，5:散剂，7:免煎颗粒')
#     is_within = models.IntegerField(null=False, verbose_name='服用方式 0 内服，1 外用')
#     special_instru = models.CharField(max_length=100, null=True, verbose_name='处方特殊说明 诊断信息')
#     hos_depart = models.CharField(max_length=50, null=True, verbose_name='医院科室')
#     hospital_num = models.CharField(max_length=50, null=True, verbose_name='住院号')
#     doctor = models.CharField(max_length=50, null=True, verbose_name='医生姓名')
#     remark = models.CharField(max_length=120, null=True, verbose_name='处方备注')
#     medication_methods = models.CharField(max_length=50, null=True, verbose_name='用药方法')
#     medication_instruction = models.CharField(max_length=50, null=True, verbose_name='用药指导')
#     is_hos = models.IntegerField(null=False, verbose_name='处方来源类型 0 默认,1门诊,2住院,3 其他')


def mysql_connect(sql):
    """
    使用原生SQL查询对方数据库视图，返回查询数据
    :return: data
    engine = create_engine('dialect+driver://username:password@host:port/database')
        [dialect -- 数据库类型, driver -- 数据库驱动选择, username -- 数据库用户名,
        password -- 用户密码, host 服务器地址, port 端口, database 数据库]
    """
    conn_pool = create_engine(
        # "mysql+pymysql://root:KM*021191@localhost:3306/zhyf?charset=utf8",
        "mysql+mysqlconnector://root:vincent021191@localhost:3306/hospital?charset=utf8",
        max_overflow=0,         # 超过连接池大小外最多创建的连接
        pool_size=5,            # 连接池大小
        pool_timeout=30,        # 池中没有线程最多等待的时间，否则报错
        pool_recycle=3600       # 多久之后对线程池中的线程进行一次连接的回收（重置）
        )
    conn = conn_pool.raw_connection()   # 从连接池中获取1个连接,开始连接
    cursor = conn.cursor()
    logging.info('==> executing:%s' % sql)
    cursor.execute(sql)
    print(cursor.description)
    data = cursor.fetchall()
    logging.info("==> Parameters:")
    for da in data:
        logging.info(da)
    cursor.close()
    conn.close()
    return data


def mysql_connect_fatchall(sql):
    """
    使用原生SQL查询对方数据库视图，返回查询数据
    :return: data
    engine = create_engine('dialect+driver://username:password@host:port/database')
        [dialect -- 数据库类型, driver -- 数据库驱动选择, username -- 数据库用户名,
        password -- 用户密码, host 服务器地址, port 端口, database 数据库]
    """
    conn_pool = create_engine(
        # "mysql+pymysql://root:KM*021191@localhost:3306/zhyf?charset=utf8",
        "mysql+mysqlconnector://root:vincent021191@localhost:3306/hospital?charset=utf8",
        max_overflow=0,
        pool_size=5,
        pool_timeout=30,
        pool_recycle=3600
        )
    conn = conn_pool.raw_connection()
    cursor = conn.cursor()
    logging.info('==> executing:%s' % sql)
    cursor.execute(sql)
    columns = [col[0] for col in cursor.description]  # 拿到对应的字段列表
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    logging.info("==> Parameters:")
    for da in data:
        logging.info(da)
    cursor.close()
    conn.close()
    return data


def get_session(connect_type, sql=""):
    """
    初始化数据库连接,返回 engine 和 session
    :return: (engine,session)
    """
    connect_strings = ""
    if connect_type == 'local':
        connect_strings += get_config('jdbc', 'mysqlConnectString')
    elif connect_type == 'per':
        connect_strings += get_config('jdbc', 'oracleConnectString')
    engine = create_engine(connect_strings, max_overflow=0, pool_size=5, pool_timeout=30, pool_recycle=3600)
    if sql:
        en = engine.raw_connection()
        cursor = en.cursor()
        logging.info('==> executing:%s' % sql)
        cursor.execute(sql)
        data = cursor.fetchall()
        logging.info("==> Parameters:")
        for da in data:
            logging.info(da)
        cursor.close()
        en.close()
        return data
    else:
        DBSession = sessionmaker(bind=engine)  # 创建会话的类
        session = DBSession()
        return engine, session


def init_db(en):
    """
    根据类创建数据库表
    :return:
    """
    Base.metadata.create_all(en)


def drop_db(en):
    """
    根据类 删除数据库表
    :return:
    """
    Base.metadata.drop_all(en)  # 这行代码很关键哦！！ 读取继承了Base类的所有表在数据库中进行删除表


if __name__ == '__main__':
    # 开发环境可以使用
    es = get_session('local')
    init_db(es[0])                    # 执行创建
    # drop_db(es[0])

    # 生产环境部署完成用来初始化
    # connect_strings = "mysql+mysqlconnector://root:zhyf@localhost:3306/zhyf_test?charset=utf8"
    # en = create_engine(connect_strings, max_overflow=0, pool_size=5, pool_timeout=30, pool_recycle=3600)
    # choice = input("需要做数据库初始化吗？(y/n)")
    # if choice == 'y':
    #     init_db(en)  # 执行创建
    #     print("数据库初始化完毕！")
    # elif choice == 'n':
    #     drop_db(en)  # 执行删除
    #     print("你已成功删库！可以跑路了土贼！")
