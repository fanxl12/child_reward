// 个人中心页逻辑
const app = getApp();
const api = require('../../utils/api');

const ROLE_OPTIONS = ['爸爸', '妈妈', '爷爷', '奶奶', '外公', '外婆'];

Page({
  data: {
    isLoggedIn: false,
    userInfo: {},
    roleOptions: ROLE_OPTIONS,
    families: [],
    currentFamily: null,
    showEditNickname: false,
    newNickname: '',
    showEditUsername: false,
    newUsername: '',
    showRolePicker: false,
    showFamilyPicker: false,
    showFamilyForm: false,
    familyFormMode: 'create',
    familyInput: '',
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
    if (isLoggedIn) {
      this.refreshUserAndFamilies();
    }
  },

  // 刷新用户和家庭信息，保证角色、当前家庭与服务端一致
  async refreshUserAndFamilies() {
    try {
      const userInfo = await api.getUserInfo();
      const familyRes = await api.getFamilies();
      const families = familyRes.families || [];
      const currentFamilyId = userInfo.current_family_id || familyRes.current_family_id;
      const currentFamily = families.find(item => item.id === currentFamilyId) || families[0] || null;
      this.setData({ userInfo, families, currentFamily });
      app.globalData.userInfo = userInfo;
      wx.setStorageSync('userInfo', userInfo);
    } catch (err) {
      console.error('刷新用户家庭信息失败', err);
    }
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

  onEditRole() {
    if (!app.checkLogin()) return;
    if (!this.data.currentFamily) {
      wx.showToast({ title: '请先创建或加入家庭', icon: 'none' });
      return;
    }
    this.setData({ showRolePicker: true });
  },

  onCloseRolePicker() {
    this.setData({ showRolePicker: false });
  },

  // 修改角色后，后续奖励币流水会记录新的角色快照
  async onSelectRole(e) {
    const role = e.currentTarget.dataset.role;
    try {
      wx.showLoading({ title: '保存中...' });
      const user = await api.updateUserInfo({ role });
      this.setData({ userInfo: user, showRolePicker: false });
      app.globalData.userInfo = user;
      wx.setStorageSync('userInfo', user);
      wx.hideLoading();
      wx.showToast({ title: '修改成功', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
    }
  },

  onSwitchFamily() {
    if (!app.checkLogin()) return;
    this.setData({ showFamilyPicker: true });
  },

  onCloseFamilyPicker() {
    this.setData({ showFamilyPicker: false });
  },

  // 切换家庭后清空当前儿童，避免继续使用上个家庭的孩子
  async onSelectFamily(e) {
    const family = e.currentTarget.dataset.family;
    if (!family || family.id === this.data.currentFamily?.id) {
      this.setData({ showFamilyPicker: false });
      return;
    }
    try {
      wx.showLoading({ title: '切换中...' });
      await api.switchFamily(family.id);
      app.setCurrentChild(null);
      await this.refreshUserAndFamilies();
      wx.hideLoading();
      this.setData({ showFamilyPicker: false });
      wx.showToast({ title: '已切换家庭', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
    }
  },

  // 退出加入的家庭后刷新列表；如果退出的是当前家庭，后端会自动切换到剩余家庭
  onLeaveFamily(e) {
    const family = e.currentTarget.dataset.family;
    if (!family || family.is_owner) return;

    wx.showModal({
      title: '退出家庭',
      content: `确定要退出「${family.name}」吗？`,
      confirmText: '退出',
      confirmColor: '#FF6B6B',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          wx.showLoading({ title: '退出中...' });
          await api.leaveFamily(family.id);
          app.setCurrentChild(null);
          await this.refreshUserAndFamilies();
          wx.hideLoading();
          wx.showToast({ title: '已退出家庭', icon: 'success' });
        } catch (err) {
          wx.hideLoading();
        }
      },
    });
  },

  // 在家庭列表中修改自己的家庭；后端按当前家庭修改，所以先确保选中目标家庭
  async onEditFamilyFromPicker(e) {
    const family = e.currentTarget.dataset.family;
    if (!family || !family.is_owner) return;

    try {
      if (family.id !== this.data.currentFamily?.id) {
        wx.showLoading({ title: '切换中...' });
        await api.switchFamily(family.id);
        app.setCurrentChild(null);
        await this.refreshUserAndFamilies();
        wx.hideLoading();
      }
      this.setData({
        showFamilyPicker: false,
        showFamilyForm: true,
        familyFormMode: 'edit',
        familyInput: family.name || '',
      });
    } catch (err) {
      wx.hideLoading();
    }
  },

  onShowCreateFamily() {
    this.setData({
      showFamilyPicker: false,
      showFamilyForm: true,
      familyFormMode: 'create',
      familyInput: '',
    });
  },

  onShowJoinFamily() {
    this.setData({
      showFamilyPicker: false,
      showFamilyForm: true,
      familyFormMode: 'join',
      familyInput: '',
    });
  },

  onFamilyInput(e) {
    this.setData({ familyInput: e.detail.value });
  },

  onCloseFamilyForm() {
    this.setData({ showFamilyForm: false });
  },

  async onSubmitFamilyForm() {
    const value = (this.data.familyInput || '').trim();
    if (!value) {
      wx.showToast({ title: '请填写内容', icon: 'none' });
      return;
    }
    try {
      wx.showLoading({ title: '提交中...' });
      if (this.data.familyFormMode === 'create') {
        await api.createFamily({ name: value });
      } else if (this.data.familyFormMode === 'edit') {
        await api.updateCurrentFamily({ name: value });
      } else {
        await api.joinFamily({ code: value.toUpperCase() });
      }
      app.setCurrentChild(null);
      await this.refreshUserAndFamilies();
      wx.hideLoading();
      this.setData({ showFamilyForm: false });
      wx.showToast({ title: '操作成功', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
    }
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

  // 当前账号未绑定微信时，允许用户主动绑定当前微信身份
  async onBindWechat() {
    if (!app.checkLogin()) return;
    if (this.data.userInfo.wechat_bound) {
      wx.showToast({ title: '当前账号已绑定微信', icon: 'none' });
      return;
    }

    try {
      wx.showLoading({ title: '绑定中...' });
      // 使用微信登录 code 让后端确认当前微信身份，再绑定到当前账号
      const { code } = await wx.login();
      if (!code) {
        wx.hideLoading();
        wx.showToast({ title: '微信绑定失败，请重试', icon: 'none' });
        return;
      }

      const user = await api.bindWechat(code);
      this.setData({ userInfo: user });
      app.globalData.userInfo = user;
      wx.setStorageSync('userInfo', user);
      wx.hideLoading();
      wx.showToast({ title: '绑定成功', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
      console.error('微信绑定失败', err);
    }
  },

  // 获取当前小程序版本号，开发版或体验版取不到时使用默认版本
  getAppVersion() {
    const defaultVersion = '1.0.0';
    const accountInfo = wx.getAccountInfoSync();
    return accountInfo.miniProgram.version || defaultVersion;
  },

  // 展示关于弹窗
  onAbout() {
    const version = this.getAppVersion();
    wx.showModal({
      title: '关于童年小印记',
      content: `版本 ${version}\n\n一款帮助家长记录儿童日常表现、管理奖励币的小程序。`,
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
