// 奖励商城页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    viewMode: 'shop', // shop | manage | history
    currentChild: {},
    rewardItems: [],
    activeItems: [],
    redemptions: [],
    
    // 商品表单
    showItemForm: false,
    editingItem: null,
    itemForm: { name: '', coin_cost: '', description: '', icon: '🎁' },
    iconOptions: ['🎁', '📺', '🎮', '🍦', '🎨', '⚽', '📚', '🎵', '🛝', '🎪', '🍰', '🎠', '🧸', '🎯', '🏊', '🎢'],
    
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
      this.setData({ redemptions: res.records || [] });
    } catch (err) {
      console.error('加载兑换记录失败', err);
    }
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

  // ---- 商品管理 ----
  onShowAddItem() {
    this.setData({
      showItemForm: true,
      editingItem: null,
      itemForm: { name: '', coin_cost: '', description: '', icon: '🎁' },
    });
  },

  onEditItem(e) {
    const item = e.currentTarget.dataset.item;
    this.setData({
      showItemForm: true,
      editingItem: item,
      itemForm: {
        name: item.name,
        coin_cost: String(item.coin_cost),
        description: item.description || '',
        icon: item.icon || '🎁',
      },
    });
  },

  onCloseItemForm() {
    this.setData({ showItemForm: false });
  },

  onItemNameInput(e) { this.setData({ 'itemForm.name': e.detail.value }); },
  onItemCostInput(e) { this.setData({ 'itemForm.coin_cost': e.detail.value }); },
  onItemDescInput(e) { this.setData({ 'itemForm.description': e.detail.value }); },
  onSelectIcon(e) { this.setData({ 'itemForm.icon': e.currentTarget.dataset.icon }); },

  async onSaveItem() {
    const { itemForm, editingItem } = this.data;
    if (!itemForm.name || !itemForm.coin_cost) {
      wx.showToast({ title: '请填写名称和所需奖励币', icon: 'none' });
      return;
    }
    try {
      wx.showLoading({ title: '保存中...' });
      const data = {
        name: itemForm.name,
        coin_cost: parseInt(itemForm.coin_cost),
        description: itemForm.description || undefined,
        icon: itemForm.icon,
      };
      
      if (editingItem) {
        await api.updateRewardItem(editingItem.id, data);
      } else {
        await api.createRewardItem(data);
      }
      
      wx.hideLoading();
      wx.showToast({ title: '保存成功', icon: 'success' });
      this.setData({ showItemForm: false });
      this.loadRewardItems();
    } catch (err) {
      wx.hideLoading();
    }
  },

  onDeleteItem(e) {
    const item = e.currentTarget.dataset.item;
    wx.showModal({
      title: '确认删除',
      content: `确定要删除「${item.name}」吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.deleteRewardItem(item.id);
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadRewardItems();
          } catch (err) {
            console.error('删除失败', err);
          }
        }
      },
    });
  },
});
