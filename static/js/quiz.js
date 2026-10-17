/**
 * NPTEL Quizzer - Comprehensive Quiz Engine
 * Supports:
 * - Weekly Assessment Mode (10 questions/week)
 * - Important Questions Bank (50, 100, full bank)
 * - Additional Practice Questions Bank (50, 100, full bank)
 * - Combined Practice Mode (All questions with Question & Option shuffling)
 *
 * Features:
 * - Option shuffling with stable original-key mapping for 100% accurate grading
 * - Instant evaluation on option click with 1-second auto-advance
 * - Right-hand navigator grid with green/red/grey state and active border
 * - Re-attempt capability with accurate non-duplicate scoring
 * - LocalStorage persistence across page reloads
 * - Comprehensive results screen with interactive review filters
 * - Light and Dark theme support
 */

const STORAGE_KEY = "nptel_quizzer_state";
const THEME_KEY = "nptel_theme";

let quizState = {
  mode: "weekly", // "weekly", "important", "additional", "all"
  week: 0,
  requestedCount: 10,
  modeTitle: "Quiz",
  shuffleQuestions: false,
  shuffleOptions: false,
  questions: [],
  currentIndex: 0,
  isFinished: false,
  score: 0,
  startTime: null
};

let autoAdvanceTimer = null;

function clearAutoAdvance() {
  if (autoAdvanceTimer) {
    clearTimeout(autoAdvanceTimer);
    autoAdvanceTimer = null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initQuiz();
});

/* ================= Theme Management ================= */
function initTheme() {
  const toggleBtn = document.getElementById("theme-toggle-btn");
  if (!toggleBtn) return;

  toggleBtn.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem(THEME_KEY, newTheme);
  });
}

/* ================= Quiz Initialization ================= */
async function initQuiz() {
  const urlParams = new URLSearchParams(window.location.search);
  const resume = urlParams.get("resume");

  // Check if we should resume from localStorage
  const savedState = localStorage.getItem(STORAGE_KEY);
  if (resume && savedState) {
    try {
      quizState = JSON.parse(savedState);
      renderQuizHeader();
      renderQuestion();
      renderNavigator();
      updateScoreChips();
      if (quizState.isFinished) {
        showResultsView();
      }
      setupEventListeners();
      return;
    } catch (e) {
      console.error("Failed to parse saved state, loading fresh quiz", e);
    }
  }

  // Load fresh quiz from server
  const mode = urlParams.get("mode") || "weekly";
  const week = parseInt(urlParams.get("week") || "0", 10);
  const count = parseInt(urlParams.get("count") || "50", 10);
  const shuffleQParam = urlParams.get("shuffle_q");
  const shuffleOptParam = urlParams.get("shuffle_opt");

  const shuffleQuestions = shuffleQParam === null ? (mode === "all") : (shuffleQParam === "1" || shuffleQParam === "true");
  const shuffleOptions = shuffleOptParam === null ? (mode === "all") : (shuffleOptParam === "1" || shuffleOptParam === "true");

  quizState.mode = mode;
  quizState.week = week;
  quizState.requestedCount = count;
  quizState.shuffleQuestions = shuffleQuestions;
  quizState.shuffleOptions = shuffleOptions;
  quizState.currentIndex = 0;
  quizState.isFinished = false;
  quizState.score = 0;
  quizState.startTime = Date.now();

  try {
    let apiUrl = "";
    if (mode === "weekly") {
      apiUrl = `/api/questions/weekly/${week}`;
      quizState.modeTitle = `Week ${week} Assessment`;
    } else if (mode === "important") {
      apiUrl = `/api/questions/important?count=${count}`;
      quizState.modeTitle = `Important Questions (${count} Questions)`;
    } else if (mode === "additional") {
      apiUrl = `/api/questions/additional?count=${count}`;
      quizState.modeTitle = `Additional Practice Questions (${count} Questions)`;
    } else if (mode === "all") {
      apiUrl = `/api/questions/all?shuffle_q=${shuffleQuestions ? 1 : 0}`;
      quizState.modeTitle = `Practice All Questions`;
    } else {
      // Fallback
      apiUrl = `/api/questions/weekly/0`;
      quizState.modeTitle = `Week 0 Assessment`;
    }

    const res = await fetch(apiUrl);
    const data = await res.json();

    if (data.status !== "success" || !data.questions || data.questions.length === 0) {
      alert("Failed to load questions. Returning to home.");
      window.location.href = "/";
      return;
    }

    if (mode === "all") {
      quizState.modeTitle = `Practice All Questions (${data.total} Questions)`;
    } else if (count >= data.total && (mode === "important" || mode === "additional")) {
      quizState.modeTitle = `${data.mode_title} (Full Bank • ${data.total} Qs)`;
    }

    // Initialize questions with option mapping
    quizState.questions = data.questions.map((q, idx) => {
      const origKeys = Object.keys(q.options).sort();
      let displayOptions = [];

      if (shuffleOptions) {
        // Randomize the order of options while assigning visual keys A, B, C, D
        const shuffledOrigKeys = [...origKeys].sort(() => Math.random() - 0.5);
        displayOptions = shuffledOrigKeys.map((origKey, i) => ({
          visualKey: String.fromCharCode(65 + i), // A, B, C, D
          origKey: origKey,
          text: q.options[origKey]
        }));
      } else {
        // Standard non-shuffled A, B, C, D
        displayOptions = origKeys.map(k => ({
          visualKey: k,
          origKey: k,
          text: q.options[k]
        }));
      }

      return {
        index: idx,
        id: q.id,
        questionNumber: q.question_number || (idx + 1),
        week: q.week,
        topic: q.topic || q.week_label || `Week ${q.week}`,
        question: q.question,
        options: q.options,
        displayOptions: displayOptions,
        correctAnswer: q.correct_answer, // Original key: e.g. "B"
        explanation: q.explanation || "",
        selectedAnswer: null, // Stores chosen origKey
        selectedVisualKey: null, // Stores chosen visualKey
        evaluated: false,
        isCorrect: null
      };
    });

    saveState();
    renderQuizHeader();
    renderQuestion();
    renderNavigator();
    updateScoreChips();
    setupEventListeners();
  } catch (err) {
    console.error("Error fetching quiz questions:", err);
    alert("Network error while loading questions.");
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(quizState));
}

