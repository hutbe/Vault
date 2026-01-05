import urllib.request
import json
from urllib.parse import urlencode
from datetime import datetime


class WeatherAPI:
    """天气API请求类"""

    def __init__(self, api_key):
        """初始化API密钥"""
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def _request(self, endpoint, params):
        """
        通用请求方法
        : param endpoint: API端点 (如 'weather', 'forecast')
        :param params: 请求参数字典
        :return: JSON数据或None
        """
        current_datetime = datetime.now()
        formatted_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        try:
            # 添加API密钥到参数
            params['appid'] = self.api_key

            # 构建完整URL
            url = f"{self.base_url}/{endpoint}?{urlencode(params)}"

            # 发送请求
            response = urllib.request.urlopen(url, timeout=120)

            # 读取并解析JSON
            data = response.read()
            result = json.loads(data)

            return result

        except urllib.error.HTTPError as e:
            print(f"{formatted_string}-HTTP错误: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"{formatted_string}-网络错误: {e.reason}")
            return None
        except json.JSONDecodeError:
            print("{formatted_string}-JSON解析失败")
            return None
        except Exception as e:
            print(f"{formatted_string}-请求失败: {e}")
            return None

    def get_current_weather(self, lat, lon, lang='zh', units='metric'):
        """
        获取当前天气
        :param lat: 纬度
        :param lon: 经度
        :param lang:  语言
        :param units:  计量单位
        :return: 天气数据
        """
        params = {
            'lat': lat,
            'lon': lon,
            'lang': lang,
            'units': units
        }
        return self._request('weather', params)

    def get_forecast(self, lat, lon, cnt=40, lang='zh', units='metric'):
        """
        获取天气预报
        :param lat:  纬度
        :param lon: 经度
        :param cnt: 预报数量
        :param lang: 语言
        :param units:  计量单位
        :return: 预报数据
        """
        params = {
            'lat': lat,
            'lon': lon,
            'cnt': cnt,
            'lang': lang,
            'units': units
        }
        return self._request('forecast', params)


# 使用示例
if __name__ == "__main__":
    # 从配置或环境变量读取API密钥
    API_KEY = "your_api_key_here"  # 替换为你的真实密钥

    # 创建API实例
    weather_api = WeatherAPI(API_KEY)

    # 深圳坐标
    latitude = 22.63404
    longitude = 113.81842

    # 获取当前天气
    print("正在获取当前天气...")
    current = weather_api.get_current_weather(latitude, longitude)
    if current:
        print(json.dumps(current, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60 + "\n")

    # 获取天气预报
    print("正在获取天气预报...")
    forecast = weather_api.get_forecast(latitude, longitude, cnt=40)
    if forecast:
        print(json.dumps(forecast, indent=2, ensure_ascii=False))