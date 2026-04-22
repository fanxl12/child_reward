// 儿童管理页逻辑
const app = getApp();
const api = require('../../utils/api');
const util = require('../../utils/util');

Page({
  data: {
    children: [],
    showForm: false,
    editingChild: null,
    childForm: { name: '', gender: '', birthday: '' },
    today: util.formatDate(new Date()),
  },

  onShow() {
    if (!app.checkLogin()) return;
    this.loadChildren();
  },

  async loadChildren() {
    try {
      const res = await api.getChildren();
      this.setData({ children: res.children || [] });
    } catch (err) {
      console.error('加载儿童列表失败', err);
    }
  },

  onShowAddChild() {
    this.setData({
      showForm: true,
      editingChild: null,
      childForm: { name: '', gender: '', birthday: '' },
    });
  },

  onEditChild(e) {
    const child = e.currentTarget.dataset.child;
    this.setData({
      showForm: true,
      editingChild: child,
      childForm: {
        name: child.name,
        gender: child.gender || '',
        birthday: child.birthday || '',
      },
    });
  },

  onCloseForm() {
    this.setData({ showForm: false });
  },

  onNameInput(e) { this.setData({ 'childForm.name': e.detail.value }); },
  onGenderSelect(e) { this.setData({ 'childForm.gender': e.currentTarget.dataset.gender }); },
  onBirthdayChange(e) { this.setData({ 'childForm.birthday': e.detail.value }); },

  async onSaveChild() {
    const { childForm, editingChild } = this.data;
    if (!childForm.name) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    
    try {
      wx.showLoading({ title: '保存中...' });
      const data = {
        name: childForm.name,
        gender: childForm.gender || undefined,
        birthday: childForm.birthday || undefined,
      };
      
      if (editingChild) {
        await api.updateChild(editingChild.id, data);
      } else {
        await api.createChild(data);
      }
      
      wx.hideLoading();
      wx.showToast({ title: '保存成功', icon: 'success' });
      this.setData({ showForm: false });
      this.loadChildren();
    } catch (err) {
      wx.hideLoading();
    }
  },

  onDeleteChild(e) {
    const child = e.currentTarget.dataset.child;
    wx.showModal({
      title: '确认删除',
      content: `确定删除「${child.name}」吗？该操作将同时删除所有关联记录，不可恢复。`,
      confirmColor: '#FF6B6B',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.deleteChild(child.id);
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadChildren();
            
            // 如果删除的是当前选中儿童，清除选择
            if (app.globalData.currentChild?.id === child.id) {
              app.setCurrentChild(null);
            }
          } catch (err) {
            console.error('删除失败', err);
          }
        }
      },
    });
  },
});