/* ================= Header Rendering ================= */
function renderQuizHeader() {
  const titleEl = document.getElementById("quiz-title");
  const subEl = document.getElementById("quiz-subtitle");

  titleEl.textContent = quizState.modeTitle;
  const total = quizState.questions.length;

  if (quizState.mode === "weekly") {
    subEl.textContent = `NPTEL Performance & Reward Management • ${total} Questions`;
  } else if (quizState.mode === "important") {
    subEl.textContent = `Focused Exam Preparation • ${total} Questions`;
  } else if (quizState.mode === "additional") {
    subEl.textContent = `Expanded Practice Questions • ${total} Questions`;
  } else if (quizState.mode === "all") {
    subEl.textContent = `NPTEL Performance & Reward Management • All ${total} Questions (Weeks 0–12)`;
  } else {
    subEl.textContent = `Practice Quiz • ${total} Questions`;
  }

  document.getElementById("nav-count-label").textContent = `${total} Questions`;
}

/* ================= Question Rendering ================= */
function renderQuestion() {
  const q = quizState.questions[quizState.currentIndex];
  if (!q) return;

  const total = quizState.questions.length;
  const currentNum = quizState.currentIndex + 1;

  // Counter & Meta
  document.getElementById("q-counter").textContent = `Question ${currentNum} of ${total}`;
  document.getElementById("q-topic-tag").textContent = q.topic;

  // Progress Bar
  const pct = Math.round((currentNum / total) * 100);
  document.getElementById("quiz-progress-bar").style.width = `${pct}%`;

  // Status Pill
  const statusPill = document.getElementById("eval-status-pill");
  if (!q.evaluated) {
    statusPill.className = "status-pill status-unanswered";
    statusPill.textContent = q.selectedAnswer ? "Option Selected" : "Unanswered";
  } else if (q.isCorrect) {
    statusPill.className = "status-pill status-correct";
    statusPill.textContent = "✓ Correct";
  } else {
    statusPill.className = "status-pill status-incorrect";
    statusPill.textContent = "✗ Incorrect";
  }

  // Question Statement
  document.getElementById("q-statement").textContent = q.question;

  // Render Options
  const container = document.getElementById("options-container");
  container.innerHTML = "";

  // Use displayOptions (handles shuffling cleanly)
  const optionsList = q.displayOptions || Object.keys(q.options).sort().map(k => ({
    visualKey: k,
    origKey: k,
    text: q.options[k]
  }));

  // Find correct visual key for feedback
  const correctOption = optionsList.find(opt => opt.origKey === q.correctAnswer);
  const correctVisualKey = correctOption ? correctOption.visualKey : q.correctAnswer;

  optionsList.forEach(opt => {
    const item = document.createElement("div");
    item.className = "option-item";
    item.dataset.visualKey = opt.visualKey;
    item.dataset.origKey = opt.origKey;

    // Apply classes based on state
    if (q.selectedAnswer === opt.origKey) {
      item.classList.add("selected");
    }

    if (q.evaluated) {
      item.classList.add("evaluated");
      if (opt.origKey === q.correctAnswer) {
        item.classList.add("eval-correct");
      }
      if (q.selectedAnswer === opt.origKey && !q.isCorrect) {
        item.classList.add("eval-wrong-selected");
      }
    }

    item.innerHTML = `
      <div class="option-badge">${opt.visualKey}</div>
      <div class="option-text">${escapeHtml(opt.text)}</div>
    `;

    // Click handler passes visualKey
    item.onclick = () => selectVisualOption(opt.visualKey);
    container.appendChild(item);
  });

  // Render Feedback Banner
  const fbBanner = document.getElementById("feedback-banner");
  const fbIcon = document.getElementById("feedback-icon");
  const fbTitle = document.getElementById("feedback-title");
  const fbText = document.getElementById("feedback-text");

  if (q.evaluated) {
    fbBanner.style.display = "flex";
    if (q.isCorrect) {
      fbBanner.className = "feedback-banner correct";
      fbIcon.textContent = "✓";
      fbTitle.textContent = "Correct! Well done.";
      fbText.textContent = q.explanation 
        ? `Explanation: ${q.explanation}` 
        : `Option ${correctVisualKey} is the correct answer.`;
    } else {
      fbBanner.className = "feedback-banner incorrect";
      fbIcon.textContent = "✗";
      fbTitle.textContent = "Incorrect.";
      const chosenVisual = q.selectedVisualKey || q.selectedAnswer;
      const correctText = correctOption ? correctOption.text : q.options[q.correctAnswer];
      fbText.textContent = `You selected (${chosenVisual}). The correct answer is Option ${correctVisualKey}: "${correctText}".` + 
        (q.explanation ? ` (${q.explanation})` : "");
    }
  } else {
    fbBanner.style.display = "none";
  }

  // Update Buttons
  updateButtons();

  // Highlight active box in navigator
  updateNavigatorActiveBox();
}

