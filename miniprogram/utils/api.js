// ============================================
// API 请求工具封装
// ============================================
// 开发环境配置（根据实际情况修改）
const DEV_BASE_URL = 'http://localhost:8000';
// 生产环境配置
const PROD_BASE_URL = 'https://api.fanxl.cn/api';

// 根据环境自动切换
const isDevelopment = true; // 开发时设置为 true，发布时设置为 false
const BASE_URL = isDevelopment ? DEV_BASE_URL : PROD_BASE_URL;

/**
 * 通用请求方法
 */
function request(url, method = 'GET', data = {}) {
  const app = getApp();
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': app && app.globalData && app.globalData.token ? `Bearer ${app.globalData.token}` : ''
      },
      success(res) {
        if (res.statusCode === 401) {
          // Token 失效，跳转登录
          if (app && app.logout) {
            app.logout();
          }
          reject(new Error('登录已过期，请重新登录'));
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const msg = res.data?.detail || '请求失败';
          wx.showToast({ title: msg, icon: 'none' });
          reject(new Error(msg));
        }
      },
      fail(err) {
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      }
    });
  });
}

// ---- 用户认证 ----
function register(data) {
  return request('/api/auth/register', 'POST', data);
}

function login(data) {
  return request('/api/auth/login', 'POST', data);
}

/**
 * 微信小程序登录
 * @param {string} code - 微信登录临时凭证
 */
function wechatLogin(code) {
  return request('/api/auth/wechat-login', 'POST', { code });
}

// 将当前登录账号绑定到当前微信身份
function bindWechat(code) {
  return request('/api/users/bind-wechat', 'POST', { code });
}

function getUserInfo() {
  return request('/api/users/me');
}

function updateUserInfo(data) {
  return request('/api/users/me', 'PUT', data);
}

function changePassword(data) {
  return request('/api/users/change-password', 'POST', data);
}

function setPassword(data) {
  return request('/api/users/set-password', 'POST', data);
}

// ---- 家庭管理 ----
function getFamilies() {
  return request('/api/families');
}

function createFamily(data) {
  return request('/api/families', 'POST', data);
}

// 修改当前家庭名称，后端会校验当前用户是否为家庭创建者
function updateCurrentFamily(data) {
  return request('/api/families/current', 'PUT', data);
}

function joinFamily(data) {
  return request('/api/families/join', 'POST', data);
}

function switchFamily(familyId) {
  return request('/api/families/switch', 'POST', { family_id: familyId });
}

// 退出加入的家庭，自己的家庭不能退出
function leaveFamily(familyId) {
  return request(`/api/families/${familyId}/membership`, 'DELETE');
}

// ---- 儿童管理 ----
function getChildren() {
  return request('/api/children');
}

function createChild(data) {
  return request('/api/children', 'POST', data);
}

function updateChild(childId, data) {
  return request(`/api/children/${childId}`, 'PUT', data);
}

function deleteChild(childId) {
  return request(`/api/children/${childId}`, 'DELETE');
}

// ---- 表现记录 ----
function getMonthlyPerformance(childId, year, month) {
  return request(`/api/children/${childId}/performance/monthly?year=${year}&month=${month}`);
}

function getDailyPerformance(childId, date) {
  return request(`/api/children/${childId}/performance/${date}`);
}

function createPerformance(childId, data) {
  return request(`/api/children/${childId}/performance`, 'POST', data);
}

function updatePerformance(childId, date, data) {
  return request(`/api/children/${childId}/performance/${date}`, 'PUT', data);
}

function addRewardRecord(childId, date, data) {
  return request(`/api/children/${childId}/performance/${date}/reward-records`, 'POST', data);
}

// ---- 奖励商城 ----
function getRewardItems() {
  return request('/api/reward-items');
}

function createRewardItem(data) {
  return request('/api/reward-items', 'POST', data);
}

function updateRewardItem(itemId, data) {
  return request(`/api/reward-items/${itemId}`, 'PUT', data);
}

function deleteRewardItem(itemId) {
  return request(`/api/reward-items/${itemId}`, 'DELETE');
}

// ---- 奖励币 & 兑换 ----
/**
 * 获取奖励币余额和交易流水
 * 默认每页展示 20 条，供奖励币明细页分页加载使用
 */
function getCoinBalance(childId, page = 1, pageSize = 20) {
  return request(`/api/children/${childId}/coins?page=${page}&page_size=${pageSize}`);
}

function redeemReward(childId, data) {
  return request(`/api/children/${childId}/redeem`, 'POST', data);
}

function getRedemptions(childId, page = 1) {
  return request(`/api/children/${childId}/redemptions?page=${page}`);
}

function updateRedemptionStatus(childId, redemptionId, data) {
  return request(`/api/children/${childId}/redemptions/${redemptionId}`, 'PUT', data);
}

module.exports = {
  request,
  register, login, wechatLogin, bindWechat, getUserInfo, updateUserInfo, changePassword, setPassword,
  getFamilies, createFamily, updateCurrentFamily, joinFamily, switchFamily, leaveFamily,
  getChildren, createChild, updateChild, deleteChild,
  getMonthlyPerformance, getDailyPerformance, createPerformance, updatePerformance, addRewardRecord,
  getRewardItems, createRewardItem, updateRewardItem, deleteRewardItem,
  getCoinBalance, redeemReward, getRedemptions, updateRedemptionStatus,
};
