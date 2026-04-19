# -*- coding: utf-8 -*-
"""日历管理工具"""
import logging
from datetime import datetime, timedelta
from app.tools.base import BaseTool, ToolParameter, registry

logger = logging.getLogger(__name__)

# 内存日历存储
_EVENTS = [
    {"id": "evt_001", "title": "周一团队例会", "start": "2026-04-20 09:00",
     "end": "2026-04-20 10:00", "location": "3楼会议室A", "attendees": ["张三", "李四", "王五"]},
    {"id": "evt_002", "title": "产品需求评审", "start": "2026-04-21 14:00",
     "end": "2026-04-21 16:00", "location": "5楼大会议室", "attendees": ["产品部", "研发部"]},
    {"id": "evt_003", "title": "客户方案汇报", "start": "2026-04-22 10:00",
     "end": "2026-04-22 11:30", "location": "腾讯会议", "attendees": ["销售部"]},
]


class CalendarQueryTool(BaseTool):
    name = "calendar_query"
    description = "查询日程安排，支持按日期范围和关键词筛选"
    category = "calendar"
    parameters = [
        ToolParameter(name="start_date", type="string", description="开始日期 YYYY-MM-DD，不填默认今天", default=""),
        ToolParameter(name="end_date", type="string", description="结束日期 YYYY-MM-DD，不填默认往后7天", default=""),
        ToolParameter(name="keyword", type="string", description="关键词（标题/地点）筛选", default=""),
    ]

    def execute(self, start_date="", end_date="", keyword="", **kwargs) -> dict:
        if not start_date:
            start_dt = datetime.now().replace(hour=0, minute=0, second=0)
        else:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": f"日期格式错误: {start_date}"}

        if not end_date:
            end_dt = start_dt + timedelta(days=7)
        else:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            except ValueError:
                return {"success": False, "error": f"日期格式错误: {end_date}"}

        results = []
        for evt in _EVENTS:
            try:
                evt_start = datetime.strptime(evt["start"], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if not (start_dt <= evt_start < end_dt):
                continue
            if keyword and keyword not in evt["title"] and keyword not in evt.get("location", ""):
                continue
            results.append(evt)

        return {
            "success": True, "count": len(results), "events": results,
            "range": f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}",
        }


class CalendarCreateTool(BaseTool):
    name = "calendar_create"
    description = "创建新的日程事件"
    category = "calendar"
    parameters = [
        ToolParameter(name="title", type="string", description="事件标题", required=True),
        ToolParameter(name="start", type="string", description="开始时间 YYYY-MM-DD HH:MM", required=True),
        ToolParameter(name="end", type="string", description="结束时间 YYYY-MM-DD HH:MM", required=True),
        ToolParameter(name="location", type="string", description="地点", default=""),
        ToolParameter(name="attendees", type="string", description="参与者，逗号分隔", default=""),
    ]

    def execute(self, title, start, end, location="", attendees="", **kwargs) -> dict:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
        except ValueError:
            return {"success": False, "error": "时间格式错误，请用 YYYY-MM-DD HH:MM"}
        if end_dt <= start_dt:
            return {"success": False, "error": "结束时间必须晚于开始时间"}

        # 检查冲突
        conflicts = []
        for evt in _EVENTS:
            try:
                es = datetime.strptime(evt["start"], "%Y-%m-%d %H:%M")
                ee = datetime.strptime(evt["end"], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if start_dt < ee and end_dt > es:
                conflicts.append(evt)

        new_event = {
            "id": f"evt_{len(_EVENTS)+1:03d}", "title": title,
            "start": start, "end": end,
            "location": location,
            "attendees": [a.strip() for a in attendees.split(",") if a.strip()],
        }
        _EVENTS.append(new_event)
        result = {"success": True, "event": new_event}
        if conflicts:
            result["conflicts"] = conflicts
            result["warning"] = f"发现 {len(conflicts)} 个时间冲突"
        return result


class CalendarConflictTool(BaseTool):
    name = "calendar_check_conflict"
    description = "检查指定时间段是否有日程冲突"
    category = "calendar"
    parameters = [
        ToolParameter(name="start", type="string", description="开始时间 YYYY-MM-DD HH:MM", required=True),
        ToolParameter(name="end", type="string", description="结束时间 YYYY-MM-DD HH:MM", required=True),
    ]

    def execute(self, start, end, **kwargs) -> dict:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
        except ValueError:
            return {"success": False, "error": "时间格式错误"}
        conflicts = []
        for evt in _EVENTS:
            try:
                es = datetime.strptime(evt["start"], "%Y-%m-%d %H:%M")
                ee = datetime.strptime(evt["end"], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if start_dt < ee and end_dt > es:
                conflicts.append(evt)
        return {"success": True, "has_conflict": len(conflicts) > 0,
                "conflicts": conflicts, "period": f"{start} ~ {end}"}


registry.register(CalendarQueryTool())
registry.register(CalendarCreateTool())
registry.register(CalendarConflictTool())
