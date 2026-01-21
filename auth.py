# auth.py - Supabase 認證整合
# TopicRadar 使用者認證模組

import os
from functools import wraps
from flask import request, jsonify, g
from supabase import create_client, Client

# Supabase 客戶端（延遲初始化）
_supabase_client: Client = None

def get_supabase() -> Client:
    """取得 Supabase 客戶端（單例模式）"""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL 和 SUPABASE_KEY 環境變數未設定")
        _supabase_client = create_client(url, key)
    return _supabase_client

def get_user_from_token(token: str):
    """從 JWT token 取得使用者資訊"""
    try:
        supabase = get_supabase()
        user = supabase.auth.get_user(token)
        return user.user if user else None
    except Exception as e:
        print(f"[AUTH] Token 驗證失敗: {e}")
        return None

def get_user_role(user_id: str) -> str:
    """取得使用者角色"""
    try:
        supabase = get_supabase()
        result = supabase.table('user_roles').select('role').eq('user_id', user_id).single().execute()
        return result.data.get('role', 'user') if result.data else 'user'
    except Exception:
        return 'user'

def is_admin(user_id: str) -> bool:
    """檢查使用者是否為管理員"""
    return get_user_role(user_id) == 'admin'

def require_auth(f):
    """
    需要登入的 API 裝飾器
    使用方式：
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user = g.user  # 當前使用者
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登入', 'code': 'UNAUTHORIZED'}), 401
        
        token = auth_header.replace('Bearer ', '')
        user = get_user_from_token(token)
        
        if not user:
            return jsonify({'error': '認證失敗', 'code': 'INVALID_TOKEN'}), 401
        
        # 將使用者資訊存到 Flask g 物件
        g.user = user
        g.user_id = user.id
        g.token = token
        g.is_admin = is_admin(user.id)
        
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    """
    需要管理員權限的 API 裝飾器
    使用方式：
        @app.route('/api/admin/users')
        @require_admin
        def admin_users():
            ...
    """
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if not g.is_admin:
            return jsonify({'error': '需要管理員權限', 'code': 'FORBIDDEN'}), 403
        return f(*args, **kwargs)
    return decorated

# ============ 認證相關函數 ============

def signup(email: str, password: str, invite_code: str):
    """
    使用者註冊（需要邀請碼）
    
    Returns:
        (user, error): 成功時 user 有值，失敗時 error 有值
    """
    supabase = get_supabase()
    
    # 驗證邀請碼
    try:
        # 查詢未使用的邀請碼（used_by 為 NULL）
        invite_result = supabase.table('invite_codes').select('*').eq('code', invite_code).execute()
        
        if not invite_result.data or len(invite_result.data) == 0:
            print(f"[AUTH] 邀請碼不存在: {invite_code}")
            return None, "邀請碼無效"
        
        invite = invite_result.data[0]
        invite_id = invite.get('id')

        # 檢查邀請碼使用次數
        max_uses = invite.get('max_uses')
        use_count = invite.get('use_count', 0)

        # 如果 max_uses 不是 NULL，檢查是否已達上限
        if max_uses is not None and use_count >= max_uses:
            print(f"[AUTH] 邀請碼已達使用上限: {invite_code} ({use_count}/{max_uses})")
            return None, f"邀請碼已達使用上限 ({use_count}/{max_uses})"

        # 檢查邀請碼是否過期
        if invite.get('expires_at'):
            from datetime import datetime, timezone
            expires_at = datetime.fromisoformat(invite['expires_at'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                print(f"[AUTH] 邀請碼已過期: {invite_code}")
                return None, "邀請碼已過期"
        
        print(f"[AUTH] 邀請碼有效: {invite_code}")
        
    except Exception as e:
        print(f"[AUTH] 驗證邀請碼時發生錯誤: {e}")
        return None, f"邀請碼驗證失敗: {str(e)}"
    
    # 註冊使用者
    try:
        result = supabase.auth.sign_up({
            'email': email,
            'password': password
        })
        
        if result.user:
            print(f"[AUTH] 使用者註冊成功: {email}, ID: {result.user.id}")

            # 增加邀請碼使用次數
            try:
                # 更新 use_count
                new_use_count = use_count + 1
                supabase.table('invite_codes').update({
                    'use_count': new_use_count
                }).eq('id', invite_id).execute()

                # 記錄使用詳情到 invite_code_uses
                try:
                    supabase.table('invite_code_uses').insert({
                        'invite_code_id': invite_id,
                        'user_id': result.user.id
                    }).execute()
                except Exception as e:
                    print(f"[AUTH] 記錄邀請碼使用詳情失敗（非致命）: {e}")

                print(f"[AUTH] 邀請碼使用次數更新: {invite_code} ({new_use_count}/{max_uses if max_uses else '無限'})")
            except Exception as e:
                print(f"[AUTH] 更新邀請碼使用次數失敗（非致命）: {e}")
            
            # 建立使用者角色（預設為一般使用者）- 使用 upsert 避免重複
            try:
                supabase.table('user_roles').upsert({
                    'user_id': result.user.id,
                    'role': 'user'
                }).execute()
                print(f"[AUTH] 使用者角色已建立: user")
            except Exception as e:
                print(f"[AUTH] 建立使用者角色失敗（非致命）: {e}")
            
            return result, None
        else:
            return None, "註冊失敗：未收到使用者資訊"
    except Exception as e:
        error_msg = str(e)
        print(f"[AUTH] 註冊失敗: {error_msg}")
        if 'already registered' in error_msg.lower():
            return None, "此 Email 已被註冊"
        if 'email' in error_msg.lower() and 'valid' in error_msg.lower():
            return None, "請輸入有效的 Email 地址"
        return None, f"註冊失敗: {error_msg}"

def login(email: str, password: str):
    """
    使用者登入
    
    Returns:
        (session, error): 成功時 session 有值，失敗時 error 有值
    """
    try:
        supabase = get_supabase()
        result = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        
        if result.session:
            return result, None
        else:
            return None, "登入失敗"
    except Exception as e:
        error_msg = str(e)
        print(f"[AUTH] 登入失敗: {error_msg}")

        # 檢查各種錯誤類型
        error_lower = error_msg.lower()

        if 'email not confirmed' in error_lower or 'not confirmed' in error_lower:
            return None, "Email 尚未確認，請先點擊確認信中的連結"

        if 'invalid' in error_lower or 'credentials' in error_lower:
            return None, "Email 或密碼錯誤"

        return None, f"登入失敗: {error_msg}"

def logout(token: str):
    """使用者登出"""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
        return True, None
    except Exception as e:
        return False, str(e)

# ============ 邀請碼管理 ============

def generate_invite_code(created_by: str, expires_days: int = 7):
    """
    生成邀請碼
    
    Args:
        created_by: 建立者的 user_id
        expires_days: 有效天數
    """
    import secrets
    import datetime
    
    code = secrets.token_urlsafe(8)[:12].upper()  # 12 位英數字
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=expires_days)
    
    try:
        supabase = get_supabase()
        result = supabase.table('invite_codes').insert({
            'code': code,
            'created_by': created_by,
            'expires_at': expires_at.isoformat()
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[AUTH] 建立邀請碼失敗: {e}")
        return None

def get_invite_codes():
    """取得所有邀請碼（管理員用）"""
    try:
        supabase = get_supabase()
        result = supabase.table('invite_codes').select('*').order('created_at', desc=True).execute()
        return result.data or []
    except Exception:
        return []

def delete_invite_code(code_id: str):
    """刪除邀請碼"""
    try:
        supabase = get_supabase()
        supabase.table('invite_codes').delete().eq('id', code_id).execute()
        return True
    except Exception:
        return False

# ============ 使用者管理 ============

def get_all_users():
    """取得所有使用者（管理員用）"""
    try:
        supabase = get_supabase()

        # 從 user_roles 取得使用者角色
        roles = supabase.table('user_roles').select('*').execute()

        # 從 user_topics 取得每個使用者的專題
        topics = supabase.table('user_topics').select('user_id, name').execute()

        # 整理每個使用者的專題列表
        user_topics_map = {}
        for t in (topics.data or []):
            uid = t['user_id']
            if uid not in user_topics_map:
                user_topics_map[uid] = []
            user_topics_map[uid].append(t['name'])

        users = []
        for role in (roles.data or []):
            uid = role['user_id']

            # 嘗試從 auth.users 取得更多資訊
            try:
                # 使用 service_role key 才能訪問 auth.users
                # 目前使用 anon key，可能無法直接訪問
                # 所以先使用基本資訊
                email = 'N/A'
                last_sign_in = None
            except:
                email = 'N/A'
                last_sign_in = None

            topic_list = user_topics_map.get(uid, [])

            users.append({
                'user_id': uid,
                'email': email,
                'role': role['role'],
                'topic_count': len(topic_list),
                'topics': topic_list,
                'created_at': role['created_at'],
                'last_sign_in_at': last_sign_in
            })

        return users
    except Exception as e:
        print(f"[AUTH] 取得使用者列表失敗: {e}")
        return []

def update_user_role(user_id: str, role: str):
    """更新使用者角色"""
    if role not in ['admin', 'user']:
        return False
    
    try:
        supabase = get_supabase()
        supabase.table('user_roles').upsert({
            'user_id': user_id,
            'role': role
        }).execute()
        return True
    except Exception:
        return False

# ============ 專題管理 ============

def get_user_topics(user_id: str):
    """取得使用者的專題"""
    try:
        supabase = get_supabase()
        result = supabase.table('user_topics').select('*').eq('user_id', user_id).order('created_at').execute()
        return result.data or []
    except Exception:
        return []

def get_all_topics_admin():
    """取得所有專題（管理員用）"""
    try:
        supabase = get_supabase()
        result = supabase.table('user_topics').select('*').order('created_at').execute()
        return result.data or []
    except Exception:
        return []

def create_topic(user_id: str, name: str, keywords: dict, icon: str = '📌', negative_keywords: list = None, order: int = 999):
    """建立專題"""
    try:
        supabase = get_supabase()
        result = supabase.table('user_topics').insert({
            'user_id': user_id,
            'name': name,
            'keywords': keywords,
            'icon': icon,
            'negative_keywords': negative_keywords or [],
            'order': order
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[AUTH] 建立專題失敗: {e}")
        return None

def update_topic(topic_id: str, user_id: str, updates: dict):
    """更新專題（驗證擁有者）"""
    try:
        supabase = get_supabase()
        # 先驗證擁有者
        existing = supabase.table('user_topics').select('user_id').eq('id', topic_id).single().execute()
        if not existing.data or existing.data['user_id'] != user_id:
            return False
        
        # 更新
        supabase.table('user_topics').update(updates).eq('id', topic_id).execute()
        return True
    except Exception:
        return False

def delete_topic(topic_id: str, user_id: str):
    """刪除專題（驗證擁有者）"""
    try:
        supabase = get_supabase()
        # 先驗證擁有者
        existing = supabase.table('user_topics').select('user_id').eq('id', topic_id).single().execute()
        if not existing.data or existing.data['user_id'] != user_id:
            return False
        
        supabase.table('user_topics').delete().eq('id', topic_id).execute()
        return True
    except Exception:
        return False

# ============ 快取管理 ============

def load_user_cache(user_id: str):
    """
    從 Supabase 載入使用者的專題快取
    回傳字典格式: {topic_id: {topics: [], international: [], summary: '', ...}}
    """
    try:
        supabase = get_supabase()
        result = supabase.table('topic_cache').select('*').eq('user_id', user_id).execute()
        
        cache_map = {}
        for row in result.data:
            tid = row['topic_id']
            cache_map[tid] = {
                'topics': row.get('domestic_news', []) or [],
                'international': row.get('intl_news', []) or [],
                'summary': {
                    'text': row.get('summary', '') or '',
                    'updated_at': row.get('summary_updated_at')
                }
            }
        return cache_map
    except Exception as e:
        print(f"[AUTH] 載入快取失敗: {e}")
        return {}

def save_topic_cache_item(user_id: str, topic_id: str, domestic_news: list, intl_news: list, summary_data: dict):
    """
    更新單一專題的快取到 Supabase (Upsert)
    """
    try:
        supabase = get_supabase()
        
        summary_text = summary_data.get('text', '')
        summary_updated_at = summary_data.get('updated_at')

        data = {
            'user_id': user_id,
            'topic_id': topic_id,
            'domestic_news': domestic_news,
            'intl_news': intl_news,
            'summary': summary_text,
            'summary_updated_at': summary_updated_at,
            'updated_at': 'now()'
        }
        supabase.table('topic_cache').upsert(data).execute()
        return True
    except Exception as e:
        print(f"[AUTH] 儲存快取失敗 ({topic_id}): {e}")
        return False

def delete_topic_cache(user_id: str, topic_id: str):
    """
    刪除專題快取
    """
    try:
        supabase = get_supabase()
        supabase.table('topic_cache').delete().eq('user_id', user_id).eq('topic_id', topic_id).execute()
        return True
    except Exception as e:
        print(f"[AUTH] 刪除快取失敗: {e}")
        return False
