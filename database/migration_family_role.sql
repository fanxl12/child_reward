-- ============================================
-- 家庭与角色迁移
-- 兼容已有用户、儿童、奖励商品和奖励币流水
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户历史角色与当前家庭；新逻辑中的角色归属 family_members
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(10) NOT NULL DEFAULT '妈妈';
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_family_id UUID;

-- 家庭表
CREATE TABLE IF NOT EXISTS families (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(50) NOT NULL,
    code            VARCHAR(6) UNIQUE NOT NULL,
    owner_user_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_families_code ON families(code);
CREATE INDEX IF NOT EXISTS idx_families_owner_user_id ON families(owner_user_id);

-- 兼容开发环境由 SQLAlchemy create_all 创建过表但没有数据库默认 UUID 的情况
ALTER TABLE families ALTER COLUMN id SET DEFAULT uuid_generate_v4();

-- 家庭成员表
CREATE TABLE IF NOT EXISTS family_members (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id   UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_family_member UNIQUE(family_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_family_members_family_id ON family_members(family_id);
CREATE INDEX IF NOT EXISTS idx_family_members_user_id ON family_members(user_id);
ALTER TABLE family_members ALTER COLUMN id SET DEFAULT uuid_generate_v4();
ALTER TABLE family_members ADD COLUMN IF NOT EXISTS role VARCHAR(10) NOT NULL DEFAULT '妈妈';

-- 儿童和奖励商品补家庭字段，保留 user_id 作为历史创建人
ALTER TABLE children ADD COLUMN IF NOT EXISTS family_id UUID REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE reward_items ADD COLUMN IF NOT EXISTS family_id UUID REFERENCES families(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_children_family_id ON children(family_id);
CREATE INDEX IF NOT EXISTS idx_reward_items_family_id ON reward_items(family_id);

-- 奖励币流水补操作者快照；历史数据没有真实角色，不强行补角色
ALTER TABLE coin_transactions ADD COLUMN IF NOT EXISTS operator_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE coin_transactions ADD COLUMN IF NOT EXISTS operator_role VARCHAR(10);
ALTER TABLE coin_transactions ADD COLUMN IF NOT EXISTS operator_nickname VARCHAR(50);

-- 仅迁移历史数据：为已有老用户创建默认家庭，避免旧儿童和旧商品丢失归属
INSERT INTO families (id, name, code, owner_user_id)
SELECT
    uuid_generate_v4(),
    COALESCE(NULLIF(u.nickname, ''), u.username) || '的家庭',
    SUBSTRING(REPLACE(UPPER(u.id::text), '-', ''), 1, 6),
    u.id
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM families f WHERE f.owner_user_id = u.id
);

-- 老用户加入自己的家庭
INSERT INTO family_members (family_id, user_id)
SELECT f.id, f.owner_user_id
FROM families f
ON CONFLICT (family_id, user_id) DO NOTHING;

-- 历史成员角色迁到家庭成员关系上，后续角色按家庭分别维护
UPDATE family_members fm
SET role = COALESCE(u.role, '妈妈')
FROM users u
WHERE u.id = fm.user_id;

-- 设置用户当前家庭
UPDATE users u
SET current_family_id = f.id
FROM families f
WHERE f.owner_user_id = u.id
  AND u.current_family_id IS NULL;

-- 历史儿童归入原用户创建的家庭
UPDATE children c
SET family_id = f.id
FROM families f
WHERE f.owner_user_id = c.user_id
  AND c.family_id IS NULL;

-- 历史奖励商品归入原用户创建的家庭
UPDATE reward_items r
SET family_id = f.id
FROM families f
WHERE f.owner_user_id = r.user_id
  AND r.family_id IS NULL;

-- 历史流水回填操作者快照
UPDATE coin_transactions t
SET
    operator_user_id = c.user_id,
    operator_role = NULL,
    operator_nickname = COALESCE(u.nickname, u.username)
FROM children c
JOIN users u ON u.id = c.user_id
WHERE t.child_id = c.id
  AND t.operator_user_id IS NULL;

-- 补外键；已存在时忽略
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_users_current_family_id'
    ) THEN
        ALTER TABLE users
        ADD CONSTRAINT fk_users_current_family_id
        FOREIGN KEY (current_family_id) REFERENCES families(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 开发库如果缺触发器，则补家庭更新时间触发器
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_families_updated_at'
    ) THEN
        CREATE TRIGGER update_families_updated_at
            BEFORE UPDATE ON families
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
