// 奖励币明细页逻辑
const app = getApp();
const api = require('../../utils/api');

Page({
  data: {
    childId: '',
    childName: '',
    balance: 0,
    transactions: [],
    totalTransactions: 0,
    page: 1,
    pageSize: 20,
    hasMore: true,
    loading: false,
  },

  /**
   * 页面加载时接收儿童 ID，并拉取第一页奖励币明细
   */
  onLoad(options) {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }

    const currentChild = app.globalData.currentChild || {};
    const childId = options.childId || currentChild.id || '';
    this.setData({
      childId,
      childName: currentChild.name || '',
      balance: currentChild.coin_balance || 0,
    });
    this.loadTransactions(true);
  },

  /**
   * 下拉刷新时重新加载第一页，保证余额和流水都是最新数据
   */
  async onPullDownRefresh() {
    await this.loadTransactions(true);
    wx.stopPullDownRefresh();
  },

  /**
   * 上拉触底时加载下一页奖励币流水
   */
  onReachBottom() {
    this.loadTransactions(false);
  },

  /**
   * 加载奖励币交易流水
   * @param {boolean} reset - 是否重置为第一页
   */
  async loadTransactions(reset = false) {
    const { childId, page, pageSize, loading, hasMore, transactions } = this.data;
    if (!childId || loading) return;
    if (!reset && !hasMore) return;

    const nextPage = reset ? 1 : page;
    this.setData({ loading: true });

    try {
      const res = await api.getCoinBalance(childId, nextPage, pageSize);
      const newTransactions = (res.transactions || []).map(item => ({
        ...item,
        typeText: this.getTypeText(item.type, item.amount),
        titleText: this.getTitleText(item.type, item.record_date || item.created_at),
        formattedTime: this.formatDateTime(item.created_at),
      }));
      const mergedTransactions = reset ? newTransactions : transactions.concat(newTransactions);
      const total = res.total_transactions || 0;

      this.setData({
        childName: res.child_name || this.data.childName,
        balance: res.balance || 0,
        transactions: mergedTransactions,
        totalTransactions: total,
        page: nextPage + 1,
        hasMore: mergedTransactions.length < total && newTransactions.length >= pageSize,
      });
    } catch (err) {
      console.error('加载奖励币明细失败', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 根据交易类型展示用户可读的变动标签
   */
  getTypeText(type, amount) {
    if (type === 'earn') return '奖励';
    if (type === 'deduct') return '惩罚';
    if (type === 'redeem') return '兑换';
    return amount >= 0 ? '增加' : '扣除';
  },

  /**
   * 根据交易日期和类型生成标题，description 单独作为备注展示
   */
  getTitleText(type, dateString) {
    const dateText = this.formatDate(dateString);
    if (type === 'earn') return `${dateText} 表现奖励`;
    if (type === 'deduct') return `${dateText} 表现惩罚`;
    if (type === 'redeem') return `${dateText} 兑换奖励`;
    return `${dateText} 奖励币变动`;
  },

  /**
   * 格式化交易日期，用于明细标题
   */
  formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },

  /**
   * 格式化交易时间，展示到分钟即可
   */
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
});
