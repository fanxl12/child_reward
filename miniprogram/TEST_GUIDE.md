# 微信登录快速测试指南

## 前置条件

✅ 后端API服务已启动 (http://localhost:8000)
✅ 微信小程序AppID已配置: `wxc510015e9422091c`
✅ 微信AppSecret已配置: `1df614ab332f54b075adde9b27c75c83`

## 测试步骤

### 1. 启动后端服务

```bash
cd d:\WorkSpace\QoderSpace\child_reward
.\api\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

验证服务启动成功：
- 访问 http://localhost:8000/docs 查看API文档
- 确认看到 `/api/auth/wechat-login` 接口

### 2. 配置微信开发者工具

1. 打开微信开发者工具
2. 导入项目：选择 `d:\WorkSpace\QoderSpace\child_reward\miniprogram` 目录
3. 确认AppID显示为：`wxc510015e9422091c`

### 3. 关闭域名校验（开发环境）

在微信开发者工具中：
1. 点击右上角 "详情" 按钮
2. 选择 "本地设置" 标签
3. ✅ 勾选 "不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书"

### 4. 测试微信登录

#### 方式一：自动登录（推荐）
1. 编译运行小程序
2. 观察控制台输出
3. 如果看到 "自动微信登录成功"，说明登录成功
4. 自动跳转到主页

#### 方式二：手动登录
1. 如果自动登录失败，会停留在登录页
2. 点击 "微信一键登录" 按钮
3. 观察登录结果

### 5. 验证登录结果

登录成功后，检查以下内容：

#### 小程序端
- ✅ 控制台显示 "自动微信登录成功"
- ✅ 自动跳转到主页（日历页）
- ✅ 本地存储中有token和userInfo

#### 后端
查看后端日志，应该看到：
```
POST /api/auth/wechat-login
```

#### 数据库
查询users表，应该看到新创建的微信用户：
```sql
SELECT * FROM users WHERE wechat_openid IS NOT NULL;
```

用户信息示例：
- username: `wx_` + openid前8位
- nickname: `微信用户`
- wechat_openid: 完整的openid

## 常见问题

### 问题1: 微信登录失败 - code无效

**原因**: code已被使用或过期（code只能使用一次，5分钟有效期）

**解决**: 
- 重新编译小程序获取新的code
- 检查后端是否正确调用微信API

### 问题2: 网络连接失败

**原因**: API地址配置错误或后端服务未启动

**解决**:
1. 检查 `miniprogram/utils/api.js` 中的 `DEV_BASE_URL`
2. 确认后端服务正在运行
3. 确认已关闭域名校验

### 问题3: 401 登录已过期

**原因**: Token无效或过期

**解决**:
- 清除本地存储，重新登录
- 检查后端SECRET_KEY配置

### 问题4: 微信API调用失败

**原因**: AppID或AppSecret配置错误

**解决**:
1. 检查 `.env` 文件中的微信配置
2. 确认AppID和AppSecret与微信后台一致
3. 查看后端日志中的错误信息

## 调试技巧

### 小程序端调试

在微信开发者工具的控制台中：
```javascript
// 查看本地存储
wx.getStorageSync('token')
wx.getStorageSync('userInfo')

// 清除本地存储
wx.clearStorageSync()

// 手动测试API
const api = require('./utils/api')
api.wechatLogin('test_code').then(console.log).catch(console.error)
```

### 后端调试

查看后端服务日志，关注：
- 微信API调用结果
- 数据库操作
- 错误堆栈信息

## 测试 checklist

- [ ] 后端服务正常启动
- [ ] API文档可访问
- [ ] 微信开发者工具已导入项目
- [ ] 已关闭域名校验
- [ ] 小程序编译成功
- [ ] 微信登录成功
- [ ] 自动跳转到主页
- [ ] 数据库中有用户记录
- [ ] Token已保存到本地存储

## 下一步

微信登录测试通过后，可以：

1. 完善用户信息（头像、昵称）
2. 实现Token自动刷新
3. 添加账号绑定功能
4. 部署到生产环境
5. 配置HTTPS和合法域名

## 技术支持

遇到问题请查看：
- 小程序端控制台日志
- 后端API服务日志
- `miniprogram/WECHAT_LOGIN.md` 详细文档
