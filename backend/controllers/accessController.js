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
    user: req.user,
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
    user: req.user,
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
    user: req.user,
  });
};
