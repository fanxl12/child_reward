// ============================================
// 儿童表现记录系统 - 小程序全局入口
// ============================================
const api = require('./utils/api');

App({
  globalData: {
    userInfo: null,
    token: null,
    currentChild: null,
    baseUrl: 'https://your-api-domain.com' // 替换为实际 API 地址
  },

  onLaunch() {
    // 尝试从本地存储恢复登录状态
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    const currentChild = wx.getStorageSync('currentChild');

    if (token) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
      this.globalData.currentChild = currentChild;
    } else {
      // 如果没有登录，尝试自动微信登录
      this.autoWechatLogin();
    }
  },

  /**
   * 自动微信登录（静默登录）
   */
  async autoWechatLogin() {
    try {
      // 调用微信登录接口获取 code
      const { code } = await wx.login();

      if (!code) {
        console.log('微信登录获取 code 失败');
        return;
      }

      // 调用后端微信登录接口
      const res = await api.wechatLogin(code);

      // 保存登录信息
      this.saveLoginInfo(res.access_token, res.user);
      
      console.log('自动微信登录成功');
    } catch (err) {
      console.log('自动微信登录失败，请手动登录', err);
    }
  },

  /**
   * 检查登录状态，未登录则跳转登录页
   */
  checkLogin() {
    if (!this.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return false;
    }
    return true;
  },

  /**
   * 保存登录信息
   */
  saveLoginInfo(token, userInfo) {
    this.globalData.token = token;
    this.globalData.userInfo = userInfo;
    wx.setStorageSync('token', token);
    wx.setStorageSync('userInfo', userInfo);
  },

  /**
   * 设置当前选中的儿童
   */
  setCurrentChild(child) {
    this.globalData.currentChild = child;
    wx.setStorageSync('currentChild', child);
  },

  /**
   * 退出登录
   */
  logout() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    this.globalData.currentChild = null;
    wx.clearStorageSync();
    wx.reLaunch({ url: '/pages/login/login' });
  }
});
