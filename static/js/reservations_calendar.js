(() => {
  const page = document.querySelector(".resv-page");
  if (!page) return;

  const slotMinutes = Number(page.dataset.slotMinutes || 30);

  const form = document.getElementById("filtersForm");
  const dateEl = document.getElementById("date");
  const durationEl = document.getElementById("duration");
  const envEl = document.getElementById("env");

  const toast = document.getElementById("toast");

  const reserveForm = document.getElementById("reserveForm");
  const reserveBtn = document.getElementById("reserveBtn");
  const selTitle = document.getElementById("selTitle");
  const selectedList = document.getElementById("selectedList");
  const selectedSlotsInput = document.getElementById("selectedSlotsInput");

  const reserveDate = document.getElementById("reserveDate");
  const reserveDuration = document.getElementById("reserveDuration");
  const reserveEnv = document.getElementById("reserveEnv");

  const slots = Array.from(document.querySelectorAll(".js-slot"));

  const showToast = (msg) => {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove("show"), 2400);
  };

  const toISO = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  };

  if (dateEl && !dateEl.value) dateEl.value = toISO(new Date());

  const shiftDate = (days) => {
    const d = new Date(`${dateEl.value}T00:00:00`);
    d.setDate(d.getDate() + days);
    dateEl.value = toISO(d);
    form.submit();
  };

  document.querySelectorAll("[data-nav]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const t = btn.dataset.nav;
      if (t === "prev") shiftDate(-1);
      if (t === "next") shiftDate(+1);
      if (t === "today") {
        dateEl.value = toISO(new Date());
        form.submit();
      }
    });
  });

  [dateEl, durationEl, envEl].forEach((el) => el && el.addEventListener("change", () => form.submit()));

  const blocksNeeded = () => {
    const dur = Number(durationEl?.value || 60);
    return Math.max(1, Math.round(dur / slotMinutes));
  };

  const selected = new Map(); // key -> {courtId,courtName,start,duration,cells:[]}

  const keyOf = (courtId, start, duration) => `${courtId}||${start}||${duration}`;

  const btnAt = (courtId, timeIndex) =>
    document.querySelector(`.js-slot[data-court-id="${courtId}"][data-time-index="${String(timeIndex)}"]`);

  const clearSel = (btn) => {
    btn.classList.remove("sel-start", "sel-cover");
    btn.setAttribute("aria-pressed", "false");
  };

  const applySel = (btn, isStart) => {
    btn.classList.add(isStart ? "sel-start" : "sel-cover");
    btn.setAttribute("aria-pressed", "true");
  };

  const updateUI = () => {
    const arr = Array.from(selected.values()).map((x) => ({
      court_id: x.courtId,
      start: x.start,
      duration: x.duration,
    }));

    selectedSlotsInput.value = JSON.stringify(arr);
    reserveBtn.disabled = arr.length === 0;

    selTitle.textContent = `Vybráno: ${arr.length} slotů`;
    selectedList.innerHTML = "";

    arr.forEach((x) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.innerHTML = `
        <span>${x.courtName} • ${x.start} • ${x.duration} min</span>
        <button type="button" aria-label="Odebrat">×</button>
      `;
      chip.querySelector("button").addEventListener("click", () => deselect(keyOf(x.court_id, x.start, x.duration)));
      selectedList.appendChild(chip);
    });

    reserveDate.value = dateEl.value;
    reserveDuration.value = durationEl.value;
    reserveEnv.value = envEl.value;
  };

  const deselect = (key) => {
    const item = selected.get(key);
    if (!item) return;
    item.cells.forEach(clearSel);
    selected.delete(key);
    updateUI();
  };

  const overlaps = (courtId, timeIndex) => {
    const b = btnAt(courtId, timeIndex);
    return !!b && (b.classList.contains("sel-start") || b.classList.contains("sel-cover"));
  };

  slots.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;

      const courtId = btn.dataset.courtId;
      const courtName = btn.dataset.courtName || "Kurt";
      const start = btn.dataset.start;
      const idx = Number(btn.dataset.timeIndex);
      const duration = Number(durationEl?.value || 60);

      const key = keyOf(courtId, start, duration);
      if (selected.has(key)) {
        deselect(key);
        return;
      }

      const need = blocksNeeded();
      const cells = [];

      for (let k = 0; k < need; k++) {
        const b = btnAt(courtId, idx + k);
        if (!b || b.disabled) {
          showToast("Tenhle čas nejde vybrat v dané délce (část je obsazená nebo mimo rozsah).");
          return;
        }
        if (overlaps(courtId, idx + k)) {
          showToast("Slot se překrývá s už vybranou rezervací.");
          return;
        }
        cells.push(b);
      }

      cells.forEach((b, i) => applySel(b, i === 0));
      selected.set(key, { courtId, courtName, start, duration, cells });
      updateUI();
    });
  });

  reserveForm?.addEventListener("submit", (e) => {
    if (selected.size === 0) {
      e.preventDefault();
      showToast("Nejdřív vyber aspoň jeden slot.");
    }
  });

  updateUI();
})();
