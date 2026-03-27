function buildDemoUser(req, fallbackRole) {
  return {
    id: "demo-user",
    name: "Demo Operator",
    email: "demo@trustsphere.local",
    role: String(req.query.role || fallbackRole || "employee").toLowerCase(),
    mode: "demo",
  };
}

exports.adminAccess = async (req, res) => {
  return res.status(200).json({
    message: "Admin access granted.",
    permissions: [
      "manage_users",
      "view_all_alerts",
      "view_all_incidents",
      "view_analytics",
      "configure_platform",
    ],
    user: buildDemoUser(req, "admin"),
  });
};

exports.analystAccess = async (req, res) => {
  return res.status(200).json({
    message: "Analyst access granted.",
    permissions: [
      "view_alerts",
      "view_incidents",
      "analyze_threats",
      "update_incident_status",
      "view_analytics",
    ],
    user: buildDemoUser(req, "analyst"),
  });
};

exports.employeeAccess = async (req, res) => {
  return res.status(200).json({
    message: "Employee access granted.",
    permissions: [
      "view_personal_alerts",
      "view_personal_risk_score",
      "trigger_limited_analysis",
    ],
    user: buildDemoUser(req, "employee"),
  });
};
