from flask import Blueprint, request, jsonify
from loguru import logger

from ...response import (
    ApiResponse,
    register_global_error_handlers,
    ValidationException,
    ResourceNotFoundException,
    BusinessRuleException,
    ErrorCodes
)

from .home_db import db_manager
from .home_model import HomeClimate, AirConditioner, HomePod, ScreenLog, Note, Fridge
from .home_db_helper import read_home_climate_last_records_with_minutes, read_home_climate_records_with_period, read_home_fridge_records_with_period

from ...utils import get_param, is_date_format_valid

clock_bp = Blueprint('smart_clock', __name__, url_prefix='/smart-clock')

@clock_bp.route('/health', methods=['GET'])
def api_health():
    return ApiResponse.success(message="You got me, I'm Clock, And I'm health")

@clock_bp.errorhandler(400)
def bad_request__error(e):
    raise ResourceNotFoundException(resource_type="Unknown", resource_id=ErrorCodes.RESOURCE_NOT_FOUND)

@clock_bp.errorhandler(500)
def internal_server_error(e):
    raise ValidationException(message="inner error", error_code=ErrorCodes.MISSING_PARAMETER)

@clock_bp.route('/screen-action/<int:count>', methods=['GET'])
def read_screen_action_api(count):
    count = get_param('count')
    with db_manager.session_scope() as session:
        try:
            # 取最新 10 条记录（按 id 倒序）
            records = session.query(ScreenLog) \
                .order_by(ScreenLog.id.desc()) \
                .limit(count) \
                .all()
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")
    return ApiResponse.success(data=records)

@clock_bp.route('/screen-action', methods=['POST'])
def insert_screen_action_api():
    action = get_param('action',None, type_=str)
    action_log = None
    if action == 'on':
        action_log = ScreenLog(action=1)
    elif action == 'off':
        action_log = ScreenLog(action=0)
    else:
        raise ValidationException(message="action参数没有传", error_code=ErrorCodes.MISSING_PARAMETER)

    with db_manager.session_scope() as session:
        try:
            session.add(action_log)
            session.commit()
            return ApiResponse.success(data=action_log.to_dict(), message="successfully")
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")

@clock_bp.route('/note<int:count>', methods=['GET'])
def read_note(count):
    with db_manager.session_scope() as session:
        try:
            # 取最新 10 条记录（按 id 倒序）
            records = session.query(Note) \
                .order_by(Note.id.desc()) \
                .limit(count) \
                .all()
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")
    return ApiResponse.success(data=records)

@clock_bp.route('/note', methods=['POST'])
def insert_note():
    note_content = get_param('note',None, type_=str)
    if note_content:
        new_note = Note(note=note_content)
        with db_manager.session_scope() as session:
            try:
                session.add(new_note)
                session.commit()
                return ApiResponse.success(data=new_note.to_dict(), message="successfully")
            except Exception as e:
                return ApiResponse.error(message=f"数据库错误: {e}")
    else:
        raise ValidationException(message="action参数没有传", error_code=ErrorCodes.MISSING_PARAMETER)



@clock_bp.route('/temperature-humidity/airconditioner', methods=['GET'])
def read_airconditioner_record():
    with db_manager.session_scope() as session:
        try:
            # 取最新 10 条记录（按 id 倒序）
            records = session.query(AirConditioner) \
                .order_by(AirConditioner.id.desc()) \
                .limit(20) \
                .all()
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")
    return ApiResponse.success(data=records)

@clock_bp.route('/temperature-humidity/airconditioner', methods=['POST'])
def insert_airconditioner_record(params):
    location = get_param('location', None, type_=str)
    temperature = get_param('temperature', None, type_=int)
    model = get_param('model', None, type_=int)
    description = get_param('description', None, type_=str)

    if location and temperature and model:
        new_item = AirConditioner(location=location, temperature=temperature, model=model, description=description)
        with db_manager.session_scope() as session:
            try:
                session.add(new_item)
                session.commit()
                return ApiResponse.success(data=new_item.to_dict(), message="successfully")
            except Exception as e:
                return ApiResponse.error(message=f"数据库错误: {e}")
    else:
        raise ValidationException(message="action参数没有传", error_code=ErrorCodes.MISSING_PARAMETER)

