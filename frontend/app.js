const API_URL = "http://localhost:8000";

const templates = {
    dashboard: `
        <div class="max-w-4xl">
            <div class="dashboard-hero">
                <h2>CMPDI AI Reporting Platform</h2>
                <p>A comprehensive AI solution for exploring, querying, and analyzing corporate annual reports and mining data using RAG and ML pipelines.</p>
            </div>
            <div class="card-grid" id="stats-grid">
                <div class="stat-card" style="align-items:center; justify-content:center; min-height: 140px;">
                    <div class="spinner-lg"></div>
                </div>
                <div class="stat-card" style="align-items:center; justify-content:center; min-height: 140px;">
                    <div class="skeleton" style="width:60px; height:36px; margin-bottom:8px;"></div>
                    <div class="skeleton" style="width:100px; height:14px;"></div>
                </div>
                <div class="stat-card" style="align-items:center; justify-content:center; min-height: 140px;">
                    <div class="skeleton" style="width:60px; height:36px; margin-bottom:8px;"></div>
                    <div class="skeleton" style="width:100px; height:14px;"></div>
                </div>
            </div>
        </div>
    `,
    ask: `
        <div class="max-w-4xl">
            <div class="panel">
                <div class="panel-header">
                    <i data-lucide="search"></i> Ask a Question
                </div>
                <div class="panel-body">
                    <div class="input-group">
                        <input type="text" id="ask-input" class="text-input" placeholder="e.g. 'What were the key safety initiatives in 2021?'" onkeypress="if(event.key === 'Enter') handleAsk()">
                        <button class="btn" id="ask-btn" onclick="handleAsk()">
                            <i data-lucide="sparkles"></i> Ask AI
                        </button>
                    </div>
                </div>
            </div>
            <div id="ask-result"></div>
        </div>
    `,
    summarize: `
        <div class="max-w-4xl">
            <div class="panel">
                <div class="panel-header">
                    <i data-lucide="file-text"></i> Document Summarization
                </div>
                <div class="panel-body">
                    <div class="file-upload-area" onclick="document.getElementById('sum-file').click()">
                        <input type="file" id="sum-file" class="file-input-hidden" accept=".pdf,.csv,.xlsx" onchange="updateFileName(this)">
                        <i data-lucide="upload-cloud"></i>
                        <h4>Click or drag to upload document</h4>
                        <p id="file-name-display">Supports PDF, CSV, XLSX</p>
                    </div>
                    <div style="margin-top: 1.25rem; text-align: right;">
                        <button class="btn" id="sum-btn" onclick="handleSummarize()">
                            <i data-lucide="zap"></i> Generate Summary
                        </button>
                    </div>
                </div>
            </div>
            <div id="sum-result"></div>
        </div>
    `,
    topics: `
        <div class="max-w-4xl" id="topics-result">
            <div class="panel">
                <div class="loading-state">
                    <div class="spinner-lg"></div>
                    <p>Running ML Topic Models&hellip; (may take 15–20s)</p>
                </div>
            </div>
        </div>
    `,
    report: `
        <div class="max-w-4xl">
            <div class="panel">
                <div class="panel-header">
                    <i data-lucide="file-bar-chart-2"></i> Automated Report Generation
                </div>
                <div class="panel-body">
                    <div class="input-group">
                        <select id="report-file" class="select-input">
                            <option value="CMPDIL_Annual_Report_2021-22.pdf">CMPDIL Annual Report 2021-22</option>
                            <option value="CMPDIL_Annual_Report_2022-23.pdf">CMPDIL Annual Report 2022-23</option>
                            <option value="Annual Report.pdf">General Annual Report (15MB)</option>
                            <option value="chap3(Policy Initiatives and Reform Measures)AnnualReport2022en.pdf">Chapter 3: Policy Initiatives (2022)</option>
                            <option value="chap7(Public Sector Undertakings)AnnualReport2021pdf.pdf">Chapter 7: Public Sector Undertakings (2021)</option>
                            <option value="chap8(Coal and Lignite Production)AnnualReport2021en.pdf">Chapter 8: Coal &amp; Lignite Production (2021)</option>
                            <option value="chap10(Research and Development)AnnualReport2021en.pdf">Chapter 10: Research and Development (2021)</option>
                            <option value="chap13(Safety in Coal Mines)AnnualReport2021en.pdf">Chapter 13: Safety in Coal Mines (2021)</option>
                            <option value="chap16(Empowerment of Women)AnnualReport2021en.pdf">Chapter 16: Empowerment of Women (2021)</option>
                            <option value="(Empowerment of Women)chap17AnnualReport2022en.pdf">Chapter 17: Empowerment of Women (2022)</option>
                            <option value="chap17(Vigilance)AnnualReport2021en.pdf">Chapter 17: Vigilance (2021)</option>
                            <option value="cdchap1.xlsx">Coal Distribution Data Chapter 1 (Excel)</option>
                            <option value="cdchap2.xlsx">Coal Distribution Data Chapter 2 (Excel)</option>
                        </select>
                        <button class="btn" id="report-btn" onclick="handleReport()">
                            <i data-lucide="settings"></i> Generate Report
                        </button>
                    </div>
                </div>
            </div>
            <div id="report-result"></div>
        </div>
    `
};

