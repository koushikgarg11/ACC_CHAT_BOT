/**
 * Analytics Career Connect AI Assistant - Frontend Logic
 */

// App State
const state = {
  activeTab: 'chat',
  conversationHistory: [],
  programs: [],
  documents: [],
  pdfDocuments: [],
  websitePages: [],
  selectedPdfDoc: 'all',
  chatDocFilter: 'all',
  currentDocPagesData: null,
  currentDocPageIndex: 0,
  singleDocActiveTab: 'reader',
  ttsEnabled: false,
  selectedCitation: null,
  activeProvider: 'local'
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  lucide.createIcons();
  await loadPrograms();
  await loadDocuments();
  await loadConfigStatus();
});

// Tab Navigation
function switchTab(tabName) {
  state.activeTab = tabName;

  // View sections
  const views = ['chat', 'programs', 'career-match', 'knowledge'];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === tabName) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  // Desktop Sidebar active classes
  views.forEach(v => {
    const btn = document.getElementById(`tab-btn-${v}`);
    if (btn) {
      if (v === tabName) {
        btn.className = "w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 bg-sky-600/20 text-sky-400 border border-sky-500/30";
      } else {
        btn.className = "w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50";
      }
    }
  });

  // Mobile nav classes
  views.forEach(v => {
    const mbtn = document.getElementById(`m-tab-${v}`);
    if (mbtn) {
      if (v === tabName) {
        mbtn.className = "flex-1 py-2.5 text-center font-medium text-sky-400 border-b-2 border-sky-500";
      } else {
        mbtn.className = "flex-1 py-2.5 text-center font-medium text-slate-400";
      }
    }
  });

  lucide.createIcons();
}

// ----------------------------------------------------
// CHAT FUNCTIONALITY
// ----------------------------------------------------

function onChatDocFilterChange(filterValue) {
  state.chatDocFilter = filterValue;
  const filterSelect = document.getElementById('chat-doc-filter');
  if (filterSelect) {
    filterSelect.value = filterValue;
  }
}

async function handleChatSubmit(e) {
  if (e) e.preventDefault();
  const inputEl = document.getElementById('chat-input');
  const query = inputEl.value.trim();
  if (!query) return;

  inputEl.value = '';
  await submitMessage(query);
}

function sendQuickPrompt(promptText) {
  switchTab('chat');
  submitMessage(promptText);
}

async function submitMessage(query) {
  const chatMessages = document.getElementById('chat-messages');
  const followupContainer = document.getElementById('followup-container');
  const sendBtn = document.getElementById('send-btn');

  // Hide followup pills while answering
  followupContainer.classList.add('hidden');

  // Append User Message Bubble
  appendUserMessage(query);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Append Typing/Thinking Indicator
  const typingId = 'typing-' + Date.now();
  appendTypingIndicator(typingId);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Disable input & button
  sendBtn.disabled = true;

  try {
    const payload = {
      message: query,
      history: state.conversationHistory.slice(-6),
      provider: state.activeProvider
    };

    if (state.chatDocFilter && state.chatDocFilter !== 'all') {
      payload.doc_filter = state.chatDocFilter;
    }

    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    // Remove typing indicator
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    if (data && data.response) {
      // Append AI Response Bubble
      appendAIMessage(data.response, data.citations, data.provider);
      state.conversationHistory.push({ role: 'user', content: query });
      state.conversationHistory.push({ role: 'assistant', content: data.response });

      // Render Suggested Follow-ups
      if (data.suggested_followups && data.suggested_followups.length > 0) {
        renderFollowups(data.suggested_followups);
      }

      // Read aloud if TTS enabled
      if (state.ttsEnabled) {
        speakText(data.response);
      }
    } else {
      appendAIMessage("Sorry, I encountered an issue retrieving the answer. Please try again.", [], "ACC Engine");
    }
  } catch (err) {
    console.error("Chat error:", err);
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    appendAIMessage("Unable to connect to the ACC server. Please ensure the backend is running.", [], "ACC Engine");
  } finally {
    sendBtn.disabled = false;
    chatMessages.scrollTop = chatMessages.scrollHeight;
    lucide.createIcons();
  }
}

