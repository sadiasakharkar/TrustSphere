import { useEffect, useMemo, useState } from 'react';
import { createSeedIncidents, withAuditEntry } from '../data/hitlIncidents';

function applyAutoExecution(incident, currentTime) {
  if (incident.status !== 'PENDING_APPROVAL') return incident;
  if (new Date(incident.approvalDeadline).getTime() > currentTime) return incident;
  return withAuditEntry(
    {
      ...incident,
      status: 'AUTO_EXECUTED',
      approvedBy: 'system',
    },
    'Auto Executed',
    'System',
  );
}

export function useIncidentApprovals() {
  const [incidents, setIncidents] = useState(() => createSeedIncidents());
  const [currentTime, setCurrentTime] = useState(Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => {
      const now = Date.now();
      setCurrentTime(now);
      setIncidents((current) => current.map((incident) => applyAutoExecution(incident, now)));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const counts = useMemo(() => ({
    active: incidents.length,
    pending: incidents.filter((incident) => incident.status === 'PENDING_APPROVAL').length,
    approved: incidents.filter((incident) => incident.status === 'APPROVED').length,
  }), [incidents]);

  const approveIncident = (incidentId, actor = 'analyst') => {
    setIncidents((current) => current.map((incident) => (
      incident.id !== incidentId
        ? incident
        : withAuditEntry({
            ...incident,
            status: 'APPROVED',
            approvedBy: actor,
          }, 'Human Approved', actor)
    )));
  };

  const rejectIncident = (incidentId, actor = 'analyst') => {
    setIncidents((current) => current.map((incident) => (
      incident.id !== incidentId
        ? incident
        : withAuditEntry({
            ...incident,
            status: 'REJECTED',
            approvedBy: actor,
          }, 'Human Rejected', actor)
    )));
  };

  const modifyIncident = (incidentId, action, actor = 'analyst') => {
    setIncidents((current) => current.map((incident) => (
      incident.id !== incidentId
        ? incident
        : withAuditEntry({
            ...incident,
            aiSuggestion: action,
            status: 'APPROVED',
            approvedBy: actor,
          }, `Human Approved`, actor)
    )));
  };

  return {
    incidents,
    currentTime,
    counts,
    approveIncident,
    rejectIncident,
    modifyIncident,
  };
}
