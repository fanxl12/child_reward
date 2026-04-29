// 日期详情页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    childId: '',
    date: '',
    record: {},
    hasRecord: false,
    dateDay: '',
    dateText: '',
    weekdayText: '',
    netCoins: 0,
    showAddReward: false,
    newReward: {
      type: 'reward',
      description: '',
      coins: '',
    },
  },

  onLoad(options) {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    const { childId, date } = options;
    this.setData({ childId, date });
    this.parseDateDisplay(date);
    this.loadDetail();
  },

  parseDateDisplay(dateStr) {
    const d = new Date(dateStr);
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    this.setData({
      dateDay: d.getDate(),
      dateText: `${d.getFullYear()}年${d.getMonth() + 1}月`,
      weekdayText: weekdays[d.getDay()],
    });
  },

  async loadDetail() {
    const { childId, date } = this.data;
    try {
      const record = await api.getDailyPerformance(childId, date);
      this.setData({
        record,
        hasRecord: true,
        netCoins: (record.coins_earned || 0) - (record.coins_deducted || 0),
      });
    } catch (err) {
      this.setData({ hasRecord: false });
    }
  },

  onAddRecord() {
    wx.navigateBack();
  },

  onOpenAddReward() {
    this.setData({
      showAddReward: true,
      newReward: {
        type: 'reward',
        description: '',
        coins: '',
      },
    });
  },

  onCloseAddReward() {
    this.setData({ showAddReward: false });
  },

  onNewRewardType(e) {
    this.setData({ 'newReward.type': e.currentTarget.dataset.type });
  },

  onNewRewardDesc(e) {
    this.setData({
      newReward: { ...this.data.newReward, description: e.detail.value },
    });
  },

  onNewRewardCoins(e) {
    const value = e.detail.value.replace(/[^0-9]/g, '');
    this.setData({
      newReward: { ...this.data.newReward, coins: value },
    });
  },

  async onSubmitAddReward() {
    const { childId, date, record, newReward } = this.data;
    const description = (newReward.description || '').trim();
    const coinsStr = String(newReward.coins || '').trim();

    if (!description || coinsStr === '') {
      wx.showToast({ title: '请填写完整', icon: 'none' });
      return;
    }

    const coins = parseInt(coinsStr, 10);
    if (!coins || coins <= 0) {
      wx.showToast({ title: '币数需大于0', icon: 'none' });
      return;
    }

    const rewardRecords = Array.isArray(record.reward_records) ? [...record.reward_records] : [];
    rewardRecords.push({
      type: newReward.type,
      description,
      coins,
    });

    try {
      wx.showLoading({ title: '保存中...' });
      await api.updatePerformance(childId, date, {
        overall_rating: record.overall_rating,
        comment: record.comment || null,
        reward_records: rewardRecords,
      });
      wx.hideLoading();
      wx.showToast({ title: '添加成功', icon: 'success' });
      this.setData({ showAddReward: false });
      this.loadDetail();
    } catch (err) {
      wx.hideLoading();
      console.error('追加奖惩失败', err);
    }
  },
});
