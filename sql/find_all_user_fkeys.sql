-- 找出所有引用 auth.users 的外鍵約束
-- 用於診斷為什麼無法刪除用戶

SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    tc.constraint_name,
    rc.update_rule,
    rc.delete_rule,
    CASE
        WHEN rc.delete_rule NOT IN ('CASCADE', 'SET NULL') THEN '⚠️ 會阻止刪除'
        ELSE '✅ 不會阻止刪除'
    END as status
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
    AND tc.table_schema = rc.constraint_schema
JOIN information_schema.constraint_column_usage ccu
    ON rc.unique_constraint_name = ccu.constraint_name
    AND rc.unique_constraint_schema = ccu.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND ccu.table_schema = 'auth'
    AND ccu.table_name = 'users'
ORDER BY
    CASE WHEN rc.delete_rule NOT IN ('CASCADE', 'SET NULL') THEN 0 ELSE 1 END,
    tc.table_name;
