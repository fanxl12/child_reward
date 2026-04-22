# 微信小程序登录集成说明

## 功能概述

已成功集成微信小程序登录功能，支持以下两种登录方式：

1. **账号密码登录** - 传统的用户名和密码登录
2. **微信一键登录** - 使用微信授权快速登录

## 已修改的文件

### 1. 小程序端文件

#### `miniprogram/utils/api.js`
- ✅ 添加 `wechatLogin(code)` 方法
- ✅ 配置开发/生产环境API地址自动切换
- ✅ 导出微信登录方法

#### `miniprogram/pages/login/login.js`
- ✅ 添加 `onWechatLogin()` 方法
- ✅ 处理微信登录流程
- ✅ 错误处理和用户提示

#### `miniprogram/pages/login/login.wxml`
- ✅ 添加微信登录按钮
- ✅ 添加分割线和图标

#### `miniprogram/pages/login/login.wxss`
- ✅ 微信登录按钮样式
- ✅ 分割线样式
- ✅ 交互动画效果

#### `miniprogram/app.js`
- ✅ 添加 `autoWechatLogin()` 方法
- ✅ 应用启动时自动微信登录
- ✅ 无感登录体验

### 2. 后端API文件

#### `api/services/wechat.py` (新建)
- ✅ 微信小程序服务类
- ✅ `code2session()` - 获取openid
- ✅ `get_access_token()` - 获取接口调用凭证

#### `api/endpoints/user.py`
- ✅ 添加 `/api/auth/wechat-login` 接口
- ✅ 自动创建微信用户
- ✅ 返回JWT Token

## 微信登录流程

```
用户打开小程序
    ↓
检查本地是否有token
    ↓ (无)
调用 wx.login() 获取 code
    ↓
发送 code 到后端 /api/auth/wechat-login
    ↓
后端调用微信 API 换取 openid
    ↓
根据 openid 查找或创建用户
    ↓
返回 JWT Token
    ↓
保存到本地存储
    ↓
进入主页
```

## 配置说明

### 1. 小程序端配置

在 `miniprogram/utils/api.js` 中配置API地址：

```javascript
// 开发环境
const DEV_BASE_URL = 'http://localhost:8000';

// 生产环境
const PROD_BASE_URL = 'https://your-api-domain.com';

// 切换环境
const isDevelopment = true; // 开发时 true，发布时 false
```

### 2. 后端配置

在 `.env` 文件中配置微信参数：

```env
WECHAT_APP_ID=wxc510015e9422091c
WECHAT_APP_SECRET=1df614ab332f54b075adde9b27c75c83
```

### 3. 微信小程序后台配置

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入小程序管理后台
3. 配置服务器域名：
   - request合法域名：`https://your-api-domain.com`
   - 开发阶段可在开发者工具中勾选"不校验合法域名"

## 使用说明

### 开发环境测试

1. 启动后端API服务：
```bash
cd api
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload
```

2. 打开微信开发者工具
3. 导入小程序项目
4. 在开发者工具中勾选"不校验合法域名"
5. 编译运行

### 测试微信登录

1. 打开小程序，自动触发微信登录
2. 或在登录页点击"微信一键登录"按钮
3. 登录成功后自动跳转到主页

## API接口文档

### 微信登录接口

**URL**: `POST /api/auth/wechat-login`

**请求参数**:
```json
{
  "code": "微信登录临时凭证"
}
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-string",
    "username": "wx_abc12345",
    "phone": null,
    "nickname": "微信用户",
    "avatar_url": null,
    "created_at": "2026-04-22T12:00:00"
  }
}
```

## 注意事项

1. **微信AppID配置**：确保 `app.json` 中配置了正确的AppID
2. **HTTPS要求**：生产环境必须使用HTTPS
3. **域名备案**：服务器域名必须已备案
4. **用户隐私**：微信登录不会获取用户头像和昵称（需额外授权）
5. **Token有效期**：JWT Token有效期7天，过期需重新登录

## 后续优化建议

1. **Token刷新**：实现Token自动刷新机制
2. **用户信息完善**：添加获取用户头像和昵称的功能
3. **账号绑定**：支持微信账号与手机号绑定
4. **登录日志**：记录用户登录日志
5. **安全加固**：添加防刷机制和频率限制

## 故障排查

### 微信登录失败

1. 检查微信AppID和AppSecret是否正确
2. 检查后端服务是否正常运行
3. 查看控制台错误日志
4. 确认微信开发者工具中已勾选"不校验合法域名"

### API请求失败

1. 检查BASE_URL配置是否正确
2. 确认后端服务端口是否为8000
3. 检查网络连接
4. 查看浏览器Network面板

## 技术支持

如有问题，请查看：
- 小程序端控制台日志
- 后端API服务日志
- 微信开发者工具调试面板
