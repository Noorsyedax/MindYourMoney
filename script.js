/* ═══════════════════════════════════════════════════════
   MindYourMoney – script.js
   Full quiz engine, API communication, result rendering
═══════════════════════════════════════════════════════ */

// ─── API BASE URL ─────────────────────────────────────────
// Always talk directly to Flask, regardless of which port
// the frontend is being served from (Live Server, etc.)
const API_BASE = 'http://127.0.0.1:5000';

// ─── PARTICLE BACKGROUND ─────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  let W, H, particles;

  const COLORS = ['#00ffa3', '#3c8eff', '#ff3cac', '#ffe600'];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function createParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.5 + 0.3,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      alpha: Math.random() * 0.5 + 0.1,
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: 90 }, createParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (const p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.fill();
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resize);
  init();
  draw();
})();

// ─── SVG GRADIENT (for confidence ring) ──────────────────
document.body.insertAdjacentHTML('beforeend', `
  <svg id="defs-svg" aria-hidden="true">
    <defs>
      <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%"   stop-color="#00ffa3"/>
        <stop offset="100%" stop-color="#3c8eff"/>
      </linearGradient>
    </defs>
  </svg>
`);

// ─── STATE ────────────────────────────────────────────────
let questions   = [];
let current     = 0;
let answers     = new Array(12).fill(null);   // selected option index per Q

// ─── SCREEN MANAGER ──────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => {
    if (s.id !== id) {
      s.classList.add('exit');
      setTimeout(() => { s.classList.remove('active', 'exit'); }, 350);
    }
  });
  setTimeout(() => {
    const target = document.getElementById(id);
    target.classList.add('active');
    target.scrollTop = 0;
  }, 200);
}

// ─── FETCH QUESTIONS ──────────────────────────────────────
async function fetchQuestions() {
  try {
    const res = await fetch(`${API_BASE}/questions`);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    questions = await res.json();
  } catch {
    // Fallback: embed a minimal set so the UI still works offline
    questions = generateFallbackQuestions();
  }
}

function generateFallbackQuestions() {
  // Same questions, client-side fallback
  return [
    { id:1,  text:"Payday just hit. First move?", options:[{text:"Instantly split it across savings goals"},{text:"Transfer rent/bills, spend the rest freely"},{text:"Yolo into crypto before I think twice"},{text:"Build a colour-coded budget spreadsheet"}] },
    { id:2,  text:"A friend begs you to co-sign a loan. You:", options:[{text:"Hard no — my credit is sacred"},{text:"Sure, they're my bestie!"},{text:"Only after reviewing their finances"},{text:"What's a co-sign? Just Venmo me later"}] },
    { id:3,  text:"You spot a 48-hour flash sale on something you've wanted:", options:[{text:"Buy immediately — this discount is fate"},{text:"Check if it fits the monthly budget first"},{text:"Skip it — I'm saving for something bigger"},{text:"Put it on the credit card, figure it out later"}] },
    { id:4,  text:"Your emergency fund should cover:", options:[{text:"6–12 months of expenses, minimum"},{text:"1–2 months is plenty, life is short"},{text:"Emergency? That's what credit cards are for"},{text:"I have a detailed tiered emergency plan"}] },
    { id:5,  text:"A hot stock tip lands in your group chat. You:", options:[{text:"Research it for weeks before deciding"},{text:"Drop 30% of savings in immediately"},{text:"Ignore it — index funds only"},{text:"Invest a small 'fun money' slice only"}] },
    { id:6,  text:"How do you feel about debt?", options:[{text:"Disgusting. Paid everything off ASAP."},{text:"Leverage is a tool — use it strategically"},{text:"It's just part of life, whatever"},{text:"Terrifying, I avoid it at all costs"}] },
    { id:7,  text:"Spending app shows you went 20% over budget last month:", options:[{text:"Immediately cut luxuries for 30 days"},{text:"Adjust the budget to match reality ¯\\_(ツ)_/¯"},{text:"Spiral into financial guilt for a week"},{text:"Conduct a full audit and recalibrate"}] },
    { id:8,  text:"You receive ₹50,000 unexpectedly. It goes to:", options:[{text:"High-yield savings, obviously"},{text:"That vacation I've been delaying"},{text:"Aggressive stock/crypto portfolio"},{text:"Split: 40% invest, 40% save, 20% treat"}] },
    { id:9,  text:"Retirement planning – where are you at?", options:[{text:"Maxing out every retirement account since 22"},{text:"I'll think about it when I'm older"},{text:"My startup is my retirement plan 😎"},{text:"I have a 20-year financial roadmap"}] },
    { id:10, text:"Your vibe when eating out with friends:", options:[{text:"Split exact amounts using an app"},{text:"I'll get this one, you get next"},{text:"I already budgeted ₹800 for dining this week"},{text:"Order everything, we only live once"}] },
    { id:11, text:"Someone offers a higher-paying but unstable job. You:", options:[{text:"Take it — calculated risk for the reward"},{text:"Stay comfortable, stability > everything"},{text:"Jump in immediately, burn that bridge later"},{text:"Negotiate a trial period with a fallback plan"}] },
    { id:12, text:"Your honest relationship with budgeting apps:", options:[{text:"I built my own custom tracking system in Notion"},{text:"Downloaded 4, used none"},{text:"I use one religiously every single day"},{text:"My bank balance IS my budget tracker"}] },
  ];
}