function appendUserMessage(text) {
  const chatMessages = document.getElementById('chat-messages');
  const msgEl = document.createElement('div');
  msgEl.className = "flex items-start justify-end gap-3 max-w-3xl ml-auto";
  msgEl.innerHTML = `
    <div class="bg-gradient-to-r from-sky-600 to-blue-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-md text-sm max-w-xl">
      ${escapeHtml(text)}
    </div>
    <div class="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 text-xs font-bold">
      You
    </div>
  `;
  chatMessages.appendChild(msgEl);
}

function appendAIMessage(markdownText, citations = [], provider = "ACC Engine") {
  const chatMessages = document.getElementById('chat-messages');
  const msgEl = document.createElement('div');
  msgEl.className = "flex items-start gap-3.5 max-w-3xl";

  const parsedHtml = marked.parse(markdownText);
  const msgId = 'msg-' + Date.now();

  let citationsHtml = '';
  if (citations && citations.length > 0) {
    citationsHtml = `
      <div class="mt-3.5 pt-3 border-t border-slate-800 flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
        <span class="font-medium text-slate-500 mr-1 flex items-center gap-1">
          <i data-lucide="bookmark" class="w-3.5 h-3.5 text-sky-400"></i> Citations:
        </span>
        ${citations.map((c, i) => `
          <button onclick="openCitationModalByIndex(${i}, '${msgId}')" class="px-2 py-0.5 rounded-md bg-[#0b1329] hover:bg-sky-950/60 border border-slate-700/70 hover:border-sky-500/40 text-[11px] text-sky-300 transition flex items-center gap-1" title="View Source: ${escapeHtml(c.title || c.source_name)}">
            <span>${c.source_type === 'Official Website' ? '🌐' : '📄'} ${escapeHtml(c.source_name.replace('.pdf', ''))}</span>
            ${c.page ? `<span class="text-slate-500">p.${c.page}</span>` : ''}
          </button>
        `).join('')}
      </div>
    `;
  }

  msgEl.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-500 to-blue-600 flex items-center justify-center text-white shrink-0 shadow-md shadow-sky-500/20">
      <i data-lucide="bot" class="w-4 h-4"></i>
    </div>
    <div id="${msgId}" class="flex-1 bg-[#101a36] border border-slate-800/90 rounded-2xl rounded-tl-sm p-4 md:p-5 shadow-lg">
      <div class="prose-custom">
        ${parsedHtml}
      </div>
      ${citationsHtml}
      
      <!-- Footer actions -->
      <div class="mt-3 pt-2 flex items-center justify-between text-[11px] text-slate-500">
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          Generated by ${escapeHtml(provider)}
        </span>
        <div class="flex items-center gap-2">
          <button onclick="copyResponse('${msgId}')" class="hover:text-slate-300 p-1 rounded transition" title="Copy answer">
            <i data-lucide="copy" class="w-3.5 h-3.5"></i>
          </button>
          <button onclick="speakResponse('${msgId}')" class="hover:text-slate-300 p-1 rounded transition" title="Read aloud">
            <i data-lucide="volume-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    </div>
  `;

  // Attach citations data to DOM element
  msgEl.dataset.citations = JSON.stringify(citations);
  chatMessages.appendChild(msgEl);
}

function appendTypingIndicator(id) {
  const chatMessages = document.getElementById('chat-messages');
  const typingEl = document.createElement('div');
  typingEl.id = id;
  typingEl.className = "flex items-start gap-3.5 max-w-xl";
  typingEl.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center shrink-0">
      <i data-lucide="bot" class="w-4 h-4"></i>
    </div>
    <div class="bg-[#101a36] border border-slate-800/90 rounded-2xl rounded-tl-sm px-5 py-4 shadow-lg flex items-center gap-4">
      <span class="text-xs text-sky-400 font-medium">Searching ACC Knowledge Base...</span>
      <div class="dot-flashing"></div>
    </div>
  `;
  chatMessages.appendChild(typingEl);
  lucide.createIcons();
}

function renderFollowups(followups) {
  const container = document.getElementById('followup-container');
  container.innerHTML = `
    <span class="text-xs text-slate-500 font-medium shrink-0 flex items-center gap-1">
      <i data-lucide="compass" class="w-3.5 h-3.5 text-sky-400"></i> Suggested:
    </span>
    ${followups.map(f => `
      <button onclick="sendQuickPrompt('${escapeHtml(f)}')" class="shrink-0 px-3 py-1 rounded-full bg-[#101a36] hover:bg-sky-950/60 border border-slate-700/60 hover:border-sky-500/40 text-xs text-slate-300 hover:text-sky-300 transition">
        ${escapeHtml(f)}
      </button>
    `).join('')}
  `;
  container.classList.remove('hidden');
  lucide.createIcons();
}

