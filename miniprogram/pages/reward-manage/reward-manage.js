// 奖励商品管理页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    rewardItems: [],

    // 商品表单
    showItemForm: false,
    editingItem: null,
    itemForm: { name: '', coin_cost: '', description: '', icon: '🎁' },
    iconOptions: ['🎁', '📺', '🎮', '🍦', '🎨', '⚽', '📚', '🎵', '🛝', '🎪', '🍰', '🎠', '🧸', '🎯', '🏊', '🎢'],
  },

  onShow() {
    if (!app.checkLogin()) return;
    this.loadRewardItems();
  },

  async loadRewardItems() {
    try {
      const res = await api.getRewardItems();
      const items = res.items || [];
      this.setData({ rewardItems: items });
    } catch (err) {
      console.error('加载商品失败', err);
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
