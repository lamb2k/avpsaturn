const form = document.querySelector("#signin"), status = document.querySelector("#status");
form.addEventListener("submit", async event => {
  event.preventDefault();
  const username = form.querySelector("#username").value, password = form.querySelector("#password").value;
  status.textContent = "";
  try {
    const r = await fetch("/signin", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }) });
    if (r.ok) location.replace("/");
    else status.textContent = r.status === 401 ? "Username or password not recognised." : r.status === 429 ? "Too many attempts. Try again in a minute." : "Sign-in unavailable.";
  } catch { status.textContent = "Connection interrupted. Try again."; }
});
