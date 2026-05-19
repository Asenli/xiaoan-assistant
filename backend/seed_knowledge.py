"""直接导入示例知识文档到向量库."""
import asyncio, sys, uuid, hashlib
sys.path.insert(0, '.')
from app.database import init_db, async_session
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.models.user import User
from sqlalchemy import select
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.embedding_service import embed_texts, add_vectors
from app.config import settings

DOCS = {
    "结算对账操作指南.txt": """结算对账操作指南

## 功能概述
结算对账模块用于处理订单金额汇总、供应商结算、对账差异处理等财务结算业务。
用户可以通过结算对账功能完成从订单核对到结算单生成的全流程操作。

## 操作步骤
第一步：登录系统后，在左侧导航菜单找到"财务管理"模块。
第二步：点击"结算对账"菜单进入结算对账页面，路由地址为 /#/orderReconciliation。
第三步：在结算对账页面选择需要结算的日期范围和供应商名称。
第四步：点击"生成结算单"按钮，系统会自动汇总所选时间范围内的订单金额。
第五步：仔细核对结算单中的订单明细、金额汇总、供应商信息是否正确。
第六步：如发现差异金额，需要先处理差异（联系相关人员确认），再点击"确认结算"。
第七步：确认无误后点击"确认结算"按钮，系统自动生成结算凭证。
第八步：结算完成后，可在凭证管理页面查看已生成的会计凭证。

## 常见问题
问：结算对账在哪里？
答：请导航到 财务管理 > 结算对账，路由地址为 /#/orderReconciliation。

问：如何生成结算单？
答：在结算对账页面选择日期和供应商后，点击"生成结算单"按钮即可。

问：结算发现差异怎么办？
答：先确认差异原因，联系相关业务人员核实，处理完差异后再进行结算。

## 注意事项
- 结算前请确认所有订单已完成对账。
- 如存在差异金额，需先处理差异再结算。
- 已结算的订单不可重复结算，请谨慎操作。
- 结算完成后系统会自动生成会计凭证，无需手动创建。
- 每月结算截止日期为当月最后一天。

## 凭证生成说明
凭证生成模块基于结算对账结果自动生成标准会计凭证。
支持凭证模板配置、批量生成、导出等功能。
操作路径：财务管理 > 凭证生成，路由地址为 /#/voucherGeneration。""",

    "食品安全法规要点.txt": """食品安全法规要点

## 《食品安全法》关键条款
1. 食品生产经营者应当依照法律、法规和食品安全标准从事生产经营活动，保证食品安全。
2. 食品生产经营者应当建立食品安全追溯体系，保证食品可追溯。
3. 食品经营者采购食品，应当查验供货者的许可证和食品合格证明文件。
4. 食品生产经营企业应当建立健全食品安全管理制度，对职工进行食品安全知识培训。
5. 食品生产经营者应当建立食品进货查验记录制度，如实记录食品的名称、规格、数量、生产日期等内容。

## 食品安全标准体系
- GB 2760 食品添加剂使用标准：规定了食品添加剂的使用原则、允许使用的品种、使用范围及最大使用量。
- GB 2762 食品中污染物限量：规定了食品中铅、镉、汞、砷等污染物的限量指标。
- GB 2763 食品中农药最大残留限量：规定了食品中各类农药的最大残留限量标准。
- GB 29921 食品中致病菌限量：规定了食品中沙门氏菌、金黄色葡萄球菌等致病菌的限量。

## 从业人员健康管理
- 食品从业人员每年应当进行健康检查，取得健康证明后方可上岗。
- 患有痢疾、伤寒、病毒性肝炎等消化道传染病的人员，不得从事接触直接入口食品的工作。

## 合规检查要点
- 食品经营许可证是否在有效期内。
- 从业人员健康证明是否齐全有效。
- 食品进货查验记录是否完整。
- 食品储存条件是否符合要求。
- 食品安全自查制度是否落实。""",
}

async def main():
    await init_db()
    async with async_session() as db:
        # 找到管理员
        result = await db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        if not admin:
            print("错误: 请先注册 admin 用户")
            return
        user_id = admin.id

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", ".", "！", "？", " ", ""],
        )

        for filename, content in DOCS.items():
            # 检查是否已存在
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.file_hash == file_hash)
            )
            if result.scalar_one_or_none():
                print(f"跳过 (已存在): {filename}")
                continue

            doc_id = str(uuid.uuid4())
            doc = KnowledgeDocument(
                id=doc_id, filename=filename, title=filename.replace(".txt", ""),
                category="knowledge", tags="操作指南,客服", file_hash=file_hash,
                file_path="", file_size=len(content), file_type="txt",
                version=1, is_public=True, status="processing", uploaded_by=user_id,
            )
            db.add(doc)
            await db.commit()

            chunks = splitter.split_text(content)
            chunks = [c for c in chunks if c.strip()]
            print(f"[{filename}] 提取 {len(content)} 字符, 分块 {len(chunks)} 个, Embedding...")

            embeddings = await embed_texts(chunks)
            chroma_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            metadatas = [
                {"document_id": doc_id, "filename": filename, "chunk_index": i,
                 "category": "knowledge", "tags": "操作指南", "user_id": user_id}
                for i in range(len(chunks))
            ]
            add_vectors(chroma_ids, chunks, embeddings, metadatas)

            for i, chunk_text in enumerate(chunks):
                db.add(DocumentChunk(
                    document_id=doc_id, chroma_id=chroma_ids[i],
                    chunk_index=i, content=chunk_text, token_count=len(chunk_text),
                ))

            doc.status = "ready"
            doc.chunk_count = len(chunks)
            await db.commit()
            print(f"[{filename}] 完成! 写入 {len(chunks)} 条向量")

        from app.services.embedding_service import get_collection
        print(f"\n向量库总量: {get_collection().count()} 条")

if __name__ == "__main__":
    asyncio.run(main())
