-- ============================================
-- 家庭成员角色增量迁移
-- 用于生产环境在已有 family_members 表基础上增量更新
-- ============================================

-- 角色字段保留为空的能力，兼容历史数据和未设置角色的成员
ALTER TABLE family_members ADD COLUMN IF NOT EXISTS role VARCHAR(10);

-- 加入家庭时由业务代码分配未使用角色，数据库不再默认写入“妈妈”
ALTER TABLE family_members ALTER COLUMN role DROP DEFAULT;

-- 历史成员可能还未设置角色，因此角色字段允许为空
ALTER TABLE family_members ALTER COLUMN role DROP NOT NULL;
