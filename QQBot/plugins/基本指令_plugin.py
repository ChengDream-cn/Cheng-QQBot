import logging

def on_load():
    logging.info("基本指令插件已加载")

def on_unload():
    logging.info("基本指令插件已卸载")

def handle_command(content, **kwargs):
    help_msg = """🤖 机器人帮助菜单 📚
    
▫️ 基础功能
/帮助 - 显示本帮助信息
/运行状态 - 查看系统资源使用情况
/获取ID - 获取当前会话ID

▫️ 统计功能
/群聊统计 - 查看群组变动记录
/单聊统计 - 查看好友变动记录
/群聊总数 - 查看群聊总数统计
/用户总数 - 查看好友用户数量
/服务统计 - 查看服务运行状态

▫️ 管理功能
/重启 - 重启机器人服务
/更新 - 检查系统更新"""

    if content == '/帮助':
        return help_msg
        
    if content == '/获取ID':
        ids = []
        if kwargs.get('group_openid'):
            ids.append(f"群组ID: {kwargs['group_openid']}")
        if kwargs.get('member_openid'):
            ids.append(f"成员ID: {kwargs['member_openid']}")
        if kwargs.get('user_openid'):
            ids.append(f"用户ID: {kwargs['user_openid']}")
        return "\n".join(ids) if ids else "未获取到ID信息"
