// ============================================
// 通用工具函数
// ============================================

/**
 * 格式化日期为 YYYY-MM-DD
 */
function formatDate(date) {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 获取某月的天数
 */
function getDaysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

/**
 * 获取某月第一天是周几（0=周日）
 */
function getFirstDayOfMonth(year, month) {
  return new Date(year, month - 1, 1).getDay();
}

/**
 * 生成日历网格数据
 */
function generateCalendarGrid(year, month) {
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);
  
  // 将周日调整为第7天（中国习惯周一开始）
  const startOffset = firstDay === 0 ? 6 : firstDay - 1;
  
  const grid = [];
  
  // 填充上月空白
  for (let i = 0; i < startOffset; i++) {
    grid.push({ day: 0, empty: true });
  }
  
  // 填充本月日期
  for (let day = 1; day <= daysInMonth; day++) {
    grid.push({
      day,
      date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
      empty: false,
      isToday: isToday(year, month, day),
    });
  }
  
  return grid;
}

/**
 * 判断是否是今天
 */
function isToday(year, month, day) {
  const today = new Date();
  return today.getFullYear() === year &&
    today.getMonth() + 1 === month &&
    today.getDate() === day;
}

/**
 * 计算年龄
 */
function calculateAge(birthday) {
  if (!birthday) return '';
  const birth = new Date(birthday);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  return age;
}

/**
 * 性别显示文本
 */
function genderText(gender) {
  const map = { male: '男', female: '女', other: '其他' };
  return map[gender] || '未设置';
}

/**
 * 月份中文名
 */
function monthName(month) {
  const names = ['', '一月', '二月', '三月', '四月', '五月', '六月',
    '七月', '八月', '九月', '十月', '十一月', '十二月'];
  return names[month] || '';
}

module.exports = {
  formatDate,
  getDaysInMonth,
  getFirstDayOfMonth,
  generateCalendarGrid,
  isToday,
  calculateAge,
  genderText,
  monthName,
};
