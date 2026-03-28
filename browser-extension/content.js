const TRUSTSPHERE_API = "http://127.0.0.1:8000/analyze";
const POPUP_ID = "trustsphere-fraud-popup";

function getPageText() {
  const bodyText = document.body?.innerText || "";
  return bodyText.trim().slice(0, 1000);
}

function removeExistingPopup() {
  const existing = document.getElementById(POPUP_ID);
  if (existing) {
    existing.remove();
  }
}

function showPopup(data) {
  removeExistingPopup();

  const popup = document.createElement("div");
  popup.id = POPUP_ID;
  popup.style.position = "fixed";
  popup.style.top = "20px";
  popup.style.right = "20px";
  popup.style.width = "320px";
  popup.style.background = "linear-gradient(180deg, #101828 0%, #111827 100%)";
  popup.style.color = "#f8fafc";
  popup.style.padding = "16px";
  popup.style.borderRadius = "14px";
  popup.style.border = "1px solid rgba(248, 113, 113, 0.45)";
  popup.style.boxShadow = "0 18px 45px rgba(15, 23, 42, 0.45)";
  popup.style.zIndex = "2147483647";
  popup.style.fontFamily = "\"Segoe UI\", Tahoma, sans-serif";

  const reasons = Array.isArray(data.reasons)
    ? data.reasons.map((reason) => `<li style="margin: 0 0 6px 0;">${reason}</li>`).join("")
    : "<li>General anomaly detected</li>";

  popup.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;">
      <h3 style="margin:0;font-size:18px;color:#fecaca;">Fraud Detected</h3>
      <span style="padding:4px 10px;border-radius:999px;background:#7f1d1d;color:#fee2e2;font-size:12px;font-weight:700;letter-spacing:0.05em;">
        ${data.severity || "UNKNOWN"}
      </span>
    </div>
    <p style="margin:0 0 8px 0;font-size:13px;color:#cbd5e1;">
      <strong style="color:#f8fafc;">Score:</strong> ${Number(data.score ?? data.risk_score ?? 0).toFixed(2)}
    </p>
    <p style="margin:0 0 8px 0;font-size:13px;color:#cbd5e1;">
      <strong style="color:#f8fafc;">Reasons</strong>
    </p>
    <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.45;color:#e2e8f0;">
      ${reasons}
    </ul>
  `;

  document.body.appendChild(popup);

  window.setTimeout(() => {
    popup.remove();
  }, 6000);
}

async function analyzePage() {
  const input = getPageText();
  if (!input) {
    return;
  }

  try {
    const response = await fetch(TRUSTSPHERE_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ input })
    });

    if (!response.ok) {
      throw new Error(`TrustSphere analyze failed with status ${response.status}`);
    }

    const data = await response.json();
    if (data.severity === "HIGH" || data.severity === "MEDIUM") {
      showPopup(data);
    }
  } catch (error) {
    console.log("TrustSphere extension error:", error);
  }
}

window.setTimeout(analyzePage, 2500);
