// ============================================
// API 请求工具封装
// ============================================
const app = getApp();

// 开发环境配置（根据实际情况修改）
const DEV_BASE_URL = 'http://localhost:8000';
// 生产环境配置
const PROD_BASE_URL = 'https://your-api-domain.com';

// 根据环境自动切换
const isDevelopment = true; // 开发时设置为 true，发布时设置为 false
const BASE_URL = isDevelopment ? DEV_BASE_URL : PROD_BASE_URL;

/**
 * 通用请求方法
 */
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': app.globalData.token ? `Bearer ${app.globalData.token}` : ''
      },
      success(res) {
        if (res.statusCode === 401) {
          // Token 失效，跳转登录
          app.logout();
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

function getUserInfo() {
  return request('/api/users/me');
}

function updateUserInfo(data) {
  return request('/api/users/me', 'PUT', data);
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
function getCoinBalance(childId, page = 1) {
  return request(`/api/children/${childId}/coins?page=${page}`);
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
  register, login, wechatLogin, getUserInfo, updateUserInfo,
  getChildren, createChild, updateChild, deleteChild,
  getMonthlyPerformance, getDailyPerformance, createPerformance, updatePerformance,
  getRewardItems, createRewardItem, updateRewardItem, deleteRewardItem,
  getCoinBalance, redeemReward, getRedemptions, updateRedemptionStatus,
};
