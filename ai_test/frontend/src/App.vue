<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>

</script>

<style>
#app {
  height: 100%;
  min-height: 100vh;
  width: 100vw;
}

/*
 * 修复 el-table fixed 列与其他列重叠显示的问题
 * Element Plus 的 sticky 固定列设置了 background: inherit，继承了 tr 的透明背景
 * 必须用硬编码颜色 + !important 强制覆盖
 */

/* 1. 强制 tr 行背景为不透明白色，使 inherit 生效 */
.el-table .el-table__body tr {
  background-color: #fff !important;
}

/* 2. 斑马纹行 */
.el-table--striped .el-table__body tr.el-table__row--striped {
  background-color: #fafafa !important;
}

/* 3. hover 行 */
.el-table .el-table__body tr:hover,
.el-table .el-table__body tr.hover-row {
  background-color: #f5f7fa !important;
}

/* 4. 直接设置固定列 td 背景（双重保险） */
.el-table__body-wrapper tr td.el-table-fixed-column--right,
.el-table__body-wrapper tr td.el-table-fixed-column--left {
  background-color: inherit !important;
  background: inherit !important;
}

/* 5. 表头固定列 */
.el-table__header-wrapper tr th.el-table-fixed-column--right,
.el-table__header-wrapper tr th.el-table-fixed-column--left {
  background-color: #f5f7fa !important;
  background: #f5f7fa !important;
}
</style>