/* ================= Option Selection & Evaluation ================= */
function selectVisualOption(visualKey) {
  clearAutoAdvance();
  const q = quizState.questions[quizState.currentIndex];
  if (!q) return;

  const total = quizState.questions.length;
  const isLast = quizState.currentIndex === total - 1;

  // Lookup the original key mapped to this visual key
  let origKey = visualKey;
  if (q.displayOptions) {
    const match = q.displayOptions.find(opt => opt.visualKey === visualKey);
    if (match) {
      origKey = match.origKey;
    }
  }

  // Record and evaluate
  q.selectedVisualKey = visualKey;
  q.selectedAnswer = origKey;
  q.evaluated = true;
  q.isCorrect = (origKey === q.correctAnswer);

  recalculateScore();
  saveState();

  // Re-render question to display green/red feedback and banner
  renderQuestion();
  updateNavigatorBox(quizState.currentIndex);
  updateScoreChips();

  // Append 1-second countdown note in feedback banner
  const fbText = document.getElementById("feedback-text");
  if (fbText) {
    const note = document.createElement("div");
    note.className = "auto-advance-note";
    note.textContent = isLast 
      ? "Finishing quiz in 1s..." 
      : "Moving to next question in 1s...";
    fbText.appendChild(note);
  }

  // Start 1-second auto-advance
  autoAdvanceTimer = setTimeout(() => {
    autoAdvanceTimer = null;
    if (isLast) {
      finishQuiz();
    } else {
      goToQuestion(quizState.currentIndex + 1);
    }
  }, 1000);

  updateButtons();
}

