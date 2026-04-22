-- ============================================
-- 数据库迁移脚本 - 兑换记录表结构调整
-- 日期: 2026-04-22
-- 说明: 移除审批相关字段，添加剩余余额字段
-- ============================================

-- 1. 删除状态索引
DROP INDEX IF EXISTS idx_redemption_status;

-- 2. 删除 approved_by 字段
ALTER TABLE redemption_records DROP COLUMN IF EXISTS approved_by;

-- 3. 删除 status 字段
ALTER TABLE redemption_records DROP COLUMN IF EXISTS status;

-- 4. 删除 updated_at 字段
ALTER TABLE redemption_records DROP COLUMN IF EXISTS updated_at;

-- 5. 添加 remaining_balance 字段
ALTER TABLE redemption_records 
ADD COLUMN remaining_balance INTEGER NOT NULL DEFAULT 0 
CHECK (remaining_balance >= 0);

-- 6. 更新已有记录的 remaining_balance
-- 注意：这里需要根据实际业务逻辑来填充历史数据
-- 以下是一个示例，假设从 coin_transactions 表中获取
UPDATE redemption_records rr
SET remaining_balance = COALESCE(
    (SELECT ct.balance_after 
     FROM coin_transactions ct 
     WHERE ct.related_reward_item_id = rr.reward_item_id 
       AND ct.child_id = rr.child_id 
       AND ct.type = 'redeem'
       AND ct.created_at >= rr.created_at
     ORDER BY ct.created_at ASC
     LIMIT 1),
    0
);

-- 7. 添加注释
COMMENT ON COLUMN redemption_records.remaining_balance IS '兑换后剩余奖励币余额';
