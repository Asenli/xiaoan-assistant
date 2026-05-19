"""Simplified diagnostic - compare ChromaDB vectors vs fresh embeddings."""
import asyncio, sys, numpy as np
sys.path.insert(0, '.')
from app.services.embedding_service import embed_text, embed_texts, get_collection

async def main():
    col = get_collection()
    count = col.count()
    print(f"Vectors: {count}")

    data = col.get(include=["embeddings", "documents", "metadatas"])

    for i in range(len(data["ids"])):
        sv = np.array(data["embeddings"][i])
        print(f"\n[{i}] {data['metadatas'][i].get('filename','?')}")
        print(f"  Storage norm: {np.linalg.norm(sv):.4f}")

        # Fresh embedding
        fv = np.array((await embed_texts([data["documents"][i]]))[0])
        print(f"  Fresh norm: {np.linalg.norm(fv):.4f}")

        diff = np.linalg.norm(sv - fv)
        cos = float(np.dot(sv, fv) / (np.linalg.norm(sv) * np.linalg.norm(fv)))
        print(f"  L2 diff: {diff:.6f}, Cos: {cos:.4f}")

        if cos > 0.99:
            print(f"  VECTORS MATCH - same model")
        else:
            print(f"  VECTORS DIFFER - different model!")

    # Query test
    q = "商品模块优化了哪些内容"
    qv = np.array(await embed_text(q))
    print(f"\nQuery norm: {np.linalg.norm(qv):.4f}")

    for i in range(len(data["ids"])):
        dbv = np.array(data["embeddings"][i])
        cs1 = float(np.dot(qv, dbv) / (np.linalg.norm(qv) * np.linalg.norm(dbv)))
        print(f"  Query vs Storage[{i}]: {cs1:.4f}")

        fv = np.array((await embed_texts([data["documents"][i]]))[0])
        cs2 = float(np.dot(qv, fv) / (np.linalg.norm(qv) * np.linalg.norm(fv)))
        print(f"  Query vs Fresh[{i}]:  {cs2:.4f} (TRUE similarity)")

    print("\nDONE")
    # Write results to file
    with open("debug_result.txt", "w") as f:
        f.write("Results written above\n")
    print("Written to debug_result.txt")

if __name__ == "__main__":
    asyncio.run(main())
