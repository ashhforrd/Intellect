import { useMemo, useState } from 'react'
import { Background, Controls, Handle, Position, ReactFlow, type Node, type NodeProps } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { type ChatGraphEdge, type ChatGraphNode } from './chatGraphStore'

type GraphFlowNode = Node<{ label: string; detail: string; kind: ChatGraphNode['kind'] }, 'chatGraph'>

function ExpandableGraphNode({ data }: NodeProps<GraphFlowNode>) {
  const [expanded, setExpanded] = useState(false)
  return <button className={`chat-graph-node ${data.kind} ${expanded ? 'expanded' : ''}`} type="button" onClick={() => setExpanded(!expanded)} title="Click to expand">
    <Handle type="target" position={Position.Top} />
    <span>{expanded ? data.detail : data.label}</span>
    <Handle type="source" position={Position.Bottom} />
  </button>
}

const nodeTypes = { chatGraph: ExpandableGraphNode }

function positionNodes(items: ChatGraphNode[], edges: ChatGraphEdge[]): GraphFlowNode[] {
  const depth = new Map(items.map((item) => [item.id, 0]))
  const incoming = new Map(items.map((item) => [item.id, 0]))
  const outgoing = new Map(items.map((item) => [item.id, [] as string[]]))
  edges.forEach((edge) => {
    incoming.set(edge.target, (incoming.get(edge.target) || 0) + 1)
    outgoing.get(edge.source)?.push(edge.target)
  })
  const queue = items.filter((item) => incoming.get(item.id) === 0).map((item) => item.id)
  for (const nodeId of queue) {
    for (const targetId of outgoing.get(nodeId) || []) {
      depth.set(targetId, Math.max(depth.get(targetId) || 0, (depth.get(nodeId) || 0) + 1))
      incoming.set(targetId, (incoming.get(targetId) || 1) - 1)
      if (incoming.get(targetId) === 0) queue.push(targetId)
    }
  }
  const layerCounts = new Map<number, number>()
  return items.map((item) => {
    const row = depth.get(item.id) || 0
    const column = layerCounts.get(row) || 0
    layerCounts.set(row, column + 1)
    return {
      id: item.id,
      type: 'chatGraph',
      data: { label: item.label, detail: item.detail || item.label, kind: item.kind },
      position: { x: 50 + column * 270, y: 40 + row * 155 },
    }
  })
}

export function ChatGraph({ nodes, edges }: { nodes: ChatGraphNode[]; edges: ChatGraphEdge[] }) {
  const flowNodes = useMemo(() => positionNodes(nodes, edges), [nodes, edges])
  return <ReactFlow
    nodes={flowNodes}
    edges={edges}
    nodeTypes={nodeTypes}
    fitView
    fitViewOptions={{ padding: 0.2 }}
    minZoom={0.25}
    maxZoom={1.8}
    nodesConnectable={false}
    colorMode="dark"
  >
    <Background color="#343434" gap={22} size={1} />
    <Controls showInteractive={false} />
  </ReactFlow>
}