function updateButtons() {
  const q = quizState.questions[quizState.currentIndex];
  const total = quizState.questions.length;
  const isLast = quizState.currentIndex === total - 1;

  // Previous Button
  const prevBtn = document.getElementById("btn-prev-q");
  prevBtn.disabled = quizState.currentIndex === 0;

  // Skip / Finish Button
  const skipBtn = document.getElementById("btn-action-primary");
  if (isLast) {
    skipBtn.textContent = autoAdvanceTimer ? "Finish Now ✓" : "Finish Quiz \u2192";
    skipBtn.className = autoAdvanceTimer ? "btn btn-success" : "btn btn-secondary";
  } else {
    skipBtn.textContent = autoAdvanceTimer ? "Skip Now \u2192" : "Skip \u2192";
    skipBtn.className = "btn btn-secondary";
  }
}

function handleSkipAction() {
  clearAutoAdvance();
  const total = quizState.questions.length;
  const isLast = quizState.currentIndex === total - 1;

  if (isLast) {
    finishQuiz();
  } else {
    goToQuestion(quizState.currentIndex + 1);
  }
}

function recalculateScore() {
  let score = 0;
  quizState.questions.forEach(q => {
    if (q.evaluated && q.isCorrect) {
      score += 1;
    }
  });
  quizState.score = score;
}

function updateScoreChips() {
  const evaluatedCount = quizState.questions.filter(q => q.evaluated).length;
  const correctCount = quizState.questions.filter(q => q.evaluated && q.isCorrect).length;
  const incorrectCount = quizState.questions.filter(q => q.evaluated && !q.isCorrect).length;
  const unansweredCount = quizState.questions.length - evaluatedCount;

  const pct = evaluatedCount > 0 ? Math.round((correctCount / evaluatedCount) * 100) : 0;

  document.getElementById("chip-score").textContent = correctCount;
  document.getElementById("chip-total").textContent = evaluatedCount;
  document.getElementById("chip-pct").textContent = `${pct}%`;

  document.getElementById("mini-correct").textContent = correctCount;
  document.getElementById("mini-incorrect").textContent = incorrectCount;
  document.getElementById("mini-unanswered").textContent = unansweredCount;
}

/* ================= Question Navigator ================= */
function renderNavigator() {
  const grid = document.getElementById("nav-grid");
  grid.innerHTML = "";

  quizState.questions.forEach((q, idx) => {
    const box = document.createElement("div");
    box.className = "nav-box";
    box.id = `nav-box-${idx}`;
    box.textContent = idx + 1;

    // Apply color status
    if (q.evaluated) {
      if (q.isCorrect) {
        box.classList.add("status-correct");
      } else {
        box.classList.add("status-incorrect");
      }
    } else {
      box.classList.add("status-unanswered");
    }

    if (idx === quizState.currentIndex) {
      box.classList.add("active-current");
    }

    box.onclick = () => goToQuestion(idx);
    grid.appendChild(box);
  });
}

function updateNavigatorBox(idx) {
  const box = document.getElementById(`nav-box-${idx}`);
  const q = quizState.questions[idx];
  if (!box || !q) return;

  box.classList.remove("status-correct", "status-incorrect", "status-unanswered");
  if (q.evaluated) {
    if (q.isCorrect) {
      box.classList.add("status-correct");
    } else {
      box.classList.add("status-incorrect");
    }
  } else {
    box.classList.add("status-unanswered");
  }
}

