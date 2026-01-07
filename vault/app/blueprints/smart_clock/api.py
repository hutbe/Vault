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
from .home_db_helper import (read_home_climate_last_records_with_minutes,
                             read_home_climate_records_with_period, read_home_fridge_records_with_period, read_home_climate_records)

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

# @clock_bp.route('/initialized_db', methods=['POST'])
# def initialized_db():
#     init_db()
#     add_image_types()
#     return ApiResponse.success("All Done!")

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
    # with db_manager.session_scope() as session:
    #     try:
    #         # 取最新 1 条记录（按 id 倒序）
    #         records = session.query(HomeClimate) \
    #             .order_by(HomeClimate.id.desc()) \
    #             .limit(1) \
    #             .all()
    #     except Exception as e:
    #         return ApiResponse.error(message=f"数据库错误: {e}")
    # # 将 HomeClimate 对象列表转换为字典列表
    # data = [record.to_dict() for record in records]
    # return ApiResponse.success(data=data)
    with db_manager.session_scope() as session:
        try:
            # 取最新 1 条记录（按 id 倒序）
            record = session.query(HomeClimate) \
                .order_by(HomeClimate.id.desc()) \
                .first()
            if record:
                return ApiResponse.success(data=record.to_dict())
            else:
                return ApiResponse.success(data={})
        except Exception as e:
            return ApiResponse.error(message=f"数据库错误: {e}")


@clock_bp.route('/temperature-humidity/history', methods=['POST', 'GET'])
def read_temp_humidity_history():
    try:
        result = read_home_climate_last_records_with_minutes(1440)
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

@clock_bp.route('/home_climate/record', methods=['POST'])
def insert_home_climate_record():
    record = get_param('record', None, type_=list)
    if record:
        # 定义字段名列表（与SQL语句顺序一致）
        # field_names = [
        #     'location', 'temperature', 'humidity', 'cup_temp', 'cpu_used_rate',
        #     'sys_uptime', 'sys_runtime', 'weather', 'weather_code', 'weather_des',
        #     'weather_icon', 'outdoors_temp', 'outdoors_feels_like', 'outdoors_temp_min',
        #     'outdoors_temp_max', 'outdoors_pressure', 'outdoors_humidity'
        # ]
        with db_manager.session_scope() as session:
            try:
                # 定义字段名列表
                home_climate = HomeClimate(
                    location=record[0],
                    temperature=record[1],
                    humidity=record[2],
                    cup_temp=record[3],
                    cpu_used_rate=record[4],
                    sys_uptime=record[5],
                    sys_runtime=record[6],
                    weather=record[7],
                    weather_code=record[8],
                    weather_des=record[9],
                    weather_icon=record[10],
                    outdoors_temp=record[11],
                    outdoors_feels_like=record[12],
                    outdoors_temp_min=record[13],
                    outdoors_temp_max=record[14],
                    outdoors_pressure=record[15],
                    outdoors_humidity=record[16]
                    # create_date 有默认值，不需要手动设置
                )
                session.add(home_climate)
                # session_scope上下文管理器会自动提交
                return ApiResponse.success(data={}, message="successfully")
            except Exception as e:
                return ApiResponse.error(message=f"数据库错误: {e}")
    return ApiResponse.error(message=f"参数错误")

@clock_bp.route('/home_climate/records', methods=['GET'])
def get_home_climate_records():
    start_date = get_param('start_date', None, type_=str)
    end_date = get_param('end_date', None, type_=str)
    timezone = get_param('timezone', "Asia/Shanghai", type_=str)
    if start_date and end_date:
        try:
            result = read_home_climate_records(start_date, end_date, timezone)
            return ApiResponse.success(data=result)
        except ValueError as e:
            return ApiResponse.error(message=f"{e}")
        except IndexError as e:
            return ApiResponse.error(message=f"{e}")
        except Exception as e:
            print(f"其他异常: {e}")
    else:
        return ApiResponse.error(message=f"参数错误")