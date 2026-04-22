// 奖励商城页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    viewMode: 'shop', // shop | history
    currentChild: {},
    rewardItems: [],
    activeItems: [],
    redemptions: [],
    
    // 兑换确认
    showRedeemConfirm: false,
    redeemTarget: {},
  },

  onShow() {
    if (!app.checkLogin()) return;
    this.setData({ currentChild: app.globalData.currentChild || {} });
    this.loadRewardItems();
  },

  switchView(e) {
    const mode = e.currentTarget.dataset.mode;
    this.setData({ viewMode: mode });
    if (mode === 'history') this.loadRedemptions();
  },

  async loadRewardItems() {
    try {
      const res = await api.getRewardItems();
      const items = res.items || [];
      this.setData({
        rewardItems: items,
        activeItems: items.filter(i => i.is_active),
      });
    } catch (err) {
      console.error('加载商品失败', err);
    }
  },

  async loadRedemptions() {
    const { currentChild } = this.data;
    if (!currentChild.id) return;
    try {
      const res = await api.getRedemptions(currentChild.id);
      const records = (res.records || []).map(record => ({
        ...record,
        formatted_time: this.formatDateTime(record.created_at)
      }));
      this.setData({ redemptions: records });
    } catch (err) {
      console.error('加载兑换记录失败', err);
    }
  },

  // 格式化日期时间
  formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  },

  // ---- 兑换流程 ----
  onRedeemItem(e) {
    const item = e.currentTarget.dataset.item;
    const { currentChild } = this.data;
    if (currentChild.coin_balance < item.coin_cost) {
      wx.showToast({ title: '奖励币不足', icon: 'none' });
      return;
    }
    this.setData({ showRedeemConfirm: true, redeemTarget: item });
  },

  onCloseRedeem() {
    this.setData({ showRedeemConfirm: false });
  },

  async onConfirmRedeem() {
    const { currentChild, redeemTarget } = this.data;
    try {
      wx.showLoading({ title: '兑换中...' });
      await api.redeemReward(currentChild.id, { reward_item_id: redeemTarget.id });
      
      // 更新本地余额
      const newBalance = currentChild.coin_balance - redeemTarget.coin_cost;
      const updatedChild = { ...currentChild, coin_balance: newBalance };
      this.setData({ currentChild: updatedChild, showRedeemConfirm: false });
      app.setCurrentChild(updatedChild);
      
      wx.hideLoading();
      wx.showToast({ title: '兑换成功！', icon: 'success' });
    } catch (err) {
      wx.hideLoading();
    }
  },


});
