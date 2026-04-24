// ============================================
// 儿童表现记录系统 - 小程序全局入口
// ============================================
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