const appContent = document.getElementById("app-content");
const pageTitle = document.getElementById("page-title");

function navigate(view, title) {
    // Update active state
    document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.querySelector(`[data-target="${view}"]`);
    if(activeBtn) activeBtn.classList.add("active");
    
    // Update Title and Content
    pageTitle.textContent = title || activeBtn.textContent.trim();
    appContent.innerHTML = templates[view];
    lucide.createIcons();
    
    // Load data if needed
    if (view === "dashboard") loadDashboard();
    if (view === "topics") loadTopics();
}

document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
        const target = e.currentTarget;
        navigate(target.dataset.target, target.textContent.trim());
    });
});

function updateFileName(input) {
    const display = document.getElementById("file-name-display");
    if (input.files && input.files[0]) {
        display.textContent = input.files[0].name;
        display.style.color = "var(--accent)";
        display.style.fontWeight = "600";
    } else {
        display.textContent = "Supports PDF, CSV, XLSX";
        display.style.color = "var(--text-muted)";
        display.style.fontWeight = "normal";
    }
}

// Load Dashboard Stats
async function loadDashboard() {
    try {
        const res = await fetch(`${API_URL}/stats`);
        const data = await res.json();
        document.getElementById("stats-grid").innerHTML = `
            <div class="stat-card">
                <div class="stat-icon"><i data-lucide="files"></i></div>
                <h3>${data.total_documents || 0}</h3>
                <p>Documents Indexed</p>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i data-lucide="database"></i></div>
                <h3>${data.total_chunks || 0}</h3>
                <p>Semantic Chunks Available</p>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i data-lucide="cpu"></i></div>
                <h3>3</h3>
                <p>Active ML Modules</p>
            </div>
        `;
        lucide.createIcons();
    } catch (e) {
        document.getElementById("stats-grid").innerHTML = `<div class="stat-card"><p>Failed to load stats.</p></div>`;
    }
}

