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

// 역방향 그래프 (BFS 영향 분석용)
let reverseGraph = {};

// 현재 선택된 노드
let selectedNode = null;

// architecture_map.json 로드 — 서버에서 fetch, 실패 시 fallback
async function loadArchitectureMap() {
    try {
        const res = await fetch('../examples/architecture_map.json');
        if (!res.ok) throw new Error("Could not fetch file");
        rawMapData = await res.json();
    } catch (e) {
        console.warn("Using inline fallback data. Run `python -m http.server` at project root to fetch the real JSON.");
        rawMapData = {
            "frontend/app.js": ["frontend/api_client.js", "frontend/renderer.js"],
            "api/routes.py": ["src/auth.py", "src/item_service.py", "src/user_service.py"],
            "src/auth.py": ["src/database.py"],
            "src/item_service.py": ["src/database.py"],
            "src/user_service.py": ["src/auth.py", "src/database.py"],
            "src/database.py": [],
            "frontend/renderer.js": [],
            "frontend/api_client.js": []
        };
    }
    // 역방향 그래프 구축
    reverseGraph = buildReverseGraph(rawMapData);
    renderGraph();
    updateStatus("안전 (Safe)", "blue");
}

// 역방향 그래프 구축: reverse[B] = [A] → B를 import하는 파일이 A
function buildReverseGraph(graph) {
    const reverse = {};
    Object.keys(graph).forEach(src => {
        graph[src].forEach(dep => {
            if (!reverse[dep]) reverse[dep] = [];
            reverse[dep].push(src);
        });
    });
    return reverse;
}

