import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import type { TreeNode } from '../types';

interface Props {
  treeData: Record<string, any> | null;
  highlightedNodes?: Set<string>;
  highlightedPaths?: string[][];
  navigationStep?: {
    current_node: string;
    selected_children: string[];
    rejected_children: string[];
  } | null;
  width?: number;
  height?: number;
}

function jsonToTreeNode(data: any, name = 'ROOT'): TreeNode {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const children: TreeNode[] = Object.entries(data).map(([k, v]) => jsonToTreeNode(v, k));
    const hasSubtree = children.some((c) => c.children && c.children.length > 0);
    return { name, children, isLeaf: !hasSubtree && children.every((c) => c.isLeaf !== false) };
  }
  return { name, value: data, isLeaf: true };
}

export default function TreeVisualization({
  treeData,
  highlightedNodes,
  highlightedPaths,
  navigationStep,
  width = 900,
  height = 600,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width, height });

  const getNodeColor = useCallback(
    (d: d3.HierarchyNode<TreeNode>) => {
      const nodeName = d.data.name;
      if (navigationStep) {
        if (nodeName === navigationStep.current_node) return '#1677ff';
        if (navigationStep.selected_children.includes(nodeName)) return '#52c41a';
        if (navigationStep.rejected_children.includes(nodeName)) return '#ff4d4f';
      }
      if (highlightedNodes?.has(nodeName)) return '#faad14';
      if (d.data.isLeaf) return '#8c8c8c';
      return '#1677ff';
    },
    [navigationStep, highlightedNodes],
  );

  useEffect(() => {
    if (!treeData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const root = d3.hierarchy(jsonToTreeNode(treeData));
    const treeLayout = d3.tree<TreeNode>().nodeSize([24, 200]);
    treeLayout(root);

    const allNodes = root.descendants();
    const xExtent = d3.extent(allNodes, (d) => d.x) as [number, number];
    const yExtent = d3.extent(allNodes, (d) => d.y) as [number, number];
    const treeW = (yExtent[1] - yExtent[0]) + 300;
    const treeH = (xExtent[1] - xExtent[0]) + 100;
    setDimensions({ width: Math.max(width, treeW), height: Math.max(height, treeH) });

    const g = svg
      .attr('width', Math.max(width, treeW))
      .attr('height', Math.max(height, treeH))
      .append('g')
      .attr('transform', `translate(80, ${-xExtent[0] + 40})`);

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 3])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);
    svg.call(zoom.transform, d3.zoomIdentity.translate(80, -xExtent[0] + 40));

    g.selectAll('.link')
      .data(root.links())
      .join('path')
      .attr('class', 'link')
      .attr('d', (d: any) =>
        `M${d.source.y},${d.source.x}C${(d.source.y + d.target.y) / 2},${d.source.x} ${(d.source.y + d.target.y) / 2},${d.target.x} ${d.target.y},${d.target.x}`,
      )
      .attr('fill', 'none')
      .attr('stroke', '#d9d9d9')
      .attr('stroke-width', 1.5);

    const node = g
      .selectAll('.node')
      .data(root.descendants())
      .join('g')
      .attr('class', 'node')
      .attr('transform', (d: any) => `translate(${d.y},${d.x})`);

    node
      .append('circle')
      .attr('r', 5)
      .attr('fill', (d: any) => getNodeColor(d))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);

    node
      .append('text')
      .attr('dy', '0.31em')
      .attr('x', (d: any) => (d.children ? -10 : 10))
      .attr('text-anchor', (d: any) => (d.children ? 'end' : 'start'))
      .attr('font-size', '11px')
      .attr('fill', '#333')
      .text((d: any) => {
        const label = String(d.data.name);
        return label.length > 35 ? label.slice(0, 35) + '…' : label;
      });

  }, [treeData, getNodeColor, width, height, highlightedNodes, highlightedPaths, navigationStep]);

  if (!treeData) {
    return (
      <div
        style={{
          width: '100%',
          height: 300,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '2px dashed #d9d9d9',
          borderRadius: 8,
          color: '#bfbfbf',
          boxSizing: 'border-box',
        }}
      >
        No tree data available
      </div>
    );
  }

  return (
    <div style={{ overflow: 'auto', border: '1px solid #f0f0f0', borderRadius: 8, background: '#fafafa' }}>
      <svg ref={svgRef} width={dimensions.width} height={dimensions.height} />
    </div>
  );
}
