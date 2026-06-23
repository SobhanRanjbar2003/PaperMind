'use client';

import 'reactflow/dist/style.css';
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
} from 'reactflow';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslations } from 'next-intl';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Maximize2, Plus, Download, Trash2 } from 'lucide-react';
import type { MindMapResultResponse } from '@/types/api';
import { cn } from '@/lib/utils';

const NODE_HORIZONTAL_GAP = 260;
const NODE_VERTICAL_GAP = 60;

interface MindmapNodeData {
  label: string;
  depth: number;
  onEditRequest: (id: string) => void;
}

// ── Layout ──────────────────────────────────────────────────────────────────
// Simple left-to-right tree layout. We compute a y-offset per node based on
// the order of descendants in a DFS, and an x-offset based on depth.

function layoutTree(data: MindMapResultResponse): {
  positions: Map<string, { x: number; y: number }>;
} {
  const positions = new Map<string, { x: number; y: number }>();

  const childrenByParent = new Map<string | null, string[]>();
  for (const n of data.nodes) {
    const arr = childrenByParent.get(n.parent_id) ?? [];
    arr.push(n.id);
    childrenByParent.set(n.parent_id, arr);
  }

  let cursor = 0;

  function place(id: string, depth: number): number {
    const childIds = childrenByParent.get(id) ?? [];
    if (childIds.length === 0) {
      const y = cursor * NODE_VERTICAL_GAP;
      cursor += 1;
      positions.set(id, { x: depth * NODE_HORIZONTAL_GAP, y });
      return y;
    }
    const childYs = childIds.map((cid) => place(cid, depth + 1));
    const minY = childYs[0] ?? 0;
    const maxY = childYs[childYs.length - 1] ?? 0;
    const y = (minY + maxY) / 2;
    positions.set(id, { x: depth * NODE_HORIZONTAL_GAP, y });
    return y;
  }

  const roots = childrenByParent.get(null) ?? [];
  for (const r of roots) place(r, 0);

  return { positions };
}

// ── Custom node ─────────────────────────────────────────────────────────────

function MindmapNode({ data, selected, id }: NodeProps<MindmapNodeData>) {
  const depthStyles = [
    'bg-primary text-primary-foreground border-primary',
    'bg-card text-card-foreground border-primary/40',
    'bg-card text-card-foreground border-border',
    'bg-card text-muted-foreground border-border',
    'bg-card text-muted-foreground border-border',
  ];
  const styleClass = depthStyles[Math.min(data.depth, depthStyles.length - 1)];
  const size =
    data.depth === 0
      ? 'text-sm font-semibold px-4 py-3 min-w-[180px]'
      : data.depth === 1
        ? 'text-sm font-medium px-3.5 py-2.5 min-w-[150px]'
        : 'text-xs px-3 py-2 min-w-[130px]';

  return (
    <div
      onDoubleClick={(e) => {
        e.stopPropagation();
        data.onEditRequest(id);
      }}
      className={cn(
        'rounded-xl border shadow-sm transition-all max-w-[260px] break-words text-start',
        styleClass,
        size,
        selected && 'ring-2 ring-primary ring-offset-2 ring-offset-background',
      )}
    >
      {data.label}
    </div>
  );
}

const nodeTypes = { mindmap: MindmapNode };

// ── Inner canvas ────────────────────────────────────────────────────────────

