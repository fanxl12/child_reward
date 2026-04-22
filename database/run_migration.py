"""
数据库迁移脚本 - 兑换记录表结构调整
执行此脚本更新数据库结构
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库连接信息
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@192.168.9.2:5432/child_reward")

# 解析数据库连接字符串
# postgresql+asyncpg://user:password@host:port/database
from urllib.parse import urlparse

parsed = urlparse(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
db_config = {
    "host": parsed.hostname,
    "port": parsed.port or 5432,
    "user": parsed.username,
    "password": parsed.password,
    "database": parsed.path.lstrip("/"),
}

async def migrate():
    """执行数据库迁移"""
    print("开始执行数据库迁移...")
    print(f"数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    try:
        # 连接数据库
        conn = await asyncpg.connect(**db_config)
        print("✓ 数据库连接成功")
        
        # 1. 删除状态索引
        print("\n[1/7] 删除状态索引...")
        await conn.execute("DROP INDEX IF EXISTS idx_redemption_status;")
        print("✓ 完成")
        
        # 2. 删除 approved_by 字段
        print("\n[2/7] 删除 approved_by 字段...")
        await conn.execute("ALTER TABLE redemption_records DROP COLUMN IF EXISTS approved_by;")
        print("✓ 完成")
        
        # 3. 删除 status 字段
        print("\n[3/7] 删除 status 字段...")
        await conn.execute("ALTER TABLE redemption_records DROP COLUMN IF EXISTS status;")
        print("✓ 完成")
        
        # 4. 删除 updated_at 字段
        print("\n[4/7] 删除 updated_at 字段...")
        await conn.execute("ALTER TABLE redemption_records DROP COLUMN IF EXISTS updated_at;")
        print("✓ 完成")
        
        # 5. 添加 remaining_balance 字段
        print("\n[5/7] 添加 remaining_balance 字段...")
        await conn.execute("""
            ALTER TABLE redemption_records 
            ADD COLUMN IF NOT EXISTS remaining_balance INTEGER NOT NULL DEFAULT 0 
            CHECK (remaining_balance >= 0);
        """)
        print("✓ 完成")
        
        # 6. 更新已有记录的 remaining_balance
        print("\n[6/7] 更新已有记录的 remaining_balance...")
        await conn.execute("""
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
            )
            WHERE rr.remaining_balance = 0;
        """)
        print("✓ 完成")
        
        # 7. 添加注释
        print("\n[7/7] 添加字段注释...")
        await conn.execute("COMMENT ON COLUMN redemption_records.remaining_balance IS '兑换后剩余奖励币余额';")
        print("✓ 完成")
        
        # 验证迁移结果
        print("\n验证迁移结果...")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'redemption_records' 
            ORDER BY ordinal_position;
        """)
        
        print("\n当前 redemption_records 表结构:")
        print("-" * 60)
        for row in result:
            print(f"  {row['column_name']:25} {row['data_type']:15} nullable={row['is_nullable']}")
        print("-" * 60)
        
        await conn.close()
        print("\n✓✓✓ 数据库迁移成功完成！ ✓✓✓")
        
    except Exception as e:
        print(f"\n✗✗✗ 迁移失败: {e} ✗✗✗")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(migrate())
