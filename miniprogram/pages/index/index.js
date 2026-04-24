// 首页 - 日历视图逻辑
const app = getApp();
const api = require('../../utils/api');
const util = require('../../utils/util');

Page({
  data: {
    // 日历状态
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    monthText: util.monthName(new Date().getMonth() + 1),
    weekDays: ['一', '二', '三', '四', '五', '六', '日'],
    calendarDays: [],

    // 儿童相关
    currentChild: {},
    children: [],
    showChildPicker: false,

    // 统计
    stats: {
      goodDays: 0,
      badDays: 0,
      totalEarned: 0,
      totalDeducted: 0,
    },

    // 添加记录弹窗
    showAddRecord: false,
    recordForm: {
      date: '',
      rating: 'good',
      comment: '',
      rewards: [],
    },
    newReward: {
      type: 'reward',
      description: '',
      coins: '',
    },

    // 月份选择弹窗
    showMonthPicker: false,
    pickerYear: new Date().getFullYear(),
    months: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  },

  onShow() {
    if (!app.checkLogin()) return;
    this.loadChildren();
  },

  /**
   * 加载儿童列表
   */
  async loadChildren() {
    try {
      const res = await api.getChildren();
      // 给每个 child 添加头像文字（取名字最后一个字）
      const children = res.children.map(c => ({
        ...c,
        avatarLetter: c.name ? c.name.slice(-1) : '?',
      }));
      this.setData({ children });

      // 设置当前儿童（使用 API 返回的最新数据，确保余额等字段已刷新）
      const saved = app.globalData.currentChild;
      const foundChild = saved && children.find(c => c.id === saved.id);
      if (foundChild) {
        this.setData({ currentChild: foundChild });
        app.setCurrentChild(foundChild);
      } else if (children.length > 0) {
        const child = children[0];
        this.setData({ currentChild: child });
        app.setCurrentChild(child);
      }

      this.loadCalendar();
    } catch (err) {
      console.error('加载儿童列表失败', err);
    }
  },

  /**
   * 加载日历数据
   */
  async loadCalendar() {
    const { year, month, currentChild } = this.data;
    
    // 先更新月份显示，不依赖儿童数据
    this.setData({ monthText: util.monthName(month) });
    
    if (!currentChild.id) return;
    
    // 生成日历网格
    const grid = util.generateCalendarGrid(year, month);
    
    // 获取月度表现数据
    try {
      const res = await api.getMonthlyPerformance(currentChild.id, year, month);
      
      // 将表现数据映射到日历格子
      const recordMap = {};
      res.records.forEach(r => {
        recordMap[r.record_date] = r;
      });
      
      grid.forEach(cell => {
        if (!cell.empty && recordMap[cell.date]) {
          const record = recordMap[cell.date];
          cell.rating = record.overall_rating;
          cell.coins = record.coins_earned - record.coins_deducted;
        }
      });
      
      this.setData({
        calendarDays: grid,
        stats: {
          goodDays: res.good_days,
          badDays: res.bad_days,
          totalEarned: res.total_coins_earned,
          totalDeducted: res.total_coins_deducted,
        },
      });
    } catch (err) {
      // API 不可用时仍显示日历框架
      this.setData({
        calendarDays: grid,
      });
    }
  },

  // ---- 月份切换 ----
  onPrevMonth() {
    let { year, month } = this.data;
    month -= 1;
    if (month < 1) { month = 12; year -= 1; }
    this.setData({ year, month });
    this.loadCalendar();
  },

  onNextMonth() {
    let { year, month } = this.data;
    month += 1;
    if (month > 12) { month = 1; year += 1; }
    this.setData({ year, month });
    this.loadCalendar();
  },

  onPickYearMonth() {
    this.setData({
      showMonthPicker: true,
      pickerYear: this.data.year,
    });
  },

  onCloseMonthPicker() {
    this.setData({ showMonthPicker: false });
  },

  onPickerPrevYear() {
    this.setData({ pickerYear: this.data.pickerYear - 1 });
  },

  onPickerNextYear() {
    this.setData({ pickerYear: this.data.pickerYear + 1 });
  },

  onSelectMonth(e) {
    const month = e.currentTarget.dataset.month;
    this.setData({
      year: this.data.pickerYear,
      month,
      showMonthPicker: false,
    });
    this.loadCalendar();
  },

  onBackToToday() {
    const today = new Date();
    this.setData({
      year: today.getFullYear(),
      month: today.getMonth() + 1,
    });
    this.loadCalendar();
  },

  // ---- 日期点击 ----
  onDayTap(e) {
    if (!app.checkLogin()) return;
    const item = e.currentTarget.dataset.item;
    if (item.empty) return;

    if (item.rating) {
      // 有记录，跳转详情
      wx.navigateTo({
        url: `/pages/detail/detail?childId=${this.data.currentChild.id}&date=${item.date}`,
      });
    } else {
      // 无记录，打开添加弹窗并预设日期
      this.setData({
        showAddRecord: true,
        recordForm: {
          date: item.date,
          rating: 'good',
          comment: '',
          rewards: [],
        },
        newReward: { type: 'reward', description: '', coins: '' },
      });
    }
  },

  // ---- 儿童切换 ----
  onSwitchChild() {
    if (!app.checkLogin()) return;
    this.setData({ showChildPicker: true });
  },

  onCloseChildPicker() {
    this.setData({ showChildPicker: false });
  },

  onSelectChild(e) {
    const child = e.currentTarget.dataset.child;
    this.setData({ currentChild: child, showChildPicker: false });
    app.setCurrentChild(child);
    this.loadCalendar();
  },

  onManageChildren() {
    this.setData({ showChildPicker: false });
    wx.navigateTo({ url: '/pages/children/children' });
  },

  // ---- 查看奖励币 ----
  onViewCoins() {
    // 可跳转奖励币详情页
    wx.showToast({
      title: `当前余额: ${this.data.currentChild.coin_balance || 0} 🪙`,
      icon: 'none',
    });
  },

  // ---- 添加记录 ----
  onAddRecord() {
    this.setData({
      showAddRecord: true,
      recordForm: {
        date: util.formatDate(new Date()),
        rating: 'good',
        comment: '',
        rewards: [],
      },
      newReward: { type: 'reward', description: '', coins: '' },
    });
  },

  onCloseAddRecord() {
    this.setData({ showAddRecord: false });
  },

  onDateChange(e) {
    this.setData({ 'recordForm.date': e.detail.value });
  },

  onRatingChange(e) {
    this.setData({ 'recordForm.rating': e.currentTarget.dataset.rating });
  },

  onCommentInput(e) {
    this.setData({ 'recordForm.comment': e.detail.value });
  },

  // ---- 奖惩明细操作 ----
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

  onAddRewardEntry() {
    const { newReward, recordForm } = this.data;
    console.log('onAddRewardEntry newReward:', newReward);

    const description = (newReward.description || '').trim();
    const coinsStr = String(newReward.coins || '').trim();
    console.log('description:', JSON.stringify(description), 'coinsStr:', JSON.stringify(coinsStr));

    if (!description || coinsStr === '') {
      wx.showToast({ title: '请填写完整', icon: 'none' });
      return;
    }

    const coins = parseInt(coinsStr);
    if (isNaN(coins)) {
      wx.showToast({ title: '币数格式错误', icon: 'none' });
      return;
    }

    const rewards = [...recordForm.rewards, {
      type: newReward.type,
      description,
      coins,
    }];

    this.setData({
      'recordForm.rewards': rewards,
      newReward: { type: 'reward', description: '', coins: '' },
    });
  },

  onDeleteRewardEntry(e) {
    const index = e.currentTarget.dataset.index;
    const rewards = [...this.data.recordForm.rewards];
    rewards.splice(index, 1);
    this.setData({ 'recordForm.rewards': rewards });
  },

  // ---- 提交记录 ----
  async onSubmitRecord() {
    const { recordForm, currentChild } = this.data;
    
    if (!recordForm.date || !recordForm.rating) {
      wx.showToast({ title: '请选择日期和评价', icon: 'none' });
      return;
    }
    
    try {
      wx.showLoading({ title: '保存中...' });
      
      await api.createPerformance(currentChild.id, {
        record_date: recordForm.date,
        overall_rating: recordForm.rating,
        comment: recordForm.comment || null,
        reward_records: recordForm.rewards,
      });
      
      wx.hideLoading();
      wx.showToast({ title: '保存成功', icon: 'success' });
      
      this.setData({ showAddRecord: false });
      this.loadChildren(); // 刷新余额
    } catch (err) {
      wx.hideLoading();
      console.error('保存记录失败', err);
    }
  },
});
