// 登录/注册页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    mode: 'login', // login | register
    username: '',
    password: '',
    phone: '',
    nickname: '',
    loading: false,
  },

  switchMode(e) {
    this.setData({ mode: e.currentTarget.dataset.mode });
  },

  onUsernameInput(e) { this.setData({ username: e.detail.value }); },
  onPasswordInput(e) { this.setData({ password: e.detail.value }); },
  onPhoneInput(e) { this.setData({ phone: e.detail.value }); },
  onNicknameInput(e) { this.setData({ nickname: e.detail.value }); },

  async onSubmit() {
    const { mode, username, password, phone, nickname } = this.data;

    if (!username || !password) {
      wx.showToast({ title: '请输入用户名和密码', icon: 'none' });
      return;
    }

    if (password.length < 6) {
      wx.showToast({ title: '密码至少6位', icon: 'none' });
      return;
    }

    this.setData({ loading: true });

    try {
      let res;
      if (mode === 'login') {
        res = await api.login({ username, password });
      } else {
        res = await api.register({
          username,
          password,
          phone: phone || undefined,
          nickname: nickname || undefined,
        });
      }

      // 保存登录信息
      app.saveLoginInfo(res.access_token, res.user);

      wx.showToast({ title: mode === 'login' ? '登录成功' : '注册成功', icon: 'success' });

      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' });
      }, 500);
    } catch (err) {
      console.error('认证失败', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 微信登录
   */
  async onWechatLogin() {
    this.setData({ loading: true });

    try {
      // 调用微信登录接口获取 code
      const { code } = await wx.login();

      if (!code) {
        wx.showToast({ title: '微信登录失败', icon: 'none' });
        return;
      }

      // 调用后端微信登录接口
      const res = await api.wechatLogin(code);

      // 保存登录信息
      app.saveLoginInfo(res.access_token, res.user);

      wx.showToast({ title: '登录成功', icon: 'success' });

      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' });
      }, 500);
    } catch (err) {
      console.error('微信登录失败', err);
      wx.showToast({ title: '微信登录失败，请重试', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },
});