// ─── BUILD DOT TRAIL ──────────────────────────────────────
function buildDotTrail() {
  const trail = document.getElementById('dotTrail');
  trail.innerHTML = '';
  for (let i = 0; i < 12; i++) {
    const d = document.createElement('div');
    d.className = 'dot' + (i < current ? ' answered' : '') + (i === current ? ' current' : '');
    trail.appendChild(d);
  }
}

// ─── RENDER QUESTION ─────────────────────────────────────
function renderQuestion(idx, direction = 'right') {
  const card  = document.getElementById('questionCard');
  const q     = questions[idx];

  // Slide out
  card.classList.add(direction === 'right' ? 'slide-out' : 'slide-in');

  setTimeout(() => {
    document.getElementById('qCurrent').textContent = idx + 1;
    document.getElementById('qLabel').textContent   = `Question ${String(idx + 1).padStart(2, '0')}`;
    document.getElementById('qText').textContent    = q.text;

    const grid = document.getElementById('optionsGrid');
    grid.innerHTML = '';
    q.options.forEach((opt, oi) => {
      const btn = document.createElement('button');
      btn.className = 'option-btn' + (answers[idx] === oi ? ' selected' : '');
      btn.innerHTML = `<span class="opt-text">${opt.text}</span>`;
      btn.addEventListener('click', () => selectOption(idx, oi));
      grid.appendChild(btn);
    });

    // Progress
    const pct = Math.round((idx / 12) * 100);
    document.getElementById('progressBar').style.width = pct + '%';
    document.getElementById('progressPct').textContent = pct;

    // Nav buttons
    document.getElementById('prevBtn').disabled = idx === 0;
    document.getElementById('nextBtn').disabled = answers[idx] === null;
    document.getElementById('nextBtn').textContent = idx === 11 ? 'Finish 🚀' : 'Next →';

    // Dots
    buildDotTrail();

    // Slide back in from opposite side
    card.classList.remove('slide-out', 'slide-in');
    card.classList.add(direction === 'right' ? 'slide-in' : 'slide-out');
    // Force reflow
    void card.offsetWidth;
    card.classList.remove('slide-in', 'slide-out');
  }, 220);
}

// ─── SELECT OPTION ────────────────────────────────────────
function selectOption(qIdx, optIdx) {
  answers[qIdx] = optIdx;

  document.querySelectorAll('.option-btn').forEach((btn, i) => {
    btn.classList.toggle('selected', i === optIdx);
  });

  document.getElementById('nextBtn').disabled = false;

  // Live trait preview
  updateTraitMini();
}

function updateTraitMini() {
  const answered = answers.filter(a => a !== null).length;
  if (answered === 0) return;
  const mini = document.getElementById('traitMini');
  mini.textContent = `${answered}/12 answered`;
}

// ─── LOADING SEQUENCE ─────────────────────────────────────
const LOADING_MSGS = [
  'Mapping your financial DNA…',
  'Running trait regression…',
  'Calculating risk vectors…',
  'Detecting spending patterns…',
  'Building your profile…',
];

async function runLoadingSequence(apiPromise) {
  showScreen('loading');

  const fill  = document.getElementById('loadingBarFill');
  const msg   = document.getElementById('loadingMsg');
  const steps = document.querySelectorAll('.step');

  let msgIdx = 0;
  let pct    = 0;

  const msgInterval = setInterval(() => {
    msgIdx = (msgIdx + 1) % LOADING_MSGS.length;
    msg.style.opacity = '0';
    setTimeout(() => {
      msg.textContent  = LOADING_MSGS[msgIdx];
      msg.style.opacity = '1';
    }, 200);
  }, 900);

  // Fake progress that slows near 90% until API returns
  const prog = setInterval(() => {
    if (pct < 85) { pct += Math.random() * 6; fill.style.width = pct + '%'; }
    // Advance step indicators
    if (pct > 25 && !steps[1].classList.contains('done')) { steps[0].classList.replace('active','done'); steps[1].classList.add('active'); }
    if (pct > 50 && !steps[2].classList.contains('done')) { steps[1].classList.replace('active','done'); steps[2].classList.add('active'); }
    if (pct > 72 && !steps[3].classList.contains('done')) { steps[2].classList.replace('active','done'); steps[3].classList.add('active'); }
  }, 200);

  // Await actual API call
  const result = await apiPromise;

  clearInterval(msgInterval);
  clearInterval(prog);

  // Finish bar
  fill.style.width = '100%';
  steps[3].classList.replace('active', 'done');

  await wait(600);
  return result;
}

// ─── API CALL ─────────────────────────────────────────────
async function analyzeAnswers() {
  const payload = { answers };
  const promise = fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(r => r.json());

  const result = await runLoadingSequence(promise);
  return result;
}

