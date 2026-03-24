import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import ModelHealthChip from '../components/soc/ModelHealthChip';
import PageHeader from '../components/soc/PageHeader';
import { getDetectionsOverview } from '../services/api/detectionService';

export default function DetectionsPage() {
  const [data, setData] = useState(null);
  useEffect(() => { getDetectionsOverview().then(setData); }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Detections focus: compare detector health, drift, and precision proxies before changing any operational thresholds.' }}>
        <PageHeader kicker="Detections" title="Detector Operations" description="Review how each detector is performing across versioning, throughput, drift, and precision before governance changes are made." />
        {!data ? <LoadingSkeleton rows={5} /> : (
          <div className="grid gap-4 xl:grid-cols-2">
            {data.detectors.map((detector) => (
              <ModelHealthChip key={detector.name} name={detector.name} status={detector.status} detail={`${detector.version} · ${detector.inferenceCount} inferences · precision ${detector.precision} · drift ${detector.drift}`} />
            ))}
          </div>
        )}
      </Layout>
    </RequireAuth>
  );
}