function MindmapCanvasInner({
  data,
  onReseed,
}: {
  data: MindMapResultResponse;
  onReseed?: () => void;
}) {
  const t = useTranslations('Mindmap');

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const handleEditRequest = useCallback((id: string) => {
    setEditingId(id);
  }, []);

  const initial = useMemo(() => {
    const { positions } = layoutTree(data);
    const nodes: Node<MindmapNodeData>[] = data.nodes.map((n) => ({
      id: n.id,
      type: 'mindmap',
      position: positions.get(n.id) ?? { x: 0, y: 0 },
      data: { label: n.label, depth: n.depth, onEditRequest: handleEditRequest },
      draggable: true,
    }));
    const edges: Edge[] = data.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: false,
    }));
    return { nodes, edges };
  }, [data, handleEditRequest]);

  const [nodes, setNodes, onNodesChange] = useNodesState<MindmapNodeData>(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);

  useEffect(() => {
    setNodes(initial.nodes);
    setEdges(initial.edges);
  }, [initial, setNodes, setEdges]);

  // Inject edit handler into every node — needed because nodes from initial
  // ship with the latest handler, but we want to keep nodes' onEditRequest
  // stable across renders.
  useEffect(() => {
    setNodes((curr) =>
      curr.map((n) => ({
        ...n,
        data: { ...n.data, onEditRequest: handleEditRequest },
      })),
    );
  }, [handleEditRequest, setNodes]);

  const onConnect = useCallback(
    (conn: Connection) => setEdges((eds) => addEdge({ ...conn, type: 'smoothstep' }, eds)),
    [setEdges],
  );

  const addRootNode = useCallback(() => {
    const id = `local-${Date.now()}`;
    setNodes((nds) => [
      ...nds,
      {
        id,
        type: 'mindmap',
        position: { x: 0, y: nds.length * 8 },
        data: { label: 'New node', depth: 2, onEditRequest: handleEditRequest },
      },
    ]);
    setEditingId(id);
  }, [handleEditRequest, setNodes]);

  const addChildOfSelected = useCallback(() => {
    const selected = nodes.find((n) => n.selected);
    if (!selected) {
      addRootNode();
      return;
    }
    const id = `local-${Date.now()}`;
    const newNode: Node<MindmapNodeData> = {
      id,
      type: 'mindmap',
      position: {
        x: selected.position.x + NODE_HORIZONTAL_GAP,
        y: selected.position.y + NODE_VERTICAL_GAP,
      },
      data: {
        label: 'New child',
        depth: Math.min(selected.data.depth + 1, 4),
        onEditRequest: handleEditRequest,
      },
    };
    setNodes((nds) => [...nds, newNode]);
    setEdges((eds) => [
      ...eds,
      { id: `e-${selected.id}-${id}`, source: selected.id, target: id, type: 'smoothstep' },
    ]);
    setEditingId(id);
  }, [nodes, addRootNode, handleEditRequest, setNodes, setEdges]);

  const deleteSelected = useCallback(() => {
    const selectedIds = new Set(nodes.filter((n) => n.selected).map((n) => n.id));
    if (selectedIds.size === 0) return;
    setNodes((nds) => nds.filter((n) => !selectedIds.has(n.id)));
    setEdges((eds) =>
      eds.filter((e) => !selectedIds.has(e.source) && !selectedIds.has(e.target)),
    );
  }, [nodes, setNodes, setEdges]);

  // Keyboard: Enter to rename, Delete to remove
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (editingId) return;
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      const selected = nodes.find((n) => n.selected);
      if (e.key === 'Enter' && selected) {
        e.preventDefault();
        handleEditRequest(selected.id);
      } else if ((e.key === 'Delete' || e.key === 'Backspace') && selected) {
        e.preventDefault();
        deleteSelected();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [editingId, nodes, deleteSelected, handleEditRequest]);

  // Editing modal
  useEffect(() => {
    if (editingId) {
      const n = nodes.find((x) => x.id === editingId);
      setEditValue(n?.data.label ?? '');
    } else {
      setEditValue('');
    }
  }, [editingId, nodes]);

  const commitEdit = () => {
    if (!editingId) return;
    const label = editValue.trim();
    if (!label) {
      setEditingId(null);
      return;
    }
    setNodes((nds) =>
      nds.map((n) => (n.id === editingId ? { ...n, data: { ...n.data, label } } : n)),
    );
    setEditingId(null);
  };

  const exportJson = () => {
    const payload = {
      title: data.title,
      nodes: nodes.map((n) => ({
        id: n.id,
        label: n.data.label,
        depth: n.data.depth,
        x: n.position.x,
        y: n.position.y,
      })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mindmap-${data.job_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Exported mind map JSON');
  };

  return (
    <div className="relative h-[calc(100vh-20rem)] min-h-[520px] w-full overflow-hidden rounded-2xl border bg-card">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
        deleteKeyCode={null /* handled manually */}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <Controls position="bottom-left" />
        <MiniMap
          pannable
          zoomable
          maskColor="hsl(var(--background) / 0.7)"
          nodeColor={(n) =>
            (n.data as MindmapNodeData).depth === 0
              ? 'hsl(var(--primary))'
              : 'hsl(var(--muted-foreground))'
          }
        />

        <Panel position="top-right" className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={addRootNode}>
            <Plus className="h-3.5 w-3.5" />
            {t('addNode')}
          </Button>
          <Button variant="outline" size="sm" onClick={addChildOfSelected}>
            <Plus className="h-3.5 w-3.5" />
            {t('addChild')}
          </Button>
          <Button variant="outline" size="sm" onClick={deleteSelected}>
            <Trash2 className="h-3.5 w-3.5" />
            {t('deleteNode')}
          </Button>
          <Button variant="outline" size="sm" onClick={exportJson}>
            <Download className="h-3.5 w-3.5" />
            {t('downloadJson')}
          </Button>
          {onReseed ? (
            <Button variant="outline" size="sm" onClick={onReseed}>
              <Maximize2 className="h-3.5 w-3.5" />
              {t('fitView')}
            </Button>
          ) : null}
        </Panel>

        <Panel position="top-left" className="hidden sm:block">
          <div className="rounded-lg border bg-background/80 backdrop-blur px-3 py-2 text-[11px] text-muted-foreground space-y-1 max-w-[260px]">
            <p className="font-medium text-foreground">{t('instructionsTitle')}</p>
            <p>{t('instructionRoot')}</p>
            <p>{t('instructionEdit')}</p>
            <p>{t('instructionDrag')}</p>
          </div>
        </Panel>
      </ReactFlow>

      {editingId ? (
        <div
          className="absolute inset-0 z-10 grid place-items-center bg-black/50 backdrop-blur-sm"
          onClick={() => setEditingId(null)}
        >
          <div
            className="w-full max-w-md rounded-2xl border bg-card p-5 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-display text-base font-semibold">{t('renameNode')}</h3>
            <input
              autoFocus
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') commitEdit();
                if (e.key === 'Escape') setEditingId(null);
              }}
              className="mt-3 h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setEditingId(null)}>
                Cancel
              </Button>
              <Button size="sm" onClick={commitEdit}>
                {t('rename')}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function MindmapCanvas(props: { data: MindMapResultResponse; onReseed?: () => void }) {
  return (
    <ReactFlowProvider>
      <MindmapCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
