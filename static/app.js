// Laya Decision Engine Client-Side Controller

const PRESETS = {
    billing: {
        state: {
            "subject": "Charged twice on Invoice #90214",
            "body": "Hi, I noticed two identical charges of $149 on my credit card this morning for my monthly plan. Please refund the duplicate transaction ASAP!",
            "sender_tier": "enterprise"
        },
        questions: {
            "intent": {
                "type": "choice",
                "instructions": "What is the primary customer intent?",
                "criteria": ["billing_refund", "account_cancellation", "technical_support", "feature_request", "sales_inquiry"]
            },
            "is_urgent": {
                "type": "noul",
                "instructions": "Is this an urgent issue requiring rapid response?"
            },
            "escalation_risk": {
                "type": "score",
                "instructions": "What is the churn or escalation risk level?",
                "criteria": ["low", "moderate", "high", "critical"]
            }
        }
    },
    security: {
        state: {
            "subject": "URGENT: Suspicious logins detected from unusual IP",
            "body": "We noticed multiple failed password attempts followed by a successful login from an unknown location. Need access revoked immediately!",
            "source": "automated_system_alert"
        },
        questions: {
            "incident_category": {
                "type": "choice",
                "instructions": "What kind of security incident is this?",
                "criteria": ["account_takeover", "phishing", "data_leak", "spam", "false_positive"]
            },
            "requires_immediate_lockout": {
                "type": "noul",
                "instructions": "Should the affected user account be suspended immediately?"
            },
            "severity_score": {
                "type": "score",
                "instructions": "Rate the severity of the threat",
                "criteria": ["p4_minor", "p3_medium", "p2_major", "p1_critical"]
            }
        }
    },
    multilingual: {
        state: {
            "subject": "Impossible de me connecter à mon compte",
            "body": "Bonjour, depuis la mise à jour hier soir, mon mot de passe n'est plus reconnu. Pouvez-vous réinitialiser mes accès s'il vous plaît?",
            "lang": "fr"
        },
        questions: {
            "demande": {
                "type": "choice",
                "instructions": "Quelle est la nature du problème?",
                "criteria": ["reinitialisation_mdp", "probleme_facturation", "annulation", "question_commerciale"]
            },
            "bloquant": {
                "type": "noul",
                "instructions": "Est-ce un problème bloquant pour l'utilisateur?"
            }
        }
    },
    lead: {
        state: {
            "company": "Acme Global Corp",
            "headcount": "2500",
            "message": "We are looking to deploy an automated triage pipeline across 50,000 daily tickets. We need enterprise SLA and HIPAA compliance. Can we schedule a demo this week?",
            "email_domain": "acmeglobal.com"
        },
        questions: {
            "deal_size": {
                "type": "choice",
                "instructions": "Projected deal tier",
                "criteria": ["self_serve", "mid_market", "strategic_enterprise"]
            },
            "high_priority_lead": {
                "type": "noul",
                "instructions": "Is this a qualified high-priority inbound lead?"
            },
            "fit_score": {
                "type": "score",
                "instructions": "Product-market fit score",
                "criteria": ["poor_fit", "possible_fit", "strong_fit", "ideal_customer"]
            }
        }
    }
};

const stateInput = document.getElementById("stateInput");
const questionsInput = document.getElementById("questionsInput");
const runBtn = document.getElementById("runDecisionBtn");
const answersContainer = document.getElementById("answersContainer");
const latencyBadge = document.getElementById("latencyBadge");
const latencyValue = document.getElementById("latencyValue");
const routingBadge = document.getElementById("routingBadge");
const routingModelName = document.getElementById("routingModelName");
const rawJsonViewer = document.getElementById("rawJsonViewer");
const deviceBadge = document.getElementById("deviceBadge");
const deviceText = document.getElementById("deviceText");

