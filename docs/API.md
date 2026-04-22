# 儿童表现记录系统 API 接口文档

## 基础信息

| 项目 | 说明 |
|------|------|
| Base URL | `https://your-api-domain.com` |
| 协议 | HTTPS |
| 数据格式 | JSON |
| 认证方式 | Bearer Token (JWT) |
| 交互式文档 | `GET /docs` (Swagger UI) |
| ReDoc 文档 | `GET /redoc` |

## 认证说明

除注册和登录接口外，所有接口均需在请求头中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

Token 有效期为 7 天，过期后需重新登录获取。

---

## 一、用户认证 (`/api/auth`)

### 1.1 用户注册

```
POST /api/auth/register
```

**请求体：**
```json
{
  "username": "zhangmama",
  "password": "123456",
  "phone": "13800138000",    // 可选
  "nickname": "张妈妈"        // 可选
}
```

**成功响应 (201)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "zhangmama",
    "phone": "13800138000",
    "nickname": "张妈妈",
    "avatar_url": null,
    "created_at": "2026-04-22T10:00:00Z"
  }
}
```

**错误响应 (400)：**
```json
{ "detail": "用户名已被注册" }
```

### 1.2 用户登录

```
POST /api/auth/login
```

**请求体：**
```json
{
  "username": "zhangmama",
  "password": "123456"
}
```

**成功响应 (200)：** 同注册响应格式

**错误响应 (401)：**
```json
{ "detail": "用户名或密码错误" }
```

---

## 二、用户管理 (`/api/users`)

### 2.1 获取当前用户信息

```
GET /api/users/me
Authorization: Bearer <token>
```

**成功响应 (200)：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "zhangmama",
  "phone": "13800138000",
  "nickname": "张妈妈",
  "avatar_url": null,
  "created_at": "2026-04-22T10:00:00Z"
}
```

### 2.2 更新用户信息

```
PUT /api/users/me
Authorization: Bearer <token>
```

**请求体：**（所有字段可选）
```json
{
  "nickname": "小明妈妈",
  "avatar_url": "https://example.com/avatar.jpg",
  "phone": "13900139000"
}
```

### 2.3 修改密码

```
POST /api/users/change-password
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "old_password": "123456",
  "new_password": "654321"
}
```

---

## 三、儿童管理 (`/api/children`)

### 3.1 获取儿童列表

```
GET /api/children
Authorization: Bearer <token>
```

**成功响应 (200)：**
```json
{
  "children": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "小明",
      "gender": "male",
      "birthday": "2019-06-15",
      "avatar_url": null,
      "coin_balance": 36,
      "created_at": "2026-04-22T10:00:00Z"
    }
  ],
  "total": 1
}
```

### 3.2 添加儿童

```
POST /api/children
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "name": "小明",
  "gender": "male",       // male / female / other，可选
  "birthday": "2019-06-15",  // 可选
  "avatar_url": null         // 可选
}
```

### 3.3 获取儿童详情

```
GET /api/children/{child_id}
Authorization: Bearer <token>
```

### 3.4 更新儿童信息

```
PUT /api/children/{child_id}
Authorization: Bearer <token>
```

**请求体：**（所有字段可选）
```json
{
  "name": "小明",
  "gender": "male",
  "birthday": "2019-06-15"
}
```

### 3.5 删除儿童

```
DELETE /api/children/{child_id}
Authorization: Bearer <token>
```

> ⚠️ 删除将同时移除该儿童的所有表现记录、交易流水和兑换记录。

---

## 四、表现记录 (`/api/children/{child_id}/performance`)

### 4.1 获取月度表现日历

```
GET /api/children/{child_id}/performance/monthly?year=2026&month=4
Authorization: Bearer <token>
```

**成功响应 (200)：**
```json
{
  "year": 2026,
  "month": 4,
  "child_id": "660e8400-e29b-41d4-a716-446655440001",
  "records": [
    {
      "record_date": "2026-04-01",
      "overall_rating": "good",
      "coins_earned": 3,
      "coins_deducted": 0
    },
    {
      "record_date": "2026-04-03",
      "overall_rating": "bad",
      "coins_earned": 0,
      "coins_deducted": 1
    }
  ],
  "good_days": 15,
  "bad_days": 4,
  "total_coins_earned": 41,
  "total_coins_deducted": 6
}
```

### 4.2 获取某日表现详情

```
GET /api/children/{child_id}/performance/{date}
Authorization: Bearer <token>
```

**路径参数：** `date` 格式 `YYYY-MM-DD`