function updateNavigatorActiveBox() {
  document.querySelectorAll(".nav-box").forEach((box, idx) => {
    if (idx === quizState.currentIndex) {
      box.classList.add("active-current");
      box.scrollIntoView({ block: "nearest", behavior: "smooth" });
    } else {
      box.classList.remove("active-current");
    }
  });
}

function goToQuestion(idx) {
  clearAutoAdvance();
  if (idx < 0 || idx >= quizState.questions.length) return;
  quizState.currentIndex = idx;
  saveState();
  renderQuestion();
}

/* ================= Quiz Completion & Results ================= */
function finishQuiz() {
  clearAutoAdvance();
  const unansweredCount = quizState.questions.filter(q => !q.evaluated).length;
  if (unansweredCount > 0) {
    const proceed = confirm(`You have ${unansweredCount} unanswered question(s). Are you sure you want to finish the quiz?`);
    if (!proceed) return;
  }

  quizState.isFinished = true;
  recalculateScore();
  saveState();
  showResultsView();
}

function showResultsView() {
  document.getElementById("active-quiz-view").style.display = "none";
  const resultsView = document.getElementById("results-view");
  resultsView.style.display = "block";

  const total = quizState.questions.length;
  const correct = quizState.questions.filter(q => q.evaluated && q.isCorrect).length;
  const incorrect = quizState.questions.filter(q => q.evaluated && !q.isCorrect).length;
  const unanswered = total - (correct + incorrect);

  const pct = Math.round((correct / total) * 100);

  document.getElementById("res-score-pct").textContent = `${pct}%`;
  document.getElementById("res-score-num").textContent = correct;
  document.getElementById("res-score-denom").textContent = total;

  document.getElementById("res-total").textContent = total;
  document.getElementById("res-correct").textContent = correct;
  document.getElementById("res-incorrect").textContent = incorrect;
  document.getElementById("res-unanswered").textContent = unanswered;

  // Trophy/Badge icon based on percentage
  const trophy = document.getElementById("results-badge-icon");
  const title = document.getElementById("results-title");
  if (pct >= 80) {
    trophy.textContent = "🏆";
    title.textContent = "Outstanding Performance!";
  } else if (pct >= 60) {
    trophy.textContent = "🎉";
    title.textContent = "Well Done! Good Practice.";
  } else {
    trophy.textContent = "📚";
    title.textContent = "Keep Practicing!";
  }

  // Populate Review List
  populateReviewList("all");
}

/* ================= Review Panel ================= */
function populateReviewList(filter = "all") {
  const container = document.getElementById("review-list");
  container.innerHTML = "";

  quizState.questions.forEach((q, idx) => {
    let statusClass = "is-unanswered";
    let statusText = "Unanswered";

    if (q.evaluated) {
      if (q.isCorrect) {
        statusClass = "is-correct";
        statusText = "Correct";
      } else {
        statusClass = "is-incorrect";
        statusText = "Incorrect";
      }
    }

    // Apply Filter
    if (filter === "wrong" && (!q.evaluated || q.isCorrect)) return;
    if (filter === "unanswered" && q.evaluated) return;
    if (filter === "correct" && (!q.evaluated || !q.isCorrect)) return;

    const card = document.createElement("div");
    card.className = `review-item-card ${statusClass}`;

    const optionsList = q.displayOptions || Object.keys(q.options).sort().map(k => ({
      visualKey: k,
      origKey: k,
      text: q.options[k]
    }));

    let optHtml = "";
    optionsList.forEach(opt => {
      let optClass = "";
      const isActualCorrect = (opt.origKey === q.correctAnswer);
      const isUserChoice = (opt.origKey === q.selectedAnswer);

      if (isActualCorrect) {
        optClass = "actual-correct";
      }
      if (isUserChoice) {
        optClass = q.isCorrect ? "user-correct" : "user-wrong";
      }

      optHtml += `
        <div class="review-opt ${optClass}">
          <strong>${opt.visualKey}.</strong> ${escapeHtml(opt.text)}
          ${isActualCorrect ? " <span class='text-success font-bold'>[Correct Key]</span>" : ""}
          ${isUserChoice && !q.isCorrect ? " <span class='text-danger font-bold'>[Your Choice]</span>" : ""}
          ${isUserChoice && q.isCorrect ? " <span class='text-success font-bold'>[Your Choice ✓]</span>" : ""}
        </div>
      `;
    });

    card.innerHTML = `
      <div class="review-card-top">
        <span class="review-q-num">Question ${idx + 1} • ${escapeHtml(q.topic)}</span>
        <span class="status-pill status-${statusClass.replace('is-', '')}">${statusText}</span>
      </div>
      <div class="review-card-question">${escapeHtml(q.question)}</div>
      <div class="review-options-list">${optHtml}</div>
      ${q.explanation ? `<div class="review-explanation"><strong>Answer Note:</strong> ${escapeHtml(q.explanation)}</div>` : ""}
    `;

    container.appendChild(card);
  });

  if (container.children.length === 0) {
    container.innerHTML = `<p class="text-muted" style="text-align: center; padding: 2rem;">No questions match this filter.</p>`;
  }
}