// Benchmark elements
const runBenchmarkBtn = document.getElementById("runBenchmarkBtn");
const benchmarkModal = document.getElementById("benchmarkModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const benchmarkLoading = document.getElementById("benchmarkLoading");
const benchmarkResults = document.getElementById("benchmarkResults");
const bmAvg = document.getElementById("bmAvg");
const bmP95 = document.getElementById("bmP95");
const bmMin = document.getElementById("bmMin");
const bmMax = document.getElementById("bmMax");

// Load preset
function loadPreset(key) {
    const p = PRESETS[key];
    if (!p) return;

    stateInput.value = JSON.stringify(p.state, null, 2);
    questionsInput.value = JSON.stringify(p.questions, null, 2);

    document.querySelectorAll(".preset-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.preset === key);
    });
}

// Check Server Status
async function checkStatus() {
    try {
        const res = await fetch("/api/status");
        if (res.ok) {
            const data = await res.json();
            deviceText.textContent = `Device: ${data.device.toUpperCase()}${data.gpu_name ? ' (' + data.gpu_name + ')' : ''}`;
            deviceBadge.classList.remove("hidden");
        }
    } catch (e) {
        console.warn("Status check failed", e);
    }
}

// Render Decisions
function renderDecisions(result, latencyMs) {
    latencyValue.textContent = `${latencyMs} ms`;
    latencyBadge.classList.remove("hidden");
    latencyBadge.classList.add("flex");

    const routing = result.routing || {};
    if (routing.model) {
        routingModelName.textContent = routing.model;
        routingBadge.classList.remove("hidden");
    }

    rawJsonViewer.textContent = JSON.stringify(result, null, 2);

    const answers = result.answers || {};
    const questionKeys = Object.keys(answers);

    if (questionKeys.length === 0) {
        answersContainer.innerHTML = `
            <div class="text-center py-8 text-slate-500">
                <i class="fa-solid fa-triangle-exclamation text-amber-500 text-2xl mb-2"></i>
                <p class="text-sm">No answers returned by model.</p>
            </div>
        `;
        return;
    }

    let cardsHtml = `<div class="space-y-3.5">`;

    for (const key of questionKeys) {
        const item = answers[key] || {};
        let valueHtml = "";
        let badgeHtml = "";
        let confidenceHtml = "";

        if (item.type === "choice" || "choice" in item) {
            badgeHtml = `<span class="px-2 py-0.5 text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded">Choice</span>`;
            valueHtml = `<span class="text-base font-bold text-white">${item.choice}</span>`;
            
            const confVal = item.answer_confidence !== undefined ? item.answer_confidence : item.confidence;
            if (confVal !== undefined && confVal !== null) {
                const pct = Math.round(confVal * 100);
                confidenceHtml = `
                    <div class="mt-2.5">
                        <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                            <span>Calibrated Confidence</span>
                            <span class="font-bold text-indigo-300">${pct}%</span>
                        </div>
                        <div class="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                            <div class="bg-gradient-to-r from-indigo-500 to-indigo-400 h-2 rounded-full transition-all duration-500" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }
        } else if (item.type === "noul" || "noul" in item || "value" in item) {
            const prob = item.noul !== undefined ? item.noul : (item.value ? 1.0 : 0.0);
            const isTrue = prob >= 0.5;
            badgeHtml = `<span class="px-2 py-0.5 text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">Noul (Boolean)</span>`;
            valueHtml = `
                <div class="flex items-center space-x-2">
                    <span class="w-3 h-3 rounded-full ${isTrue ? 'bg-emerald-400' : 'bg-rose-400'}"></span>
                    <span class="text-base font-bold ${isTrue ? 'text-emerald-400' : 'text-rose-400'}">${isTrue ? 'YES (True)' : 'NO (False)'}</span>
                </div>
            `;
            
            const pct = Math.round(prob * 100);
            confidenceHtml = `
                <div class="mt-2.5">
                    <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                        <span>Likelihood</span>
                        <span class="font-bold ${isTrue ? 'text-emerald-300' : 'text-rose-300'}">${pct}%</span>
                    </div>
                    <div class="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                        <div class="bg-gradient-to-r ${isTrue ? 'from-emerald-500 to-teal-400' : 'from-rose-500 to-amber-500'} h-2 rounded-full transition-all duration-500" style="width: ${pct}%"></div>
                    </div>
                </div>
            `;
        } else if (item.type === "score" || "score" in item) {
            badgeHtml = `<span class="px-2 py-0.5 text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded">Score</span>`;
            const scoreVal = typeof item.score === "number" ? item.score.toFixed(2) : item.score;
            let levelStr = "";
            if (item.legend && typeof item.score === "number") {
                const closestIdx = String(Math.round(item.score));
                if (item.legend[closestIdx]) {
                    levelStr = ` (${item.legend[closestIdx]})`;
                }
            }
            valueHtml = `
                <div class="flex items-center space-x-2">
                    <span class="text-base font-bold text-amber-300">${scoreVal}</span>
                    <span class="text-xs text-slate-400 font-normal">${levelStr}</span>
                </div>
            `;
        } else {
            valueHtml = `<pre class="text-xs text-slate-300 font-mono">${JSON.stringify(item, null, 2)}</pre>`;
        }

        cardsHtml += `
            <div class="decision-card bg-slate-950/70 border border-slate-800 rounded-xl p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-mono text-xs font-semibold text-slate-300 tracking-wide">${key}</span>
                    ${badgeHtml}
                </div>
                <div>${valueHtml}</div>
                ${confidenceHtml}
            </div>
        `;
    }

    cardsHtml += `</div>`;
    answersContainer.innerHTML = cardsHtml;
}

// Execute Prediction
async function executePrediction() {
    let state, questions;
    try {
        state = JSON.parse(stateInput.value);
    } catch (e) {
        alert("Invalid State JSON: " + e.message);
        return;
    }

    try {
        questions = JSON.parse(questionsInput.value);
    } catch (e) {
        alert("Invalid Questions JSON: " + e.message);
        return;
    }

    runBtn.disabled = true;
    runBtn.innerHTML = `<i class="fa-solid fa-spinner animate-spin text-xs"></i> <span>Evaluating...</span>`;
    answersContainer.innerHTML = `
        <div class="text-center py-12 text-slate-400">
            <i class="fa-solid fa-bolt-lightning text-3xl text-indigo-400 animate-pulse mb-3"></i>
            <p class="text-sm font-medium">Forward pass in progress...</p>
        </div>
    `;

    try {
        const response = await fetch("/api/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ state, questions })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Server error");
        }

        renderDecisions(data.result, data.latency_ms);
    } catch (err) {
        answersContainer.innerHTML = `
            <div class="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs">
                <div class="font-bold mb-1 flex items-center space-x-1.5">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <span>Prediction Error</span>
                </div>
                <div>${err.message}</div>
            </div>
        `;
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = `<i class="fa-solid fa-play text-xs"></i> <span>Run Decision</span>`;
    }
}

// Run Speed Benchmark
async function executeBenchmark() {
    benchmarkModal.classList.remove("hidden");
    benchmarkLoading.classList.remove("hidden");
    benchmarkResults.classList.add("hidden");

    try {
        const res = await fetch("/api/benchmark?iterations=15", { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Benchmark failed");

        bmAvg.textContent = `${data.avg_ms} ms`;
        bmP95.textContent = `${data.p95_ms} ms`;
        bmMin.textContent = `${data.min_ms} ms`;
        bmMax.textContent = `${data.max_ms} ms`;

        benchmarkLoading.classList.add("hidden");
        benchmarkResults.classList.remove("hidden");
    } catch (e) {
        alert("Benchmark error: " + e.message);
        benchmarkModal.classList.add("hidden");
    }
}

// Event Listeners
document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => loadPreset(btn.dataset.preset));
});

runBtn.addEventListener("click", executePrediction);
runBenchmarkBtn.addEventListener("click", executeBenchmark);
closeModalBtn.addEventListener("click", () => benchmarkModal.classList.add("hidden"));
benchmarkModal.addEventListener("click", (e) => {
    if (e.target === benchmarkModal) benchmarkModal.classList.add("hidden");
});

// Init
window.addEventListener("DOMContentLoaded", () => {
    loadPreset("billing");
    checkStatus();
});
