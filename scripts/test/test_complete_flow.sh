#!/bin/bash
# TopicRadar 完整功能測試腳本

echo "========================================="
echo " TopicRadar 功能測試"
echo "========================================="
echo ""

# 測試1: 登入
echo "【測試 1】登入功能..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:5001/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@topicradar.com","password":"test123456"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ 登入失敗"
    echo "回應: $LOGIN_RESPONSE"
    exit 1
else
    echo "✅ 登入成功"
    echo "Token: ${TOKEN:0:50}..."
fi

echo ""

# 測試2: Token 驗證
echo "【測試 2】Token 驗證..."
AUTH_STATUS=$(curl -s "http://localhost:5001/api/auth/status" \
  -H "Authorization: Bearer $TOKEN")

IS_AUTH=$(echo $AUTH_STATUS | python3 -c "import sys, json; print(json.load(sys.stdin).get('authenticated', False))" 2>/dev/null)

echo "認證狀態: $AUTH_STATUS"
echo ""

# 測試3: 取得專題列表
echo "【測試 3】取得專題列表..."
TOPICS_RESPONSE=$(curl -s "http://localhost:5001/api/all" \
  -H "Authorization: Bearer $TOKEN")

TOPIC_COUNT=$(echo $TOPICS_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('topics', {})))" 2>/dev/null)

if [ -z "$TOPIC_COUNT" ]; then
    echo "❌ 取得專題失敗"
    echo "回應: $TOPICS_RESPONSE"
else
    echo "✅ 成功取得專題列表"
    echo "專題數量: $TOPIC_COUNT"
fi

echo ""

# 測試4: 建立專題
echo "【測試 4】建立測試專題..."
CREATE_RESPONSE=$(curl -s -X POST "http://localhost:5001/api/admin/topics" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試專題",
    "keywords": {"zh": ["測試", "驗證"], "en": ["test"], "ja": ["テスト"]},
    "icon": "🧪"
  }')

CREATE_STATUS=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('status', d.get('error', 'unknown')))" 2>/dev/null)

echo "建立結果: $CREATE_STATUS"
echo ""

# 測試5: 再次取得專題列表（應該有1個）
echo "【測試 5】確認專題已建立..."
TOPICS_RESPONSE2=$(curl -s "http://localhost:5001/api/all" \
  -H "Authorization: Bearer $TOKEN")

TOPIC_COUNT2=$(echo $TOPICS_RESPONSE2 | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('topics', {})))" 2>/dev/null)

echo "專題數量: $TOPIC_COUNT2"

if [ "$TOPIC_COUNT2" -gt "$TOPIC_COUNT" ]; then
    echo "✅ 專題建立成功"
else
    echo "⚠️  專題數量未增加"
fi

echo ""

# 測試6: 未登入存取測試
echo "【測試 6】未登入存取測試..."
UNAUTH_RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:5001/api/all" -o /dev/null)

if [ "$UNAUTH_RESPONSE" == "401" ]; then
    echo "✅ 未登入正確返回 401"
else
    echo "⚠️  未登入返回: $UNAUTH_RESPONSE（預期 401）"
fi

echo ""
echo "========================================="
echo " 測試完成"
echo "========================================="
