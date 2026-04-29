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
});