@clock_bp.route('/control/screen', methods=['POST'])
def pi_control_screen_action():
    state = get_param('state', None, type_=str)
    if state == 'on' or state == '开' or state == 'turnOn' or state == '打开' or state == '1':
        pass
        # state = ScreenControl.turn_screen_on()
    elif state == 'off' or state == '关' or state == '关闭' or state == 'turnOff' or state == '0':
        pass
        # state = ScreenControl.turn_screen_off()
    if state:
        return ApiResponse.success(data= {"result": True}, message="successfully")
    else:
        result = {"result": state}
        return ApiResponse.error(message=f"Screen operate {result}")

@clock_bp.route('/control/screen', methods=['GET'])
def pi_control_screen_state():
    # state = ScreenControl.current_screen_state()
    state_result = {"state": True}
    return ApiResponse.success(data= {"result": state_result}, message="successfully")


@clock_bp.route('/temperature-humidity/homepod', methods=['POST'])
def insert_home_pod_record():
    temp = get_param('temp', None, type_=float)
    humidity = get_param('humidity', None, type_=float)

    if temp and humidity:
        raise ValidationException(message="参数没有传", error_code=ErrorCodes.MISSING_PARAMETER)

    record = HomePod(temperature=temp,humidity=humidity)

    with db_manager.session_scope() as session:
        try:
            session.add(record)
            session.commit()
            return ApiResponse.success(data=record.to_dict(), message="successfully")
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")

@clock_bp.route('/temperature-humidity/homepod', methods=['GET'])
def read_home_pod_records():
    with db_manager.session_scope() as session:
        try:
            # 取最新 10 条记录（按 id 倒序）
            records = session.query(HomePod) \
                .order_by(HomePod.id.desc()) \
                .limit(20) \
                .all()
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")
    return ApiResponse.success(data=records)

# 获取温湿度
@clock_bp.route('/temperature-humidity', methods=['POST', 'GET'])
def read_temp_humidity():
    with db_manager.session_scope() as session:
        try:
            # 取最新 10 条记录（按 id 倒序）
            records = session.query(HomeClimate) \
                .order_by(HomeClimate.id.desc()) \
                .limit(1) \
                .all()
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")
    return ApiResponse.success(data=records)

@clock_bp.route('/temperature-humidity/history', methods=['POST', 'GET'])
def read_temp_humidity_history():
    try:
        result = read_home_climate_last_records_with_minutes(480)
        return ApiResponse.success(data=result)
    except Exception as e:
        return ApiResponse.error(message=f"数据库错误: {e}")

@clock_bp.route('/home_climate/history', methods=['POST', 'GET'])
def reads_home_climate_records_period():
    start_date = get_param('startDate', None, type_=str)
    end_date = get_param('endDate', None, type_=str)
    if start_date and end_date:
        result = read_home_climate_records_with_period(start_date, end_date)
        return ApiResponse.success(data=result)
    else:
        return ApiResponse.error(message=f"数据库错误")

@clock_bp.route('/fridge/history', methods=['POST', 'GET'])
def read_fridge_records():
    start_date = get_param('startDate', None, type_=str)
    end_date = get_param('endDate', None, type_=str)

    if start_date and end_date:
        result = read_home_fridge_records_with_period(start_date, end_date)
        return ApiResponse.success(data=result)
    else:
        return ApiResponse.error(message=f"数据库错误")
#
# @clock_bp.route('/surroundings/record', methods=['POST'])
# def insert_SurroundingRecord():
#     params = getRequestParamters(request)
#     result_dic = {}
#     if params is not None:
#         if 'record' in params:
#             record_para = params['record']
#             print(f"insertASurroundingRecord record_para: {record_para}")
#             result_dic = insertARecord(record_para)
#         else:
#             result_dic = {'message': 'A record must have a record parameter'}
#     response = response_manager.json_response(result_dic)
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     return response