// VAULT: browser side of the password generator.
// Passwords come from the server's /api/generate endpoint. They are only
// kept in memory to display and copy them, and are never stored or logged.

(() => {
  "use strict";

  const app = document.getElementById("app");
  const MIN_LENGTH = Number(app.dataset.minLength);
  const MAX_LENGTH = Number(app.dataset.maxLength);

  const output = document.getElementById("password-output");
  const meta = document.getElementById("password-meta");
  const status = document.getElementById("status");
  const lengthInput = document.getElementById("length-input");
  const lengthValue = document.getElementById("length-value");
  const toggles = Array.from(document.querySelectorAll(".toggle input"));
  const configError = document.getElementById("config-error");
  const revealButton = document.getElementById("reveal-button");
  const revealText = document.getElementById("reveal-text");
  const regenerateButton = document.getElementById("regenerate-button");
  const copyButton = document.getElementById("copy-button");
  const copyText = document.getElementById("copy-text");

  const strengthLabel = document.getElementById("strength-label");
  const strengthMeter = document.getElementById("strength-meter");
  const entropyValue = document.getElementById("entropy-value");
  const entropyFormula = document.getElementById("entropy-formula");
  const criteria = {
    length: document.querySelector('[data-criterion="length"]'),
    types: document.querySelector('[data-criterion="types"]'),
    entropy: document.querySelector('[data-criterion="entropy"]'),
  };

  // Lower bounds, in bits, for each strength tier (also listed on the page).
  const TIERS = [
    { name: "excellent", label: "Excellent", minBits: 90 },
    { name: "strong", label: "Strong", minBits: 65 },
    { name: "fair", label: "Fair", minBits: 45 },
    { name: "weak", label: "Weak", minBits: 0 },
  ];

  let password = "";
  let isHidden = false;
  let latestRequest = 0;
  let activeController = null;
  let copyResetTimer = null;
  let lengthTimer = null;

  // ---------- Settings ----------

  function getSettings() {
    const settings = { length: Number(lengthInput.value) };
    for (const toggle of toggles) {
      settings[toggle.name] = toggle.checked;
    }
    return settings;
  }

  function selectedToggles() {
    return toggles.filter((toggle) => toggle.checked);
  }

  function updateLengthDisplay() {
    const length = Number(lengthInput.value);
    lengthValue.textContent = length;
    const percent = ((length - MIN_LENGTH) / (MAX_LENGTH - MIN_LENGTH)) * 100;
    lengthInput.style.setProperty("--fill", `${percent}%`);
    lengthInput.setAttribute("aria-valuetext", `${length} characters`);
  }

  // ---------- Strength estimate ----------

  function updateStrength() {
    const length = Number(lengthInput.value);
    const selected = selectedToggles();
    const poolSize = selected.reduce((sum, toggle) => sum + Number(toggle.dataset.poolSize), 0);

    if (poolSize === 0) {
      strengthLabel.textContent = "No types";
      strengthLabel.dataset.tier = "none";
      strengthMeter.dataset.tier = "none";
      strengthMeter.setAttribute("aria-valuenow", "0");
      strengthMeter.setAttribute("aria-valuetext", "No character types selected");
      entropyValue.textContent = "0";
      entropyFormula.textContent = "Select a character type to see an estimate.";
      setCriteria(length, 0, 0);
      return;
    }

    const bits = length * Math.log2(poolSize);
    const tier = TIERS.find((t) => bits >= t.minBits);
    const roundedBits = Math.round(bits);

    strengthLabel.textContent = tier.label;
    strengthLabel.dataset.tier = tier.name;
    strengthMeter.dataset.tier = tier.name;
    strengthMeter.setAttribute("aria-valuenow", String(Math.min(roundedBits, 128)));
    strengthMeter.setAttribute("aria-valuetext", `${tier.label}, about ${roundedBits} bits`);
    entropyValue.textContent = `≈${roundedBits}`;
    entropyFormula.textContent =
      `${length} × log₂(${poolSize}) = ${length} × ${Math.log2(poolSize).toFixed(2)} ≈ ${roundedBits} bits`;
    setCriteria(length, selected.length, bits);
  }

  function setCriteria(length, typeCount, bits) {
    criteria.length.classList.toggle("is-met", length >= 16);
    criteria.types.classList.toggle("is-met", typeCount >= 3);
    criteria.entropy.classList.toggle("is-met", bits >= 80);
  }

  // ---------- Validation ----------

  // Returns true when at least one character type is selected.
  function updateValidity() {
    const isValid = selectedToggles().length > 0;
    configError.hidden = isValid;
    regenerateButton.disabled = !isValid;
    if (!isValid) {
      // Cancel, and ignore, any reply still on its way for the old settings.
      cancelPendingRequest();
      latestRequest++;
      regenerateButton.classList.remove("is-busy");
      password = "";
      renderPassword();
      copyButton.disabled = true;
      revealButton.disabled = true;
    }
    return isValid;
  }

  // ---------- Password display ----------

  function characterClass(character) {
    if (/[0-9]/.test(character)) return "ch-digit";
    if (/[A-Za-z]/.test(character)) return "ch-letter";
    return "ch-symbol";
  }

  function renderPassword() {
    output.replaceChildren();
    output.classList.toggle("is-masked", isHidden && password !== "");

    if (password === "") {
      const placeholder = document.createElement("span");
      placeholder.className = "password-placeholder";
      placeholder.textContent = selectedToggles().length
        ? "Generating…"
        : "Choose at least one character type below.";
      output.append(placeholder);
      meta.textContent = "";
      return;
    }

    if (isHidden) {
      output.textContent = "•".repeat(password.length);
    } else {
      // Built with textContent, never innerHTML, so characters are always shown literally.
      for (const character of password) {
        const span = document.createElement("span");
        span.className = characterClass(character);
        span.textContent = character;
        output.append(span);
      }
    }
    meta.textContent = `${password.length} chars`;
  }

  function setHidden(hidden) {
    isHidden = hidden;
    revealButton.classList.toggle("is-hidden", hidden);
    revealText.textContent = hidden ? "Show" : "Hide";
    renderPassword();
  }

  // ---------- Status messages ----------

  function showStatus(message, kind = "info") {
    status.textContent = message;
    status.dataset.kind = kind;
  }

  // ---------- Generate ----------

  function cancelPendingRequest() {
    if (activeController) {
      activeController.abort();
      activeController = null;
    }
  }

  async function generate({ announce = false } = {}) {
    if (!updateValidity()) return;

    // Only the newest request matters: cancel the previous one, and ignore
    // its reply if it still arrives.
    cancelPendingRequest();
    const controller = new AbortController();
    activeController = controller;
    const requestNumber = ++latestRequest;
    regenerateButton.classList.add("is-busy");

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(getSettings()),
        cache: "no-store",
        signal: controller.signal,
      });
      const data = await response.json().catch(() => ({}));
      if (requestNumber !== latestRequest) return;

      if (!response.ok || typeof data.password !== "string") {
        throw new Error(data.error || "The server could not generate a password.");
      }

      password = data.password;
      renderPassword();
      copyButton.disabled = false;
      revealButton.disabled = false;
      resetCopyButton();
      // Replace any earlier message, such as "copied", that was about the old password.
      showStatus(announce ? "New password generated." : "");
    } catch (error) {
      if (requestNumber !== latestRequest) return;
      const message = error instanceof TypeError
        ? "Couldn't reach the VAULT server. Check that the app is still running."
        : error.message;
      showStatus(message, "error");
    } finally {
      if (activeController === controller) {
        activeController = null;
      }
      if (requestNumber === latestRequest) {
        regenerateButton.classList.remove("is-busy");
      }
    }
  }

  // ---------- Copy ----------

  function resetCopyButton() {
    clearTimeout(copyResetTimer);
    copyButton.classList.remove("is-copied");
    copyText.textContent = "Copy";
  }

  async function copyPassword() {
    if (password === "") return;
    try {
      await navigator.clipboard.writeText(password);
      copyButton.classList.add("is-copied");
      copyText.textContent = "Copied";
      showStatus("Password copied to clipboard.", "success");
      clearTimeout(copyResetTimer);
      copyResetTimer = setTimeout(resetCopyButton, 2000);
    } catch {
      // While hidden, selecting the text would copy dots, so say to show it first.
      const hint = isHidden
        ? "Choose Show, then select the password and copy it manually."
        : "Select the password and copy it manually.";
      showStatus(`Couldn't copy automatically. ${hint}`, "error");
    }
  }

  // ---------- Events ----------

  lengthInput.addEventListener("input", () => {
    updateLengthDisplay();
    updateStrength();
    // Wait until the slider pauses before asking the server for a new password.
    clearTimeout(lengthTimer);
    lengthTimer = setTimeout(() => generate(), 150);
  });

  for (const toggle of toggles) {
    toggle.addEventListener("change", () => {
      updateStrength();
      if (updateValidity()) {
        generate();
      } else {
        showStatus("");
      }
    });
  }

  regenerateButton.addEventListener("click", () => generate({ announce: true }));
  copyButton.addEventListener("click", copyPassword);
  revealButton.addEventListener("click", () => setHidden(!isHidden));

  // ---------- Start ----------

  updateLengthDisplay();
  updateStrength();
  generate();
})();
