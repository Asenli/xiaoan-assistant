"""初始化种子数据 — 系统菜单 + 示例知识文档."""
import asyncio
from app.database import init_db, async_session
from app.models.user import User
from app.models.menu import SystemMenu
from app.core.security import hash_password

SAMPLE_MENUS = [
    {"name": "财务管理", "parent_id": None, "level": 0, "sort_order": 1,
     "route_path": "/#/finance", "icon": "💰", "description": "财务管理主模块",
     "business_desc": "包含结算对账、凭证生成、账单管理等财务相关功能",
     "keywords": "财务,结算,对账,凭证,账单,支付,收款"},
    {"name": "结算对账", "parent_id": None, "level": 1, "sort_order": 1,
     "route_path": "/#/orderReconciliation", "icon": "📋", "description": "订单结算与对账管理",
     "business_desc": "订单金额汇总、供应商结算、对账差异处理、结算单生成",
     "keywords": "结算对账,对账,结算单,订单结算,供应商结算,差异处理"},
    {"name": "凭证生成", "parent_id": None, "level": 1, "sort_order": 2,
     "route_path": "/#/voucherGeneration", "icon": "📝", "description": "财务凭证自动生成",
     "business_desc": "基于结算对账结果生成会计凭证，支持凭证模板配置、批量生成、导出",
     "keywords": "凭证生成,凭证,会计凭证,凭证模板,批量生成"},
    {"name": "账单管理", "parent_id": None, "level": 1, "sort_order": 3,
     "route_path": "/#/billManagement", "icon": "🧾", "description": "账单查询与管理",
     "business_desc": "账单列表查询、账单详情查看、账单导出、账单审核",
     "keywords": "账单管理,账单,账单查询,账单导出,账单审核"},

    {"name": "订单管理", "parent_id": None, "level": 0, "sort_order": 2,
     "route_path": "/#/order", "icon": "🛒", "description": "订单管理模块",
     "business_desc": "包含订单查询、订单审核、退单处理等订单相关功能",
     "keywords": "订单,查询,审核,退单,详情"},
    {"name": "订单查询", "parent_id": None, "level": 1, "sort_order": 1,
     "route_path": "/#/orderSearch", "icon": "🔍", "description": "多条件订单搜索查询",
     "business_desc": "按日期、状态、供应商、产品等多维度查询订单，支持导出",
     "keywords": "订单查询,搜索,订单列表,导出订单"},
    {"name": "退单处理", "parent_id": None, "level": 1, "sort_order": 2,
     "route_path": "/#/refundProcess", "icon": "↩️", "description": "退单审批与处理",
     "business_desc": "退单申请、审批流程、退款处理、退单记录查询",
     "keywords": "退单,退款,退单审批,退单处理"},

    {"name": "采购管理", "parent_id": None, "level": 0, "sort_order": 3,
     "route_path": "/#/purchase", "icon": "📦", "description": "采购管理模块",
     "business_desc": "包含采购订单、供应商管理、采购入库等采购相关功能",
     "keywords": "采购,供应商,入库,采购订单"},
    {"name": "供应商管理", "parent_id": None, "level": 1, "sort_order": 1,
     "route_path": "/#/supplierManagement", "icon": "🏭", "description": "供应商信息管理",
     "business_desc": "供应商注册、信息维护、资质审核、供应商评价",
     "keywords": "供应商,供应商管理,供应商信息,资质"},

    {"name": "食安管理", "parent_id": None, "level": 0, "sort_order": 4,
     "route_path": "/#/foodSafety", "icon": "🛡️", "description": "食品安全管理模块",
     "business_desc": "包含食安法规库、合规检查、风险预警、溯源管理等食品安全功能",
     "keywords": "食安,食品安全,法规,合规,溯源,风险"},
    {"name": "法规库", "parent_id": None, "level": 1, "sort_order": 1,
     "route_path": "/#/regulationLibrary", "icon": "📚", "description": "食品安全法规库",
     "business_desc": "收录国家及地方食品安全法规、标准、部门规章，支持全文检索",
     "keywords": "法规,食安法规,标准,GB,食品安全法,法规查询"},

    {"name": "系统设置", "parent_id": None, "level": 0, "sort_order": 99,
     "route_path": "/#/settings", "icon": "⚙️", "description": "系统配置与设置",
     "business_desc": "用户管理、角色权限、系统参数配置、操作日志",
     "keywords": "设置,系统设置,用户管理,权限,配置"},
]

SAMPLE_KNOWLEDGE = """# 结算对账操作指南

## 功能概述
结算对账模块用于处理订单金额汇总、供应商结算、对账差异处理等财务结算业务。

## 操作步骤
1. 登录系统后，在左侧导航菜单找到"财务管理"模块
2. 点击"结算对账"进入结算对账页面
3. 选择需要结算的日期范围和供应商
4. 点击"生成结算单"按钮，系统自动汇总订单金额
5. 核对结算单信息，确认无误后点击"确认结算"
6. 系统自动生成结算凭证，可在凭证管理页面查看

## 注意事项
- 结算前请确认所有订单已完成对账
- 如存在差异金额，需先处理差异再结算
- 已结算的订单不可重复结算

---

# 食品安全法规要点

## 《食品安全法》关键条款
1. 食品生产经营者应当依照法律、法规和食品安全标准从事生产经营活动
2. 建立食品安全追溯体系，保证食品可追溯
3. 食品经营者采购食品，应当查验供货者的许可证和食品合格证明文件

## 食品安全标准体系
- GB 2760 食品添加剂使用标准
- GB 2762 食品中污染物限量
- GB 2763 食品中农药最大残留限量
- GB 29921 食品中致病菌限量

## 合规要求
- 食品从业人员需持有效健康证明
- 建立食品进货查验记录制度
- 定期进行食品安全自查

---

# 凭证生成操作说明

## 功能介绍
凭证生成模块基于结算对账结果自动生成标准会计凭证。

## 操作流程
1. 确认结算单已审批通过
2. 进入"凭证生成"页面
3. 选择结算单号或日期范围
4. 系统自动匹配凭证模板
5. 预览生成的凭证信息
6. 确认无误后点击"生成凭证"
7. 凭证生成后可导出为PDF或Excel格式

## 凭证类型
- 采购入库凭证
- 销售出库凭证
- 结算付款凭证
- 费用报销凭证
"""


async def seed():
    await init_db()
    async with async_session() as db:
        # 创建默认管理员
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.username == "admin"))
        if not existing.scalar_one_or_none():
            user = User(username="admin", password_hash=hash_password("admin123"), role="admin")
            db.add(user)
            print("Created admin user: admin / admin123")

        # 导入菜单
        menu_count = 0
        for item in SAMPLE_MENUS:
            existing_menu = await db.execute(
                select(SystemMenu).where(SystemMenu.name == item["name"])
            )
            if not existing_menu.scalar_one_or_none():
                db.add(SystemMenu(**item))
                menu_count += 1

        await db.commit()
        print(f"Seeded {menu_count} new menus")
        print("Seed data created successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
