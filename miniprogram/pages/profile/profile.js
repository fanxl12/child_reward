// 个人中心页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    isLoggedIn: false,
    userInfo: {},
    showEditNickname: false,
    newNickname: '',
    showEditUsername: false,
    newUsername: '',
    showChangePassword: false,
    hasPassword: true,
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
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

  onEditUsername() {
    if (!app.checkLogin()) return;
    this.setData({
      showEditUsername: true,
      newUsername: this.data.userInfo.username || '',
    });
  },

  onCloseEditUsername() {
    this.setData({ showEditUsername: false });
  },

  onUsernameInput(e) {
    this.setData({ newUsername: e.detail.value });
  },

  async onSaveUsername() {
    let { newUsername } = this.data;
    newUsername = (newUsername || '').trim();
    if (newUsername.length < 3) {
      wx.showToast({ title: '用户名至少 3 个字符', icon: 'none' });
      return;
    }
    if (newUsername === (this.data.userInfo.username || '')) {
      this.setData({ showEditUsername: false });
      return;
    }
    try {
      wx.showLoading({ title: '保存中...' });
      await api.updateUserInfo({ username: newUsername });
      const updated = { ...this.data.userInfo, username: newUsername };
      this.setData({ userInfo: updated, showEditUsername: false });
      app.globalData.userInfo = updated;
      wx.setStorageSync('userInfo', updated);
      wx.hideLoading();
      wx.showToast({ title: '修改成功', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
    }
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
    const hasPassword = this.data.userInfo.has_password !== false;
    this.setData({
      showChangePassword: true,
      hasPassword,
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
    });
  },

  onCloseChangePassword() {
    this.setData({ showChangePassword: false });
  },

  onOldPasswordInput(e) {
    this.setData({ oldPassword: e.detail.value });
  },

  onNewPasswordInput(e) {
    this.setData({ newPassword: e.detail.value });
  },

  onConfirmPasswordInput(e) {
    this.setData({ confirmPassword: e.detail.value });
  },

  async onSavePassword() {
    const { hasPassword, oldPassword, newPassword, confirmPassword } = this.data;
    if (!newPassword || !confirmPassword || (hasPassword && !oldPassword)) {
      wx.showToast({ title: '请完整填写密码信息', icon: 'none' });
      return;
    }
    if (newPassword.length < 6) {
      wx.showToast({ title: '新密码至少 6 位', icon: 'none' });
      return;
    }
    if (newPassword !== confirmPassword) {
      wx.showToast({ title: '两次输入的新密码不一致', icon: 'none' });
      return;
    }
    if (oldPassword === newPassword) {
      wx.showToast({ title: '新密码不能与原密码相同', icon: 'none' });
      return;
    }

    try {
      wx.showLoading({ title: '提交中...' });
      if (hasPassword) {
        await api.changePassword({
          old_password: oldPassword,
          new_password: newPassword,
        });
      } else {
        await api.setPassword({
          new_password: newPassword,
        });
      }
      wx.hideLoading();
      const updated = { ...this.data.userInfo, has_password: true };
      this.setData({
        userInfo: updated,
        showChangePassword: false,
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
      app.globalData.userInfo = updated;
      wx.setStorageSync('userInfo', updated);
      wx.showToast({ title: hasPassword ? '密码修改成功' : '密码设置成功', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
    }
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
