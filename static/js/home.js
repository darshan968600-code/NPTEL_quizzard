/**
 * NPTEL Quizzer - Homepage Logic
 * Handles session resumption and starting new quizzes
 */

const STORAGE_KEY = "nptel_quizzer_state";

document.addEventListener("DOMContentLoaded", () => {
  checkSavedSession();
});

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

function startWeeklyQuiz(week) {
  // Clear any existing session to ensure fresh start
  localStorage.removeItem(STORAGE_KEY);
  window.location.href = `/quiz?mode=weekly&week=${week}`;
}

function startPyqQuiz(count) {
  // Clear any existing session to ensure fresh start
  localStorage.removeItem(STORAGE_KEY);
  window.location.href = `/quiz?mode=pyq&count=${count}`;
}
