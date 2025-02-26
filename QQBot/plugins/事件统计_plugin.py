# plugins/事件统计_plugin.py
import logging
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from threading import Lock

logger = logging.getLogger("EventStats")

class EventStatistics:
    """事件统计核心类，提供完整的事件记录和查询功能"""
    
    def __init__(self):
        self.lock = Lock()
        self.conn = self._create_connection()
        self._init_db()

    def _create_connection(self) -> sqlite3.Connection:
        """创建并配置数据库连接"""
        conn = sqlite3.connect(
            'event_stats.db',
            check_same_thread=False,
            timeout=15,
            isolation_level=None  # 自动提交模式
        )
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -10000")  # 10MB缓存
        return conn

    def _init_db(self):
        """初始化数据库表结构"""
        with self.conn:
            # 群组事件表（包含当前状态标记）
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    group_id TEXT PRIMARY KEY,
                    last_action TEXT CHECK(last_action IN ('加入', '退出')),
                    operator_id TEXT,
                    timestamp DATETIME NOT NULL
                )
            ''')

            # 好友事件表（包含当前状态标记）
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS friends (
                    user_id TEXT PRIMARY KEY,
                    last_action TEXT CHECK(last_action IN ('添加', '删除')),
                    timestamp DATETIME NOT NULL
                )
            ''')

            # 创建优化索引
            self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_groups_time 
                ON groups(timestamp DESC)
            ''')
            self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_friends_time 
                ON friends(timestamp DESC)
            ''')

    def _parse_page_param(self, param: str) -> int:
        """解析分页参数"""
        try:
            page = max(1, int(param))
            return page
        except ValueError:
            raise ValueError("无效的页码参数")

    def record_group_event(self, action: str, group_id: str, operator: str):
        """记录群组事件"""
        with self.lock:
            self.conn.execute('''
                INSERT INTO groups 
                (group_id, last_action, operator_id, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(group_id) DO UPDATE SET
                    last_action = excluded.last_action,
                    operator_id = excluded.operator_id,
                    timestamp = excluded.timestamp
            ''', (group_id, action, operator, datetime.now().isoformat()))

    def record_friend_event(self, action: str, user_id: str):
        """记录好友事件"""
        with self.lock:
            self.conn.execute('''
                INSERT INTO friends 
                (user_id, last_action, timestamp)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_action = excluded.last_action,
                    timestamp = excluded.timestamp
            ''', (user_id, action, datetime.now().isoformat()))

    def get_groups(self, page: int = 1, per_page: int = 10) -> Tuple[int, List[Tuple[str, str]]]:
        """获取当前群组分页数据"""
        try:
            offset = (page - 1) * per_page
            
            # 获取有效群组总数（最后动作为加入的群组）
            total = self.conn.execute('''
                SELECT COUNT(*) FROM groups 
                WHERE last_action = '加入'
            ''').fetchone()[0]

            # 获取分页数据（按最后活跃时间倒序）
            data = self.conn.execute('''
                SELECT group_id, timestamp 
                FROM groups 
                WHERE last_action = '加入'
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (per_page, offset)).fetchall()

            return total, data
        except sqlite3.Error as e:
            logger.error(f"群组查询失败: {str(e)}")
            return 0, []

    def get_friends(self, page: int = 1, per_page: int = 10) -> Tuple[int, List[Tuple[str, str]]]:
        """获取当前好友分页数据"""
        try:
            offset = (page - 1) * per_page
            
            # 获取有效好友总数（最后动作为添加的好友）
            total = self.conn.execute('''
                SELECT COUNT(*) FROM friends 
                WHERE last_action = '添加'
            ''').fetchone()[0]

            # 获取分页数据（按最后活跃时间倒序）
            data = self.conn.execute('''
                SELECT user_id, timestamp 
                FROM friends 
                WHERE last_action = '添加'
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (per_page, offset)).fetchall()

            return total, data
        except sqlite3.Error as e:
            logger.error(f"好友查询失败: {str(e)}")
            return 0, []

    def get_group_stats(self) -> Dict[str, Any]:
        """获取群组统计概览"""
        try:
            total_joined = self.conn.execute('''
                SELECT COUNT(*) FROM groups 
                WHERE last_action = '加入'
            ''').fetchone()[0]

            total_left = self.conn.execute('''
                SELECT COUNT(*) FROM groups 
                WHERE last_action = '退出'
            ''').fetchone()[0]

            return {
                "total_joined": total_joined,
                "total_left": total_left,
                "current_count": total_joined - total_left
            }
        except sqlite3.Error as e:
            logger.error(f"群组统计失败: {str(e)}")
            return {}

    def get_friend_stats(self) -> Dict[str, Any]:
        """获取好友统计概览"""
        try:
            total_added = self.conn.execute('''
                SELECT COUNT(*) FROM friends 
                WHERE last_action = '添加'
            ''').fetchone()[0]

            total_removed = self.conn.execute('''
                SELECT COUNT(*) FROM friends 
                WHERE last_action = '删除'
            ''').fetchone()[0]

            return {
                "total_added": total_added,
                "total_removed": total_removed,
                "current_count": total_added - total_removed
            }
        except sqlite3.Error as e:
            logger.error(f"好友统计失败: {str(e)}")
            return {}

