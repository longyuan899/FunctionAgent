# -*- coding: utf-8 -*-
"""搜索与信息查询工具"""
import logging
import random
from app.tools.base import BaseTool, ToolParameter, registry

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "搜索互联网信息，返回标题/URL/摘要"
    category = "search"
    parameters = [
        ToolParameter(name="query", type="string", description="搜索关键词", required=True),
        ToolParameter(name="num_results", type="integer", description="返回结果数量", default=5),
    ]

    def execute(self, query, num_results=5, **kwargs) -> dict:
        # 生产环境接入 SERP API / DuckDuckGo
        results = [
            {"rank": 1, "title": f"{query} - 相关结果 1", "url": "https://example.com/1",
             "snippet": f"关于「{query}」的第一条搜索结果摘要"},
            {"rank": 2, "title": f"{query} - 相关结果 2", "url": "https://example.com/2",
             "snippet": f"关于「{query}」的第二条搜索结果摘要"},
            {"rank": 3, "title": f"{query} - 相关结果 3", "url": "https://example.com/3",
             "snippet": f"关于「{query}」的第三条搜索结果摘要"},
        ]
        return {"success": True, "query": query, "results": results[:num_results]}


class WeatherQueryTool(BaseTool):
    name = "weather_query"
    description = "查询城市天气预报"
    category = "search"
    parameters = [
        ToolParameter(name="city", type="string", description="城市名称", required=True),
        ToolParameter(name="days", type="integer", description="预报天数 1-7", default=1),
    ]

    def execute(self, city, days=1, **kwargs) -> dict:
        conditions = ["晴", "多云", "阴", "小雨", "晴转多云"]
        data = []
        for i in range(min(days, 7)):
            data.append({
                "date": f"第{i+1}天",
                "weather": random.choice(conditions),
                "temp_high": random.randint(18, 32),
                "temp_low": random.randint(10, 22),
                "humidity": f"{random.randint(40, 90)}%",
                "wind": random.choice(["东南风3级", "北风2级", "西风4级", "无持续风向"]),
            })
        return {
            "success": True, "city": city,
            "forecast": data,
            "note": "（演示数据，接入真实天气 API 后返回真实预报）",
        }


class UnitConvertTool(BaseTool):
    name = "unit_convert"
    description = "单位换算工具"
    category = "search"
    parameters = [
        ToolParameter(name="value", type="number", description="数值", required=True),
        ToolParameter(name="from_unit", type="string", description="源单位: km/m/cm/kg/g/°C/°F", required=True),
        ToolParameter(name="to_unit", type="string", description="目标单位", required=True),
    ]

    def execute(self, value, from_unit, to_unit, **kwargs) -> dict:
        conversions = {
            ("km", "m"): value * 1000,
            ("m", "km"): value / 1000,
            ("cm", "m"): value / 100,
            ("m", "cm"): value * 100,
            ("kg", "g"): value * 1000,
            ("g", "kg"): value / 1000,
            ("°C", "°F"): value * 9 / 5 + 32,
            ("°F", "°C"): (value - 32) * 5 / 9,
            ("km", "km"): value,
            ("m", "m"): value,
            ("kg", "kg"): value,
        }
        key = (from_unit.strip().lower(), to_unit.strip().lower())
        # 精确匹配
        result = conversions.get(key)
        if result is None:
            # 模糊匹配
            for (f, t), v in conversions.items():
                if from_unit.lower() in f and to_unit.lower() in t:
                    result = v
                    break
        if result is None:
            return {"success": False, "error": f"不支持 {from_unit} → {to_unit} 的换算"}
        return {"success": True, "input": f"{value} {from_unit}",
                "output": f"{round(result, 6)} {to_unit}", "result": result}


registry.register(WebSearchTool())
registry.register(WeatherQueryTool())
registry.register(UnitConvertTool())
