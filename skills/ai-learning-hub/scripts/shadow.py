import os
import sys
import json
import sqlite3
import subprocess
from datetime import datetime

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(SKILL_DIR, "assets", "config.json")
DB_PATH = os.path.join(SKILL_DIR, "assets", "shadow.db")

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # 建立源文档元数据表 (记录更新时间)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS docs_meta (
            doc_token TEXT PRIMARY KEY,
            updated_at TEXT
        )
    ''')
    # 建立FTS5全文检索引擎存储片段
    cur.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_chunks USING fts5(
            doc_token,
            chunk_text,
            chunk_id UNINDEXED
        )
    ''')
    conn.commit()
    return conn

def sync_doc(doc_token):
    # 1. 获取在线文档元数据 (假设依赖 lark-cli 的结果或为简化我们直接 fetch)
    # 为减少依赖，MVP 直接调用 lark-cli 获取内容，不校验时间戳，直接全量覆写
    # 实际应用中可以先调用 API 获取最后更新时间戳。这里我们用简化的覆盖逻辑。
    print(f"[*] Shadow Syncing: 拉取云端文档 {doc_token}...")
    try:
        result = subprocess.run(
            ["lark-cli", "docs", "+fetch", "--doc", doc_token, "--as", "user"],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"[!] 拉取失败: {e.stderr}")
        return

    try:
        data = json.loads(result.stdout)
        markdown = data.get("data", {}).get("markdown", "")
    except Exception:
        markdown = result.stdout # 退化为原始输出
        
    # 切片逻辑 (按段落或标题简单切分，MVP 采用双空行切分)
    chunks = [c.strip() for c in markdown.split("\n\n") if len(c.strip()) > 30]
    
    conn = ensure_db()
    cur = conn.cursor()
    
    # 清理旧数据
    cur.execute("DELETE FROM docs_chunks WHERE doc_token=?", (doc_token,))
    
    for i, chunk in enumerate(chunks):
        cur.execute("INSERT INTO docs_chunks(doc_token, chunk_id, chunk_text) VALUES(?,?,?)", 
                    (doc_token, i, chunk))
        
    cur.execute("INSERT OR REPLACE INTO docs_meta (doc_token, updated_at) VALUES (?, ?)", 
                (doc_token, datetime.now().isoformat()))
    conn.commit()
    print(f"[+] 影子入库完成: 文档切分为 {len(chunks)} 个碎片以供极速检索。")

def search(query):
    conn = ensure_db()
    cur = conn.cursor()
    # 基于 FTS5 进行相似度查询 (MATCH)
    # SQLite fts5 tokenizer 默认按空格切分，MVP 支持关键字
    words = " OR ".join(query.split())
    try:
        cur.execute("""
            SELECT doc_token, chunk_text 
            FROM docs_chunks 
            WHERE chunk_text MATCH ? 
            ORDER BY rank LIMIT 3
        """, (words,))
        rows = cur.fetchall()
        if not rows:
            print("未能找到极度相似的书签。")
        for idx, r in enumerate(rows):
            print(f"\n--- 匹配碎片 [{idx+1}] (源文档: {r[0]}) ---")
            print(r[1])
    except sqlite3.OperationalError:
        print(f"[!] 检索语法不支持: {words}，请使用简单的词组合。")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: shadow.py <sync|search> <doc_token|query>")
        sys.exit(1)
        
    action = sys.argv[1]
    arg = sys.argv[2]
    
    if action == "sync":
        sync_doc(arg)
    elif action == "search":
        search(arg)
    else:
        print("Unknown action")
