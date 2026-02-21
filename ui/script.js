// DOM Elements
const networkContainer = document.getElementById('mynetwork');
const simulateBtn = document.getElementById('simulateBtn');
const resetBtn = document.getElementById('resetBtn');
const statusText = document.getElementById('statusText');
const statusPanel = document.getElementById('statusPanel');
const reportContainer = document.getElementById('reportContainer');
const emptyState = document.getElementById('emptyState');

// Global Network Reference
let network = null;
let nodes = new vis.DataSet();
let edges = new vis.DataSet();
let rawMapData = null;

// Mock the architecture_map.json since browsers block local file loading via fetch usually without local server
// BUT, if served via Python HTTP server, we can fetch it. Let's try fetching, else fallback to mock.
async function loadArchitectureMap() {
    try {
        const res = await fetch('../examples/architecture_map.json');
        if (!res.ok) throw new Error("Could not fetch file");
        rawMapData = await res.json();
    } catch (e) {
        console.warn("Using inline fallback data. Run `python -m http.server` at project root to fetch the real JSON.");
        rawMapData = {
            "src/auth.py": ["src/user_service.py", "api/routes.py"],
            "src/database.py": ["src/auth.py", "src/user_service.py", "src/item_service.py"],
            "api/routes.py": ["frontend/app.js"],
            "src/user_service.py": ["api/routes.py"]
        };
    }
    renderGraph();
    updateStatus("안전 (Safe)", "blue");
}

function renderGraph() {
    nodes.clear();
    edges.clear();

    const nodeSet = new Set();
    const edgeList = [];

    // Parse the adjacency list
    Object.keys(rawMapData).forEach(source => {
        nodeSet.add(source);
        rawMapData[source].forEach(target => {
            nodeSet.add(target);
            edgeList.push({ from: source, to: target });
        });
    });

    // Add Nodes
    Array.from(nodeSet).forEach((nodeId, idx) => {
        nodes.add({
            id: nodeId,
            label: nodeId.split('/').pop(), // Basename
            title: nodeId, // Hover text
            color: { background: "#3b82f6", border: "#1d4ed8" }, // Blue
            font: { color: "#ffffff" },
            shape: "box",
            margin: 10,
        });
    });

    // Add Edges
    edgeList.forEach((edge, idx) => {
        edges.add({
            id: `edge_${idx}`,
            from: edge.from,
            to: edge.to,
            arrows: "to",
            color: { color: "#9ca3af" }
        });
    });

    const data = { nodes, edges };
    const options = {
        interaction: { hover: true },
        physics: {
            hierarchicalRepulsion: { nodeDistance: 150 },
            solver: "hierarchicalRepulsion"
        },
        layout: {
            hierarchical: {
                direction: "LR", // Left to Right
                sortMethod: "directed"
            }
        }
    };

    network = new vis.Network(networkContainer, data, options);
}

// Simulation Logic
simulateBtn.addEventListener('click', () => {
    const targetFile = "src/auth.py";

    // 1. Highlight the target node
    if (nodes.get(targetFile)) {
        nodes.update({
            id: targetFile,
            color: { background: "#dc2626", border: "#991b1b" }, // Red
            font: { size: 16 }
        });
    }

    // 2. Find and Highlight Blast Radius (Dependencies)
    const impactedNodes = rawMapData[targetFile] || [];
    impactedNodes.forEach(nodeId => {
        nodes.update({
            id: nodeId,
            color: { background: "#fb923c", border: "#f97316" }, // Orange
        });
    });

    // Color Edges
    impactedNodes.forEach((nodeId) => {
        const edgeId = edges.get().find(e => e.from === targetFile && e.to === nodeId)?.id;
        if (edgeId) {
            edges.update({ id: edgeId, color: { color: "#ef4444", highlight: "#ef4444" }, width: 2 });
        }
    });

    // 3. Optional: further cascading impacts (e.g. user_service -> routes)
    // For demo simplicity, we just manually mark routes since logic is simple
    const cascadeTarget = "api/routes.py";
    nodes.update({ id: cascadeTarget, color: { background: "#fb923c", border: "#f97316" } });
    edges.update({ id: edges.get().find(e => e.from === "src/user_service.py" && e.to === cascadeTarget)?.id, color: { color: "#ef4444" }, width: 2 });

    nodes.update({ id: "frontend/app.js", color: { background: "#fb923c", border: "#f97316" } });

    // 4. Update UI statuses
    updateStatus("⚠️ High Risk (위험)", "red");
    emptyState.classList.add('hidden');
    reportContainer.classList.remove('hidden');
    reportContainer.innerHTML = generateMockReportText(targetFile);
});

resetBtn.addEventListener('click', () => {
    renderGraph();
    emptyState.classList.remove('hidden');
    reportContainer.classList.add('hidden');
    reportContainer.innerHTML = "";
    updateStatus("안전 (Safe)", "blue");
});

function updateStatus(text, color) {
    statusText.innerText = text;
    statusPanel.className = `bg-white rounded p-4 border-l-4 shadow-sm mb-4 border-${color}-500`;
    statusText.className = `text-lg font-bold text-${color}-600`;
}

function generateMockReportText(target) {
    return `<span class="text-red-600 font-bold"># ⚠️ [IMPACT REPORT] 변경 영향도 분석 리포트</span>

> <b>Target Modified:</b> <span class="bg-gray-200 px-1 rounded">${target}</span>

<b>[AI 아키텍처 스캐너 결과]</b>
해당 모듈은 시스템 내 여러 중요 계층과 연결되어 있습니다. 변경 코드를 분석(git diff)한 결과 심각한 파급이 예상됩니다.

<span class="text-blue-600 font-bold">## 🛠 파급 범위 (Blast Radius)</span>
1. <b>API 계층</b>: <span class="bg-orange-100 text-orange-800 px-1 rounded">api/routes.py</span> 
   - Login Endpoint 파라미터 처리 변경으로 <span class="bg-orange-100 text-orange-800 px-1 rounded">frontend/app.js</span> 연동 실패 감지.
2. <b>서비스 계층</b>: <span class="bg-orange-100 text-orange-800 px-1 rounded">src/user_service.py</span>
   - 내부 데이터 파싱 로직에서 Unhandled Exception 발생 가능성 (95%).

<span class="text-green-600 font-bold">## 💡 AI 권고 사항 (Action Required)</span>
- [ ] DB 스키마 마이그레이션 스크립트를 추가로 작성하세요.
- [ ] 하위 호환성을 보장하는 Fallback 코드를 구현 후 다시 스캔하세요.
- <b>PR 반영 전 담당 리뷰어의 승인이 강제됩니다.</b>
`;
}

// Initial Call
loadArchitectureMap();
