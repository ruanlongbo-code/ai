<template>
  <div class="flowchart-container" ref="containerRef">
    <VueFlow
      :nodes="layoutNodes"
      :edges="styledEdges"
      :default-viewport="{ zoom: 0.85, x: 50, y: 30 }"
      :min-zoom="0.3"
      :max-zoom="2"
      fit-view-on-init
      class="vue-flow-wrapper"
    >
      <Background pattern-color="#e8e8e8" :gap="20" />
      <template #node-custom="{ data }">
        <div :class="['custom-node', `node-${data.nodeType}`]">
          <div class="node-label" v-html="data.label.replace(/\\n/g, '<br/>')"></div>
        </div>
      </template>
    </VueFlow>
    <div class="flowchart-legend">
      <span class="legend-item"><i class="dot dot-start"></i>开始</span>
      <span class="legend-item"><i class="dot dot-process"></i>处理</span>
      <span class="legend-item"><i class="dot dot-decision"></i>判断</span>
      <span class="legend-item"><i class="dot dot-warning"></i>异常分支</span>
      <span class="legend-item"><i class="dot dot-error"></i>错误</span>
      <span class="legend-item"><i class="dot dot-end"></i>结束</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import dagre from 'dagre'

const props = defineProps({
  flowchart: {
    type: Object,
    default: () => ({ nodes: [], edges: [] })
  }
})

const nodeWidth = 180
const nodeHeight = 60

function getLayoutedElements(nodes, edges) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 100, marginx: 40, marginy: 40 })

  nodes.forEach((node) => {
    g.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  })
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target)
  })

  dagre.layout(g)

  return nodes.map((node) => {
    const pos = g.node(node.id)
    return {
      ...node,
      position: { x: pos.x - nodeWidth / 2, y: pos.y - nodeHeight / 2 },
    }
  })
}

const layoutNodes = computed(() => {
  if (!props.flowchart?.nodes?.length) return []
  const rawNodes = props.flowchart.nodes.map((n) => ({
    id: n.id,
    type: 'custom',
    data: { label: n.label || '', nodeType: n.type || 'process' },
    position: { x: 0, y: 0 },
  }))
  const rawEdges = (props.flowchart.edges || []).map((e) => ({
    id: `${e.source}-${e.target}`,
    source: e.source,
    target: e.target,
  }))
  return getLayoutedElements(rawNodes, rawEdges)
})

const styledEdges = computed(() => {
  if (!props.flowchart?.edges?.length) return []
  return props.flowchart.edges.map((e) => ({
    id: `${e.source}-${e.target}`,
    source: e.source,
    target: e.target,
    label: e.label || '',
    animated: false,
    style: { stroke: '#8c8c8c', strokeWidth: 1.5 },
    labelStyle: { fontSize: '11px', fill: '#595959' },
    markerEnd: { type: 'arrowclosed', color: '#8c8c8c' },
  }))
})
</script>

<style scoped>
.flowchart-container {
  width: 100%;
  height: 500px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  position: relative;
  background: #fafafa;
}
.vue-flow-wrapper {
  width: 100%;
  height: 100%;
}
.custom-node {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  text-align: center;
  min-width: 140px;
  line-height: 1.4;
  border: 2px solid;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.node-start {
  border-color: #52c41a;
  background: #f6ffed;
  border-radius: 20px;
}
.node-end {
  border-color: #8c8c8c;
  background: #fafafa;
  border-radius: 20px;
}
.node-process {
  border-color: #1890ff;
  background: #e6f7ff;
}
.node-decision {
  border-color: #faad14;
  background: #fffbe6;
  transform: rotate(0deg);
  border-radius: 4px;
  border-style: dashed;
}
.node-warning {
  border-color: #fadb14;
  background: #feffe6;
  border-style: dashed;
}
.node-error {
  border-color: #ff4d4f;
  background: #fff2f0;
  border-style: dashed;
}
.node-label {
  white-space: nowrap;
}
.flowchart-legend {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  gap: 12px;
  background: rgba(255,255,255,0.9);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #595959;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.dot-start { background: #52c41a; }
.dot-process { background: #1890ff; }
.dot-decision { background: #faad14; }
.dot-warning { background: #fadb14; }
.dot-error { background: #ff4d4f; }
.dot-end { background: #8c8c8c; }
</style>