// BFS로 영향 범위 계산
function computeBlastRadius(targetFile) {
    const directImpact = [];
    const indirectImpact = [];
    const impactPaths = {};
    const visited = new Set([targetFile]);
    const queue = [];

    // 1단계: 직접 영향 (targetFile을 import하는 파일)
    const directDeps = reverseGraph[targetFile] || [];
    directDeps.forEach(dep => {
        if (!visited.has(dep)) {
            directImpact.push(dep);
            visited.add(dep);
            queue.push({ node: dep, path: [targetFile, dep] });
            impactPaths[dep] = [targetFile, dep];
        }
    });

    // 2단계 이상: 간접 영향 (연쇄 전파)
    while (queue.length > 0) {
        const { node: current, path } = queue.shift();
        const cascadeDeps = reverseGraph[current] || [];
        cascadeDeps.forEach(dep => {
            if (!visited.has(dep)) {
                indirectImpact.push(dep);
                visited.add(dep);
                const newPath = [...path, dep];
                queue.push({ node: dep, path: newPath });
                impactPaths[dep] = newPath;
            }
        });
    }

    return { directImpact, indirectImpact, impactPaths };
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
    Array.from(nodeSet).forEach((nodeId) => {
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

    // 노드 클릭 이벤트 — 클릭한 노드 기준 BFS 시뮬레이션
    network.on('click', (params) => {
        if (params.nodes.length > 0) {
            const clickedNode = params.nodes[0];
            runSimulation(clickedNode);
        }
    });
}

// 시뮬레이션 실행 — 임의의 노드에 대해 BFS 영향 분석
function runSimulation(targetFile) {
    // 먼저 그래프를 초기 상태로 리셋
    resetNodeColors();
    selectedNode = targetFile;

    const { directImpact, indirectImpact, impactPaths } = computeBlastRadius(targetFile);

    // 1. 변경 대상 노드 — 빨간색
    if (nodes.get(targetFile)) {
        nodes.update({
            id: targetFile,
            color: { background: "#dc2626", border: "#991b1b" },
            font: { size: 16, color: "#ffffff" }
        });
    }

    // 2. 직접 영향 노드 — 주황색
    directImpact.forEach(nodeId => {
        nodes.update({
            id: nodeId,
            color: { background: "#fb923c", border: "#f97316" },
        });
    });

    // 3. 간접 영향 노드 — 노란색
    indirectImpact.forEach(nodeId => {
        nodes.update({
            id: nodeId,
            color: { background: "#facc15", border: "#eab308" },
            font: { color: "#1f2937" }
        });
    });

    // 4. 영향 경로 엣지 하이라이트
    const allImpacted = [...directImpact, ...indirectImpact];
    allImpacted.forEach(nodeId => {
        const path = impactPaths[nodeId];
        if (path) {
            for (let i = 0; i < path.length - 1; i++) {
                const fromNode = path[i];
                const toNode = path[i + 1];
                // 역방향 그래프 기준: toNode가 fromNode를 import → 엣지는 toNode → fromNode
                const edgeId = edges.get().find(e => e.from === toNode && e.to === fromNode)?.id;
                if (edgeId) {
                    edges.update({ id: edgeId, color: { color: "#ef4444", highlight: "#ef4444" }, width: 3 });
                }
            }
        }
    });

    // 5. 위험도 판정
    const totalImpacted = directImpact.length + indirectImpact.length;
    const criticalPatterns = ['auth', 'security', 'database', 'config', 'api/', 'payment', 'migration'];
    const allAffected = [targetFile, ...allImpacted];
    const hasCritical = allAffected.some(f =>
        criticalPatterns.some(p => f.toLowerCase().includes(p))
    );

    let riskLevel, riskIcon;
    if (totalImpacted >= 4 || (totalImpacted >= 2 && hasCritical)) {
        riskLevel = 'High'; riskIcon = '🔴';
    } else if (totalImpacted >= 2 || (totalImpacted >= 1 && hasCritical)) {
        riskLevel = 'Medium'; riskIcon = '🟡';
    } else {
        riskLevel = 'Low'; riskIcon = '🟢';
    }

    // 6. UI 상태 업데이트
    const statusColor = riskLevel === 'High' ? 'red' : riskLevel === 'Medium' ? 'yellow' : 'blue';
    updateStatus(`${riskIcon} ${riskLevel} Risk (${targetFile})`, statusColor);
    emptyState.classList.add('hidden');
    reportContainer.classList.remove('hidden');
    reportContainer.innerHTML = generateDynamicReport(
        targetFile, directImpact, indirectImpact, impactPaths, riskLevel, riskIcon
    );
}

// 노드 색상 초기化
function resetNodeColors() {
    nodes.forEach(node => {
        nodes.update({
            id: node.id,
            color: { background: "#3b82f6", border: "#1d4ed8" },
            font: { size: 14, color: "#ffffff" }
        });
    });
    edges.forEach(edge => {
        edges.update({
            id: edge.id,
            color: { color: "#9ca3af" },
            width: 1
        });
    });
}

// 시뮬레이트 버튼 — 예제 시나리오 (src/auth.py)
simulateBtn.addEventListener('click', () => {
    runSimulation("src/auth.py");
});

resetBtn.addEventListener('click', () => {
    selectedNode = null;
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

function generateDynamicReport(target, directImpact, indirectImpact, impactPaths, riskLevel, riskIcon) {
    const totalImpacted = directImpact.length + indirectImpact.length;

    const reviewMsg = {
        'High': '이번 변경은 배포 전 반드시 통합 테스트(Integration Test)를 거쳐야 합니다.',
        'Medium': '관련 모듈의 단위 테스트를 권장합니다.',
        'Low': '자동 병합 가능한 수준입니다. 일반 리뷰를 진행하세요.',
    };

    let html = `<span class="text-red-600 font-bold"># ${riskIcon} [IMPACT REPORT] 변경 영향도 분석 리포트</span>

> <b>Target Modified:</b> <span class="bg-gray-200 px-1 rounded">${target}</span>

<b>📊 Summary</b>
- <b>영향받는 파일 수</b>: ${totalImpacted}개 (직접 ${directImpact.length}개 + 간접 ${indirectImpact.length}개)
- <b>전체 위험도</b>: ${riskIcon} ${riskLevel}
- <b>리뷰 권장</b>: ${reviewMsg[riskLevel] || ''}
`;

    if (directImpact.length > 0) {
        html += `\n<span class="text-blue-600 font-bold">## 🛠 직접 영향 (Direct Impact)</span>\n`;
        directImpact.forEach((f, i) => {
            html += `${i + 1}. <span class="bg-orange-100 text-orange-800 px-1 rounded">${f}</span>\n`;
        });
    }

    if (indirectImpact.length > 0) {
        html += `\n<span class="text-yellow-600 font-bold">## ⚡ 간접 영향 (Indirect Impact)</span>\n`;
        indirectImpact.forEach((f, i) => {
            html += `${i + 1}. <span class="bg-yellow-100 text-yellow-800 px-1 rounded">${f}</span>\n`;
        });
    }

    if (Object.keys(impactPaths).length > 0) {
        html += `\n<span class="text-green-600 font-bold">## 🔗 영향 전파 경로 (Impact Paths)</span>\n`;
        Object.entries(impactPaths).sort().forEach(([target, path]) => {
            html += `- ${path.map(p => `<code>${p}</code>`).join(' → ')}\n`;
        });
    }

    html += `\n<span class="text-green-600 font-bold">## 💡 조치 권고</span>\n`;
    if (riskLevel === 'High') {
        html += `- 통합 테스트(Integration Test)를 반드시 수행하세요.\n`;
        html += `- <b>PR 반영 전 시니어 리뷰어의 승인을 받으세요.</b>\n`;
    } else if (riskLevel === 'Medium') {
        html += `- 관련 모듈의 단위 테스트를 실행하세요.\n`;
    } else {
        html += `- 자동 병합이 가능한 수준입니다.\n`;
    }

    html += `\n<span class="text-gray-400 text-sm">💡 TIP: 그래프에서 아무 노드를 클릭하면 해당 파일 기준으로 영향 분석이 실행됩니다.</span>`;

    return html;
}

// Initial Call
loadArchitectureMap();
