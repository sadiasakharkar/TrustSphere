import { useEffect, useMemo, useState } from 'react';
import { createSeedIncidents, withActivityEntry, withAuditEntry } from '../data/hitlIncidents';

function applyAutoExecution(incident, currentTime) {
  if (incident.status !== 'PENDING_APPROVAL') return incident;
  if (new Date(incident.approvalDeadline).getTime() > currentTime) return incident;
  return withActivityEntry(
    withAuditEntry(
      {
        ...incident,
        status: 'AUTO_EXECUTED',
        approvedBy: 'System',
      },
      'Auto Executed',
      'System',
    ),
    'Auto Executed',
    'System',
  );
}

export function useIncidentApprovals() {
  const [incidents, setIncidents] = useState(() => createSeedIncidents());
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [liveActivity, setLiveActivity] = useState(() => [
    { id: 'live-1', message: 'AI suggested HITL-1001', timestamp: new Date().toISOString() },
    { id: 'live-2', message: 'Fraud alert mailed to SOC Analyst Queue', timestamp: new Date().toISOString() },
  ]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      const now = Date.now();
      setCurrentTime(now);
      setIncidents((current) => current.map((incident) => applyAutoExecution(incident, now)));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const messages = [
      'Packet burst flagged',
      'Approval queue updated',
      'Vault access correlated',
      'Security mail alert sent',
      'Risk window refreshed',
    ];
    const timer = window.setInterval(() => {
      const timestamp = new Date().toISOString();
      const message = messages[Math.floor(Math.random() * messages.length)];
      setLiveActivity((current) => [
        { id: `${timestamp}-${message}`, message, timestamp },
        ...current,
      ].slice(0, 6));
    }, 12000);
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
        : withActivityEntry(
            withAuditEntry({
              ...incident,
              status: 'APPROVED',
              approvedBy: actor,
            }, 'Approved', actor),
            'Approved',
            actor,
          )
    )));
    setLiveActivity((current) => [
      { id: `${incidentId}-approved-${Date.now()}`, message: `${incidentId} approved`, timestamp: new Date().toISOString() },
      ...current,
    ].slice(0, 6));
  };

  const rejectIncident = (incidentId, actor = 'analyst') => {
    setIncidents((current) => current.map((incident) => (
      incident.id !== incidentId
        ? incident
        : withActivityEntry(
            withAuditEntry({
              ...incident,
              status: 'REJECTED',
              approvedBy: actor,
            }, 'Rejected', actor),
            'Rejected',
            actor,
          )
    )));
    setLiveActivity((current) => [
      { id: `${incidentId}-rejected-${Date.now()}`, message: `${incidentId} rejected`, timestamp: new Date().toISOString() },
      ...current,
    ].slice(0, 6));
  };

  const modifyIncident = (incidentId, action, actor = 'analyst') => {
    setIncidents((current) => current.map((incident) => (
      incident.id !== incidentId
        ? incident
        : withActivityEntry(
            withAuditEntry({
              ...incident,
              aiSuggestion: action,
              status: 'APPROVED',
              approvedBy: actor,
            }, 'Approved', actor),
            `Modified: ${action}`,
            actor,
          )
    )));
    setLiveActivity((current) => [
      { id: `${incidentId}-modified-${Date.now()}`, message: `${incidentId} set ${action}`, timestamp: new Date().toISOString() },
      ...current,
    ].slice(0, 6));
  };

  return {
    incidents,
    currentTime,
    counts,
    liveActivity,
    approveIncident,
    rejectIncident,
    modifyIncident,
  };
}
