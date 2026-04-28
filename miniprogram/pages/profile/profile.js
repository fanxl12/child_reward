// 个人中心页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    isLoggedIn: false,
    userInfo: {},
    showEditNickname: false,
    newNickname: '',
  },

  onShow() {
    const isLoggedIn = !!app.globalData.token;
    this.setData({
      isLoggedIn,
      userInfo: app.globalData.userInfo || {},
    });
  },

  goToLogin() {
    wx.navigateTo({ url: '/pages/login/login?redirect=profile' });
  },

  goToChildren() {
    if (!app.checkLogin()) return;
    wx.navigateTo({ url: '/pages/children/children' });
  },

  goToRewardShop() {
    if (!app.checkLogin()) return;
    wx.navigateTo({ url: '/pages/reward-manage/reward-manage' });
  },

  onEditProfile() {
    if (!app.checkLogin()) return;
    this.setData({
      showEditNickname: true,
      newNickname: this.data.userInfo.nickname || '',
    });
  },

  onCloseEdit() {
    this.setData({ showEditNickname: false });
  },

  onNicknameInput(e) {
    this.setData({ newNickname: e.detail.value });
  },

  async onSaveNickname() {
    const { newNickname } = this.data;
    if (!newNickname) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' });
      return;
    }
    try {
      wx.showLoading({ title: '保存中...' });
      const user = await api.updateUserInfo({ nickname: newNickname });
      
      const updated = { ...this.data.userInfo, nickname: newNickname };
      this.setData({ userInfo: updated, showEditNickname: false });
      app.globalData.userInfo = updated;
      wx.setStorageSync('userInfo', updated);
      
      wx.hideLoading();
      wx.showToast({ title: '修改成功', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
    }
  },

  onChangePassword() {
    if (!app.checkLogin()) return;
    wx.showToast({ title: '密码修改功能开发中', icon: 'none' });
  },

  onAbout() {
    wx.showModal({
      title: '关于童年小印记',
      content: '版本 1.0.0\n\n一款帮助家长记录儿童日常表现、管理奖励币的小程序。',
      showCancel: false,
    });
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      confirmColor: '#FF6B6B',
      success: (res) => {
        if (res.confirm) {
          app.logout();
          this.setData({
            isLoggedIn: false,
            userInfo: {},
          });
        }
      },
    });
  },
});
