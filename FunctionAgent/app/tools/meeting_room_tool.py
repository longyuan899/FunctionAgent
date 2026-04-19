# -*- coding: utf-8 -*-
"""会议室预约工具"""
import logging
from datetime import datetime
from app.tools.base import BaseTool, ToolParameter, registry

logger = logging.getLogger(__name__)

_ROOMS = [
    {"id": "room_001", "name": "3楼A会议室", "capacity": 10, "floor": 3,
     "equipment": ["投影仪", "白板", "视频会议"], "status": "available"},
    {"id": "room_002", "name": "3楼B会议室", "capacity": 20, "floor": 3,
     "equipment": ["投影仪", "白板", "音响"], "status": "available"},
    {"id": "room_003", "name": "5楼大会客厅", "capacity": 50, "floor": 5,
     "equipment": ["投影仪", "音响", "视频会议", "直播设备"], "status": "available"},
    {"id": "room_004", "name": "5楼小会议室", "capacity": 6, "floor": 5,
     "equipment": ["白板", "显示屏"], "status": "available"},
    {"id": "room_005", "name": "7楼多功能厅", "capacity": 100, "floor": 7,
     "equipment": ["投影仪", "音响", "视频会议", "舞台灯光"], "status": "available"},
]

_BOOKINGS = [
    {"id": "bk_001", "room_id": "room_001", "title": "产品评审",
     "date": "2026-04-20", "start": "09:00", "end": "10:00", "booker": "张三"},
    {"id": "bk_002", "room_id": "room_003", "title": "客户接待",
     "date": "2026-04-22", "start": "10:00", "end": "12:00", "booker": "李四"},
]


class RoomSearchTool(BaseTool):
    name = "room_search"
    description = "查询可用会议室，支持日期/时间/人数/设备筛选"
    category = "meeting_room"
    parameters = [
        ToolParameter(name="date", type="string", description="日期 YYYY-MM-DD", required=True),
        ToolParameter(name="start_time", type="string", description="开始时间 HH:MM", default="09:00"),
        ToolParameter(name="end_time", type="string", description="结束时间 HH:MM", default="10:00"),
        ToolParameter(name="min_capacity", type="integer", description="最少容纳人数", default=1),
        ToolParameter(name="equipment", type="string", description="所需设备，逗号分隔，如: 投影仪,白板", default=""),
    ]

    def execute(self, date, start_time="09:00", end_time="10:00",
                min_capacity=1, equipment="", **kwargs) -> dict:
        try:
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return {"success": False, "error": "时间格式错误"}

        # 已预订的房间
        booked = set()
        for bk in _BOOKINGS:
            if bk["date"] != date:
                continue
            try:
                bs = datetime.strptime(f"{date} {bk['start']}", "%Y-%m-%d %H:%M")
                be = datetime.strptime(f"{date} {bk['end']}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if start_dt < be and end_dt > bs:
                booked.add(bk["room_id"])

        needed = [e.strip() for e in equipment.split(",") if e.strip()]
        available = []
        for room in _ROOMS:
            if room["id"] in booked:
                continue
            if room["capacity"] < min_capacity:
                continue
            if needed and not all(eq in room["equipment"] for eq in needed):
                continue
            slots = [f"{bk['start']}-{bk['end']}" for bk in _BOOKINGS
                     if bk["room_id"] == room["id"] and bk["date"] == date]
            available.append({**room, "booked_slots": slots})

        return {
            "success": True, "date": date,
            "time_range": f"{start_time} ~ {end_time}",
            "available_rooms": available,
        }


class RoomBookTool(BaseTool):
    name = "room_book"
    description = "预定指定会议室"
    category = "meeting_room"
    parameters = [
        ToolParameter(name="room_id", type="string", description="会议室ID", required=True),
        ToolParameter(name="date", type="string", description="日期 YYYY-MM-DD", required=True),
        ToolParameter(name="start_time", type="string", description="开始时间 HH:MM", required=True),
        ToolParameter(name="end_time", type="string", description="结束时间 HH:MM", required=True),
        ToolParameter(name="title", type="string", description="会议主题", required=True),
        ToolParameter(name="booker", type="string", description="预订人姓名", required=True),
    ]

    def execute(self, room_id, date, start_time, end_time, title, booker, **kwargs) -> dict:
        try:
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return {"success": False, "error": "时间格式错误"}
        if end_dt <= start_dt:
            return {"success": False, "error": "结束时间必须晚于开始时间"}

        room = next((r for r in _ROOMS if r["id"] == room_id), None)
        if not room:
            return {"success": False, "error": f"会议室不存在: {room_id}"}

        for bk in _BOOKINGS:
            if bk["room_id"] != room_id or bk["date"] != date:
                continue
            try:
                bs = datetime.strptime(f"{date} {bk['start']}", "%Y-%m-%d %H:%M")
                be = datetime.strptime(f"{date} {bk['end']}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if start_dt < be and end_dt > bs:
                return {"success": False,
                        "error": f"时间冲突：{bk['title']}（{bk['booker']}）已预订 {bk['start']}-{bk['end']}"}

        new_bk = {"id": f"bk_{len(_BOOKINGS)+1:03d}", "room_id": room_id,
                  "room_name": room["name"], "title": title,
                  "date": date, "start": start_time, "end": end_time, "booker": booker}
        _BOOKINGS.append(new_bk)
        return {
            "success": True, "booking": new_bk,
            "message": f"会议室 {room['name']} 预约成功！",
        }


registry.register(RoomSearchTool())
registry.register(RoomBookTool())
