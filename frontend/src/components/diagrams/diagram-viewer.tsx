import { useEffect } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";

const nodeTypes = {
  input: ({ data }: { data: { label: string } }) => (
    <div className="rounded-lg border-2 border-green-500 bg-green-50 px-4 py-2 text-sm font-medium dark:bg-green-950">
      {data.label}
    </div>
  ),
  controller: ({ data }: { data: { label: string } }) => (
    <div className="rounded-lg border-2 border-blue-500 bg-blue-50 px-4 py-2 text-sm font-medium dark:bg-blue-950">
      {data.label}
    </div>
  ),
  default: ({ data }: { data: { label: string } }) => (
    <div className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm dark:border-gray-700 dark:bg-gray-900">
      {data.label}
    </div>
  ),
};

interface DiagramViewerProps {
  diagram: { nodes: Array<{ id: string; label: string; type?: string }>; edges: Array<{ id: string; source: string; target: string; label?: string }> };
  title: string;
}

export function DiagramViewer({ diagram, title }: DiagramViewerProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (diagram?.nodes) {
      setNodes(
        diagram.nodes.map((n, i) => ({
          id: n.id,
          data: { label: n.label },
          position: { x: (i % 4) * 200, y: Math.floor(i / 4) * 100 },
          type: n.type || "default",
        }))
      );
    }
    if (diagram?.edges) {
      setEdges(
        diagram.edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
          animated: true,
        }))
      );
    }
  }, [diagram, setNodes, setEdges]);

  return (
    <div className="h-[500px] w-full rounded-lg border border-gray-200 dark:border-gray-800">
      <p className="border-b border-gray-200 p-3 text-sm font-medium dark:border-gray-800">{title}</p>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