stats = EventStatistics()

def on_load():
    """插件加载初始化"""
    try:
        logger.info("事件统计插件已加载")
        # 预热缓存
        stats.get_group_stats()
        stats.get_friend_stats()
    except Exception as e:
        logger.error(f"插件初始化失败: {str(e)}")

def on_unload():
    """插件卸载处理"""
    try:
        stats.conn.close()
        logger.info("数据库连接已安全关闭")
    except Exception as e:
        logger.error(f"关闭连接时出错: {str(e)}")

def handle_command(content: str, **kwargs) -> Optional[str]:
    """处理所有统计命令"""
    try:
        parts = content.strip().split()
        if not parts:
            return None

        command = parts[0].lower()
        page = 1

        # 解析分页参数
        if len(parts) > 1:
            try:
                page = max(1, int(parts[1]))
            except ValueError:
                return "⚠️ 页码必须是大于0的整数"

        # 群聊总数分页查询
        if command == '/群聊总数':
            total, data = stats.get_groups(page=page)
            if total == 0:
                return "当前没有加入任何群聊"
            
            total_pages = (total + 9) // 10  # 每页10条
            page = min(page, total_pages)
            
            response = [
                f"📌 当前群聊总数: {total}",
                f"📖 第 {page}/{total_pages} 页（每页显示10个）",
                "最近活跃群组ID："
            ]
            response.extend([f"{idx+1}. {group[0]} ({group[1][:10]})" 
                           for idx, group in enumerate(data)])
            return "\n".join(response)

        # 用户总数分页查询
        elif command == '/用户总数':
            total, data = stats.get_friends(page=page)
            if total == 0:
                return "当前没有好友"
            
            total_pages = (total + 9) // 10
            page = min(page, total_pages)
            
            response = [
                f"📌 当前好友总数: {total}",
                f"📖 第 {page}/{total_pages} 页（每页显示10个）",
                "最近添加好友ID："
            ]
            response.extend([f"{idx+1}. {user[0]} ({user[1][:10]})" 
                           for idx, user in enumerate(data)])
            return "\n".join(response)

        # 群聊统计概览
        elif command == '/群聊统计':
            data = stats.get_group_stats()
            return (
                "👥 群聊统计概览\n"
                f"▫️ 历史加入总数: {data['total_joined']}\n"
                f"▫️ 历史退出总数: {data['total_left']}\n"
                f"▫️ 当前群聊数量: {data['current_count']}"
            )

        # 好友统计概览
        elif command == '/单聊统计':
            data = stats.get_friend_stats()
            return (
                "💬 好友统计概览\n"
                f"▫️ 历史添加总数: {data['total_added']}\n"
                f"▫️ 历史删除总数: {data['total_removed']}\n"
                f"▫️ 当前好友数量: {data['current_count']}"
            )

    except Exception as e:
        logger.error(f"命令处理失败: {str(e)}", exc_info=True)
    return None

def handle_event(event_type: str, event_data: dict):
    """处理所有事件"""
    try:
        # 群组事件处理
        if event_type in ('GROUP_ADD_ROBOT', 'GROUP_DEL_ROBOT'):
            action = '加入' if 'ADD' in event_type else '退出'
            stats.record_group_event(
                action=action,
                group_id=event_data.get('group_openid'),
                operator=event_data.get('op_member_openid', '未知')
            )

        # 好友事件处理
        elif event_type in ('FRIEND_ADD', 'FRIEND_DEL'):
            action = '添加' if 'ADD' in event_type else '删除'
            stats.record_friend_event(
                action=action,
                user_id=event_data.get('openid')
            )

    except Exception as e:
        logger.error(f"事件处理失败: {str(e)}", exc_info=True)
