-- ============================================
-- 儿童表现记录系统 - 数据库 Schema
-- PostgreSQL 15+
-- ============================================

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. 用户表 (家长)
-- ============================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(50) UNIQUE NOT NULL,
    phone           VARCHAR(20) UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    nickname        VARCHAR(50),
    avatar_url      VARCHAR(500),
    wechat_openid   VARCHAR(100) UNIQUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_wechat_openid ON users(wechat_openid);

COMMENT ON TABLE users IS '用户表（家长账户）';
COMMENT ON COLUMN users.username IS '用户名，唯一';
COMMENT ON COLUMN users.phone IS '手机号码，唯一';
COMMENT ON COLUMN users.password_hash IS '密码哈希值';
COMMENT ON COLUMN users.nickname IS '昵称';
COMMENT ON COLUMN users.avatar_url IS '头像地址';
COMMENT ON COLUMN users.wechat_openid IS '微信 OpenID，用于小程序登录';

-- ============================================
-- 2. 儿童信息表
-- ============================================
CREATE TABLE children (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(50) NOT NULL,
    gender          VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    birthday        DATE,
    avatar_url      VARCHAR(500),
    coin_balance    INTEGER NOT NULL DEFAULT 0 CHECK (coin_balance >= 0),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_children_user_id ON children(user_id);

COMMENT ON TABLE children IS '儿童信息表';
COMMENT ON COLUMN children.user_id IS '所属家长用户 ID';
COMMENT ON COLUMN children.name IS '儿童姓名';
COMMENT ON COLUMN children.gender IS '性别：male/female/other';
COMMENT ON COLUMN children.birthday IS '出生日期';
COMMENT ON COLUMN children.coin_balance IS '当前奖励币余额';

-- ============================================
-- 3. 每日表现记录表
-- ============================================
CREATE TABLE performance_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id        UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    record_date     DATE NOT NULL,
    overall_rating  VARCHAR(10) NOT NULL CHECK (overall_rating IN ('good', 'bad')),
    comment         TEXT,
    coins_earned    INTEGER NOT NULL DEFAULT 0 CHECK (coins_earned >= 0),
    coins_deducted  INTEGER NOT NULL DEFAULT 0 CHECK (coins_deducted >= 0),
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_id, record_date)
);

CREATE INDEX idx_performance_child_id ON performance_records(child_id);
CREATE INDEX idx_performance_record_date ON performance_records(record_date);
CREATE INDEX idx_performance_child_date ON performance_records(child_id, record_date);

COMMENT ON TABLE performance_records IS '每日表现记录表';
COMMENT ON COLUMN performance_records.child_id IS '关联儿童 ID';
COMMENT ON COLUMN performance_records.record_date IS '记录日期（每个儿童每天仅一条）';
COMMENT ON COLUMN performance_records.overall_rating IS '总体评价：good（好）/ bad（差）';
COMMENT ON COLUMN performance_records.comment IS '家长评语';
COMMENT ON COLUMN performance_records.coins_earned IS '当日获得奖励币数';
COMMENT ON COLUMN performance_records.coins_deducted IS '当日扣除奖励币数';
COMMENT ON COLUMN performance_records.created_by IS '记录创建者（家长 ID）';

-- ============================================
-- 4. 奖惩明细记录表
-- ============================================
CREATE TABLE reward_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    performance_id  UUID NOT NULL REFERENCES performance_records(id) ON DELETE CASCADE,
    type            VARCHAR(10) NOT NULL CHECK (type IN ('reward', 'punishment')),
    description     TEXT NOT NULL,
    coins           INTEGER NOT NULL CHECK (coins > 0),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reward_records_performance_id ON reward_records(performance_id);

COMMENT ON TABLE reward_records IS '奖惩明细记录（关联每日表现）';
COMMENT ON COLUMN reward_records.type IS '类型：reward（奖励）/ punishment（惩罚）';
COMMENT ON COLUMN reward_records.description IS '奖惩描述';
COMMENT ON COLUMN reward_records.coins IS '涉及奖励币数量（正数）';

-- ============================================
-- 5. 奖励商城商品表
-- ============================================
CREATE TABLE reward_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    coin_cost       INTEGER NOT NULL CHECK (coin_cost > 0),
    icon            VARCHAR(100) DEFAULT '🎁',
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reward_items_user_id ON reward_items(user_id);

COMMENT ON TABLE reward_items IS '奖励商城商品配置表';
COMMENT ON COLUMN reward_items.user_id IS '所属家长用户 ID';
COMMENT ON COLUMN reward_items.name IS '奖励名称';
COMMENT ON COLUMN reward_items.coin_cost IS '所需奖励币数量';
COMMENT ON COLUMN reward_items.icon IS '图标标识';
COMMENT ON COLUMN reward_items.sort_order IS '排序权重';
COMMENT ON COLUMN reward_items.is_active IS '是否启用';

-- ============================================
-- 6. 奖励币交易流水表
-- ============================================
CREATE TABLE coin_transactions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id                UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    type                    VARCHAR(20) NOT NULL CHECK (type IN ('earn', 'deduct', 'redeem')),
    amount                  INTEGER NOT NULL,
    balance_after           INTEGER NOT NULL,
    description             TEXT,
    related_performance_id  UUID REFERENCES performance_records(id) ON DELETE SET NULL,
    related_reward_item_id  UUID REFERENCES reward_items(id) ON DELETE SET NULL,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coin_transactions_child_id ON coin_transactions(child_id);
CREATE INDEX idx_coin_transactions_type ON coin_transactions(type);
CREATE INDEX idx_coin_transactions_created_at ON coin_transactions(created_at);

COMMENT ON TABLE coin_transactions IS '奖励币交易流水表';
COMMENT ON COLUMN coin_transactions.type IS '交易类型：earn（获得）/ deduct（扣除）/ redeem（兑换）';
COMMENT ON COLUMN coin_transactions.amount IS '交易金额（正数为收入，负数为支出）';
COMMENT ON COLUMN coin_transactions.balance_after IS '交易后余额';

-- ============================================
-- 7. 兑换记录表
-- ============================================
CREATE TABLE redemption_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id        UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    reward_item_id  UUID NOT NULL REFERENCES reward_items(id),
    reward_name     VARCHAR(100) NOT NULL,
    coins_spent     INTEGER NOT NULL CHECK (coins_spent > 0),
    remaining_balance INTEGER NOT NULL DEFAULT 0 CHECK (remaining_balance >= 0),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_redemption_child_id ON redemption_records(child_id);

COMMENT ON TABLE redemption_records IS '兑换记录表';
COMMENT ON COLUMN redemption_records.reward_name IS '兑换时奖励名称快照';
COMMENT ON COLUMN redemption_records.coins_spent IS '消耗奖励币数量';
COMMENT ON COLUMN redemption_records.remaining_balance IS '兑换后剩余奖励币余额';

-- ============================================
-- 更新时间自动触发器
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_children_updated_at
    BEFORE UPDATE ON children
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_performance_records_updated_at
    BEFORE UPDATE ON performance_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reward_items_updated_at
    BEFORE UPDATE ON reward_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_redemption_records_updated_at
    BEFORE UPDATE ON redemption_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 初始化示例数据（可选）
-- ============================================
-- INSERT INTO users (username, phone, password_hash, nickname)
-- VALUES ('demo_parent', '13800138000', '$2b$12$...', '示例家长');
