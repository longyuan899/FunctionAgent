# -*- coding: utf-8 -*-
"""数据库操作工具 — 自然语言转SQL"""
import logging
import re
from typing import Optional
from app.tools.base import BaseTool, ToolParameter, registry

logger = logging.getLogger(__name__)

# 示例数据库元数据
_DB_SCHEMA = """
表: employees（员工表）
- id: INTEGER PRIMARY KEY
- name: TEXT 姓名
- department: TEXT 部门
- position: TEXT 职位
- salary: REAL 薪资
- hire_date: TEXT 入职日期

表: orders（订单表）
- id: INTEGER PRIMARY KEY
- customer_name: TEXT 客户姓名
- product: TEXT 产品名称
- amount: REAL 订单金额
- status: TEXT 订单状态 (pending/paid/shipped/completed/cancelled)
- order_date: TEXT 下单日期

表: products（产品表）
- id: INTEGER PRIMARY KEY
- name: TEXT 产品名称
- category: TEXT 分类
- price: REAL 价格
- stock: INTEGER 库存
"""


class NLToSQLTool(BaseTool):
    """自然语言转 SQL 查询（演示模式）"""
    name = "db_query"
    description = "将自然语言问题转换为 SQL 查询并执行（仅支持员工/订单/产品表）"
    category = "database"
    parameters = [
        ToolParameter(name="nl_question", type="string",
                      description="用户的自然语言问题，如：有多少员工？工资最高的是谁？", required=True),
    ]

    def execute(self, nl_question, **kwargs) -> dict:
        q = nl_question.lower().strip()
        sql, answer = self._translate(q)
        return {
            "success": True,
            "nl_question": nl_question,
            "generated_sql": sql,
            "answer": answer,
            "note": "（演示模式，接入真实数据库需配置连接）",
        }

    def _translate(self, q: str) -> tuple:
        # 规则化 NL→SQL 映射
        if "多少" in q or "总数" in q or "数量" in q:
            if "员工" in q:
                return ("SELECT COUNT(*) FROM employees",
                        "公司共有 128 名员工")
            if "订单" in q or "单" in q:
                return ("SELECT COUNT(*) FROM orders",
                        "共有 3,456 条订单记录")
            if "产品" in q:
                return ("SELECT COUNT(*) FROM products",
                        "产品目录共收录 892 个SKU")

        if "最高" in q or "最多" in q or "最大" in q:
            if "工资" in q or "薪资" in q or "salary" in q:
                return ("SELECT name, MAX(salary) FROM employees",
                        "薪资最高的是技术部的张工，月薪 45,800 元")
            if "订单" in q or "金额" in q:
                return ("SELECT customer_name, MAX(amount) FROM orders",
                        "订单金额最高的是阿里巴巴，金额 128 万元")

        if "部门" in q and ("平均" in q or "平均工资" in q):
            return ("SELECT department, AVG(salary) FROM employees GROUP BY department",
                    "各部门平均薪资：技术部 ¥28,500 / 产品部 ¥22,300 / 销售部 ¥18,600")

        if "最近" in q or "最新" in q or "最近" in q:
            if "订单" in q:
                return ("SELECT * FROM orders ORDER BY order_date DESC LIMIT 10",
                        "最近10笔订单：TS20260415001（¥12,800）等")

        if "待处理" in q or "pending" in q or "未完成" in q:
            return ("SELECT * FROM orders WHERE status='pending'",
                    "待处理订单共 47 笔，总金额 ¥1,230,000")

        if "库存" in q:
            return ("SELECT name, stock FROM products WHERE stock < 100 ORDER BY stock",
                    "库存不足100件的产品：鼠标(82件)、键盘(65件)、耳机(41件)")

        if "产品" in q and ("最贵" in q or "价格高" in q):
            return ("SELECT name, MAX(price) FROM products",
                    "最贵的产品是 MacBook Pro 16寸，价格 ¥29,999")

        return ("-- 无法解析，请尝试更具体的问题",
                "我理解了你的问题，但数据库中可能没有对应数据，请换个问法试试")


class DBExplainTool(BaseTool):
    """数据库结构说明"""
    name = "db_schema"
    description = "查询数据库表结构说明"
    category = "database"
    parameters = [
        ToolParameter(name="table_name", type="string",
                      description="表名：employees / orders / products", required=True),
    ]

    def execute(self, table_name, **kwargs) -> dict:
        schemas = {
            "employees": {
                "name": "员工表",
                "rows": 128,
                "columns": [
                    {"name": "id", "type": "INTEGER", "desc": "主键"},
                    {"name": "name", "type": "TEXT", "desc": "姓名"},
                    {"name": "department", "type": "TEXT", "desc": "部门"},
                    {"name": "position", "type": "TEXT", "desc": "职位"},
                    {"name": "salary", "type": "REAL", "desc": "月薪"},
                    {"name": "hire_date", "type": "TEXT", "desc": "入职日期"},
                ]
            },
            "orders": {
                "name": "订单表",
                "rows": 3456,
                "columns": [
                    {"name": "id", "type": "INTEGER", "desc": "主键"},
                    {"name": "customer_name", "type": "TEXT", "desc": "客户姓名"},
                    {"name": "product", "type": "TEXT", "desc": "产品名称"},
                    {"name": "amount", "type": "REAL", "desc": "订单金额"},
                    {"name": "status", "type": "TEXT", "desc": "状态"},
                    {"name": "order_date", "type": "TEXT", "desc": "下单日期"},
                ]
            },
            "products": {
                "name": "产品表",
                "rows": 892,
                "columns": [
                    {"name": "id", "type": "INTEGER", "desc": "主键"},
                    {"name": "name", "type": "TEXT", "desc": "产品名称"},
                    {"name": "category", "type": "TEXT", "desc": "分类"},
                    {"name": "price", "type": "REAL", "desc": "价格"},
                    {"name": "stock", "type": "INTEGER", "desc": "库存数量"},
                ]
            },
        }
        table = schemas.get(table_name.lower())
        if not table:
            return {"success": False, "error": f"表 {table_name} 不存在，可选: employees / orders / products"}
        return {"success": True, **table}


registry.register(NLToSQLTool())
registry.register(DBExplainTool())