// ─── RENDER RESULT ────────────────────────────────────────
function renderResult(data) {
  document.getElementById('resultEmoji').textContent  = data.emoji || '💸';
  document.getElementById('resultTitle').textContent  = data.personality;
  document.getElementById('resultDesc').textContent   = data.description;

  // Risk badge
  const riskEl = document.getElementById('riskBadge');
  riskEl.textContent = data.risk_level;
  const riskClass = data.risk_level.toLowerCase().replace(/\s+/g, '-').replace('to-medium','');
  riskEl.className = 'risk-badge ' + (riskClass === 'low' ? 'low' : riskClass === 'medium' ? 'medium' : riskClass.includes('very') ? 'very-high' : 'high');

  // Pattern badge
  const patternEl = document.getElementById('patternBadge');
  patternEl.textContent = data.behavior_pattern;
  patternEl.className   = 'pattern-badge ' + (data.pattern_color || 'info');
  document.getElementById('patternDesc').textContent = data.pattern_description;

  // Confidence ring
  const conf   = data.confidence_score;
  const circum = 314;
  const offset = circum - (conf / 100) * circum;
  const ringFill = document.getElementById('ringFill');
  ringFill.style.strokeDashoffset = circum; // reset
  document.getElementById('confidenceNumber').textContent = '0%';

  setTimeout(() => {
    ringFill.style.strokeDashoffset = offset;
    animateCount(document.getElementById('confidenceNumber'), 0, conf, 1500, v => v.toFixed(1) + '%');
  }, 300);

  // Trait bars
  const barsEl = document.getElementById('traitBars');
  barsEl.innerHTML = '';
  const traitMap = {
    'Saver':      'saver',
    'Spender':    'spender',
    'Risk Taker': 'risk-taker',
    'Planner':    'planner',
  };
  const traitEmoji = { 'Saver':'🔐', 'Spender':'💳', 'Risk Taker':'🎲', 'Planner':'📐' };

  Object.entries(data.trait_percentages).forEach(([name, pct], i) => {
    const row = document.createElement('div');
    row.className = 'trait-row';
    row.style.animationDelay = (i * 0.1) + 's';
    row.innerHTML = `
      <span class="trait-name">${traitEmoji[name] || ''} ${name}</span>
      <div class="trait-track"><div class="trait-fill ${traitMap[name] || ''}" style="width:0%" data-target="${pct}"></div></div>
      <span class="trait-pct" data-target="${pct}">0%</span>
    `;
    barsEl.appendChild(row);
  });

  // Animate bars
  setTimeout(() => {
    document.querySelectorAll('.trait-fill').forEach(fill => {
      fill.style.width = fill.dataset.target + '%';
    });
    document.querySelectorAll('.trait-pct').forEach(pct => {
      animateCount(pct, 0, parseFloat(pct.dataset.target), 1200, v => v.toFixed(1) + '%');
    });
  }, 400);

  // Advice
  document.getElementById('adviceText').textContent = data.loan_advice;

  showScreen('result');
}

// ─── UTILS ────────────────────────────────────────────────
function wait(ms) { return new Promise(res => setTimeout(res, ms)); }

function animateCount(el, from, to, duration, formatter) {
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    el.textContent = formatter(from + (to - from) * ease);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ─── RESET ────────────────────────────────────────────────
function reset() {
  current = 0;
  answers = new Array(12).fill(null);
  // Reset loading bar + steps
  document.getElementById('loadingBarFill').style.width = '0%';
  document.querySelectorAll('.step').forEach((s, i) => {
    s.className = 'step' + (i === 0 ? ' active' : '');
  });
  document.getElementById('loadingMsg').textContent = 'Mapping your financial DNA…';
}

// ─── EVENT LISTENERS ──────────────────────────────────────
document.getElementById('startBtn').addEventListener('click', async () => {
  if (questions.length === 0) await fetchQuestions();
  reset();
  showScreen('quiz');
  setTimeout(() => renderQuestion(0), 250);
});

document.getElementById('prevBtn').addEventListener('click', () => {
  if (current > 0) {
    current--;
    renderQuestion(current, 'left');
  }
});

document.getElementById('nextBtn').addEventListener('click', async () => {
  if (answers[current] === null) return;

  if (current < 11) {
    current++;
    renderQuestion(current, 'right');
  } else {
    // All answered — submit
    try {
      const result = await analyzeAnswers();
      if (result.error) throw new Error(result.error);
      renderResult(result);
    } catch (err) {
      console.error('Analysis failed:', err);
      // Show a friendly error
      showScreen('landing');
      alert('Hmm, something went wrong. Make sure the Flask server is running on localhost:5000!');
    }
  }
});

document.getElementById('playAgainBtn').addEventListener('click', () => {
  reset();
  showScreen('quiz');
  setTimeout(() => renderQuestion(0), 250);
});

// ─── INIT ─────────────────────────────────────────────────
(async function init() {
  await fetchQuestions();
})();