function clearChatHistory() {
  if (confirm("Clear current conversation?")) {
    state.conversationHistory = [];
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
      <div class="max-w-3xl mx-auto bg-[#101a36]/80 border border-slate-800/90 rounded-2xl p-5 md:p-6 shadow-xl backdrop-blur">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-400 to-blue-600 flex items-center justify-center text-white shrink-0 shadow-md shadow-sky-500/20">
            <i data-lucide="sparkles" class="w-5 h-5"></i>
          </div>
          <div class="flex-1">
            <h3 class="text-base font-bold text-white">Chat cleared!</h3>
            <p class="text-xs md:text-sm text-slate-300 mt-1 leading-relaxed">
              How can I assist you with Analytics Career Connect programs or documentation today?
            </p>
          </div>
        </div>
      </div>
    `;
    document.getElementById('followup-container').classList.add('hidden');
    lucide.createIcons();
  }
}

function exportChat() {
  if (state.conversationHistory.length === 0) {
    alert("No messages to export yet.");
    return;
  }
  let mdContent = `# Analytics Career Connect - Conversation Transcript\n\n`;
  state.conversationHistory.forEach(msg => {
    mdContent += `### ${msg.role === 'user' ? 'User' : 'ACC AI Assistant'}\n${msg.content}\n\n---\n\n`;
  });

  const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ACC_Chat_${new Date().toISOString().slice(0, 10)}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

function copyResponse(msgId) {
  const el = document.getElementById(msgId);
  if (!el) return;
  const text = el.querySelector('.prose-custom').innerText;
  navigator.clipboard.writeText(text).then(() => {
    alert("Answer copied to clipboard!");
  });
}

// ----------------------------------------------------
// VOICE INPUT & TEXT-TO-SPEECH (TTS)
// ----------------------------------------------------

function toggleTTS() {
  state.ttsEnabled = !state.ttsEnabled;
  const icon = document.getElementById('tts-icon');
  const label = document.getElementById('tts-text');
  if (state.ttsEnabled) {
    icon.setAttribute('data-lucide', 'volume-2');
    label.innerText = 'Voice On';
    alert("Auto voice readout enabled!");
  } else {
    icon.setAttribute('data-lucide', 'volume-x');
    label.innerText = 'Voice Off';
    window.speechSynthesis.cancel();
  }
  lucide.createIcons();
}

function speakText(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const clean = text.replace(/[#*`_~]/g, '');
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

function speakResponse(msgId) {
  const el = document.getElementById(msgId);
  if (!el) return;
  const text = el.querySelector('.prose-custom').innerText;
  speakText(text);
}

function startVoiceInput() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert("Voice input is not supported in this browser. Please use Chrome or Edge.");
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;

  const btn = document.getElementById('voice-input-btn');
  btn.classList.add('text-rose-400', 'animate-pulse');

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const inputEl = document.getElementById('chat-input');
    inputEl.value = transcript;
    btn.classList.remove('text-rose-400', 'animate-pulse');
    submitMessage(transcript);
  };

  recognition.onerror = () => {
    btn.classList.remove('text-rose-400', 'animate-pulse');
  };

  recognition.onend = () => {
    btn.classList.remove('text-rose-400', 'animate-pulse');
  };

  recognition.start();
}

// ----------------------------------------------------
// CITATION SLIDEOVER MODAL
// ----------------------------------------------------

function openCitationModalByIndex(index, msgId) {
  const msgEl = document.getElementById(msgId).closest('[data-citations]');
  if (!msgEl) return;
  const citations = JSON.parse(msgEl.dataset.citations || '[]');
  const citation = citations[index];
  if (!citation) return;

  document.getElementById('modal-citation-title').innerText = citation.title || "Citation Excerpt";
  document.getElementById('modal-citation-source').innerText = citation.source_name + (citation.page ? ` (Page ${citation.page})` : '');
  document.getElementById('modal-citation-badge').innerText = citation.category || citation.source_type;
  document.getElementById('modal-citation-text').innerText = citation.snippet || "No snippet available.";
  
  const linkEl = document.getElementById('modal-citation-link');
  if (citation.url) {
    linkEl.href = citation.url;
    linkEl.classList.remove('hidden');
  } else {
    linkEl.href = "https://analyticscareerconnect.com/";
  }

  document.getElementById('citation-modal').classList.remove('hidden');
}

function closeCitationModal() {
  document.getElementById('citation-modal').classList.add('hidden');
}

// ----------------------------------------------------
// PROGRAMS CATALOG
// ----------------------------------------------------

async function loadPrograms() {
  try {
    const res = await fetch('/api/programs');
    const data = await res.json();
    state.programs = data.programs || [];
    renderPrograms(state.programs);
  } catch (err) {
    console.error("Error loading programs:", err);
  }
}

function filterPrograms(filterType) {
  // Update buttons
  document.querySelectorAll('.prog-filter-btn').forEach(btn => {
    if (btn.dataset.filter === filterType) {
      btn.className = "prog-filter-btn px-3.5 py-1.5 rounded-lg text-xs font-medium bg-sky-600 text-white transition active";
    } else {
      btn.className = "prog-filter-btn px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 transition";
    }
  });

  let filtered = state.programs;
  if (filterType === '2026') {
    filtered = state.programs.filter(p => p.batch.includes('2026') || p.id.includes('2026') || p.id.includes('datayug'));
  } else if (filterType === '2027') {
    filtered = state.programs.filter(p => p.batch.includes('2027') || p.id.includes('2027'));
  } else if (filterType === 'marketing') {
    filtered = state.programs.filter(p => p.id.includes('marketing') || p.id.includes('founder'));
  }

  renderPrograms(filtered);
}

function renderPrograms(programsList) {
  const container = document.getElementById('programs-grid');
  if (!container) return;

  container.innerHTML = programsList.map(prog => `
    <div class="bg-[#101a36] border border-slate-800 hover:border-sky-500/50 rounded-2xl p-6 shadow-xl flex flex-col justify-between transition-all duration-200 group">
      <div>
        <!-- Top Badges -->
        <div class="flex flex-wrap items-center gap-2 mb-3">
          <span class="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            ${escapeHtml(prog.type)}
          </span>
          <span class="px-2.5 py-1 rounded-md text-[11px] font-medium bg-slate-800 text-slate-300">
            Batch: ${escapeHtml(prog.batch)}
          </span>
          ${prog.stipend.includes('Free') || prog.stipend.includes('FREE') ? `
            <span class="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-950/40 text-emerald-400 border border-emerald-500/30">
              100% Free
            </span>
          ` : ''}
        </div>

        <h3 class="text-lg font-bold text-white group-hover:text-sky-300 transition">
          ${escapeHtml(prog.title)}
        </h3>
        
        <p class="text-xs text-slate-300 mt-2 leading-relaxed">
          ${escapeHtml(prog.description)}
        </p>

        <!-- Highlights Bullet Points -->
        <div class="mt-4 space-y-1.5">
          ${(prog.highlights || []).slice(0, 4).map(h => `
            <div class="flex items-start gap-2 text-xs text-slate-300">
              <i data-lucide="check" class="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5"></i>
              <span>${escapeHtml(h)}</span>
            </div>
          `).join('')}
        </div>

        <!-- Key Skills Pills -->
        <div class="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap gap-1.5">
          ${(prog.key_skills || []).map(s => `
            <span class="px-2 py-0.5 rounded bg-[#0b1329] border border-slate-700/60 text-[10px] text-slate-300 font-medium">
              ${escapeHtml(s)}
            </span>
          `).join('')}
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mt-6 pt-4 border-t border-slate-800 flex items-center gap-2.5">
        <a href="${prog.google_form || prog.apply_url}" target="_blank" class="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold text-xs shadow-md shadow-sky-500/20 hover:opacity-95 transition text-center flex items-center justify-center gap-1.5">
          <i data-lucide="send" class="w-3.5 h-3.5"></i>
          <span>Apply Now</span>
        </a>
        <button onclick="sendQuickPrompt('Give me complete details, curriculum, and placement assistance for: ${escapeHtml(prog.title)}')" class="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition flex items-center gap-1.5" title="Ask AI about this">
          <i data-lucide="message-circle" class="w-3.5 h-3.5 text-sky-400"></i>
          <span class="hidden sm:inline">Ask AI</span>
        </button>
      </div>
    </div>
  `).join('');

  lucide.createIcons();
}

// ----------------------------------------------------
// CAREER MATCH CALCULATOR
// ----------------------------------------------------

async function handleCareerMatchSubmit(e) {
  e.preventDefault();
  const year = parseInt(document.getElementById('cm-year').value);
  const level = document.getElementById('cm-level').value;
  const role = document.getElementById('cm-role').value;

  const checkedSkills = Array.from(document.querySelectorAll('input[name="skills"]:checked')).map(cb => cb.value);

  const submitBtn = document.getElementById('cm-submit-btn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Analyzing Profile & Matching Tracks...</span>`;

  try {
    const res = await fetch('/api/career-match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        graduation_year: year,
        current_skills: checkedSkills,
        knowledge_level: level,
        weekly_hours: 20,
        target_role: role
      })
    });

    const data = await res.json();
    renderCareerMatchResult(data);
  } catch (err) {
    console.error("Match error:", err);
    alert("Failed to compute career match. Please try again.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<i data-lucide="calculator" class="w-4 h-4"></i><span>Evaluate My Profile & Recommend Track</span>`;
    lucide.createIcons();
  }
}

function renderCareerMatchResult(data) {
  const resultCard = document.getElementById('cm-result-card');
  const prog = data.recommended_program;
  const gaps = data.skill_gap_analysis;

  resultCard.innerHTML = `
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
      <div>
        <span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-950/40 text-emerald-400 border border-emerald-500/30">
          🎯 Fit Match Score: ${gaps.match_score_percentage}%
        </span>
        <h3 class="text-xl font-bold text-white mt-2">${escapeHtml(data.track_title)}</h3>
        <p class="text-xs text-sky-400 font-medium">${escapeHtml(data.cost_status)}</p>
      </div>
      <a href="${data.apply_url}" target="_blank" class="px-6 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold text-xs shadow-lg shadow-sky-500/25 hover:opacity-95 transition flex items-center justify-center gap-2">
        <i data-lucide="arrow-right-circle" class="w-4 h-4"></i>
        <span>Direct Official Application</span>
      </a>
    </div>

    <!-- Summary & Gaps -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
      <div class="bg-[#0b1329] p-4 rounded-xl border border-slate-800">
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Track Overview</h4>
        <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(data.summary)}</p>
        <p class="text-xs text-slate-400 mt-3"><strong>Duration:</strong> ${escapeHtml(prog.duration)}</p>
      </div>

      <div class="bg-[#0b1329] p-4 rounded-xl border border-slate-800">
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Recommended Skills to Master</h4>
        <div class="flex flex-wrap gap-1.5 mt-2">
          ${gaps.recommended_skills_to_learn.map(s => `
            <span class="px-2.5 py-1 rounded bg-amber-950/40 border border-amber-500/30 text-amber-300 text-xs font-medium">
              + ${escapeHtml(s)}
            </span>
          `).join('')}
        </div>
      </div>
    </div>

    <!-- Tailored Roadmap Steps -->
    <div class="mt-6 pt-6 border-t border-slate-800">
      <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Your Tailored 4-Phase ACC Roadmap</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        ${data.tailored_roadmap.map(r => `
          <div class="p-3.5 rounded-xl bg-[#0b1329] border border-slate-800 flex flex-col justify-between">
            <div>
              <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider">Phase 0${r.step} • ${escapeHtml(r.phase)}</span>
              <p class="text-xs text-slate-300 mt-1.5 leading-relaxed">${escapeHtml(r.goal)}</p>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  resultCard.classList.remove('hidden');
  resultCard.scrollIntoView({ behavior: 'smooth' });
  lucide.createIcons();
}

// ----------------------------------------------------
// KNOWLEDGE BASE & DOCUMENTS HUB
// ----------------------------------------------------

async function loadDocuments() {
  try {
    const res = await fetch('/api/documents');
    const data = await res.json();
    state.pdfDocuments = data.pdf_documents || [];
    state.websitePages = data.website_pages || [];

    // Render All PDFs Grid
    const pdfContainer = document.getElementById('pdf-docs-list');
    if (pdfContainer && state.pdfDocuments) {
      pdfContainer.innerHTML = state.pdfDocuments.map(doc => `
        <div class="bg-[#101a36] border border-slate-800 hover:border-sky-500/40 rounded-xl p-5 flex flex-col justify-between shadow-md transition group">
          <div>
            <div class="flex items-center justify-between text-xs mb-2">
              <span class="px-2 py-0.5 rounded-md font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">${escapeHtml(doc.category)}</span>
              <span class="text-slate-400 text-[11px]">${doc.pages} Pages</span>
            </div>
            <h4 class="text-sm font-bold text-white group-hover:text-sky-300 transition">${escapeHtml(doc.title)}</h4>
            <p class="text-xs text-slate-300 mt-1.5 leading-relaxed">${escapeHtml(doc.description)}</p>
            <div class="mt-2.5 flex items-center gap-2 text-[11px] text-slate-400">
              <span class="font-medium text-slate-300">Target Batch:</span>
              <span>${escapeHtml(doc.target_batch)}</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
            <button onclick="onPdfSelectorChange('${escapeHtml(doc.filename)}')" class="px-3 py-1.5 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 border border-sky-500/30 text-xs text-sky-300 font-medium transition flex items-center gap-1.5">
              <i data-lucide="eye" class="w-3.5 h-3.5"></i>
              <span>Select Single PDF</span>
            </button>
            <button onclick="askAIAboutDocDirect('${escapeHtml(doc.filename)}')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition flex items-center gap-1.5">
              <i data-lucide="message-square" class="w-3.5 h-3.5 text-sky-400"></i>
              <span>Ask AI</span>
            </button>
          </div>
        </div>
      `).join('');
    }

    // Render Website Pages
    const webContainer = document.getElementById('web-pages-list');
    if (webContainer && state.websitePages) {
      webContainer.innerHTML = state.websitePages.map(w => `
        <div class="bg-[#101a36] border border-slate-800 rounded-xl p-3.5 flex flex-col justify-between">
          <div>
            <div class="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
              <i data-lucide="link" class="w-3.5 h-3.5"></i>
              <span>${escapeHtml(w.name)}</span>
            </div>
            <p class="text-xs text-slate-300 mt-1">${escapeHtml(w.topics)}</p>
          </div>
          <div class="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
            <a href="${w.url}" target="_blank" class="text-sky-400 hover:underline flex items-center gap-1">
              <span>Visit Page</span>
              <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
            <button onclick="sendQuickPrompt('What information is on the ACC ${escapeHtml(w.name)} website page?')" class="text-slate-400 hover:text-white">
              Query
            </button>
          </div>
        </div>
      `).join('');
    }

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading documents:", err);
  }
}

// Single PDF Selector Handler
async function onPdfSelectorChange(filename) {
  state.selectedPdfDoc = filename;

  // Update Dropdown
  const selector = document.getElementById('pdf-doc-selector');
  if (selector) selector.value = filename;

  // Update Filter Buttons active state
  document.querySelectorAll('.pdf-filter-btn').forEach(btn => {
    if (btn.dataset.doc === filename) {
      btn.className = "pdf-filter-btn px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 text-white transition active";
    } else {
      btn.className = "pdf-filter-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition";
    }
  });

  const allContainer = document.getElementById('all-pdfs-container');
  const singleContainer = document.getElementById('single-pdf-container');

  if (filename === 'all') {
    if (allContainer) allContainer.classList.remove('hidden');
    if (singleContainer) singleContainer.classList.add('hidden');
  } else {
    if (allContainer) allContainer.classList.add('hidden');
    if (singleContainer) singleContainer.classList.remove('hidden');

    // Find document metadata
    const docMeta = state.pdfDocuments.find(d => d.filename === filename) || {
      title: filename.replace('.pdf', ''),
      filename: filename,
      category: 'Official Document',
      target_batch: 'All',
      pages: 10,
      description: 'Official ACC PDF Documentation.'
    };

    // Update Single PDF Banner
    document.getElementById('single-doc-title').innerText = docMeta.title;
    document.getElementById('single-doc-desc').innerText = docMeta.description;
    document.getElementById('single-doc-category').innerText = docMeta.category;
    document.getElementById('single-doc-batch').innerText = docMeta.target_batch;
    document.getElementById('single-doc-pages').innerText = `${docMeta.pages} Pages`;
    document.getElementById('single-doc-filename').innerText = `File: ${docMeta.filename}`;

    const pdfUrl = `/api/documents/pdf/${encodeURIComponent(filename)}`;
    const openLink = document.getElementById('single-doc-open-link');
    if (openLink) openLink.href = pdfUrl;

    const iframe = document.getElementById('sdoc-iframe');
    if (iframe) iframe.src = pdfUrl;

    // Load Structured Page Data
    await loadSingleDocPages(filename);
  }

  lucide.createIcons();
}

async function loadSingleDocPages(filename) {
  const contentEl = document.getElementById('sdoc-page-content');
  contentEl.innerText = "Loading extracted text from document...";

  try {
    const res = await fetch(`/api/documents/pages/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error("Failed to fetch pages");
    const data = await res.json();
    state.currentDocPagesData = data;
    state.currentDocPageIndex = 0;

    // Update File size
    const sizeBadge = document.getElementById('single-doc-size');
    if (sizeBadge && data.file_size_kb) {
      sizeBadge.innerText = `${data.file_size_kb} KB`;
    }

    // Populate Page Dropdown
    const pageSelect = document.getElementById('sdoc-page-select');
    if (pageSelect && data.pages) {
      pageSelect.innerHTML = data.pages.map(p => `
        <option value="${p.page_number}">Page ${p.page_number}</option>
      `).join('');
    }

    const totalPagesLabel = document.getElementById('sdoc-total-pages-label');
    if (totalPagesLabel) {
      totalPagesLabel.innerText = `of ${data.total_pages}`;
    }

    renderDocPage(0);
  } catch (err) {
    console.error("Error loading single doc pages:", err);
    contentEl.innerText = "Error loading document text. You can view the document via the Live PDF Preview tab.";
  }
}

function renderDocPage(pageIndex) {
  if (!state.currentDocPagesData || !state.currentDocPagesData.pages) return;
  const pages = state.currentDocPagesData.pages;
  if (pageIndex < 0 || pageIndex >= pages.length) return;

  state.currentDocPageIndex = pageIndex;
  const page = pages[pageIndex];

  const contentEl = document.getElementById('sdoc-page-content');
  contentEl.innerText = page.text || "(This page has no extractable text or contains graphical elements)";

  const charLabel = document.getElementById('sdoc-char-count-label');
  if (charLabel) {
    charLabel.innerText = `${page.char_count || 0} Characters`;
  }

  const pageSelect = document.getElementById('sdoc-page-select');
  if (pageSelect) {
    pageSelect.value = page.page_number;
  }

  // Update prev / next buttons
  const prevBtn = document.getElementById('sdoc-prev-btn');
  const nextBtn = document.getElementById('sdoc-next-btn');
  if (prevBtn) prevBtn.disabled = (pageIndex === 0);
  if (nextBtn) nextBtn.disabled = (pageIndex === pages.length - 1);
}

function goToDocPage(pageNum) {
  renderDocPage(pageNum - 1);
}

function prevDocPage() {
  if (state.currentDocPageIndex > 0) {
    renderDocPage(state.currentDocPageIndex - 1);
  }
}

function nextDocPage() {
  if (state.currentDocPagesData && state.currentDocPageIndex < state.currentDocPagesData.pages.length - 1) {
    renderDocPage(state.currentDocPageIndex + 1);
  }
}

function copyCurrentPageText() {
  if (!state.currentDocPagesData || !state.currentDocPagesData.pages) return;
  const page = state.currentDocPagesData.pages[state.currentDocPageIndex];
  if (page && page.text) {
    navigator.clipboard.writeText(page.text).then(() => {
      alert(`Copied Page ${page.page_number} text to clipboard!`);
    });
  }
}

function switchSingleDocTab(tabName) {
  state.singleDocActiveTab = tabName;
  const readerTab = document.getElementById('sdoc-tab-reader');
  const previewTab = document.getElementById('sdoc-tab-preview');
  const readerBtn = document.getElementById('sdoc-tab-btn-reader');
  const previewBtn = document.getElementById('sdoc-tab-btn-preview');

  if (tabName === 'reader') {
    readerTab.classList.remove('hidden');
    previewTab.classList.add('hidden');
    readerBtn.className = "px-5 py-3 text-xs font-semibold text-sky-400 border-b-2 border-sky-500 flex items-center gap-2";
    previewBtn.className = "px-5 py-3 text-xs font-semibold text-slate-400 hover:text-slate-200 flex items-center gap-2";
  } else {
    readerTab.classList.add('hidden');
    previewTab.classList.remove('hidden');
    previewBtn.className = "px-5 py-3 text-xs font-semibold text-sky-400 border-b-2 border-sky-500 flex items-center gap-2";
    readerBtn.className = "px-5 py-3 text-xs font-semibold text-slate-400 hover:text-slate-200 flex items-center gap-2";
  }
  lucide.createIcons();
}

function askAIAboutCurrentSingleDoc(customPrompt) {
  const currentFilename = state.selectedPdfDoc;
  if (!currentFilename || currentFilename === 'all') {
    switchTab('chat');
    return;
  }

  // Set chat filter to this single doc
  state.chatDocFilter = currentFilename;
  const chatFilterSelect = document.getElementById('chat-doc-filter');
  if (chatFilterSelect) chatFilterSelect.value = currentFilename;

  // Switch to chat and submit prompt
  switchTab('chat');
  const prompt = customPrompt || `Summarize the key points, role expectations, and requirements from this document: ${currentFilename}`;
  submitMessage(prompt);
}

function askAIAboutDocDirect(filename) {
  state.chatDocFilter = filename;
  const chatFilterSelect = document.getElementById('chat-doc-filter');
  if (chatFilterSelect) chatFilterSelect.value = filename;

  switchTab('chat');
  submitMessage(`Summarize key points, batch eligibility, and requirements from document: ${filename}`);
}

async function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  alert(`Uploading and indexing "${file.name}" into your session...`);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert(`Success! "${file.name}" indexed (${data.chars_extracted} characters). You can now ask questions about your uploaded file!`);
      
      // Add uploaded file to selectors
      const selector = document.getElementById('pdf-doc-selector');
      if (selector) {
        const opt = document.createElement('option');
        opt.value = file.name;
        opt.innerText = `📄 Custom Upload: ${file.name}`;
        selector.appendChild(opt);
      }

      const chatSelector = document.getElementById('chat-doc-filter');
      if (chatSelector) {
        const copt = document.createElement('option');
        copt.value = file.name;
        copt.innerText = `📄 Uploaded: ${file.name}`;
        chatSelector.appendChild(copt);
      }

      sendQuickPrompt(`Review my uploaded document "${file.name}" against Analytics Career Connect requirements and recommend the best track.`);
    } else {
      alert("Upload failed: " + (data.detail || "Unknown error"));
    }
  } catch (err) {
    console.error("Upload error:", err);
    alert("Failed to upload file.");
  }
}

// ----------------------------------------------------
// SETTINGS & CONFIG
// ----------------------------------------------------

async function loadConfigStatus() {
  try {
    const res = await fetch('/api/config/status');
    const data = await res.json();
    state.activeProvider = data.active_provider || 'local';
    document.getElementById('cfg-provider').value = state.activeProvider;
    
    const label = document.getElementById('engine-status-label');
    if (state.activeProvider === 'local') {
      label.innerText = 'ACC Smart Engine Live';
    } else {
      label.innerText = `${state.activeProvider.toUpperCase()} Cloud Active`;
    }
  } catch (err) {
    console.error("Config status error:", err);
  }
}

function openSettingsModal() {
  document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
  document.getElementById('settings-modal').classList.add('hidden');
}

async function handleSettingsSave(e) {
  e.preventDefault();
  const provider = document.getElementById('cfg-provider').value;
  const geminiKey = document.getElementById('cfg-gemini-key').value;
  const groqKey = document.getElementById('cfg-groq-key').value;
  const openaiKey = document.getElementById('cfg-openai-key').value;

  try {
    const res = await fetch('/api/config/keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        preferred_provider: provider,
        gemini_key: geminiKey || undefined,
        groq_key: groqKey || undefined,
        openai_key: openaiKey || undefined
      })
    });
    const data = await res.json();
    state.activeProvider = provider;
    
    const label = document.getElementById('engine-status-label');
    if (provider === 'local') {
      label.innerText = 'ACC Smart Engine Live';
    } else {
      label.innerText = `${provider.toUpperCase()} Cloud Active`;
    }
    
    closeSettingsModal();
    alert("Settings saved! Active provider is now: " + provider);
  } catch (err) {
    console.error("Save settings error:", err);
    alert("Failed to save settings.");
  }
}

// Helper: Escape HTML
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
