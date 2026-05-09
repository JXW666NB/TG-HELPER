import os
import json
import re
import threading
import time
import sqlite3
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

# ==================== 可选依赖（向量检索）====================
VECTOR_AVAILABLE = False
try:
    import chromadb
    from chromadb.utils import embedding_functions
    VECTOR_AVAILABLE = True
except ImportError:
    pass

class Memory:
    """
    三级记忆系统 + 混合检索 + 人格隔离
    """
    
    def __init__(self, mind_dir: str = "./mind", persona_name: str = "default", config: Optional[Dict] = None):
        self.mind_dir = Path(mind_dir)
        self.persona_name = persona_name
        self.persona_dir = self.mind_dir / persona_name
        self.persona_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件路径
        self.short_term_file = self.persona_dir / "短期记忆.txt"
        self.long_term_file = self.persona_dir / "长期记忆.txt"
        self.summary_file = self.persona_dir / "对话摘要.txt"
        self.core_memory_file = self.persona_dir / "MEMORY.md"
        self.config_file = self.persona_dir / "配置.json"
        self.db_path = self.persona_dir / "memory.db"
        
        # 确保文件存在
        for f in [self.short_term_file, self.long_term_file, self.summary_file, self.core_memory_file]:
            if not f.exists():
                f.touch()
        
        self.config = self._default_config()
        if config:
            self.config.update(config)
        self._load_config()
        
        # 初始化 SQLite 和 FTS5
        self._init_db()
        
        # 短期记忆缓冲区
        self._short_term_lines = []
        self._load_short_term_lines()
        
        # 后台反思线程
        self._reflection_thread = None
        self._stop_reflection = False
        self._reflection_interval = self.config.get("reflection_interval_seconds", 3600)
        
        # 向量检索（可选）
        self.vector_client = None
        self.vector_collection = None
        if VECTOR_AVAILABLE and self.config.get("enable_vector", False):
            self._init_vector_db()
        
        self._start_reflection()
        self.half_life_days = self.config.get("half_life_days", 7)
    
    def _default_config(self) -> Dict:
        return {
            # 短期记忆：高阈值，归档后保留最近30条
            "max_short_term_entries": 420,
            "archive_trigger": 420,
            "summarize_trigger": 420,
            "keep_short_term_after_archive": 30,
            # 检索参数
            "retrieve_limit": 10,
            "recent_entries_for_context": 10,
            "max_context_tokens": 8000,
            "fts_weight": 0.7,
            "vector_weight": 0.3,
            "relevance_threshold": 0.35,
            "time_decay_enabled": True,
            # 反思
            "reflection_interval_seconds": 3600,
            "reflection_batch_size": 5,
            # 向量开关
            "enable_vector": False,
            "half_life_days": 7,
        }
    
    def _init_db(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts 
            USING fts5(content, session_id, timestamp, role, metadata)
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS session_meta (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                message_count INTEGER,
                archived_at TEXT,
                reflected INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()
    
    def _init_vector_db(self):
        if not VECTOR_AVAILABLE:
            return
        try:
            vector_dir = self.persona_dir / "vector_db"
            vector_dir.mkdir(exist_ok=True)
            self.vector_client = chromadb.PersistentClient(path=str(vector_dir))
            embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction()
            self.vector_collection = self.vector_client.get_or_create_collection(
                name="tg_memory",
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"[Memory] 向量数据库已启用，已有 {self.vector_collection.count()} 条记录")
        except Exception as e:
            print(f"[Memory] 向量数据库初始化失败: {e}")
            self.vector_collection = None
    
    def _load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except:
                pass
        self._save_config()
    
    def _save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def _load_short_term_lines(self):
        if self.short_term_file.exists():
            with open(self.short_term_file, 'r', encoding='utf-8') as f:
                self._short_term_lines = f.readlines()
        else:
            self._short_term_lines = []
    
    def _save_short_term_lines(self):
        with open(self.short_term_file, 'w', encoding='utf-8') as f:
            f.writelines(self._short_term_lines)
    
    # ==================== 核心添加接口 ====================
    def add_short_term(self, role: str, content: str, metadata: Optional[Dict] = None):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[{timestamp}] {role}: {content}\n"
        self._short_term_lines.append(line)
        
        if len(self._short_term_lines) >= self.config["archive_trigger"]:
            self._archive_short_term()
        else:
            self._save_short_term_lines()
        
        if self.vector_collection:
            self._add_to_vector(f"{role}: {content}", {"role": role, "timestamp": timestamp})
    
    def _archive_short_term(self):
        """归档短期记忆：保留最近 keep_count 条，其余存入 SQLite"""
        keep_count = self.config.get("keep_short_term_after_archive", 30)
        if len(self._short_term_lines) <= keep_count:
            return
        to_archive = self._short_term_lines[:-keep_count]
        self._short_term_lines = self._short_term_lines[-keep_count:]
        
        if not to_archive:
            return
        
        session_id = hashlib.md5(f"{datetime.now()}{len(to_archive)}".encode()).hexdigest()[:16]
        start_time = None
        end_time = None
        messages = []
        
        for line in to_archive:
            match = re.match(r'\[(.*?)\] (.*?): (.*)', line)
            if match:
                ts_str, role, msg = match.groups()
                if start_time is None:
                    start_time = ts_str
                end_time = ts_str
                messages.append({"role": role, "content": msg, "timestamp": ts_str})
                self.conn.execute(
                    "INSERT INTO sessions_fts (content, session_id, timestamp, role, metadata) VALUES (?, ?, ?, ?, ?)",
                    (msg, session_id, ts_str, role, json.dumps({}))
                )
        if messages:
            self.conn.execute(
                "INSERT INTO session_meta (session_id, start_time, end_time, message_count, archived_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, start_time, end_time, len(messages), datetime.now().isoformat())
            )
            self.conn.commit()
            print(f"[Memory] 归档会话 {session_id}，包含 {len(messages)} 条消息，保留最近 {keep_count} 条短期记忆")
        
        self._save_short_term_lines()
    
    def _add_to_vector(self, text: str, metadata: Dict):
        if not self.vector_collection:
            return
        mem_id = hashlib.md5(f"{datetime.now()}{text}".encode()).hexdigest()
        try:
            self.vector_collection.add(
                ids=[mem_id],
                documents=[text],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"[Memory] 向量添加失败: {e}")
    
    def add_long_term(self, text: str, metadata: Optional[Dict] = None):
        with open(self.long_term_file, 'a', encoding='utf-8') as f:
            f.write(text.strip() + "\n")
        with open(self.core_memory_file, 'a', encoding='utf-8') as f:
            f.write(f"- {text.strip()}  (记录于 {datetime.now().strftime('%Y-%m-%d')})\n")
        session_id = "long_term_core"
        self.conn.execute(
            "INSERT INTO sessions_fts (content, session_id, timestamp, role, metadata) VALUES (?, ?, ?, ?, ?)",
            (text, session_id, datetime.now().isoformat(), "system", json.dumps(metadata or {}))
        )
        self.conn.commit()
        if self.vector_collection:
            self._add_to_vector(text, {"role": "system", "type": "long_term"})
    
    # ==================== 检索与上下文构建 ====================
    def get_context_for_llm(self, current_query: str = "", max_tokens: int = None) -> str:
        max_tokens = max_tokens or self.config.get("max_context_tokens", 8000)
        context_parts = []
        
        recent_count = self.config.get("recent_entries_for_context", 10)
        recent_lines = self._short_term_lines[-recent_count:] if self._short_term_lines else []
        if recent_lines:
            context_parts.append("【最近对话】\n" + "".join(recent_lines))
        
        if current_query:
            retrieved = self._hybrid_search(current_query)
            if retrieved:
                context_parts.append("【相关历史记忆】\n" + "\n".join(retrieved))
        
        if self.core_memory_file.exists():
            with open(self.core_memory_file, 'r', encoding='utf-8') as f:
                core_mem = f.read().strip()
            if core_mem:
                if len(core_mem) > 2000:
                    core_mem = core_mem[:2000] + "..."
                context_parts.append("【核心长期记忆】\n" + core_mem)
        
        summaries = self.get_summaries(max_count=3)
        if summaries:
            context_parts.append("【历史摘要】\n" + "".join(summaries))
        
        full_context = "\n\n".join(context_parts)
        estimated_tokens = len(full_context) // 4
        if estimated_tokens > max_tokens:
            full_context = full_context[:max_tokens * 4]
        return full_context
    
    def _hybrid_search(self, query: str) -> List[str]:
        limit = self.config["retrieve_limit"]
        fts_weight = self.config["fts_weight"]
        vector_weight = self.config["vector_weight"] if self.vector_collection else 1.0
        threshold = self.config["relevance_threshold"]
        
        fts_results = self._fts_search(query, limit * 2)
        vector_results = self._vector_search(query, limit * 2) if self.vector_collection else []
        
        merged = {}
        for doc, score in fts_results:
            merged[doc] = merged.get(doc, 0) + score * fts_weight
        for doc, score in vector_results:
            merged[doc] = merged.get(doc, 0) + score * vector_weight
        
        sorted_items = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        filtered = [(doc, score) for doc, score in sorted_items if score >= threshold]
        
        result_lines = []
        for doc, score in filtered[:limit]:
            result_lines.append(f"[置信度 {score:.2f}] {doc}")
        return result_lines
    
    def _fts_search(self, query: str, limit: int) -> List[Tuple[str, float]]:
        # 修复 FTS5 特殊字符错误：将查询作为短语查询（双引号包裹）
        # 对内部双引号进行转义
        escaped_query = query.replace('"', '""')
        phrase_query = f'"{escaped_query}"'
        try:
            cursor = self.conn.execute(
                "SELECT content, rank FROM sessions_fts WHERE sessions_fts MATCH ? ORDER BY rank LIMIT ?",
                (phrase_query, limit)
            )
            rows = cursor.fetchall()
            results = []
            for content, rank in rows:
                confidence = 1.0 / (1.0 + rank) if rank > 0 else 1.0
                if self.config["time_decay_enabled"]:
                    match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', content)
                    if match:
                        try:
                            ts = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                            days_ago = (datetime.now() - ts).total_seconds() / 86400.0
                            if days_ago > 0:
                                decay = 0.5 ** (days_ago / self.half_life_days)
                                confidence *= max(decay, 0.05)
                        except:
                            pass
                results.append((content, confidence))
            return results
        except Exception as e:
            print(f"[Memory] FTS 检索失败: {e}")
            # 降级：尝试移除特殊字符后重试一次
            try:
                clean_query = re.sub(r'[\[\]\(\)\-:<>]', ' ', query)
                escaped_clean = clean_query.replace('"', '""')
                phrase_clean = f'"{escaped_clean}"'
                cursor = self.conn.execute(
                    "SELECT content, rank FROM sessions_fts WHERE sessions_fts MATCH ? ORDER BY rank LIMIT ?",
                    (phrase_clean, limit)
                )
                rows = cursor.fetchall()
                results = []
                for content, rank in rows:
                    confidence = 1.0 / (1.0 + rank) if rank > 0 else 1.0
                    if self.config["time_decay_enabled"]:
                        match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', content)
                        if match:
                            try:
                                ts = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                                days_ago = (datetime.now() - ts).total_seconds() / 86400.0
                                if days_ago > 0:
                                    decay = 0.5 ** (days_ago / self.half_life_days)
                                    confidence *= max(decay, 0.05)
                            except:
                                pass
                    results.append((content, confidence))
                return results
            except Exception as e2:
                print(f"[Memory] FTS 降级检索也失败: {e2}")
                return []
    
    def _vector_search(self, query: str, limit: int) -> List[Tuple[str, float]]:
        if not self.vector_collection:
            return []
        try:
            results = self.vector_collection.query(
                query_texts=[query],
                n_results=limit
            )
            documents = results['documents'][0] if results['documents'] else []
            distances = results['distances'][0] if results['distances'] else []
            sims = [1.0 - d for d in distances]
            return list(zip(documents, sims))
        except Exception as e:
            print(f"[Memory] 向量检索失败: {e}")
            return []
    
    # ==================== 反思机制 ====================
    def _start_reflection(self):
        if self._reflection_thread and self._reflection_thread.is_alive():
            return
        self._stop_reflection = False
        self._reflection_thread = threading.Thread(target=self._reflection_loop, daemon=True)
        self._reflection_thread.start()
    
    def _reflection_loop(self):
        while not self._stop_reflection:
            time.sleep(self._reflection_interval)
            try:
                self._run_reflection()
            except Exception as e:
                print(f"[Memory] 反思过程出错: {e}")
    
    def _run_reflection(self):
        cursor = self.conn.execute(
            "SELECT session_id, start_time, message_count FROM session_meta WHERE reflected = 0 ORDER BY start_time DESC LIMIT ?",
            (self.config["reflection_batch_size"],)
        )
        sessions = cursor.fetchall()
        if not sessions:
            return
        
        for session_id, start_time, msg_count in sessions:
            cursor2 = self.conn.execute(
                "SELECT content, role, timestamp FROM sessions_fts WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            )
            messages = cursor2.fetchall()
            if not messages:
                continue
            dialog = "\n".join([f"{role}: {content}" for content, role, ts in messages])
            if hasattr(self, '_ai_reflection_callback') and self._ai_reflection_callback:
                summary = self._ai_reflection_callback(dialog)
                if summary:
                    with open(self.core_memory_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n## 反思于 {start_time}\n{summary}\n")
                    self.conn.execute("UPDATE session_meta SET reflected = 1 WHERE session_id = ?", (session_id,))
                    self.conn.commit()
                    print(f"[Memory] 反思完成，会话 {session_id} 已处理")
    
    def set_ai_reflection_callback(self, callback):
        self._ai_reflection_callback = callback
    
    # ==================== 旧接口兼容 ====================
    def get_short_term(self, days=None, max_entries=None):
        lines = self._short_term_lines.copy()
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for line in lines:
                if line.startswith('['):
                    try:
                        ts_str = line[1:20]
                        ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        if ts >= cutoff:
                            filtered.append(line)
                    except:
                        filtered.append(line)
                else:
                    filtered.append(line)
            lines = filtered
        if max_entries is not None and len(lines) > max_entries:
            lines = lines[-max_entries:]
        return ''.join(lines)
    
    def get_long_term(self):
        if self.long_term_file.exists():
            with open(self.long_term_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def query_long_term(self, query: str, n_results=5):
        content = self.get_long_term()
        lines = content.splitlines()
        keywords = set(query.lower().split())
        scored = []
        for line in lines:
            line_lower = line.lower()
            score = sum(1 for kw in keywords if kw in line_lower)
            if score > 0:
                scored.append((score, line))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [line for score, line in scored[:n_results]]
    
    def get_summaries(self, max_count=5):
        if self.summary_file.exists():
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return lines[-max_count:] if lines else []
        return []
    
    def clear_short_term(self):
        self._short_term_lines = []
        self._save_short_term_lines()
    
    def backup_short_term(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.persona_dir / f"短期记忆_{timestamp}.txt"
        shutil.copy2(str(self.short_term_file), str(backup_path))
        return str(backup_path)
    
    # ==================== 摘要回调兼容 ====================
    def set_ai_summarize_callback(self, callback):
        self._ai_summarize_callback = callback
    
    def _generate_summary(self, lines):
        if hasattr(self, '_ai_summarize_callback') and self._ai_summarize_callback:
            return self._ai_summarize_callback(lines)
        return None
    
    def _add_summary(self, summary):
        with open(self.summary_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {summary}\n")
    
    def _maybe_crop_and_summarize(self):
        # 新版使用归档机制，此方法保留以兼容旧调用
        pass
    
    def shutdown(self):
        self._stop_reflection = True
        if self._reflection_thread:
            self._reflection_thread.join(timeout=2)
        if hasattr(self, 'conn'):
            self.conn.close()