/* ================= Event Listeners & Shortcuts ================= */
function setupEventListeners() {
  document.getElementById("btn-prev-q").onclick = () => {
    clearAutoAdvance();
    if (quizState.currentIndex > 0) {
      goToQuestion(quizState.currentIndex - 1);
    }
  };

  document.getElementById("btn-action-primary").onclick = () => {
    handleSkipAction();
  };

  document.getElementById("btn-finish-early").onclick = () => {
    clearAutoAdvance();
    finishQuiz();
  };

  // Results screen buttons
  const btnReview = document.getElementById("btn-toggle-review");
  const reviewPanel = document.getElementById("review-panel");
  btnReview.onclick = () => {
    if (reviewPanel.style.display === "none") {
      reviewPanel.style.display = "block";
      btnReview.textContent = "▲ Hide Review";
      reviewPanel.scrollIntoView({ behavior: "smooth" });
    } else {
      reviewPanel.style.display = "none";
      btnReview.textContent = "📝 Review Answers";
    }
  };

  document.getElementById("btn-restart-quiz").onclick = () => {
    clearAutoAdvance();
    if (confirm("Restart this quiz? Your current answers will be cleared.")) {
      quizState.questions.forEach(q => {
        q.selectedAnswer = null;
        q.selectedVisualKey = null;
        q.evaluated = false;
        q.isCorrect = null;
      });
      quizState.currentIndex = 0;
      quizState.isFinished = false;
      quizState.score = 0;
      saveState();

      document.getElementById("results-view").style.display = "none";
      document.getElementById("active-quiz-view").style.display = "grid";
      renderQuestion();
      renderNavigator();
      updateScoreChips();
    }
  };

  // Review filters
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      populateReviewList(btn.dataset.filter);
    };
  });

  // Home link confirmation
  document.getElementById("btn-home-link").onclick = () => {
    clearAutoAdvance();
  };

  // Keyboard navigation
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (quizState.isFinished) return;

    const key = e.key.toUpperCase();
    if (["A", "B", "C", "D"].includes(key)) {
      const q = quizState.questions[quizState.currentIndex];
      if (q && q.displayOptions) {
        const opt = q.displayOptions.find(o => o.visualKey === key);
        if (opt) {
          selectVisualOption(key);
        }
      } else if (q && q.options && q.options[key]) {
        selectVisualOption(key);
      }
    } else if (["1", "2", "3", "4"].includes(e.key)) {
      const numIdx = parseInt(e.key, 10) - 1;
      const visualKey = String.fromCharCode(65 + numIdx);
      selectVisualOption(visualKey);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleSkipAction();
    } else if (e.key === "ArrowLeft") {
      clearAutoAdvance();
      if (quizState.currentIndex > 0) {
        goToQuestion(quizState.currentIndex - 1);
      }
    } else if (e.key === "ArrowRight") {
      handleSkipAction();
    }
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