// Handle Ask
async function handleAsk() {
    const input = document.getElementById("ask-input").value;
    if (!input) return;
    
    const btn = document.getElementById("ask-btn");
    const resultBox = document.getElementById("ask-result");
    
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner-sm"></div> Thinking...`;

    // Show skeleton loading state
    resultBox.innerHTML = `
        <div class="answer-card">
            <div class="skeleton" style="height:16px; width:80%; margin-bottom:10px;"></div>
            <div class="skeleton" style="height:16px; width:95%; margin-bottom:10px;"></div>
            <div class="skeleton" style="height:16px; width:70%; margin-bottom:10px;"></div>
            <div class="skeleton" style="height:16px; width:88%;"></div>
        </div>
    `;
    
    try {
        const res = await fetch(`${API_URL}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: input })
        });
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || "Unknown error occurred");
        }
        
        let sourcesHtml = "";
        if (data.sources && data.sources.length > 0) {
            sourcesHtml = `
                <span class="sources-label">Citations</span>
                <div class="sources-list">
                    ${data.sources.map(s => `<span class="chip"><i data-lucide="file-text"></i> ${s}</span>`).join('')}
                </div>
            `;
        }
            
        const answerText = data.answer || "No response provided by the API.";
        resultBox.innerHTML = `
            <div class="answer-card">
                <div class="markdown-content">${marked.parse(answerText)}</div>
                <div class="meta-footer">
                    ${sourcesHtml}
                    <div class="badges-row">
                        <span class="badge badge-time">
                            <i data-lucide="timer"></i> ${data.elapsed_seconds ? data.elapsed_seconds.toFixed(2) : '0.00'}s
                        </span>
                        ${data.provider ? `
                            <span class="badge badge-provider">
                                <i data-lucide="bot"></i> ${data.provider}
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        lucide.createIcons();
    } catch (e) {
        resultBox.innerHTML = `
            <div class="answer-card error-state">
                <i data-lucide="alert-circle"></i> Error: ${e.message}
            </div>`;
        lucide.createIcons();
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="sparkles"></i> Ask AI`;
        lucide.createIcons();
    }
}

// Handle Summarize
async function handleSummarize() {
    const fileInput = document.getElementById("sum-file");
    if (!fileInput.files[0]) return alert("Please select a file to upload first.");
    
    const btn = document.getElementById("sum-btn");
    const resultBox = document.getElementById("sum-result");
    
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner-sm"></div> Processing...`;

    // Show skeleton
    resultBox.innerHTML = `
        <div class="answer-card">
            <div class="skeleton" style="height:20px; width:200px; margin-bottom:16px;"></div>
            <div class="skeleton" style="height:14px; width:100%; margin-bottom:8px;"></div>
            <div class="skeleton" style="height:14px; width:95%; margin-bottom:8px;"></div>
            <div class="skeleton" style="height:14px; width:88%; margin-bottom:8px;"></div>
            <div class="skeleton" style="height:14px; width:92%;"></div>
        </div>
    `;
    
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    
    try {
        const res = await fetch(`${API_URL}/summarize`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if(!res.ok) throw new Error(data.detail);
        
        const summaryText = data.summary || "No summary provided by the API.";
        resultBox.innerHTML = `
            <div class="answer-card">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:1rem; border-bottom:1px solid var(--border-soft); padding-bottom:1rem;">
                    <i data-lucide="align-left" style="color:var(--accent); width:16px; height:16px;"></i>
                    <h2 style="font-size:0.9375rem; font-weight:700; letter-spacing:-0.01em;">Executive Summary</h2>
                </div>
                <div class="markdown-content">${marked.parse(summaryText)}</div>
            </div>
        `;
        lucide.createIcons();
    } catch (e) {
        resultBox.innerHTML = `
            <div class="answer-card error-state">
                <i data-lucide="alert-circle"></i> Error: ${e.message}
            </div>`;
        lucide.createIcons();
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="zap"></i> Generate Summary`;
        lucide.createIcons();
    }
}

// Load Topics
async function loadTopics() {
    try {
        const res = await fetch(`${API_URL}/topics`);
        const data = await res.json();
        
        let topicsHtml = data.map((t, i) => `
            <div class="topic-item">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">
                    <h4><i data-lucide="folder-kanban"></i> ${t.name}</h4>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:6px;">
                    ${t.keywords.map(kw => `<span class="chip" style="background:var(--accent-dim); border:1px solid var(--accent-border); color:var(--accent); font-size:0.75rem;">${kw}</span>`).join('')}
                </div>
            </div>
        `).join('');
        
        document.getElementById("topics-result").innerHTML = `
            <div class="topic-grid">
                <div class="img-panel">
                    <div class="section-heading"><i data-lucide="image"></i> Word Cloud</div>
                    <p style="font-size:0.8125rem; color:var(--text-muted); margin-bottom:1rem; line-height:1.5;">
                        A visual representation of the most frequent terms found across all uploaded documents.
                    </p>
                    <img src="${API_URL}/wordcloud?t=${Date.now()}" alt="Word Cloud">
                </div>
                <div>
                    <div class="section-heading"><i data-lucide="list"></i> Semantic Clusters</div>
                    <p style="font-size:0.875rem; color:var(--text-secondary); margin-bottom:1.5rem; line-height:1.6;">
                        These clusters are automatically generated by the ML model. The algorithm reads all documents, 
                        finds underlying themes based on context, and groups them into these specific topics.
                    </p>
                    <div class="topic-list">${topicsHtml}</div>
                </div>
            </div>
        `;
        lucide.createIcons();
    } catch (e) {
        document.getElementById("topics-result").innerHTML = `
            <div class="panel">
                <div class="error-state" style="margin:1.5rem;">
                    <i data-lucide="alert-triangle"></i> Failed to load topics. ${e.message}
                </div>
            </div>
        `;
        lucide.createIcons();
    }
}

// Handle Report
async function handleReport() {
    const filename = document.getElementById("report-file").value;
    const btn = document.getElementById("report-btn");
    const resultBox = document.getElementById("report-result");
    
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner-sm"></div> Generating...`;

    // Show skeleton
    resultBox.innerHTML = `
        <div class="answer-card" style="margin-top:0;">
            <div class="skeleton" style="height:24px; width:240px; margin-bottom:20px;"></div>
            <div class="report-preview">
                <div class="report-section">
                    <div class="skeleton" style="height:14px; width:120px; margin-bottom:16px;"></div>
                    <div class="skeleton" style="height:12px; width:80%; margin-bottom:8px;"></div>
                    <div class="skeleton" style="height:12px; width:60%;"></div>
                </div>
                <div class="report-section">
                    <div class="skeleton" style="height:14px; width:140px; margin-bottom:16px;"></div>
                    <div class="skeleton" style="height:12px; width:100%; margin-bottom:6px;"></div>
                    <div class="skeleton" style="height:12px; width:95%; margin-bottom:6px;"></div>
                    <div class="skeleton" style="height:12px; width:88%;"></div>
                </div>
            </div>
        </div>
    `;
    
    try {
        const res = await fetch(`${API_URL}/generate-report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename })
        });
        const data = await res.json();
        if(!res.ok) throw new Error(data.detail);
        
        const f = data.fields;
        
        let metricsHtml = "";
        if (f.operational_and_production_metrics && f.operational_and_production_metrics.length > 0) {
            metricsHtml = `
                <table class="data-table">
                    <tr><th>Metric</th><th>Value</th><th>Unit</th></tr>
                    ${f.operational_and_production_metrics.map(m => `<tr><td>${m.metric_name || '-'}</td><td>${m.value || '-'}</td><td>${m.unit || '-'}</td></tr>`).join('')}
                </table>
            `;
        } else {
            metricsHtml = "<p style='color:var(--text-muted); font-size:0.875rem;'>No operational metrics extracted from this file.</p>";
        }

        resultBox.innerHTML = `
            <div class="answer-card" style="margin-top: 0;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; padding-bottom:1.25rem; border-bottom:1px solid var(--border-soft);">
                    <h2 style="font-size:1rem; font-weight:700; margin:0; display:flex; align-items:center; gap:8px; letter-spacing:-0.02em;">
                        <i data-lucide="check-circle-2" style="color:#059669; width:18px; height:18px;"></i> Extraction Complete
                    </h2>
                    <a href="${API_URL}/download-report/${data.filename}" download class="btn">
                        <i data-lucide="download"></i> Download .docx Report
                    </a>
                </div>
                
                <div class="report-preview">
                    <div class="report-section">
                        <h3><i data-lucide="building"></i> Company Info</h3>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
                            <p style="font-size:0.875rem;"><strong>Subsidiary:</strong> ${f.subsidiary_name || 'N/A'}</p>
                            <p style="font-size:0.875rem;"><strong>Year:</strong> ${f.report_year || 'N/A'}</p>
                        </div>
                    </div>
                    
                    <div class="report-section">
                        <h3><i data-lucide="file-text"></i> Executive Summary</h3>
                        <p style="color:var(--text-secondary); font-size:0.875rem; line-height:1.7;">${f.executive_summary || 'N/A'}</p>
                    </div>
                    
                    <div class="report-section">
                        <h3><i data-lucide="bar-chart-3"></i> Operational Metrics</h3>
                        ${metricsHtml}
                    </div>
                </div>
            </div>
        `;
        lucide.createIcons();
    } catch (e) {
        resultBox.innerHTML = `
            <div class="answer-card error-state" style="margin-top:0;">
                <i data-lucide="alert-circle"></i> Error: ${e.message}
            </div>`;
        lucide.createIcons();
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="settings"></i> Generate Report`;
        lucide.createIcons();
    }
}

// Init
navigate("dashboard", "Dashboard");
lucide.createIcons();
