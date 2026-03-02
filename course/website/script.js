/* ============================================================
   Agentic AI Masterclass — Interactivity
   Copy buttons, OS toggle, sidebar nav, progress tracking
   ============================================================ */

(function () {
  'use strict';

  // --- OS Toggle -----------------------------------------------------------
  const OS_KEY = 'aiq-os';
  let currentOS = localStorage.getItem(OS_KEY) || (navigator.platform.startsWith('Win') ? 'windows' : 'mac');

  function setOS(os) {
    currentOS = os;
    localStorage.setItem(OS_KEY, os);
    // Update toggle buttons
    document.querySelectorAll('.os-toggle button').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.os === os);
    });
    // Update OS-specific command blocks
    document.querySelectorAll('.os-command').forEach(el => {
      const text = el.dataset[os] || el.dataset.mac || '';
      el.querySelector('code').textContent = text;
    });
  }

  // --- Copy to Clipboard ----------------------------------------------------
  function addCopyButtons() {
    document.querySelectorAll('pre:not(.no-copy), .os-command').forEach(block => {
      if (block.querySelector('.copy-btn')) return;
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'Copy';
      btn.addEventListener('click', () => {
        const code = block.querySelector('code')
          ? block.querySelector('code').textContent
          : block.textContent;
        navigator.clipboard.writeText(code).then(() => {
          btn.textContent = 'Copied!';
          btn.classList.add('copied');
          setTimeout(() => {
            btn.textContent = 'Copy';
            btn.classList.remove('copied');
          }, 2000);
        });
      });
      block.style.position = 'relative';
      block.appendChild(btn);
    });
  }

  // --- Sidebar Active Highlight (scroll spy) --------------------------------
  function setupScrollSpy() {
    const links = document.querySelectorAll('.sidebar a[href^="#"]');
    if (!links.length) return;

    const sections = [];
    links.forEach(link => {
      const id = link.getAttribute('href').slice(1);
      const el = document.getElementById(id);
      if (el) sections.push({ link, el });
    });

    function updateActive() {
      let current = sections[0];
      const scrollY = window.scrollY + 120;
      for (const s of sections) {
        if (s.el.offsetTop <= scrollY) current = s;
      }
      links.forEach(l => l.classList.remove('active'));
      if (current) current.link.classList.add('active');
    }

    window.addEventListener('scroll', updateActive, { passive: true });
    updateActive();
  }

  // --- Progress Tracking (localStorage) -------------------------------------
  const PROGRESS_KEY = 'aiq-progress';

  function getProgress() {
    try { return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {}; }
    catch { return {}; }
  }

  function saveProgress(data) {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(data));
  }

  function setupProgressCheckboxes() {
    const progress = getProgress();
    document.querySelectorAll('.section-check input[type="checkbox"]').forEach(cb => {
      const id = cb.id;
      if (!id) return;
      cb.checked = !!progress[id];
      cb.addEventListener('change', () => {
        const p = getProgress();
        p[id] = cb.checked;
        saveProgress(p);
        updateProgressBar();
      });
    });
    updateProgressBar();
  }

  function updateProgressBar() {
    const fill = document.querySelector('.progress-bar-fill');
    const label = document.querySelector('.progress-pct');
    if (!fill) return;

    const all = document.querySelectorAll('.section-check input[type="checkbox"]');
    if (!all.length) {
      // Global progress bar — count from all pages
      const progress = getProgress();
      const totalSections = 18; // Approximate total across all modules
      const checked = Object.values(progress).filter(Boolean).length;
      const pct = Math.round((checked / totalSections) * 100);
      fill.style.width = pct + '%';
      if (label) label.textContent = pct + '%';
      return;
    }

    const checked = Array.from(all).filter(cb => cb.checked).length;
    const pct = Math.round((checked / all.length) * 100);
    fill.style.width = pct + '%';
    if (label) label.textContent = pct + '%';
  }

  // --- Download .py files (data URI) ----------------------------------------
  function setupDownloadButtons() {
    document.querySelectorAll('.download-btn[data-filename]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        // Try: 1) inside lab-code-section, 2) sibling lab-code-section, 3) next lab-code-section after parent
        let section = btn.closest('.lab-code-section');
        if (!section) {
          const parent = btn.closest('.lab-header');
          if (parent) section = parent.nextElementSibling;
          while (section && !section.classList.contains('lab-code-section')) section = section.nextElementSibling;
        }
        // Collect ALL code blocks in the section and join them
        const codeBlocks = section ? section.querySelectorAll('pre code') : [];
        let code = '';
        if (codeBlocks.length > 0) {
          code = Array.from(codeBlocks).map(cb => cb.textContent).join('\n\n');
        }
        code = code || btn.dataset.content || '';
        if (!code) return;
        const blob = new Blob([code], { type: 'text/x-python' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = btn.dataset.filename;
        a.click();
        URL.revokeObjectURL(url);
      });
    });
  }

  // --- Mobile Sidebar Toggle ------------------------------------------------
  function setupMobileNav() {
    const hamburger = document.querySelector('.hamburger');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    if (!hamburger || !sidebar) return;

    function toggle() {
      sidebar.classList.toggle('open');
      overlay?.classList.toggle('open');
    }

    hamburger.addEventListener('click', toggle);
    overlay?.addEventListener('click', toggle);

    // Close on link click (mobile)
    sidebar.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        if (window.innerWidth <= 900) toggle();
      });
    });
  }

  // --- Initialize -----------------------------------------------------------
  document.addEventListener('DOMContentLoaded', () => {
    // OS Toggle
    document.querySelectorAll('.os-toggle button').forEach(btn => {
      btn.addEventListener('click', () => setOS(btn.dataset.os));
    });
    setOS(currentOS);

    addCopyButtons();
    setupScrollSpy();
    setupProgressCheckboxes();
    setupDownloadButtons();
    setupMobileNav();
  });

})();
