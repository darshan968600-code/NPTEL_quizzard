/**
 * NPTEL Quizzer - Homepage Logic
 * Handles session resumption, theme switching, and starting practice quizzes
 */

const STORAGE_KEY = "nptel_quizzer_state";
const THEME_KEY = "nptel_theme";

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  checkSavedSession();
  initModalListeners();
});

/* ================= Theme Toggle ================= */
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

/* ================= Session Resumption ================= */
function checkSavedSession() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return;

  try {
    const state = JSON.parse(saved);
    if (!state || !state.questions || state.questions.length === 0 || state.isFinished) {
      return;
    }

    const banner = document.getElementById("resume-banner");
    const title = document.getElementById("resume-title");
    const desc = document.getElementById("resume-desc");
    const btnResume = document.getElementById("btn-resume-quiz");
    const btnDiscard = document.getElementById("btn-discard-quiz");

    const answeredCount = state.questions.filter(q => q.evaluated).length;
    const totalCount = state.questions.length;
    const currentQNum = (state.currentIndex || 0) + 1;

    let modeDesc = state.modeTitle || "Practice Quiz";
    title.textContent = `Resume Ongoing: ${modeDesc}`;
    desc.textContent = `Progress: Question ${currentQNum} of ${totalCount} • ${answeredCount} evaluated • Score: ${state.score || 0}/${answeredCount}`;

    banner.style.display = "flex";

    btnResume.onclick = () => {
      window.location.href = `/quiz?resume=1`;
    };

    btnDiscard.onclick = () => {
      if (confirm("Are you sure you want to discard your current quiz progress?")) {
        localStorage.removeItem(STORAGE_KEY);
        banner.style.display = "none";
      }
    };
  } catch (e) {
    console.error("Error reading saved quiz state:", e);
  }
}

/* ================= Navigation & Quiz Starters ================= */
function startWeeklyQuiz(week) {
  localStorage.removeItem(STORAGE_KEY);
  window.location.href = `/quiz?mode=weekly&week=${week}`;
}

function startImportantQuiz(count) {
  localStorage.removeItem(STORAGE_KEY);
  window.location.href = `/quiz?mode=important&count=${count}`;
}

function startImportantWeekQuiz() {
  const select = document.getElementById("select-important-week");
  const week = select ? select.value : "";
  if (week === "" || week === null) {
    alert("Please select a week to practice from the dropdown.");
    return;
  }
  localStorage.removeItem(STORAGE_KEY);
  window.location.href = `/quiz?mode=important&week=${week}`;
}

function startAdditionalQuiz(count) {
  localStorage.removeItem(STORAGE_KEY);
  window.location.href = `/quiz?mode=additional&count=${count}`;
}

/* ================= Combined Practice Settings Modal ================= */
function openCombinedSettingsModal() {
  const modal = document.getElementById("combined-settings-modal");
  if (modal) {
    modal.style.display = "flex";
  }
}

function closeCombinedSettingsModal() {
  const modal = document.getElementById("combined-settings-modal");
  if (modal) {
    modal.style.display = "none";
  }
}

function confirmStartCombinedQuiz() {
  const shuffleQ = document.getElementById("setting-shuffle-q")?.checked ? 1 : 0;
  const shuffleOpt = document.getElementById("setting-shuffle-opt")?.checked ? 1 : 0;

  localStorage.removeItem(STORAGE_KEY);
  window.location.href = `/quiz?mode=all&shuffle_q=${shuffleQ}&shuffle_opt=${shuffleOpt}`;
}

function initModalListeners() {
  const modal = document.getElementById("combined-settings-modal");
  if (!modal) return;

  // Close when clicking on backdrop
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeCombinedSettingsModal();
    }
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.style.display === "flex") {
      closeCombinedSettingsModal();
    }
  });
}
