document.addEventListener("DOMContentLoaded", () => {
  const playersContainer = document.getElementById("players");
  const addBtn = document.getElementById("add-player");
  const template = document.getElementById("player-template");
  const form = document.querySelector("form");
  
  if (!form) {
    console.error("Form not found");
    return;
  }
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const response = await fetch(form.action || window.location.pathname, {
      method: "POST",
      body: new FormData(form)
    });

    let result;
    const contentType = response.headers.get("content-type");

    if (contentType && contentType.includes("application/json")) {
      result = await response.json();
    } else {
      const text = await response.text();
      console.error("Server returned non-JSON:", text);
      showError("Unexpected server error.");
      return;
    }

    if (!response.ok || !result.ok) {
      showError(result.error || "Submission failed.");
    } else {
      showSuccess?.();
      form.reset();
    }
  });

  function renumberPlayers() {
    [...playersContainer.children].forEach((player, index) => {
      // Update header number
      player.querySelector(".player-number").textContent = index + 1;

      // Update input names + default place
      player.querySelectorAll("input").forEach(input => {
        input.name = input.name.replace(
          /players\[\d+]/,
          `players[${index}]`
        );

        if (input.name.endsWith("[place]")) {
          input.value = index + 1;
        }
      });
    });
  }

  function addPlayer() {
    const index = playersContainer.children.length;
    const clone = template.content.cloneNode(true);

    clone.querySelector(".player-number").textContent = index + 1;

    clone.querySelectorAll("input").forEach(input => {
      input.name = input.name
        .replace("__NAME__", `players[${index}][name]`)
        .replace("__DECK__", `players[${index}][deck]`)
        .replace("__COMMANDER__", `players[${index}][commander]`)
        .replace("__PLACE__", `players[${index}][place]`)
        .replace("__TURN__", `players[${index}][turn_order]`);
    });

    // Default placement = order added
    clone.querySelector('input[name$="[place]"]').value = index + 1;

    // Remove handler
    clone.querySelector(".remove-player").addEventListener("click", e => {
      e.target.closest(".player").remove();
      renumberPlayers();
    });

    const playerEl = clone.querySelector(".player");

    // Update summary live as user types
    clone.querySelectorAll(
      'input[name$="[name]"], input[name$="[deck]"], input[name$="[commander]"]'
    ).forEach(input => {
      input.addEventListener("input", () => updatePlayerSummary(playerEl));
    });

    // Collapse others, open new
    playersContainer.querySelectorAll("details").forEach(d => d.open = false);
    clone.querySelector("details").open = true;

    setupAutocomplete(clone.querySelector(".deck-input"), PRECON_DATA, item => `${item.deck_name} — ${item.commander_name || ""}`);
    setupAutocomplete(clone.querySelector(".commander-input"), COMMANDERS, item => item); 
    setupAutocomplete(clone.querySelector(".name-input"), NAMES, item => item);

    playersContainer.appendChild(clone);
  }

  addBtn.addEventListener("click", addPlayer);

  // Start with one player
  addPlayer();
});

function updatePlayerSummary(playerEl) {
  const name =
    playerEl.querySelector('input[name$="[name]"]')?.value.trim();
  const deck =
    playerEl.querySelector('input[name$="[deck]"]')?.value.trim();
  const commander =
    playerEl.querySelector('input[name$="[commander]"]')?.value.trim();

  const parts = [name, deck, commander].filter(Boolean);
  const summarySpan = playerEl.querySelector(".player-summary");



  summarySpan.textContent = parts.length
    ? " — " + parts.join(" | ")
    : "";
}
function setupAutocomplete(input, data, formatItem) {
    // input: the <input> element
    // data: array of objects or strings
    // formatItem: function to turn a data item into display text

    const container = input.closest(".autocomplete");
    const resultsBox = container.querySelector(".autocomplete-results");

    input.addEventListener("input", () => {
        const query = input.value.toLowerCase();
        resultsBox.innerHTML = "";

        if (!query) return;

        // Filter the data
        const matches = data.filter(item => {
            const text = formatItem(item).toLowerCase();
            return text.includes(query);
        }).slice(0, 5); // limit results

        // Render results
        matches.forEach(item => {
            const div = document.createElement("div");
            div.className = "autocomplete-item";
            div.textContent = formatItem(item);
            div.addEventListener("click", () => {
                input.value = formatItem(item);
                resultsBox.innerHTML = "";
            });
            resultsBox.appendChild(div);
        });
    });



  document.addEventListener("click", e => {
    if (!container.contains(e.target)) {
      resultsBox.innerHTML = "";
    }
  });

}


function showError(message) {
  document.getElementById("error-message").textContent = message;
  document.getElementById("error-modal").classList.remove("hidden");
}

function closeError() {
  document.getElementById("error-modal").classList.add("hidden");
}