**成功响应 (200)：**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "child_id": "660e8400-e29b-41d4-a716-446655440001",
  "record_date": "2026-04-01",
  "overall_rating": "good",
  "comment": "今天主动完成了所有作业，还帮妈妈收拾了餐桌，非常棒！",
  "coins_earned": 3,
  "coins_deducted": 0,
  "reward_records": [
    {
      "id": "880e8400-...",
      "type": "reward",
      "description": "主动完成作业",
      "coins": 2,
      "created_at": "2026-04-01T18:00:00Z"
    },
    {
      "id": "880e8401-...",
      "type": "reward",
      "description": "帮忙做家务",
      "coins": 1,
      "created_at": "2026-04-01T18:00:00Z"
    }
  ],
  "created_at": "2026-04-01T18:00:00Z"
}
```

### 4.3 创建每日表现记录

```
POST /api/children/{child_id}/performance
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "record_date": "2026-04-22",
  "overall_rating": "good",
  "comment": "今天自己整理了书包和房间",
  "reward_records": [
    { "type": "reward", "description": "整理书包", "coins": 1 },
    { "type": "reward", "description": "整理房间", "coins": 2 }
  ]
}
```

> 系统自动计算奖励币并更新儿童余额和交易流水。

### 4.4 更新某日表现记录

```
PUT /api/children/{child_id}/performance/{date}
Authorization: Bearer <token>
```

**请求体：**（所有字段可选）
```json
{
  "overall_rating": "bad",
  "comment": "修改后的评语",
  "reward_records": [
    { "type": "punishment", "description": "说谎", "coins": 3 }
  ]
}
```

> 更新奖惩明细时会自动重新计算币数变动。

---

## 五、奖励商城 (`/api/reward-items`)

### 5.1 获取奖励商品列表

```
GET /api/reward-items
Authorization: Bearer <token>
```

**成功响应 (200)：**
```json
{
  "items": [
    {
      "id": "990e8400-...",
      "name": "看电视30分钟",
      "description": "可以看喜欢的动画片",
      "coin_cost": 10,
      "icon": "📺",
      "sort_order": 0,
      "is_active": true,
      "created_at": "2026-04-20T10:00:00Z"
    }
  ],
  "total": 6
}
```

### 5.2 创建奖励商品

```
POST /api/reward-items
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "name": "看电视30分钟",
  "description": "可以看喜欢的动画片",
  "coin_cost": 10,
  "icon": "📺",
  "sort_order": 0
}
```

### 5.3 更新奖励商品

```
PUT /api/reward-items/{item_id}
Authorization: Bearer <token>
```

### 5.4 删除奖励商品

```
DELETE /api/reward-items/{item_id}
Authorization: Bearer <token>
```

---

## 六、奖励币 & 兑换 (`/api/children/{child_id}`)

### 6.1 获取奖励币余额及流水

```
GET /api/children/{child_id}/coins?page=1&page_size=20
Authorization: Bearer <token>
```

**成功响应 (200)：**
```json
{
  "child_id": "660e8400-...",
  "child_name": "小明",
  "balance": 36,
  "transactions": [
    {
      "id": "aa0e8400-...",
      "type": "earn",
      "amount": 3,
      "balance_after": 36,
      "description": "2026-04-22 表现奖励",
      "created_at": "2026-04-22T18:00:00Z"
    },
    {
      "id": "aa0e8401-...",
      "type": "redeem",
      "amount": -10,
      "balance_after": 33,
      "description": "兑换奖励：看电视30分钟",
      "created_at": "2026-04-20T18:30:00Z"
    }
  ],
  "total_transactions": 25
}
```

### 6.2 兑换奖励

```
POST /api/children/{child_id}/redeem
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "reward_item_id": "990e8400-..."
}
```

**成功响应 (201)：**
```json
{
  "id": "bb0e8400-...",
  "child_id": "660e8400-...",
  "reward_item_id": "990e8400-...",
  "reward_name": "看电视30分钟",
  "coins_spent": 10,
  "status": "pending",
  "created_at": "2026-04-22T19:00:00Z"
}
```

**错误响应 (400)：**
```json
{ "detail": "奖励币余额不足，当前 36，需要 50" }
```

### 6.3 获取兑换记录

```
GET /api/children/{child_id}/redemptions?page=1&page_size=20
Authorization: Bearer <token>
```

### 6.4 审批兑换记录

```
PUT /api/children/{child_id}/redemptions/{redemption_id}
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "status": "approved"  // approved / rejected / completed
}
```

> 拒绝兑换时系统自动退回奖励币。

---

## 通用错误格式

| HTTP 状态码 | 说明 |
|------------|------|
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 失效 |
| 404 | 资源不存在 |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |

**错误响应格式：**
```json
{
  "detail": "错误信息描述"
}
```

---

## 系统接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 系统信息 & 健康检查 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger 交互式文档 |
| `/redoc` | GET | ReDoc 文档 |
