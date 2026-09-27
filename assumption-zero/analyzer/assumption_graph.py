"""
Assumption Graph

Builds a node/edge graph that connects a SINGLE human assumption (rooted in
a POLICY.md requirement) across every layer that independently encodes it
(frontend, backend, database, tests, resilience). This is the
differentiator: instead of a flat lint-warning list, judges can see that
"every applicant has a surname" is baked into 4 separate places.

Output shape is deliberately simple JSON (nodes + edges) so it can be
rendered by any lightweight graph library (React Flow, etc) in the
dashboard.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.models import Finding


@dataclass
class GraphNode:
    id: str
    label: str
    kind: str  # "requirement" | "frontend" | "backend" | "database" | "tests" | "resilience"
    data: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str


@dataclass
class AssumptionGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.__dict__ for n in self.nodes],
            "edges": [e.__dict__ for e in self.edges],
        }


REQUIREMENT_LABELS = {
    "REQ-1": "Every person has a surname",
    "REQ-2": "Every person has a permanent address",
    "REQ-3": "Every phone number is US-format",
    "REQ-4": "Every submission completes exactly once",
    "REQ-5": "Every name uses Latin characters",
}


def build_graph(findings: list[Finding]) -> AssumptionGraph:
    graph = AssumptionGraph()
    seen_nodes: set[str] = set()

    by_requirement: dict[str, list[Finding]] = {}
    for f in findings:
        by_requirement.setdefault(f.human_requirement, []).append(f)

    for req_id, req_findings in sorted(by_requirement.items()):
        req_node_id = f"req::{req_id}"
        if req_node_id not in seen_nodes:
            graph.nodes.append(
                GraphNode(
                    id=req_node_id,
                    label=REQUIREMENT_LABELS.get(req_id, req_id),
                    kind="requirement",
                    data={"requirement_id": req_id},
                )
            )
            seen_nodes.add(req_node_id)

        for f in req_findings:
            finding_node_id = f"finding::{f.assumption_id}"
            if finding_node_id not in seen_nodes:
                graph.nodes.append(
                    GraphNode(
                        id=finding_node_id,
                        label=f.detected_assumption,
                        kind=f.layer,
                        data=f.to_dict(),
                    )
                )
                seen_nodes.add(finding_node_id)
            graph.edges.append(GraphEdge(source=req_node_id, target=finding_node_id))

    return graph
