"""RAG 检索增强生成服务 — 混合检索 + 意图识别 + 菜单推荐."""
import logging
import re
from app.config import settings
from app.services.embedding_service import embed_text, search_vectors, get_collection

logger = logging.getLogger(__name__)


async def detect_intent(query: str) -> tuple[str, float]:
    """
    意图识别 — 判断用户问题是哪种类型.
    返回: (intent_type, confidence)
    intent_type: menu_navigation / how_to / regulation / general_qa
    """
    query_lower = query.lower()

    menu_patterns = [
        r"(怎么|如何|在哪里|从哪|去哪).*(进|找|打开|访问|导航|前往|去到|使用|操作).*(菜单|页面|功能|模块|入口)",
        r"(需要|想要|我要|帮我).*(对账|结算|凭证|报表|查询|管理|设置|配置|导出|导入|审批|提交|审核)",
        r".*(系统|功能|模块).*(有哪些|在哪里|怎么用|怎么进)",
        r"(找不到|没找到|找一下).*(功能|菜单|页面|模块)",
        r"(财务管理|订单管理|采购管理|库存管理|报表管理|系统设置).*",
    ]

    howto_patterns = [
        r"(怎么|如何|怎样).*(操作|做|处理|创建|生成|配置|设置|上传|下载|导入|导出)",
        r"(操作步骤|操作流程|步骤|教程).*",
        r".*(流程|步骤).*(是什么|有哪些|怎么样)",
    ]

    regulation_patterns = [
        r"(食安|食品安全|卫生|监管|合规|法规|规定|标准|条例).*",
        r".*(规定|要求|标准|法规).*(是什么|有哪些|怎么样)",
        r"(GB|HACCP|ISO).*",
    ]

    for pattern in menu_patterns:
        if re.search(pattern, query):
            return "menu_navigation", 0.85

    for pattern in howto_patterns:
        if re.search(pattern, query):
            return "how_to", 0.85

    for pattern in regulation_patterns:
        if re.search(pattern, query):
            return "regulation", 0.85

    return "general_qa", 0.7


async def hybrid_retrieve(
    query: str,
    top_k: int | None = None,
    document_ids: list[str] | None = None,
    category: str | None = None,
) -> list[dict]:
    """混合检索 — 向量检索为主，可选结合 BM25 关键词检索."""
    if top_k is None:
        top_k = settings.retrieval_top_k

    # Check collection size
    collection = get_collection()
    total_vectors = collection.count()
    print(f"[RETRIEVE] 向量库总量: {total_vectors}, 查询: '{query[:60]}'")

    query_embedding = await embed_text(query)
    where_filter = None

    if document_ids:
        if len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        else:
            where_filter = {"$or": [{"document_id": did} for did in document_ids]}
    if category:
        cat_filter = {"category": category}
        where_filter = {"$and": [where_filter, cat_filter]} if where_filter else cat_filter

    results = search_vectors(query_embedding, n_results=top_k * 2, where=where_filter)

    raw_hits = len(results["ids"][0]) if results["ids"] and results["ids"][0] else 0
    print(f"[RETRIEVE] ChromaDB 返回: {raw_hits} 条")

    chunks = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            score = round(1 - results["distances"][0][i], 4)
            doc_name = results["metadatas"][0][i].get("filename", "?")[:50]
            print(f"[RETRIEVE]   [{i}] score={score:.4f} (阈值={settings.retrieval_score_threshold}) doc={doc_name}")
            if score < settings.retrieval_score_threshold:
                print(f"[RETRIEVE]   [{i}] => 低于阈值，丢弃")
                continue
            chunks.append({
                "content": results["documents"][0][i],
                "document_name": results["metadatas"][0][i].get("filename", ""),
                "document_id": results["metadatas"][0][i].get("document_id", ""),
                "category": results["metadatas"][0][i].get("category", ""),
                "tags": results["metadatas"][0][i].get("tags", ""),
                "score": score,
                "chunk_id": results["ids"][0][i],
            })

    print(f"[RETRIEVE] 最终结果: {len(chunks)} 条 (阈值: {settings.retrieval_score_threshold})")
    return chunks[:top_k]


async def build_rag_context(query: str, chunks: list[dict]) -> str:
    """构建 RAG 上下文 — 将检索到的文档片段格式化为 LLM 可用的上下文."""
    if not chunks:
        return ""

    context_parts = []
    for i, c in enumerate(chunks):
        context_parts.append(
            f"[文档片段 {i + 1}] 来源: {c['document_name']} | "
            f"分类: {c.get('category', '通用')} | 相关度: {c['score']:.1%}\n"
            f"内容: {c['content']}\n"
        )
    return "\n---\n".join(context_parts)


async def extract_action_steps(chunks: list[dict]) -> list[dict]:
    """从检索到的文档中提取操作步骤."""
    steps = []
    step_patterns = [
        r'(?:第[一二三四五六七八九十\d]+步[：:。\.])',
        r'(?:\d+[\.\、\)）])',
        r'(?:步骤\s*\d+)',
        r'(?:[①②③④⑤⑥⑦⑧⑨⑩])',
    ]

    for chunk in chunks:
        for pattern in step_patterns:
            matches = re.findall(f"{pattern}.+", chunk["content"])
            for match in matches:
                steps.append({"step": match.strip(), "source": chunk["document_name"]})

    return steps[:10]
